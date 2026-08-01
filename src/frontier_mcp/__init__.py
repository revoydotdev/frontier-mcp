"""frontier-mcp — live state-of-the-art from arXiv + GitHub + HuggingFace.

Read-only research surface: search + fetch primary material so an agent reasons from
what exists *now*, not from a stale training cutoff. No mutating tools; nothing to gate.
GitHub auth is picked up from GITHUB_TOKEN/GH_TOKEN or `gh auth token`; HuggingFace uses
the cached HF token if present; arXiv needs no key.
"""

__version__ = "0.1.0"
