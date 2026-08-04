package main

import (
	"os"
	"path/filepath"
	"regexp"
	"sort"
	"strings"
)

type giRule struct {
	re      *regexp.Regexp
	negate  bool
	dirOnly bool
}

func giTranslate(p string) string {
	var b strings.Builder
	for i := 0; i < len(p); i++ {
		c := p[i]
		if c == '*' {
			if strings.HasPrefix(p[i:], "**/") {
				b.WriteString("(?:.*/)?")
				i += 2
				continue
			}
			if strings.HasPrefix(p[i:], "**") {
				b.WriteString(".*")
				i++
				continue
			}
			b.WriteString("[^/]*")
		} else if c == '?' {
			b.WriteString("[^/]")
		} else if c == '/' {
			b.WriteByte('/')
		} else {
			b.WriteString(regexp.QuoteMeta(string(c)))
		}
	}
	return b.String()
}

func giMakeRule(line, base string) giRule {
	negate, dirOnly, body := false, false, line
	if strings.HasPrefix(body, "!") {
		negate = true
		body = body[1:]
	}
	if strings.HasSuffix(body, "/") {
		dirOnly = true
		body = strings.TrimSuffix(body, "/")
	}
	anchored := strings.HasPrefix(body, "/") || strings.Contains(strings.TrimRight(body, "/"), "/")
	body = strings.TrimLeft(body, "/")
	prefix := ""
	if base != "" {
		prefix = regexp.QuoteMeta(base + "/")
	}
	frag := giTranslate(body)
	var re *regexp.Regexp
	if anchored {
		re = regexp.MustCompile("^" + prefix + frag + "(?:/.*)?$")
	} else {
		re = regexp.MustCompile("^" + prefix + "(?:.*/)?" + frag + "(?:/.*)?$")
	}
	return giRule{re: re, negate: negate, dirOnly: dirOnly}
}

func buildGitignore(root string) []giRule {
	type found struct {
		depth int
		base  string
		path  string
	}
	var fs []found
	filepath.WalkDir(root, func(p string, d os.DirEntry, err error) error {
		if err != nil {
			return nil
		}
		if d.IsDir() {
			n := d.Name()
			if n == ".git" || n == ".hg" || n == ".svn" {
				return filepath.SkipDir
			}
			return nil
		}
		if d.Name() == ".gitignore" {
			rel, _ := filepath.Rel(root, filepath.Dir(p))
			rel = filepath.ToSlash(rel)
			if rel == "." {
				rel = ""
			}
			depth := 0
			if rel != "" {
				depth = strings.Count(rel, "/") + 1
			}
			fs = append(fs, found{depth, rel, p})
		}
		return nil
	})
	sort.Slice(fs, func(a, b int) bool {
		if fs[a].depth != fs[b].depth {
			return fs[a].depth < fs[b].depth
		}
		return fs[a].base < fs[b].base
	})
	var rules []giRule
	for _, f := range fs {
		data, err := os.ReadFile(f.path)
		if err != nil {
			continue
		}
		for _, raw := range strings.Split(string(data), "\n") {
			line := strings.TrimRight(raw, " \t\r")
			if line == "" || strings.HasPrefix(strings.TrimLeft(line, " \t"), "#") {
				continue
			}
			rules = append(rules, giMakeRule(line, f.base))
		}
	}
	return rules
}

func giIgnored(rules []giRule, rel string, isDir bool) bool {
	rel = strings.TrimPrefix(filepath.ToSlash(rel), "./")
	decision := false
	for _, r := range rules {
		if r.dirOnly && !isDir {
			continue
		}
		if r.re.MatchString(rel) {
			decision = !r.negate
		}
	}
	return decision
}
