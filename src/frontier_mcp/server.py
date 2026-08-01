"""FastMCP server: live SOTA from arXiv + GitHub + HuggingFace. All tools read-only."""

from __future__ import annotations

import logging
import sys
from collections.abc import Callable
from typing import Any

from fastmcp import FastMCP

from frontier_mcp import __version__, sources

log = logging.getLogger("frontier_mcp")

INSTRUCTIONS = """\
Pull live state-of-the-art to reason from primary material, not a training cutoff. Start
with `survey(topic)` — it hits arXiv (theory + newest results), GitHub (implementations),
and HuggingFace (models) in one call and returns a merged frontier snapshot. Then drill:
`arxiv_search`/`arxiv_get`/`arxiv_fetch` for papers, `gh_search_repos`/`gh_repo` for code,
`hf_search_models`/`hf_search_datasets`/`hf_model` for models & data. Cite every id/repo/model
you rely on — these are current references, not memory. Two standing rules: (1) an empty
result is a finding — record the query and its emptiness rather than silently retrying;
these sources skew academic/ML, and systems/kernel/vendor topics live in kernel docs, LWN,
changelogs, and issue trackers instead. (2) Any repo you recommend for further study must be
cited with its maturity signals (stars, forks, last push) and license — a 3-star SSPL repo
and a 300-star Apache repo are different recommendations."""

mcp: FastMCP = FastMCP(name="frontier", instructions=INSTRUCTIONS)


def _guard(fn: Callable[[], Any]) -> dict[str, Any]:
    try:
        return {"ok": True, "result": fn()}
    except Exception as e:
        return {"ok": False, "error_code": type(e).__name__, "error_detail": str(e)}


@mcp.tool(description=(
    "One-shot frontier snapshot of a topic: top arXiv papers, top GitHub repos, and top "
    "HuggingFace models, in one call. The 'breathe the state of the art' first move — run "
    "this before reasoning about any frontier problem. `max_each` per source (default 5). "
    "Coverage limit: these three sources skew academic/ML — for systems, kernel, and "
    "vendor-tool topics the primary literature lives in kernel docs, LWN, changelogs, and "
    "issue trackers, so read the returned `hits` counts and fall through fast rather than "
    "re-running variants."))
def survey(topic: str, max_each: int = 5) -> dict[str, Any]:
    def run() -> dict[str, Any]:
        out: dict[str, Any] = {"topic": topic}
        for key, fn in (
            ("papers", lambda: sources.arxiv_search(topic, max_results=max_each, sort="relevance")),
            ("repos", lambda: sources.gh_search_repos(topic, sort="stars", limit=max_each)),
            ("models", lambda: sources.hf_search_models(topic, sort="downloads", limit=max_each)),
        ):
            try:
                out[key] = fn()
            except Exception as e:  # one dead source shouldn't sink the survey
                out[key] = {"error": f"{type(e).__name__}: {e}"}
        out["hits"] = {k: len(v) if isinstance(v, list) else 0
                       for k, v in out.items() if k in ("papers", "repos", "models")}
        if sum(out["hits"].values()) == 0:
            out["note"] = (
                "Zero hits across arXiv+GitHub+HF. This is a finding, not a dead end: "
                "either the terms don't match the field's vocabulary, or the topic's primary "
                "literature is non-academic (kernel docs, LWN, vendor changelogs, issue "
                "trackers) — try one targeted arxiv_search/gh_search_repos rephrase, then "
                "switch to web search/fetch of those sources. Record empty queries in your "
                "output; do not keep re-running survey variants.")
        return out

    return _guard(run)


@mcp.tool(description="Search arXiv. `sort`: relevance|submitted|updated. Optional `category` (e.g. cs.LG, cs.AI). Returns title/authors/abstract/categories/pdf_url per paper.")
def arxiv_search(query: str, max_results: int = 10, category: str | None = None,
                 sort: str = "relevance") -> dict[str, Any]:
    return _guard(lambda: sources.arxiv_search(query, max_results, category, sort))


@mcp.tool(description="Full arXiv record (abstract + metadata + pdf_url) for an arXiv id (e.g. 2401.12345).")
def arxiv_get(arxiv_id: str) -> dict[str, Any]:
    return _guard(lambda: sources.arxiv_get(arxiv_id))


@mcp.tool(description="Download an arXiv paper's PDF to disk (default ~/frontier-material/arxiv) and return its path — for pulling material to read in depth.")
def arxiv_fetch(arxiv_id: str, out_dir: str | None = None) -> dict[str, Any]:
    return _guard(lambda: sources.arxiv_fetch(arxiv_id, out_dir))


@mcp.tool(description="Search GitHub repositories. `sort`: stars|updated. Optional `language`. Returns name/stars/forks/license/description/topics/pushed_at. Cite the maturity signals (stars/forks/pushed_at) and license for any repo you recommend onward. Uses gh auth for higher rate limits + private repos.")
def gh_search_repos(query: str, language: str | None = None, sort: str = "stars",
                    limit: int = 10) -> dict[str, Any]:
    return _guard(lambda: sources.gh_search_repos(query, language, sort, limit))


@mcp.tool(description="Full metadata + README excerpt for a GitHub repo given 'owner/name'.")
def gh_repo(repo: str) -> dict[str, Any]:
    return _guard(lambda: sources.gh_repo(repo))


@mcp.tool(description="Search HuggingFace models. `sort`: downloads|likes|modified|created|trending. Optional `task` (e.g. text-generation). Returns id/downloads/likes/pipeline_tag/tags.")
def hf_search_models(query: str, task: str | None = None, sort: str = "downloads",
                     limit: int = 10) -> dict[str, Any]:
    return _guard(lambda: sources.hf_search_models(query, task, sort, limit))


@mcp.tool(description="Search HuggingFace datasets. `sort`: downloads|likes|modified|created|trending.")
def hf_search_datasets(query: str, sort: str = "downloads", limit: int = 10) -> dict[str, Any]:
    return _guard(lambda: sources.hf_search_datasets(query, sort, limit))


@mcp.tool(description="Full HuggingFace model card metadata (license, base_model, datasets, tags) for a model id.")
def hf_model(model_id: str) -> dict[str, Any]:
    return _guard(lambda: sources.hf_model(model_id))


def _setup_logging() -> None:
    h = logging.StreamHandler(sys.stderr)
    h.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(name)s: %(message)s"))
    logging.basicConfig(level=logging.INFO, handlers=[h])


def build_server() -> FastMCP:
    _setup_logging()
    log.info("frontier-mcp %s ready", __version__)
    return mcp
