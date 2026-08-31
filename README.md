<div align="center">

# frontier-mcp

### Live research context for MCP clients

Search primary material across [arXiv](https://arxiv.org/), [GitHub](https://github.com/), and [Hugging Face](https://huggingface.co/) without leaving the agent workflow.

[![CI](https://github.com/revoydotdev/frontier-mcp/actions/workflows/ci.yml/badge.svg)](https://github.com/revoydotdev/frontier-mcp/actions/workflows/ci.yml)
[![Python 3.11+](https://img.shields.io/badge/Python-3.11%2B-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-526b4e.svg)](LICENSE)

[Quick start](#quick-start) · [Tools](#tools) · [Operational boundaries](#operational-boundaries) · [Development](#development)

</div>

`frontier-mcp` is a stdio [Model Context Protocol](https://modelcontextprotocol.io/) server for research that benefits from current, attributable material. It searches papers, implementation repositories, models, and datasets, then returns their identifiers, links, metadata, and selected primary content in a stable result envelope.

The server is intentionally narrow: it is a retrieval surface, not a recommender or an execution environment. Start with a cross-source survey, follow the source records that matter, and cite the paper ID, repository, or model/dataset ID in the resulting work.

## Quick start

### Requirements

- Python 3.11 or newer
- [uv](https://docs.astral.sh/uv/) (recommended for an isolated, locked install)
- Network access to the sources you use

Clone the repository and create the project environment:

```bash
git clone https://github.com/revoydotdev/frontier-mcp.git
cd frontier-mcp
uv sync --locked
```

Add the server to Claude Code at user scope:

```bash
claude mcp add -s user frontier -- "$PWD/.venv/bin/python" -m frontier_mcp
```

Any MCP client that supports stdio can run the same command and arguments:

```text
command: /absolute/path/to/frontier-mcp/.venv/bin/python
args:    ["-m", "frontier_mcp"]
```

The command starts a stdio server; it is not an interactive CLI. Use your MCP client's tool inspector or a connected agent to call it.

### First query

Ask the client to call:

```text
survey("retrieval-augmented generation")
```

The response combines the top matching arXiv papers, GitHub repositories, and Hugging Face models. Use its `hits` counts to see which sources contributed, then use the provider-specific tools to inspect promising records.

## Tools

Every tool returns one of these envelopes, so clients can handle provider failures consistently:

```json
{"ok": true, "result": {}}
```

```json
{"ok": false, "error_code": "ExceptionType", "error_detail": "…"}
```

| Tool | Purpose | Key parameters |
|---|---|---|
| `survey` | Search papers, repositories, and models together. A failure from one provider is reported in that provider's field without discarding the other results. | `topic`, `max_each=5` |
| `arxiv_search` | Search arXiv paper records. Results include title, authors, abstract, categories, dates, and paper/PDF URLs. | `query`, `max_results=10`, `category`, `sort=relevance\|submitted\|updated` |
| `arxiv_get` | Retrieve a full arXiv record by identifier. | `arxiv_id` |
| `arxiv_fetch` | Download a paper PDF for local reading and return its filesystem path. | `arxiv_id`, `out_dir` |
| `gh_search_repos` | Search GitHub repositories with maturity and licensing metadata. | `query`, `language`, `sort=stars\|updated`, `limit=10` |
| `gh_repo` | Retrieve repository metadata and, when GitHub returns it, a README excerpt capped at 5,000 characters. | `repo` (`owner/name`) |
| `hf_search_models` | Search Hugging Face models. | `query`, `task`, `sort=downloads\|likes\|modified\|created\|trending`, `limit=10` |
| `hf_search_datasets` | Search Hugging Face datasets. | `query`, `sort=downloads\|likes\|modified\|created\|trending`, `limit=10` |
| `hf_model` | Retrieve model-card metadata, including available license, base-model, and dataset fields. | `model_id` |

For repository recommendations, preserve the returned stars, forks, last-push time, and license alongside the repository URL. Those details help distinguish active, broadly adopted code from a merely relevant search hit.

## Authentication and local files

| Source | Credentials | Behavior |
|---|---|---|
| arXiv | None | Paper search and retrieval work without a key. |
| GitHub | `GITHUB_TOKEN` or `GH_TOKEN`; otherwise `gh auth token` when available | Authentication raises rate limits and may expose repositories the token can access. Public search works without it, subject to GitHub's unauthenticated limits. |
| Hugging Face | Cached Hugging Face token when present | Public model and dataset search works without a token. |

All network operations are read-only: this server does not create, modify, or submit content to arXiv, GitHub, or Hugging Face. `arxiv_fetch` is the one local write: it saves a PDF under `~/frontier-material/arxiv` by default, or in the supplied `out_dir`.

## Operational boundaries

The three sources are deliberately useful but incomplete. They favor academic and ML-oriented material; systems, kernel, and vendor-tool research may instead require official documentation, changelogs, issue trackers, or other web sources. A zero-result survey is useful evidence about the query or source coverage, not proof that the subject does not exist.

Search output is current at retrieval time, not a quality, security, compatibility, or licensing determination. Inspect the linked primary material before adopting a dependency or making a claim. In particular, repository metadata is a signal to cite and assess, not an endorsement.

## Development

The locked development environment and the repository's CI use:

```bash
uv sync --extra dev --locked
uv run ruff check .
uv run pytest
```

Run the server directly during local MCP-client development:

```bash
uv run frontier-mcp
```

The test suite covers the stable error envelope and `survey` fan-out behavior, including partial provider failures and the all-zero-results guidance path.

## License

[MIT](LICENSE) © 2026 revelri
