"""Tests for the frontier research MCP's error envelope + survey fan-out isolation."""

from __future__ import annotations

from frontier_mcp import server
from frontier_mcp.server import _guard


def test_guard_success_envelope() -> None:
    r = _guard(lambda: {"ok": "value"})
    assert r == {"ok": True, "result": {"ok": "value"}}


def test_guard_failure_envelope() -> None:
    def boom() -> dict:
        raise ValueError("bad input")

    r = _guard(boom)
    assert r["ok"] is False
    assert r["error_code"] == "ValueError"
    assert r["error_detail"] == "bad input"


def test_survey_all_sources_succeed(monkeypatch) -> None:
    monkeypatch.setattr(server.sources, "arxiv_search", lambda q, **k: [{"id": "p1"}])
    monkeypatch.setattr(server.sources, "gh_search_repos", lambda q, **k: [{"full_name": "r1"}])
    monkeypatch.setattr(server.sources, "hf_search_models", lambda q, **k: [{"id": "m1"}])

    out = server.survey("quantum")
    assert out["ok"] is True
    hits = out["result"]["hits"]
    assert hits == {"papers": 1, "repos": 1, "models": 1}
    assert "note" not in out["result"]


def test_survey_one_dead_source_does_not_sink_call(monkeypatch) -> None:
    def dead(q, **k):
        raise RuntimeError("arxiv down")

    monkeypatch.setattr(server.sources, "arxiv_search", dead)
    monkeypatch.setattr(server.sources, "gh_search_repos", lambda q, **k: [{"full_name": "r1"}])
    monkeypatch.setattr(server.sources, "hf_search_models", lambda q, **k: [{"id": "m1"}])

    out = server.survey("quantum")
    assert out["ok"] is True  # the other two still produce a usable result
    papers = out["result"]["papers"]
    assert "error" in papers and "RuntimeError" in papers["error"]
    assert out["result"]["hits"]["repos"] == 1


def test_survey_zero_hits_returns_guidance_note(monkeypatch) -> None:
    monkeypatch.setattr(server.sources, "arxiv_search", lambda q, **k: [])
    monkeypatch.setattr(server.sources, "gh_search_repos", lambda q, **k: [])
    monkeypatch.setattr(server.sources, "hf_search_models", lambda q, **k: [])
    out = server.survey("nonsense-topic")
    assert out["ok"] is True
    assert "note" in out["result"]
    assert "Zero hits" in out["result"]["note"]
