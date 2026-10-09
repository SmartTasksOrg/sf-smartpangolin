"""UML data objects for SmartPangolin — the diagram in the README is these classes."""
from __future__ import annotations
from dataclasses import dataclass

@dataclass
class Finding:
    rule: str
    severity: str
    path: str
    detail: str

@dataclass
class Policy:
    rules: list[str]
    hash: str

@dataclass
class ScanResult:
    findings: list[Finding]
    verdict: str
    policy_hash: str
