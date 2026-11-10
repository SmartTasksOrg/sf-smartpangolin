<!-- mcp-name: io.github.smarttasksorg/sf-smartpangolin -->
<h1 align="center">🦔 SmartPangolin</h1>
<p align="center"><b>Scan before you share. Stop leaking secrets into AI models, agents, and tools.</b></p>
<p align="center">
  <a href="https://iaiso.org">IAIso §1 · Secure Sharing</a> ·
  <a href="https://smarttasks.cloud">SmartTasks.cloud</a> ·
  <a href="#part-of-the-smart-family">the Smart* family</a>
</p>

---

## You paste your repo into an AI. What did you just leak?

As AI reshapes how we work, a new gap opens: feeding code/docs to ai leaks secrets, keys, and internal detail. **SmartPangolin** closes it —
`scan` at the exact moment the gap bites, and it works the second you clone it
(a synthetic demo ships in `demo/`).

## Install

```bash
python -m pip install sf-smartpangolin
sf-smartpangolin --demo
```

Every file of `sf-smartpangolin` on PyPI is built and published by this repository's release
workflow (`.github/workflows/release.yml`, PyPI trusted publishing) and carries a
provenance attestation that names this repository and that workflow; PyPI shows
it under "Verified details". The same workflow records a GitHub attestation for
the same files, which you can check with
`gh attestation verify <file> --repo SmartTasksOrg/sf-smartpangolin`. A release file without
that provenance is not ours, and neither is a package called `smartpangolin` (without
`sf-`) on any registry. The PyPI package `pango` is a placeholder published by someone else; it is not this tool.

Version 3.0.0 (published 2026-10-09) is the first release under this name.

To install from a clone instead (Python 3.8 or later):

```bash
git clone https://github.com/SmartTasksOrg/sf-smartpangolin
cd sf-smartpangolin
python -m venv .venv
. .venv/bin/activate          # Windows PowerShell: .\.venv\Scripts\Activate.ps1
python -m pip install .
sf-smartpangolin --demo
```

### Text files instead of a zip

The zip is the default. For a model that does not take a zip, `--format txt` writes the same content as
plain `.txt` parts, with checksums and the share report next to them; `--format both` gives both. Limits per
part are hard limits: a large file is split at line boundaries rather than overflowing a part.

```bash
sf-smartpangolin pack --root . --format txt --max-chars 400000 --max-files 10
sf-smartpangolin verify extracted_source/share_archive/<name>      # checks every part
```

`--max-bytes` limits each part in bytes instead. If the share needs more parts than `--max-files`, nothing is
written and the message says which limit would fit. All options: [docs/cli.md](docs/cli.md).

## Status

- **Version 3.1.0, experimental.** A deterministic secret-scanning packager with 43 tests, including red-team regression cases; [SECURITY.md](SECURITY.md#detection-scope--limitations-be-honest-with-yourself) lists what it does not detect.
- **Published:** PyPI `sf-smartpangolin` (see Install). Nothing else is published.
- **Tested:** lint, the 31 tests and a `sf-smartpangolin pack` dry run on Linux, Windows and macOS with Python 3.8, 3.10 and 3.12, on every push to master and every pull request (`.github/workflows/ci.yml`).
- **Not tested:** Python 3.9, 3.11 and 3.13.
- **Ports:** Go, Java, Node and PHP ports in `ports/` are checked against the Python reference by `ports/conformance/run.sh` (run by hand, not in CI); they are not published on any registry.
- **Security review:** none independent. Report vulnerabilities as described in [SECURITY.md](SECURITY.md).

## Run it in your stack

| Where you work | How you run it |
|---|---|
| **Python** | `python -m pip install sf-smartpangolin` |
| **Go · Java · Node · PHP** | native ports in [`ports/`](ports/), each verified against the Python reference by [`ports/conformance/run.sh`](ports/conformance/run.sh) |
| **LangChain · LlamaIndex · function-calling · MCP** | drop-in integration kits in [`kits/`](kits/) |
| **Flowise · VS Code** | ready-made wrappers in [`integrations/`](integrations/), all calling one `adapter.py` |
| **CI / pre-commit** | add the hook from [`.pre-commit-hooks.yaml`](.pre-commit-hooks.yaml) |

## What's in this repo

- **Core engine** — [`src/sf_smartpangolin/`](src/sf_smartpangolin/): scan() -> ScanResult. Deterministic, dependency-free.
- **CLI** — `sf-smartpangolin pack | verify | triage | tree | purge | policy | init`, the full fail-closed packager. `sf-smartpangolin --demo` runs the quick demo; the family `scan()` API is the lightweight scanner.
- **Language ports** — [`ports/`](ports/): native Go, Java, Node, PHP implementations that reproduce the Python reference, with a shared conformance harness.
- **Integration kits** — [`kits/`](kits/): LangChain, LlamaIndex, function-calling, MCP, CI, and pre-commit starters.
- **Adapters** — [`adapters/`](adapters/): GitHub Action and language adapters.
- **Framework integrations** — [`integrations/`](integrations/): Flowise, VS Code extension — each a thin wrapper over one `adapter.py` bound to the core.
- **MCP server** — `sf-smartpangolin-mcp` console script, for agentic/AI-coding clients.
- **Reference docs** — [`docs/`](docs/): 10 documents (CLI, policy, design, FAQ, porting…).
- **Also included** — a runnable [`demo/`](demo/), [`examples/`](examples/), the IAIso mapping [`spec/iaiso-map.json`](spec/iaiso-map.json), a browser [`site/playground.html`](site/playground.html), plus public smoke tests in `tests/`.

## How it works

Rule IDs are namespaced `SEC-*` so output looks kin to the rest of the family
(SmartCheck's `CHECK-*`, SmartSeal's `SEAL-*`, etc.). Deterministic, dependency-free, fail-loud.

### The data objects (UML)

These are real dataclasses in [`src/sf_smartpangolin/models.py`](src/sf_smartpangolin/models.py) — the
diagram and the code are the same thing:

```mermaid
classDiagram
    class Finding {
      +rule: str
      +severity: str
      +path: str
      +detail: str
    }
    class Policy {
      +rules: list[str]
      +hash: str
    }
    class ScanResult {
      +findings: list[Finding]
      +verdict: str
      +policy_hash: str
    }
    note "Implements IAIso §1 · Secure Sharing"
```

## Where it sits in the architecture

<!-- smart-family-diagram:start -->
<!-- generated by fleet-docs from family.json; change family.json, not this block -->

Where SmartPangolin sits among the Smart* tools and the IAIso standard:

```mermaid
graph LR
    IAIso(["IAIso standard"]):::std
    subgraph SEC["Implement an IAIso section"]
        direction TB
        SmartPangolin["SmartPangolin<br/>§1 · Secure Sharing"]:::tool
        SmartCheck["SmartCheck<br/>§2 · Verification"]:::tool
        SmartSeal["SmartSeal<br/>§3 · Provenance"]:::tool
        SmartPrompt["SmartPrompt<br/>§4 · Context"]:::tool
        SmartRoute["SmartRoute<br/>§5 · Orchestration"]:::tool
        SmartMoat["SmartMoat<br/>§6 · Workforce"]:::tool
        SmartStandard["SmartStandard<br/>§7 · Standards"]:::tool
        SmartSim["SmartSim<br/>§8 · Foresight"]:::tool
        SmartFeed["SmartFeed<br/>§9 · Awareness"]:::tool
    end
    subgraph MORE["More Smart* tools"]
        direction TB
        SmartFabric["SmartFabric<br/>§0 · Fabric"]:::tool
        SmartDelegate["SmartDelegate<br/>§10 · Delegation (working label)"]:::tool
        SmartPolicyTranslator["SmartPolicyTranslator"]:::tool
        SmartAgency["SmartAgency"]:::tool
        SmartGate["SmartGate"]:::tool
        SmartSwitch["SmartSwitch"]:::tool
        SmartWatch["SmartWatch"]:::tool
        SmartLLMCost["SmartLLMCost"]:::tool
        SmartSavant["SmartSavant"]:::tool
    end
    SEC -. "implement" .-> IAIso
    SmartFabric -. "labels itself" .-> IAIso
    SmartDelegate -. "labels itself" .-> IAIso
    SmartPolicyTranslator -. "writes policy files for" .-> IAIso
    SmartAgency ==>|"depends on"| SmartFabric
    classDef tool fill:#1c232d,stroke:#f5b83d,color:#efe9f5;
    classDef std fill:#04121f,stroke:#46d6c8,color:#46d6c8;
    style SmartPangolin stroke-width:3px,stroke:#ff6b6b;
```

Thick arrow: the package requires the other one in its `pyproject.toml`. Dashed arrow: what the tool's README states about IAIso. A tool with no thick arrow does not depend on any other family package; each one installs and runs on its own.

<!-- smart-family-diagram:end -->

Open [`site/playground.html`](site/playground.html) for the interactive version.

## Part of the Smart* family

<!-- smart-family:start -->
<!-- generated by fleet-docs from family.json; change family.json, not this block -->

18 open-source tools by SmartTasks Lab, each standalone, plus the [IAIso standard](https://github.com/SmartTasksOrg/IAISO). Every tool is on PyPI under its `sf-` name; a package without the `sf-` prefix is not ours.

| Tool | IAIso | What it does |
|---|---|---|
| **[SmartPangolin](https://github.com/SmartTasksOrg/sf-smartpangolin)** (this repository) | §1 · Secure Sharing | Scan before you share. Stop leaking secrets into AI models, agents, and tools. |
| [SmartCheck](https://github.com/SmartTasksOrg/sf-smartcheck) | §2 · Verification | Check before you sign off. Catch the AI when it's confidently wrong. |
| [SmartSeal](https://github.com/SmartTasksOrg/sf-smartseal) | §3 · Provenance | Seal what you ship. A signed receipt so anyone can verify what they received. |
| [SmartPrompt](https://github.com/SmartTasksOrg/sf-smartprompt) | §4 · Context | Lint before you send. Bad prompt in, bad work out — and it's your name on it. |
| [SmartRoute](https://github.com/SmartTasksOrg/sf-smartroute) | §5 · Orchestration | Route only what you trust. Gate agents and tools with trust scores and guardrails. |
| [SmartMoat](https://github.com/SmartTasksOrg/sf-smartmoat) | §6 · Workforce | Know your moat. Score the tasks AI can't easily take — and widen them. |
| [SmartStandard](https://github.com/SmartTasksOrg/sf-smartstandard) | §7 · Standards | Standardize before you scale. One shared, auditable convention for AI-assisted work. |
| [SmartSim](https://github.com/SmartTasksOrg/sf-smartsim) | §8 · Foresight | Simulate before it hits you. See your role's task-by-task collapse sequence. |
| [SmartFeed](https://github.com/SmartTasksOrg/sf-smartfeed) | §9 · Awareness | Distill the firehose. A tight brief of only what moves your work. |
| [SmartFabric](https://github.com/SmartTasksOrg/sf-smartfabric) | §0 · Fabric | IAIso Fabric Protocol (IFP) — carry & enforce IAIso containment across a fleet of governed AI nodes. |
| [SmartDelegate](https://github.com/SmartTasksOrg/sf-smartdelegate) | §10 · Delegation (working label) | Delegate, don't hand over the keys. An agent never holds more than the human's role for the task: IAM for LLM agents. |
| [SmartPolicyTranslator](https://github.com/SmartTasksOrg/sf-smartpolicytranslator) | writes IAIso policy files | Translate natural-language regulation into REAL, schema-conformant IAIso policy files. |
| [SmartAgency](https://github.com/SmartTasksOrg/sf-smartagency) | — | Signed contracts that say what an AI agent may do, a ledger to suspend and revoke them, and a monitor that enforces them on every action, with SmartFabric pressure limits. |
| [SmartGate](https://github.com/SmartTasksOrg/sf-smartgate) | — | Decision friction and a human override for AI agents: score each action, ask a person before risky ones, kill any action or agent with one logged call. |
| [SmartSwitch](https://github.com/SmartTasksOrg/sf-smartswitch) | — | A quorum kill switch for AI agent fleets: no single keyholder can halt the fleet or block a halt; every agent verifies the signatures itself and stops when cut off. |
| [SmartWatch](https://github.com/SmartTasksOrg/sf-smartwatch) | — | Coupling-density monitor for multi-agent systems: measures how densely agents talk to each other, raises graded alerts, and proposes or issues resets before coordination outgrows human oversight. |
| [SmartLLMCost](https://github.com/SmartTasksOrg/sf-smartllmcost) | — | Apples-to-apples LLM cost & performance benchmark — cost per successful task, reproducible. |
| [SmartSavant](https://github.com/SmartTasksOrg/sf-smartsavant) | — | A model-agnostic design council: stakeholder views and a juror merge per design-sprint phase, schema-checked adapter answers, exports (spec, stories, decision tree, trainset) and audits of council runs before anyone builds or trains from them. |

<!-- smart-family:end -->

**Backed by the standard:** SmartPangolin implements **IAIso §1 · Secure Sharing**.
**Open-source edition:** this repo is the simplified, single-purpose version, built for any org to integrate into its own architecture. SmartTasks' desktop app and [SmartTasks.cloud](https://smarttasks.cloud) run a more advanced, deeply-integrated implementation of the same IAIso governance — a separate product, not this code bundled.

## Who's behind this

- **Roen Branham** — CEO & AI Strategy Architect · CISSP-certified AI, security & governance architect; author of IAIso and sole inventor of the Z4 Semantic Fabric patent application. [LinkedIn](https://www.linkedin.com/in/roen-branham-167ab29/)
- **Le Vu Tanh** — CTO & Core Engineering Lead · Chief architect of the Cortex engine; large-scale system reliability and low-latency infrastructure — the engineer who ships what gets architected. [LinkedIn](https://www.linkedin.com/in/lee-thanh-76aa8ba0/)

The team behind IAIso & SmartTasks: a CISSP-certified security & governance architect
and a large-scale systems engineer — 20+ years shipping secure, AI-driven platforms for
regulated, blue-chip environments (Allianz, BMW, Rolls-Royce, Heidenhain).

<!-- SMARTTASKS-MODELS:START -->
## Runs on governed local models

Every build ships **SHA256SUMS** and a supply-chain + red-team scan — the same provenance discipline SmartPangolin enforces on your repos.

This tool is local-first, so pair it with models you can actually vet. **SmartTasks** publishes 21+ governance-validated GGUF builds on Hugging Face — each with a machine-readable **scorecard** (capability tiers L1 Layman → L5 Agentic, IAIso conformance invariants (pass/warn/fail), OWASP-mapped garak red-team, transparency probes (viewpoint-alignment / over-refusal), and per-file SHA-256). Gate model selection on evidence, not vibes — and every finding, including warnings, is published in full.

→ **[SmartTasks on Hugging Face](https://huggingface.co/smarttasks)** · [Qwen3.6-27B](https://huggingface.co/smarttasks/Qwen3.6-27B-GGUF) (L5 agentic) · [react-agent-coder-llama-3.1-8b](https://huggingface.co/smarttasks/react-agent-coder-llama-3.1-8b-GGUF) (agentic coder) · [gpt-oss-20b](https://huggingface.co/smarttasks/gpt-oss-20b-GGUF) (open reasoning)
<!-- SMARTTASKS-MODELS:END -->

## Get in touch

- **Companies & enterprises:** [enterprise@smarttasks.cloud](mailto:enterprise@smarttasks.cloud) — we help
  teams integrate SmartPangolin + IAIso into their architecture so governance and
  audit-readiness become a byproduct of how they already work.
- **The standard:** [IAIso](https://github.com/SmartTasksOrg/IAIso) · [iaiso.org](https://iaiso.org)
- **The product:** [SmartTasks.cloud](https://smarttasks.cloud)

Built by **SmartTasks Lab**. Apache-2.0. Contributions welcome.

<!-- SMARTBENCH-METRICS:START -->
## Measured effectiveness (benchmarked)

SmartTasks tests this tool against live local models, not just unit fixtures. Headline recall across difficulty levels: **100%**.

**How to read this.** These come from the Smart\* *effectiveness benchmark*: a local model is driven to produce content of increasing difficulty; the tool (detects secrets (API keys, private keys, dangerous files), including base64/hex-encoded ones) is then run and its verdict scored against an independent oracle (broader than the tool's own rules, so a miss is a real gap).

- **Recall** — of cases that genuinely contained the target, the share the tool caught. Low recall = coverage gap.
- **Precision** — of what the tool flagged, the share that were real problems. Below 100% = false positives.
- **Levels** — 0 canary · 1 basic · 2 realistic · 3 obfuscated · 4 adversarial (hardest).
- **Invalid** — the model failed to produce the scenario (e.g. emitted a placeholder, not a real secret); not scored, so the tool is neither credited nor penalized.
- **Sample size** — model output varies run-to-run; small *n* is noisy. Pooled numbers combine recent runs.

| level | n | accuracy | precision | recall |
|---|---|---|---|---|
| 0 · canary | 2 | 100% | 100% | 100% |
| 1 · basic | 8 | 100% | 100% | 100% |
| 2 · realistic | 8 | 100% | 100% | 100% |
| 3 · obfuscated | 7 | 100% | 100% | 100% |
| 4 · adversarial | 8 | 100% | 100% | 100% |

**What this run shows:**
- Instrument check (canary) passes — the fixed sanity cases are all correct, so the higher-level numbers are trustworthy.
- **Strong** at: basic, realistic, obfuscated, adversarial — near-complete recall.
- No false positives observed (precision 100%) — the tool does not flag clean input.

_Source: run `20260804T134233-fad704` · 2026-08-04T13:45:23 · model(s): llama-3.1-8b-lexi-uncensored-v2 · repeats 8. Numbers reflect these model(s); output varies run-to-run, so re-run and regenerate to refresh._
<!-- SMARTBENCH-METRICS:END -->
