"""Tests that run the agent loop with a fake Claude client (no API key needed)."""

import json
from types import SimpleNamespace as NS

import pytest

from social_agent import agent as agent_mod
from social_agent import tools


@pytest.fixture(autouse=True)
def temp_drafts(tmp_path, monkeypatch):
    monkeypatch.setattr(tools, "DRAFTS_FILE", tmp_path / "drafts.json")


class FakeClient:
    """Returns scripted responses and records each request."""

    def __init__(self, responses):
        self.responses = list(responses)
        self.requests = []
        self.beta = NS(messages=NS(create=self._create))

    def _create(self, **kwargs):
        self.requests.append({**kwargs, "messages": list(kwargs["messages"])})
        return self.responses.pop(0)


def text(t):
    return NS(type="text", text=t)


def tool_use(id, name, input):
    return NS(type="tool_use", id=id, name=name, input=input)


def test_tool_round_trip_saves_draft():
    client = FakeClient([
        NS(stop_reason="tool_use", content=[
            tool_use("t1", "check_post_length", {"platform": "x", "text": "Hello world"}),
            tool_use("t2", "save_draft", {"platform": "x", "text": "Hello world", "scheduled_for": "2026-11-01"}),
        ]),
        NS(stop_reason="end_turn", content=[text("Saved!")]),
    ])
    a = agent_mod.SocialAgent(client)
    assert a.send("write and save a tweet") == "Saved!"

    # Both tool results go back in one user message.
    results = client.requests[1]["messages"][-1]["content"]
    assert [r["tool_use_id"] for r in results] == ["t1", "t2"]
    assert results[0]["content"].startswith("OK: 11/280")
    saved = json.loads(tools.DRAFTS_FILE.read_text())
    assert saved[0]["scheduled_for"] == "2026-11-01"
    assert client.requests[0]["fallbacks"] == "default"


def test_refusal_rolls_back_turn():
    client = FakeClient([
        NS(stop_reason="tool_use", content=[tool_use("t1", "list_drafts", {"platform": "all"})]),
        NS(stop_reason="refusal", content=[]),
    ])
    a = agent_mod.SocialAgent(client)
    assert "can't help" in a.send("something")
    assert a.messages == []


def test_api_error_rolls_back_turn():
    class Boom(Exception):
        pass

    def fail(**kwargs):
        raise Boom()

    a = agent_mod.SocialAgent(FakeClient([]))
    a.client.beta.messages.create = fail
    with pytest.raises(Boom):
        a.send("hi")
    assert a.messages == []


def test_bad_tool_input_is_reported_as_error():
    assert tools.run_tool("save_draft", {"platform": "x", "text": "hi", "scheduled_for": "tomorrow"})[1]
    assert tools.run_tool("nope", {})[1]
    assert "TOO LONG" in tools.check_post_length("x", "a" * 300)
    assert "Not saved" in tools.save_draft("x", "a" * 300)


def test_pause_turn_continues():
    client = FakeClient([
        NS(stop_reason="pause_turn", content=[text("searching")]),
        NS(stop_reason="end_turn", content=[text("Trends: ...")]),
    ])
    a = agent_mod.SocialAgent(client)
    assert a.send("what's trending?") == "Trends: ..."
    assert len(a.messages) == 3  # user, paused assistant, final assistant
