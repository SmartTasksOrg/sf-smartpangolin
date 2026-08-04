// PangolinScanner — native Java port of SmartPangolin (JavaBean-style API).
// Reproduces the path/content/local/gitignore rule IDs from the shared policy.
// Java regex supports lookahead + inline (?i)(?m), so no shim is needed.
import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.nio.file.*;
import java.util.*;
import java.util.regex.*;

public class Scanner {
    private String mode = "public";
    private boolean respectGitignore = true;
    private boolean pii = false;

    // --- JavaBean getters/setters ---
    public String getMode() { return mode; }
    public void setMode(String m) { this.mode = m; }
    public boolean isRespectGitignore() { return respectGitignore; }
    public void setRespectGitignore(boolean b) { this.respectGitignore = b; }
    public boolean isPii() { return pii; }
    public void setPii(boolean b) { this.pii = b; }

    private static final Set<String> DIRS = new HashSet<>(Arrays.asList(Policy.DIRS));
    private static final Set<String> ALLOW = new HashSet<>(Arrays.asList(Policy.ALLOW));
    private static final Pattern[] CONTENT = compile(Policy.CONTENT);
    private static final Pattern[] LOCAL = compile(Policy.LOCAL);
    private static final Pattern[] PII = compile(Policy.PII);
    private static final Pattern AUTHOR = (Policy.AUTHOR == null || Policy.AUTHOR.isEmpty()) ? null : Pattern.compile(Policy.AUTHOR);

    private static Pattern[] compile(Policy.Rule[] rules) {
        Pattern[] p = new Pattern[rules.length];
        for (int i = 0; i < rules.length; i++) p[i] = Pattern.compile(rules[i].regex);
        return p;
    }

    private static String globToRegex(String g) {
        StringBuilder b = new StringBuilder("^");
        for (int i = 0; i < g.length(); i++) {
            char c = g.charAt(i);
            if (c == '*') b.append(".*");
            else if (c == '?') b.append('.');
            else if (".+^$(){}|[]\\".indexOf(c) >= 0) b.append('\\').append(c);
            else b.append(c);
        }
        return b.append('$').toString();
    }
    private static final Pattern[][] PATH_RE = buildPathRe();
    private static Pattern[][] buildPathRe() {
        Pattern[][] out = new Pattern[Policy.PATH.length][];
        for (int i = 0; i < Policy.PATH.length; i++) {
            String[] gl = Policy.PATH[i].globs;
            Pattern[] ps = new Pattern[gl.length];
            for (int j = 0; j < gl.length; j++) ps[j] = Pattern.compile(globToRegex(gl[j]));
            out[i] = ps;
        }
        return out;
    }

    private String matchName(String name) {
        String low = name.toLowerCase();
        if (ALLOW.contains(low)) return null;
        for (int i = 0; i < Policy.PATH.length; i++)
            for (Pattern p : PATH_RE[i]) if (p.matcher(low).matches()) return Policy.PATH[i].id;
        return null;
    }

    private String classifyContent(String text) {
        int bestOff = Integer.MAX_VALUE, bestOrder = Integer.MAX_VALUE;
        String best = null;
        for (int i = 0; i < CONTENT.length; i++) {
            Matcher m = CONTENT[i].matcher(text);
            if (m.find() && (m.start() < bestOff || (m.start() == bestOff && i < bestOrder))) {
                bestOff = m.start(); bestOrder = i; best = Policy.CONTENT[i].id;
            }
        }
        if ("public".equals(mode)) {
            int base = CONTENT.length;
            for (int i = 0; i < LOCAL.length; i++) {
                Matcher m = LOCAL[i].matcher(text);
                if (m.find() && (m.start() < bestOff || (m.start() == bestOff && base + i < bestOrder))) {
                    bestOff = m.start(); bestOrder = base + i; best = Policy.LOCAL[i].id;
                }
            }
        }
        return best;
    }

    private static String lineOf(String t, int off) {
        int start = t.lastIndexOf('\n', off - 1) + 1;
        int end = t.indexOf('\n', off);
        return end < 0 ? t.substring(start) : t.substring(start, end + 1);
    }

    private String scanPII(String text) {
        int bestOff = Integer.MAX_VALUE; String best = null;
        for (int i = 0; i < PII.length; i++) {
            Matcher m = PII[i].matcher(text);
            while (m.find()) {
                if (AUTHOR != null && AUTHOR.matcher(lineOf(text, m.start())).find()) continue;
                if (m.start() < bestOff) { bestOff = m.start(); best = Policy.PII[i].id; }
            }
        }
        return best;
    }

    private static boolean isVenv(String n) {
        return n.startsWith("venv_") || n.endsWith("_venv") || n.endsWith("-venv");
    }

    /** Scan a tree; returns rel-path -> ruleId or "INCLUDE". */
    public TreeMap<String, String> scan(Path root) throws IOException {
        TreeMap<String, String> out = new TreeMap<>();
        List<Gitignore.Rule> gi = respectGitignore ? Gitignore.build(root) : Collections.emptyList();
        walk(root, root, gi, out);
        return out;
    }

    private void walk(Path root, Path dir, List<Gitignore.Rule> gi, Map<String, String> out) throws IOException {
        List<Path> entries = new ArrayList<>();
        try (DirectoryStream<Path> ds = Files.newDirectoryStream(dir)) {
            for (Path p : ds) entries.add(p);
        } catch (IOException e) { return; }
        Collections.sort(entries);
        for (Path p : entries) {
            String rel = root.relativize(p).toString().replace('\\', '/');
            if (Files.isDirectory(p)) {
                String low = p.getFileName().toString().toLowerCase();
                if (DIRS.contains(low) || low.equals("share_archive") || low.equals("extracted_source") || isVenv(low)) continue;
                if (!gi.isEmpty() && Gitignore.ignored(gi, rel, true)) { out.put(rel, "OPS-GITIGNORE"); continue; }
                walk(root, p, gi, out);
            } else {
                if (!gi.isEmpty() && Gitignore.ignored(gi, rel, false)) { out.put(rel, "OPS-GITIGNORE"); continue; }
                String pr = matchName(p.getFileName().toString());
                if (pr != null) { out.put(rel, pr); continue; }
                byte[] b;
                try { b = Files.readAllBytes(p); } catch (IOException e) { out.put(rel, "OPS-UNREADABLE"); continue; }
                boolean bin = false;
                for (int i = 0; i < Math.min(b.length, 8192); i++) if (b[i] == 0) { bin = true; break; }
                if (bin) { out.put(rel, "OPS-BINARY"); continue; }
                String text = new String(b, StandardCharsets.UTF_8).replaceAll("[\u200B-\u200D\u2060\uFEFF\u00AD]", "");
                String dec = classifyContent(text);
                if (dec == null) dec = "INCLUDE";
                if (dec.equals("INCLUDE") && pii) { String pv = scanPII(text); if (pv != null) dec = pv; }
                out.put(rel, dec);
            }
        }
    }
}
