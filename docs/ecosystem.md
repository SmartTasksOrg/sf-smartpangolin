# Ecosystem

SmartPangolin is the sharing gate for a wider body of work from **SmartTasks Lab** on
making AI systems safe to build on. The through-line is "ship the evidence with
the artifact."

## IAIso — pressure-based control of systems

[iaiso.org](https://iaiso.org). A git-repo framework for controlling systems by
pressure rather than by hope. SmartPangolin is fail-closed by the same principle: a
seal is judged by whether it holds *under pressure* (an unreadable file, an
unknown binary, a novel token format) — not by whether it usually passes. When in
doubt, the gate closes.

## SmartTasks — the data fabric it came from

[smarttasks.cloud](https://smarttasks.cloud). The desktop data-fabric app that SmartPangolin's sharing gate was extracted and
hardened from.

## Model repacks + assurance on Hugging Face

[huggingface.co/smarttasks](https://huggingface.co/smarttasks). 35+ GGUF builds —
gpt-oss-20b, Qwen3 (0.6B–30B), Llama-3.2, Mistral, Falcon3, Phi-4, plus embedding
and reranker models — each published with scorecards, metrics, and hashes from a
model-assurance framework, so a downstream system can authenticate what it is
loading.

## The common stance

A GGUF ships with a model card and a hash so a consumer can trust what they load.
SmartPangolin makes your **source** ship the same way: a share zip carries a manifest,
an exclusion audit, the exact policy that ran, and a `content_sha256`. The
manifest is to a share what a model card is to a model.
