'use strict';
/*
 * pangolin-check — native Node scanner.
 * Loads the shared policy.json (the contract) and reproduces SmartPangolin's
 * path / content / local / gitignore rule IDs. Zero runtime dependencies.
 *
 * This is a CI / pre-publish gate. Never ship a secret scanner to the browser.
 */
const fs = require('fs');
const path = require('path');
const POLICY = require('./policy.json');

const DIR_NAMES = new Set();
for (const d of POLICY.dir_rules) for (const n of d.names) DIR_NAMES.add(n.toLowerCase());
const ARCHIVE_DIRS = new Set(['share_archive', 'extracted_source']);
const ALLOW = new Set(POLICY.path_allowlist.map(s => s.toLowerCase()));

function globToRe(g) {
  let re = '^';
  for (let i = 0; i < g.length; i++) {
    const c = g[i];
    if (c === '*') re += '.*';
    else if (c === '?') re += '.';
    else if ('.+^${}()|[]\\'.includes(c)) re += '\\' + c;
    else re += c;
  }
  return new RegExp(re + '$');
}

/* Python-style inline flags (?i)(?m) -> JS RegExp flags */
function compilePy(pattern) {
  let flags = '';
  pattern = pattern.replace(/\(\?([ims]+)\)/g, (_, f) => {
    for (const c of f) if (!flags.includes(c)) flags += c;
    return '';
  });
  return new RegExp(pattern, flags);
}

const PATH_RE = POLICY.path_rules.map(r => ({ id: r.id, res: r.globs.map(globToRe) }));
const CONTENT_RE = POLICY.content_rules.map(r => ({ id: r.id, re: compilePy(r.regex) }));
const LOCAL_RE = POLICY.local_rules.map(r => ({ id: r.id, re: compilePy(r.regex) }));
const PII_RE = (POLICY.pii_rules || []).map(r => ({ id: r.id, re: new RegExp(r.regex, "g") }));
const AUTHOR_RE = POLICY.pii_author_regex ? compilePy(POLICY.pii_author_regex) : null;
function lineStarts(t){ const s=[0]; let p=0; for (const ln of t.split(/(?<=\n)/)){ p+=ln.length; s.push(p);} return s; }
function lineOf(t, off, starts){ for (let i=0;i<starts.length-1;i++){ if (starts[i]<=off && off<starts[i+1]) return t.slice(starts[i], starts[i+1]); } return ""; }
function scanPII(text){
  const starts = lineStarts(text); const hits = [];
  for (const r of PII_RE){ r.re.lastIndex=0; let m;
    while ((m = r.re.exec(text)) !== null){
      if (AUTHOR_RE && AUTHOR_RE.test(lineOf(text, m.index, starts))) continue;
      hits.push([m.index, r.id]);
    } }
  if (!hits.length) return null; hits.sort((a,b)=>a[0]-b[0]); return hits[0][1];
}


/* ---------------- gitignore (subset, mirrors the Python matcher) ---------- */
function translate(p) {
  let out = '', i = 0;
  while (i < p.length) {
    const c = p[i];
    if (c === '*') {
      if (p.slice(i, i + 3) === '**/') { out += '(?:.*/)?'; i += 3; continue; }
      if (p.slice(i, i + 2) === '**') { out += '.*'; i += 2; continue; }
      out += '[^/]*';
    } else if (c === '?') out += '[^/]';
    else if (c === '/') out += '/';
    else out += c.replace(/[.+^${}()|[\]\\]/g, '\\$&');
    i++;
  }
  return out;
}
function makeRule(line, base) {
  let negate = false, dirOnly = false, body = line;
  if (body.startsWith('!')) { negate = true; body = body.slice(1); }
  if (body.endsWith('/')) { dirOnly = true; body = body.slice(0, -1); }
  const anchored = body.startsWith('/') || body.replace(/\/+$/, '').includes('/');
  body = body.replace(/^\/+/, '');
  const prefix = base ? base.replace(/[.+^${}()|[\]\\]/g, '\\$&') + '/' : '';
  const frag = translate(body);
  const re = anchored
    ? new RegExp('^' + prefix + frag + '(?:/.*)?$')
    : new RegExp('^' + prefix + '(?:.*/)?' + frag + '(?:/.*)?$');
  return { re, negate, dirOnly };
}
function buildGitignore(root) {
  const rules = [];
  const found = [];
  (function walk(dir) {
    let ents; try { ents = fs.readdirSync(dir, { withFileTypes: true }); } catch { return; }
    const rel = path.relative(root, dir).split(path.sep).join('/');
    const base = rel === '' ? '' : rel;
    for (const e of ents) {
      if (e.isDirectory()) {
        if (['.git', '.hg', '.svn'].includes(e.name)) continue;
        walk(path.join(dir, e.name));
      } else if (e.name === '.gitignore') {
        found.push([base.split('/').filter(Boolean).length, base, path.join(dir, e.name)]);
      }
    }
  })(root);
  found.sort((a, b) => a[0] - b[0] || a[1].localeCompare(b[1]));
  for (const [, base, file] of found) {
    for (const raw of fs.readFileSync(file, 'utf8').split(/\r?\n/)) {
      const line = raw.replace(/\s+$/, '');
      if (!line || line.trimStart().startsWith('#')) continue;
      rules.push(makeRule(line, base));
    }
  }
  return rules;
}
function ignored(rules, rel, isDir) {
  rel = rel.split(path.sep).join('/').replace(/^\.\//, '');
  let decision = false;
  for (const r of rules) {
    if (r.dirOnly && !isDir) continue;
    if (r.re.test(rel)) decision = !r.negate;
  }
  return decision;
}

/* ---------------- classification ---------------------------------------- */
function classifyName(name) {
  const low = name.toLowerCase();
  if (ALLOW.has(low)) return null;
  for (const r of PATH_RE) for (const re of r.res) if (re.test(low)) return r.id;
  return null;
}
function classifyContent(text, mode) {
  const hits = [];
  CONTENT_RE.forEach((r, order) => { const m = r.re.exec(text); if (m) hits.push([m.index, order, r.id]); });
  if (mode === 'public') {
    const base = CONTENT_RE.length;
    LOCAL_RE.forEach((r, i) => { const m = r.re.exec(text); if (m) hits.push([m.index, base + i, r.id]); });
  }
  if (!hits.length) return null;
  hits.sort((a, b) => a[0] - b[0] || a[1] - b[1]);
  return hits[0][2];
}

function scan(root, opts = {}) {
  const mode = opts.mode || 'public';
  const gi = opts.respectGitignore === false ? [] : buildGitignore(root);
  const decisions = {};
  (function walk(dir) {
    let ents; try { ents = fs.readdirSync(dir, { withFileTypes: true }); } catch { return; }
    for (const e of ents) {
      const full = path.join(dir, e.name);
      const rel = path.relative(root, full).split(path.sep).join('/');
      if (e.isDirectory()) {
        const low = e.name.toLowerCase();
        if (DIR_NAMES.has(low) || ARCHIVE_DIRS.has(low) ||
            low.startsWith('venv_') || low.endsWith('_venv') || low.endsWith('-venv')) continue;
        if (gi.length && ignored(gi, rel, true)) { decisions[rel] = 'OPS-GITIGNORE'; continue; }
        walk(full);
      } else {
        if (gi.length && ignored(gi, rel, false)) { decisions[rel] = 'OPS-GITIGNORE'; continue; }
        const pr = classifyName(e.name);
        if (pr) { decisions[rel] = pr; continue; }
        let text = '';
        try {
          const buf = fs.readFileSync(full);
          if (buf.includes(0)) { decisions[rel] = 'OPS-BINARY'; continue; }
          text = buf.toString('utf8').replace(/[\u200B-\u200D\u2060\uFEFF\u00AD]/g, '');
        } catch { decisions[rel] = 'OPS-UNREADABLE'; continue; }
        const cr = classifyContent(text, mode);
        let dec = cr || 'INCLUDE';
        if (dec === 'INCLUDE' && opts.pii) { const p = scanPII(text); if (p) dec = p; }
        decisions[rel] = dec;
      }
    }
  })(root);
  return decisions;
}

module.exports = { scan, POLICY_VERSION: POLICY.policy_version };
