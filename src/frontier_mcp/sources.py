"""Backend clients: arXiv, GitHub, HuggingFace. Pure functions returning plain dicts."""

from __future__ import annotations

import os
import subprocess
from pathlib import Path
from typing import Any

import arxiv
import requests
from huggingface_hub import HfApi

# ------------------------------------------------------------------ arXiv

_ARXIV = arxiv.Client(page_size=100, delay_seconds=3.0, num_retries=5)
_ARXIV_SORT = {
    "relevance": arxiv.SortCriterion.Relevance,
    "submitted": arxiv.SortCriterion.SubmittedDate,
    "updated": arxiv.SortCriterion.LastUpdatedDate,
}


def _paper(r: arxiv.Result) -> dict[str, Any]:
    return {
        "id": r.get_short_id(),
        "title": r.title.strip(),
        "authors": [a.name for a in r.authors][:10],
        "published": r.published.isoformat() if r.published else None,
        "updated": r.updated.isoformat() if r.updated else None,
        "primary_category": r.primary_category,
        "categories": r.categories,
        "abstract": r.summary.strip(),
        "pdf_url": r.pdf_url,
        "url": r.entry_id,
    }


def arxiv_search(query: str, max_results: int = 10, category: str | None = None,
                 sort: str = "relevance") -> list[dict[str, Any]]:
    q = f"cat:{category} AND ({query})" if category else query
    search = arxiv.Search(query=q, max_results=max_results,
                          sort_by=_ARXIV_SORT.get(sort, arxiv.SortCriterion.Relevance))
    return [_paper(r) for r in _ARXIV.results(search)]


def arxiv_get(arxiv_id: str) -> dict[str, Any]:
    r = next(_ARXIV.results(arxiv.Search(id_list=[arxiv_id])))
    return _paper(r)


def arxiv_fetch(arxiv_id: str, out_dir: str | None = None) -> dict[str, Any]:
    base = Path(out_dir).expanduser() if out_dir else Path.home() / "frontier-material" / "arxiv"
    base.mkdir(parents=True, exist_ok=True)
    r = next(_ARXIV.results(arxiv.Search(id_list=[arxiv_id])))
    path = r.download_pdf(dirpath=str(base))
    return {"id": r.get_short_id(), "title": r.title.strip(), "pdf": path}


# ------------------------------------------------------------------ GitHub

def _gh_token() -> str | None:
    for v in ("GITHUB_TOKEN", "GH_TOKEN"):
        if os.environ.get(v):
            return os.environ[v].strip()
    try:
        p = subprocess.run(["gh", "auth", "token"], capture_output=True, text=True, timeout=5)
        if p.returncode == 0 and p.stdout.strip():
            return p.stdout.strip()
    except Exception:
        pass
    return None


def _gh_headers(raw: bool = False) -> dict[str, str]:
    h = {
        "Accept": "application/vnd.github.raw+json" if raw else "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
    }
    tok = _gh_token()
    if tok:
        h["Authorization"] = f"Bearer {tok}"
    return h


def gh_search_repos(query: str, language: str | None = None, sort: str = "stars",
                    limit: int = 10) -> list[dict[str, Any]]:
    q = query + (f" language:{language}" if language else "")
    r = requests.get("https://api.github.com/search/repositories",
                     params={"q": q, "sort": sort, "order": "desc", "per_page": min(limit, 50)},
                     headers=_gh_headers(), timeout=25)
    r.raise_for_status()
    return [{
        "full_name": i["full_name"], "stars": i["stargazers_count"],
        "forks": i.get("forks_count"), "license": (i.get("license") or {}).get("spdx_id"),
        "description": i.get("description"), "language": i.get("language"),
        "url": i["html_url"], "pushed_at": i.get("pushed_at"), "topics": i.get("topics", []),
    } for i in r.json().get("items", [])[:limit]]


def gh_repo(repo: str) -> dict[str, Any]:
    r = requests.get(f"https://api.github.com/repos/{repo}", headers=_gh_headers(), timeout=25)
    r.raise_for_status()
    d = r.json()
    readme = ""
    rr = requests.get(f"https://api.github.com/repos/{repo}/readme", headers=_gh_headers(raw=True), timeout=25)
    if rr.ok:
        readme = rr.text[:5000]
    return {
        "full_name": d["full_name"], "stars": d["stargazers_count"], "forks": d["forks_count"],
        "description": d.get("description"), "language": d.get("language"), "url": d["html_url"],
        "pushed_at": d.get("pushed_at"), "topics": d.get("topics", []),
        "license": (d.get("license") or {}).get("spdx_id"), "readme_excerpt": readme,
    }


# ------------------------------------------------------------------ HuggingFace

_HF = HfApi()
_HF_SORT = {"downloads": "downloads", "likes": "likes", "modified": "last_modified",
            "created": "created_at", "trending": "trending_score"}


def hf_search_models(query: str, task: str | None = None, sort: str = "downloads",
                     limit: int = 10) -> list[dict[str, Any]]:
    models = _HF.list_models(search=query, pipeline_tag=task,
                             sort=_HF_SORT.get(sort, "downloads"), limit=limit)
    return [{
        "id": m.id, "downloads": getattr(m, "downloads", None), "likes": getattr(m, "likes", None),
        "pipeline_tag": getattr(m, "pipeline_tag", None), "tags": (getattr(m, "tags", None) or [])[:12],
        "last_modified": str(getattr(m, "last_modified", None)), "url": f"https://huggingface.co/{m.id}",
    } for m in models]


def hf_search_datasets(query: str, sort: str = "downloads", limit: int = 10) -> list[dict[str, Any]]:
    ds = _HF.list_datasets(search=query, sort=_HF_SORT.get(sort, "downloads"), limit=limit)
    return [{
        "id": d.id, "downloads": getattr(d, "downloads", None), "likes": getattr(d, "likes", None),
        "tags": (getattr(d, "tags", None) or [])[:12], "last_modified": str(getattr(d, "last_modified", None)),
        "url": f"https://huggingface.co/datasets/{d.id}",
    } for d in ds]


def hf_model(model_id: str) -> dict[str, Any]:
    m = _HF.model_info(model_id)
    cd = getattr(m, "card_data", None) or getattr(m, "cardData", None)
    card = cd.to_dict() if cd is not None and hasattr(cd, "to_dict") else (dict(cd) if isinstance(cd, dict) else {})
    return {
        "id": m.id, "downloads": getattr(m, "downloads", None), "likes": getattr(m, "likes", None),
        "pipeline_tag": getattr(m, "pipeline_tag", None), "library_name": getattr(m, "library_name", None),
        "tags": (getattr(m, "tags", None) or [])[:20], "last_modified": str(getattr(m, "last_modified", None)),
        "url": f"https://huggingface.co/{m.id}",
        "license": card.get("license"), "datasets": card.get("datasets"),
        "base_model": card.get("base_model"),
    }
