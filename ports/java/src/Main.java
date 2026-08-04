import java.nio.file.*;
import java.util.*;

public class Main {
    public static void main(String[] a) throws Exception {
        String root = ".", mode = "public"; boolean json = false, noGit = false, pii = false;
        for (int i = 0; i < a.length; i++) {
            switch (a[i]) {
                case "--mode": mode = a[++i]; break;
                case "--json": json = true; break;
                case "--no-gitignore": noGit = true; break;
                case "--pii": pii = true; break;
                default: if (!a[i].startsWith("-")) root = a[i];
            }
        }
        Scanner sc = new Scanner();
        sc.setMode(mode); sc.setRespectGitignore(!noGit); sc.setPii(pii);
        TreeMap<String, String> dec = sc.scan(Paths.get(root));
        if (json) {
            StringBuilder b = new StringBuilder("{\n");
            int i = 0;
            for (Map.Entry<String, String> e : dec.entrySet()) {
                b.append("  \"").append(e.getKey().replace("\\","\\\\").replace("\"","\\\""))
                 .append("\": \"").append(e.getValue()).append("\"");
                b.append(++i < dec.size() ? ",\n" : "\n");
            }
            b.append("}"); System.out.println(b);
        } else {
            Map<String,Integer> byRule = new TreeMap<>(); int incl = 0;
            for (String v : dec.values()) { if (v.equals("INCLUDE")) incl++; else byRule.merge(v,1,Integer::sum); }
            System.out.printf("pangolin-check (policy %s, mode=%s)%n", Policy.VERSION, mode);
            System.out.printf("  %d file(s) OK to share, %d excluded%n", incl, dec.size()-incl);
            for (Map.Entry<String,Integer> e : byRule.entrySet())
                System.out.printf("    %-18s %d%n", e.getKey(), e.getValue());
        }
        for (String v : dec.values()) if (v.startsWith("SEC-")) { System.exit(1); }
    }
}
