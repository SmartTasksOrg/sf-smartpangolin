# PangolinScanner (Java)

Native Java port. `java.util.regex` supports lookahead and inline `(?i)(?m)`,
so patterns are used verbatim. The ruleset is compiled into `Policy.java`
(generated from `spec/policy.json` by `tools/export_policy.py`).

## Build & run
```bash
javac -d out src/*.java
java -cp out Main <path> [--mode public|private] [--json] [--no-gitignore]
```

## JavaBean API
```java
Scanner sc = new Scanner();
sc.setMode("public");
sc.setRespectGitignore(true);
java.util.TreeMap<String,String> decisions = sc.scan(java.nio.file.Paths.get("."));
```

A `pom.xml` can wire `javac`/exec into a Maven `verify` phase; the class has no
third-party dependencies.
