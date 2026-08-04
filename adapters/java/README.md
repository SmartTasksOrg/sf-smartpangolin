# SmartPangolin — Java

Wire the Python tool into Maven/Gradle as a verification step, or port the
scanner against the policy spec.

## Maven exec example

```xml
<plugin>
  <groupId>org.codehaus.mojo</groupId>
  <artifactId>exec-maven-plugin</artifactId>
  <executions>
    <execution>
      <id>pangolin-guard</id>
      <phase>verify</phase>
      <goals><goal>exec</goal></goals>
      <configuration>
        <executable>pango</executable>
        <arguments>
          <argument>pack</argument><argument>--root</argument><argument>.</argument>
          <argument>--share</argument><argument>public</argument>
          <argument>--dry-run</argument>
        </arguments>
      </configuration>
    </execution>
  </executions>
</plugin>
```

## Consume an artifact (works today)

`java.util.zip.ZipFile` + any JSON lib reads `_SHARE/MANIFEST.json`; the
`SHA256SUMS` file verifies each entry with `MessageDigest.getInstance("SHA-256")`.

## Port the scanner (roadmap)

`java.util.regex` handles the anchored patterns from `pango policy`.
Reproduce the `content_sha256` recipe from
[../../docs/porting.md](../../docs/porting.md) to stay byte-conformant.

> **Update:** a real, conformance-tested native port now lives in `ports/java/`.
