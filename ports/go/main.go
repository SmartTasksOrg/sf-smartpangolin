// pangolin-check — native Go port of SmartPangolin.
// Loads the shared policy.json and reproduces the path/content/local/gitignore
// rule IDs. RE2 has no lookahead, so the two lookahead rules are shimmed with a
// base pattern + a code-level post-filter. Zero third-party dependencies.
package main

import (
	_ "embed"
	"encoding/json"
	"fmt"
	"os"
	"path/filepath"
	"regexp"
	"sort"
	"strings"
)

//go:embed policy.json
var policyBytes []byte

type Policy struct {
	PolicyVersion string `json:"policy_version"`
	PathRules     []struct {
		ID    string   `json:"id"`
		Globs []string `json:"globs"`
	} `json:"path_rules"`
	DirRules []struct {
		Names []string `json:"names"`
	} `json:"dir_rules"`
	ContentRules []struct {
		ID    string `json:"id"`
		Regex string `json:"regex"`
	} `json:"content_rules"`
	LocalRules []struct {
		ID    string `json:"id"`
		Regex string `json:"regex"`
	} `json:"local_rules"`
	PiiRules []struct {
		ID    string `json:"id"`
		Regex string `json:"regex"`
	} `json:"pii_rules"`
	PiiAuthorRegex string `json:"pii_author_regex"`
	PathAllowlist []string `json:"path_allowlist"`
}

type rule struct {
	id     string
	re     *regexp.Regexp
	filter func(match string) bool // nil => always valid
}

var (
	policy      Policy
	dirNames    = map[string]bool{}
	allow       = map[string]bool{}
	contentRule []rule
	localRule   []rule
	piiRule     []rule
	authorRe    *regexp.Regexp
)

// RE2 shim: strip a lookahead group, return (cleaned pattern, post-filter).
func shim(id, pat string) (string, func(string) bool) {
	switch id {
	case "SEC-CONT-OPENAI":
		return `\bsk-(?:proj-)?[A-Za-z0-9_\-]{32,}\b`,
			func(m string) bool { return !strings.HasPrefix(m, "sk-ant-") }
	case "LOC-NIXUSER":
		return `/(?:home|Users)/[A-Za-z0-9._\-]+/`,
			func(m string) bool {
				parts := strings.Split(strings.Trim(m, "/"), "/")
				if len(parts) >= 2 {
					u := parts[1]
					return !(u == "runner" || u == "user" || u == "ubuntu")
				}
				return true
			}
	}
	return pat, nil
}

func compile(id, pat string) rule {
	clean, f := shim(id, pat)
	return rule{id: id, re: regexp.MustCompile(clean), filter: f}
}

func loadPolicy() {
	if err := json.Unmarshal(policyBytes, &policy); err != nil {
		panic(err)
	}
	for _, d := range policy.DirRules {
		for _, n := range d.Names {
			dirNames[strings.ToLower(n)] = true
		}
	}
	for _, a := range policy.PathAllowlist {
		allow[strings.ToLower(a)] = true
	}
	for _, r := range policy.ContentRules {
		contentRule = append(contentRule, compile(r.ID, r.Regex))
	}
	for _, r := range policy.LocalRules {
		localRule = append(localRule, compile(r.ID, r.Regex))
	}
	for _, r := range policy.PiiRules {
		piiRule = append(piiRule, compile(r.ID, r.Regex))
	}
	if policy.PiiAuthorRegex != "" {
		authorRe = regexp.MustCompile(policy.PiiAuthorRegex)
	}
}

func matchName(name string) string {
	low := strings.ToLower(name)
	if allow[low] {
		return ""
	}
	for _, pr := range policy.PathRules {
		for _, g := range pr.Globs {
			if ok, _ := filepath.Match(g, low); ok {
				return pr.ID
			}
		}
	}
	return ""
}

// first valid match offset for a rule, or -1
func firstMatch(r rule, text string) int {
	locs := r.re.FindAllStringIndex(text, -1)
	for _, l := range locs {
		if r.filter == nil || r.filter(text[l[0]:l[1]]) {
			return l[0]
		}
	}
	return -1
}

func classifyContent(text, mode string) string {
	type hit struct {
		off, order int
		id         string
	}
	var hits []hit
	for i, r := range contentRule {
		if off := firstMatch(r, text); off >= 0 {
			hits = append(hits, hit{off, i, r.id})
		}
	}
	if mode == "public" {
		base := len(contentRule)
		for i, r := range localRule {
			if off := firstMatch(r, text); off >= 0 {
				hits = append(hits, hit{off, base + i, r.id})
			}
		}
	}
	if len(hits) == 0 {
		return ""
	}
	sort.Slice(hits, func(a, b int) bool {
		if hits[a].off != hits[b].off {
			return hits[a].off < hits[b].off
		}
		return hits[a].order < hits[b].order
	})
	return hits[0].id
}

func isVenv(n string) bool {
	return strings.HasPrefix(n, "venv_") || strings.HasSuffix(n, "_venv") || strings.HasSuffix(n, "-venv")
}

func lineOf(text string, off int) string {
	start := strings.LastIndex(text[:off], "\n") + 1
	end := strings.IndexByte(text[off:], '\n')
	if end < 0 { return text[start:] }
	return text[start : off+end+1]
}

func stripInvisible(s string) string {
	return strings.Map(func(r rune) rune {
		switch r {
		case 0x200B, 0x200C, 0x200D, 0x2060, 0xFEFF, 0x00AD:
			return -1
		}
		return r
	}, s)
}

func scanPII(text string) string {
	bestOff, best := 1<<62, ""
	for _, r := range piiRule {
		for _, loc := range r.re.FindAllStringIndex(text, -1) {
			if authorRe != nil && authorRe.MatchString(lineOf(text, loc[0])) { continue }
			if loc[0] < bestOff { bestOff, best = loc[0], r.id }
		}
	}
	return best
}

func scan(root, mode string, respectGit, pii bool) map[string]string {
	gi := []giRule{}
	if respectGit {
		gi = buildGitignore(root)
	}
	out := map[string]string{}
	filepath.WalkDir(root, func(p string, d os.DirEntry, err error) error {
		if err != nil {
			return nil
		}
		rel, _ := filepath.Rel(root, p)
		rel = filepath.ToSlash(rel)
		if rel == "." {
			return nil
		}
		if d.IsDir() {
			low := strings.ToLower(d.Name())
			if dirNames[low] || low == "share_archive" || low == "extracted_source" || isVenv(low) {
				return filepath.SkipDir
			}
			if len(gi) > 0 && giIgnored(gi, rel, true) {
				out[rel] = "OPS-GITIGNORE"
				return filepath.SkipDir
			}
			return nil
		}
		if len(gi) > 0 && giIgnored(gi, rel, false) {
			out[rel] = "OPS-GITIGNORE"
			return nil
		}
		if id := matchName(d.Name()); id != "" {
			out[rel] = id
			return nil
		}
		b, e := os.ReadFile(p)
		if e != nil {
			out[rel] = "OPS-UNREADABLE"
			return nil
		}
		for _, c := range b[:min(len(b), 8192)] {
			if c == 0 {
				out[rel] = "OPS-BINARY"
				return nil
			}
		}
		text := stripInvisible(string(b))
		dec := classifyContent(text, mode)
		if dec == "" { dec = "INCLUDE" }
		if dec == "INCLUDE" && pii { if p := scanPII(text); p != "" { dec = p } }
		out[rel] = dec
		return nil
	})
	return out
}

func main() {
	root, mode, jsonOut, noGit, pii := ".", "public", false, false, false
	for i := 1; i < len(os.Args); i++ {
		a := os.Args[i]
		switch {
		case a == "--mode":
			i++
			mode = os.Args[i]
		case a == "--json":
			jsonOut = true
		case a == "--no-gitignore":
			noGit = true
		case a == "--pii":
			pii = true
		case !strings.HasPrefix(a, "-"):
			root = a
		}
	}
	loadPolicy()
	dec := scan(root, mode, !noGit, pii)
	if jsonOut {
		b, _ := json.MarshalIndent(dec, "", "  ")
		fmt.Println(string(b))
		return
	}
	byRule := map[string]int{}
	incl := 0
	for _, v := range dec {
		if v == "INCLUDE" {
			incl++
		} else {
			byRule[v]++
		}
	}
	fmt.Printf("pangolin-check (policy %s, mode=%s)\n", policy.PolicyVersion, mode)
	fmt.Printf("  %d file(s) OK to share, %d excluded\n", incl, len(dec)-incl)
	keys := []string{}
	for k := range byRule {
		keys = append(keys, k)
	}
	sort.Strings(keys)
	for _, k := range keys {
		fmt.Printf("    %-18s %d\n", k, byRule[k])
	}
	for _, v := range dec {
		if strings.HasPrefix(v, "SEC-") {
			os.Exit(1)
		}
	}
}
