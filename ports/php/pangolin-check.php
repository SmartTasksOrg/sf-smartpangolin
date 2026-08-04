<?php
/*
 * pangolin-check — native PHP port of SmartPangolin.
 * Loads the shared policy.json and reproduces the path/content/local/gitignore
 * rule IDs. PCRE supports lookahead and inline (?i)(?m), so patterns are used
 * verbatim. No Composer dependencies. Intended as a CI / pre-commit gate.
 */

final class Pangolin
{
    private array $policy;
    private array $dirNames = [];
    private array $allow = [];
    private array $content = [];   // [id, delimited-regex]
    private array $local = [];
    private array $pii = [];
    private ?string $authorRe = null;
    private const ARCHIVE = ['share_archive', 'extracted_source'];

    public function __construct(string $policyPath)
    {
        $this->policy = json_decode(file_get_contents($policyPath), true);
        foreach ($this->policy['dir_rules'] as $d) {
            foreach ($d['names'] as $n) $this->dirNames[strtolower($n)] = true;
        }
        foreach ($this->policy['path_allowlist'] as $a) $this->allow[strtolower($a)] = true;
        foreach ($this->policy['content_rules'] as $r) $this->content[] = [$r['id'], '~' . $r['regex'] . '~'];
        foreach ($this->policy['local_rules'] as $r)   $this->local[]   = [$r['id'], '~' . $r['regex'] . '~'];
        foreach (($this->policy['pii_rules'] ?? []) as $r) $this->pii[] = [$r['id'], '~' . $r['regex'] . '~'];
        if (!empty($this->policy['pii_author_regex'])) $this->authorRe = '~' . $this->policy['pii_author_regex'] . '~';
    }

    public function version(): string { return $this->policy['policy_version']; }

    private function matchName(string $name): ?string
    {
        $low = strtolower($name);
        if (isset($this->allow[$low])) return null;
        foreach ($this->policy['path_rules'] as $pr) {
            foreach ($pr['globs'] as $g) if (fnmatch($g, $low)) return $pr['id'];
        }
        return null;
    }

    private function firstOffset(string $rx, string $text): int
    {
        return preg_match($rx, $text, $m, PREG_OFFSET_CAPTURE) ? $m[0][1] : -1;
    }

    private function classifyContent(string $text, string $mode): ?string
    {
        $hits = [];
        foreach ($this->content as $i => [$id, $rx]) {
            $off = $this->firstOffset($rx, $text);
            if ($off >= 0) $hits[] = [$off, $i, $id];
        }
        if ($mode === 'public') {
            $base = count($this->content);
            foreach ($this->local as $i => [$id, $rx]) {
                $off = $this->firstOffset($rx, $text);
                if ($off >= 0) $hits[] = [$off, $base + $i, $id];
            }
        }
        if (!$hits) return null;
        usort($hits, fn($a, $b) => $a[0] <=> $b[0] ?: $a[1] <=> $b[1]);
        return $hits[0][2];
    }

    private static function isVenv(string $n): bool
    {
        return str_starts_with($n, 'venv_') || str_ends_with($n, '_venv') || str_ends_with($n, '-venv');
    }

    private function lineOf(string $t, int $off): string {
        $start = strrpos(substr($t, 0, $off), "\n"); $start = $start === false ? 0 : $start + 1;
        $end = strpos($t, "\n", $off);
        return $end === false ? substr($t, $start) : substr($t, $start, $end - $start + 1);
    }

    private function scanPII(string $text): ?string {
        $bestOff = PHP_INT_MAX; $best = null;
        foreach ($this->pii as [$id, $rx]) {
            if (preg_match_all($rx, $text, $ms, PREG_OFFSET_CAPTURE)) {
                foreach ($ms[0] as $m) {
                    if ($this->authorRe && preg_match($this->authorRe, $this->lineOf($text, $m[1]))) continue;
                    if ($m[1] < $bestOff) { $bestOff = $m[1]; $best = $id; }
                }
            }
        }
        return $best;
    }

    public function scan(string $root, string $mode = 'public', bool $respectGit = true, bool $pii = false): array
    {
        $gi = $respectGit ? Gitignore::build($root) : [];
        $out = [];
        $this->walk($root, $root, $gi, $mode, $pii, $out);
        ksort($out);
        return $out;
    }

    private function walk(string $root, string $dir, array $gi, string $mode, bool $pii, array &$out): void
    {
        $entries = @scandir($dir);
        if ($entries === false) return;
        sort($entries);
        foreach ($entries as $e) {
            if ($e === '.' || $e === '..') continue;
            $full = $dir . DIRECTORY_SEPARATOR . $e;
            $rel = ltrim(str_replace('\\', '/', substr($full, strlen($root))), '/');
            if (is_dir($full)) {
                $low = strtolower($e);
                if (isset($this->dirNames[$low]) || in_array($low, self::ARCHIVE, true) || self::isVenv($low)) continue;
                if ($gi && Gitignore::ignored($gi, $rel, true)) { $out[$rel] = 'OPS-GITIGNORE'; continue; }
                $this->walk($root, $full, $gi, $mode, $pii, $out);
            } else {
                if ($gi && Gitignore::ignored($gi, $rel, false)) { $out[$rel] = 'OPS-GITIGNORE'; continue; }
                if (($pr = $this->matchName($e)) !== null) { $out[$rel] = $pr; continue; }
                $buf = @file_get_contents($full);
                if ($buf === false) { $out[$rel] = 'OPS-UNREADABLE'; continue; }
                if (strpos(substr($buf, 0, 8192), "\0") !== false) { $out[$rel] = 'OPS-BINARY'; continue; }
                $buf = preg_replace('~[\x{200B}-\x{200D}\x{2060}\x{FEFF}\x{00AD}]~u', '', $buf);
                $dec = $this->classifyContent($buf, $mode) ?? 'INCLUDE';
                if ($dec === 'INCLUDE' && $pii) { $p = $this->scanPII($buf); if ($p !== null) $dec = $p; }
                $out[$rel] = $dec;
            }
        }
    }
}

final class Gitignore
{
    public static function build(string $root): array
    {
        $files = [];
        self::gather($root, $root, $files);
        usort($files, fn($a, $b) => $a[0] <=> $b[0] ?: strcmp($a[1], $b[1]));
        $rules = [];
        foreach ($files as [$depth, $base, $path]) {
            foreach (explode("\n", file_get_contents($path)) as $raw) {
                $line = rtrim($raw, " \t\r");
                if ($line === '' || str_starts_with(ltrim($line), '#')) continue;
                $rules[] = self::makeRule($line, $base);
            }
        }
        return $rules;
    }

    private static function gather(string $root, string $dir, array &$files): void
    {
        foreach (@scandir($dir) ?: [] as $e) {
            if ($e === '.' || $e === '..') continue;
            $full = $dir . DIRECTORY_SEPARATOR . $e;
            if (is_dir($full)) {
                if (in_array($e, ['.git', '.hg', '.svn'], true)) continue;
                self::gather($root, $full, $files);
            } elseif ($e === '.gitignore') {
                $base = ltrim(str_replace('\\', '/', substr($dir, strlen($root))), '/');
                $depth = $base === '' ? 0 : substr_count($base, '/') + 1;
                $files[] = [$depth, $base, $full];
            }
        }
    }

    private static function translate(string $p): string
    {
        $out = '';
        for ($i = 0; $i < strlen($p); $i++) {
            $c = $p[$i];
            if ($c === '*') {
                if (substr($p, $i, 3) === '**/') { $out .= '(?:.*/)?'; $i += 2; continue; }
                if (substr($p, $i, 2) === '**') { $out .= '.*'; $i += 1; continue; }
                $out .= '[^/]*';
            } elseif ($c === '?') $out .= '[^/]';
            elseif ($c === '/') $out .= '/';
            else $out .= preg_quote($c, '~');
        }
        return $out;
    }

    private static function makeRule(string $line, string $base): array
    {
        $negate = false; $dirOnly = false; $body = $line;
        if (str_starts_with($body, '!')) { $negate = true; $body = substr($body, 1); }
        if (str_ends_with($body, '/')) { $dirOnly = true; $body = substr($body, 0, -1); }
        $anchored = str_starts_with($body, '/') || str_contains(rtrim($body, '/'), '/');
        $body = ltrim($body, '/');
        $prefix = $base === '' ? '' : preg_quote($base . '/', '~');
        $frag = self::translate($body);
        $rx = $anchored ? '~^' . $prefix . $frag . '(?:/.*)?$~'
                        : '~^' . $prefix . '(?:.*/)?' . $frag . '(?:/.*)?$~';
        return ['re' => $rx, 'negate' => $negate, 'dirOnly' => $dirOnly];
    }

    public static function ignored(array $rules, string $rel, bool $isDir): bool
    {
        $rel = ltrim(str_replace('\\', '/', $rel), './');
        $decision = false;
        foreach ($rules as $r) {
            if ($r['dirOnly'] && !$isDir) continue;
            if (preg_match($r['re'], $rel)) $decision = !$r['negate'];
        }
        return $decision;
    }
}

// ---- CLI ----
$args = array_slice($argv, 1);
$root = '.'; $mode = 'public'; $json = false; $noGit = false; $pii = false;
for ($i = 0; $i < count($args); $i++) {
    $a = $args[$i];
    if ($a === '--mode') $mode = $args[++$i];
    elseif ($a === '--json') $json = true;
    elseif ($a === '--no-gitignore') $noGit = true;
    elseif ($a === '--pii') $pii = true;
    elseif ($a[0] !== '-') $root = $a;
}
$p = new Pangolin(__DIR__ . '/policy.json');
$dec = $p->scan($root, $mode, !$noGit, $pii);
if ($json) {
    echo json_encode($dec, JSON_PRETTY_PRINT | JSON_UNESCAPED_SLASHES), "\n";
} else {
    $byRule = []; $incl = 0;
    foreach ($dec as $v) { if ($v === 'INCLUDE') $incl++; else $byRule[$v] = ($byRule[$v] ?? 0) + 1; }
    printf("pangolin-check (policy %s, mode=%s)\n", $p->version(), $mode);
    printf("  %d file(s) OK to share, %d excluded\n", $incl, count($dec) - $incl);
    ksort($byRule);
    foreach ($byRule as $r => $n) printf("    %-18s %d\n", $r, $n);
}
foreach ($dec as $v) if (str_starts_with($v, 'SEC-')) exit(1);
