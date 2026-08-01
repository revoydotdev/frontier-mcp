# frontier-mcp

Live **state-of-the-art** for a research/frontier agent: search + fetch primary material
from **arXiv** (papers), **GitHub** (implementations), and **HuggingFace** (models/datasets),
so the agent reasons from what exists *now* rather than a training cutoff. All tools are
read-only; nothing to gate.

Built for the **`the-future`** agent and rolled into the **`prior-art-research`** skill as its
material-pulling engine.

## Install

```bash
uv venv .venv --python 3.13
uv pip install -e . --python .venv/bin/python
claude mcp add frontier -s user -- /home/revelri/Dev/revelri/frontier-mcp/.venv/bin/python -m frontier_mcp
```

## Auth
- **arXiv** — none.
- **GitHub** — `GITHUB_TOKEN`/`GH_TOKEN`, else `gh auth token` (higher rate limits + private repos).
- **HuggingFace** — cached HF token if present (public search works without one).

## Tools
- **`survey(topic, max_each=5)`** — the headline: top arXiv papers + GitHub repos + HF models in one call (one dead source doesn't sink the rest). The "breathe SOTA" first move.
- `arxiv_search(query, max_results, category?, sort=relevance|submitted|updated)`, `arxiv_get(id)`, `arxiv_fetch(id, out_dir?)` (download PDF).
- `gh_search_repos(query, language?, sort=stars|updated, limit)`, `gh_repo("owner/name")` (+ README excerpt).
- `hf_search_models(query, task?, sort=downloads|likes|modified|created|trending, limit)`, `hf_search_datasets(...)`, `hf_model(id)`.
