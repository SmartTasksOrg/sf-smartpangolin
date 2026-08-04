import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.nio.file.*;
import java.util.*;
import java.util.regex.Pattern;

public final class Gitignore {
    public static final class Rule {
        final Pattern re; final boolean negate, dirOnly;
        Rule(Pattern re, boolean n, boolean d) { this.re = re; negate = n; dirOnly = d; }
    }

    private static String translate(String p) {
        StringBuilder b = new StringBuilder();
        for (int i = 0; i < p.length(); i++) {
            char c = p.charAt(i);
            if (c == '*') {
                if (p.startsWith("**/", i)) { b.append("(?:.*/)?"); i += 2; continue; }
                if (p.startsWith("**", i)) { b.append(".*"); i += 1; continue; }
                b.append("[^/]*");
            } else if (c == '?') b.append("[^/]");
            else if (c == '/') b.append('/');
            else b.append(Pattern.quote(String.valueOf(c)));
        }
        return b.toString();
    }

    static Rule makeRule(String line, String base) {
        boolean negate = false, dirOnly = false;
        String body = line;
        if (body.startsWith("!")) { negate = true; body = body.substring(1); }
        if (body.endsWith("/")) { dirOnly = true; body = body.substring(0, body.length() - 1); }
        String trimmed = body.replaceAll("/+$", "");
        boolean anchored = body.startsWith("/") || trimmed.contains("/");
        body = body.replaceAll("^/+", "");
        String prefix = base.isEmpty() ? "" : Pattern.quote(base + "/");
        String frag = translate(body);
        String rx = anchored ? "^" + prefix + frag + "(?:/.*)?$"
                             : "^" + prefix + "(?:.*/)?" + frag + "(?:/.*)?$";
        return new Rule(Pattern.compile(rx), negate, dirOnly);
    }

    public static List<Rule> build(Path root) throws IOException {
        List<Path> files = new ArrayList<>();
        Files.walk(root)
             .filter(p -> !containsVcs(root, p))
             .filter(p -> p.getFileName() != null && p.getFileName().toString().equals(".gitignore"))
             .forEach(files::add);
        files.sort(Comparator.comparingInt((Path p) -> depth(root, p)).thenComparing(Object::toString));
        List<Rule> rules = new ArrayList<>();
        for (Path f : files) {
            String base = root.relativize(f.getParent()).toString().replace('\\', '/');
            if (base.equals(".")) base = "";
            for (String raw : new String(Files.readAllBytes(f), StandardCharsets.UTF_8).split("\n", -1)) {
                String line = raw.replaceAll("[ \t\r]+$", "");
                if (line.isEmpty() || line.stripLeading().startsWith("#")) continue;
                rules.add(makeRule(line, base));
            }
        }
        return rules;
    }
    private static boolean containsVcs(Path root, Path p) {
        for (Path seg : root.relativize(p)) {
            String s = seg.toString();
            if (s.equals(".git") || s.equals(".hg") || s.equals(".svn")) return true;
        }
        return false;
    }
    private static int depth(Path root, Path f) {
        String base = root.relativize(f.getParent()).toString().replace('\\', '/');
        if (base.equals(".") || base.isEmpty()) return 0;
        return (int) base.chars().filter(c -> c == '/').count() + 1;
    }

    public static boolean ignored(List<Rule> rules, String rel, boolean isDir) {
        rel = rel.replace('\\', '/');
        if (rel.startsWith("./")) rel = rel.substring(2);
        boolean decision = false;
        for (Rule r : rules) {
            if (r.dirOnly && !isDir) continue;
            if (r.re.matcher(rel).matches()) decision = !r.negate;
        }
        return decision;
    }
}
