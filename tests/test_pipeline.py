"""Planner -> store -> hub -> export, with a fake Claude client (no API key needed)."""

import json
from datetime import date
from types import SimpleNamespace as NS

import pytest

from hifuel import export, hub
from hifuel.config import load_config
from hifuel.models import PostDraft, WeekPlan
from hifuel.planner import plan_period
from hifuel.store import Store
from tests.test_claims import make_post

CFG = load_config()


class FakeStream:
    def __init__(self, message):
        self.message = message

    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False

    def get_final_message(self):
        return self.message


class FakeClient:
    """Returns one scripted plan per call and records the requests."""

    def __init__(self, plans: dict, stop_reason="end_turn"):
        self.plans, self.requests, self.stop_reason = plans, [], stop_reason
        self.beta = NS(messages=NS(stream=self._stream))

    def _stream(self, **kwargs):
        self.requests.append(kwargs)
        usage = NS(input_tokens=10_000, output_tokens=5_000, cache_read_input_tokens=0, cache_creation_input_tokens=0)
        text = kwargs["messages"][0]["content"]
        plan = next(p for account, p in self.plans.items() if f"({account})" in text)
        return FakeStream(NS(stop_reason=self.stop_reason, parsed_output=plan, usage=usage))


def draft(**kw):
    return PostDraft(**make_post(**kw))


@pytest.fixture
def store(tmp_path):
    return Store(tmp_path)


def test_plan_period_end_to_end(store, tmp_path):
    hifuel_plan = WeekPlan(summary="ESG week", questions_for_team=["Can we name the client?"], posts=[
        draft(account="hifuel_advisory", date="2026-10-27", idea_id="brsr-basics"),
        draft(account="hifuel_advisory", date="2026-10-28", idea_id="hype",
              caption="We are India's first growth ecosystem."),
        draft(account="hifuel_advisory", date="2026-12-01", idea_id="outside-period"),
    ])
    pathvik_plan = WeekPlan(summary="Clarity week", questions_for_team=[], posts=[
        draft(account="pathvik", platform="instagram", date="2026-10-27", idea_id="doubts",
              hashtags=["#Pathvik", "#CareerClarity", "#Students"], caption="No job guarantees. Just a real plan."),
    ])
    client = FakeClient({"hifuel_advisory": hifuel_plan, "pathvik": pathvik_plan})
    plan = plan_period(CFG, store, date(2026, 10, 26), 7, accounts=["pathvik", "hifuel_advisory"],
                       campaigns=["Pathvik applications open"], client=client, on_progress=lambda *_: None)

    # Out-of-period post dropped, ids and times assigned, claims checked.
    assert len(plan["post_ids"]) == 3
    posts = {p["idea_id"]: p for p in store.posts.values()}
    assert set(posts) == {"brsr-basics", "hype", "doubts"}
    assert posts["hype"]["blocked"] and not posts["brsr-basics"]["blocked"]
    assert posts["doubts"]["time"] and posts["doubts"]["slot_source"] in {"benchmark", "explore"}
    assert plan["questions_for_team"] == ["[hifuel_advisory] Can we name the client?"]
    assert plan["cost_usd"] == pytest.approx(2 * (10_000 * 4 + 5_000 * 20) / 1e6, abs=0.01)

    # The second call sees the first account's ideas, and the request uses the right settings.
    second = client.requests[1]
    assert "(hifuel_advisory)" in second["messages"][0]["content"]
    assert "idea_id: doubts" in second["messages"][0]["content"]
    assert second["fallbacks"] == "default" and second["output_format"] is WeekPlan
    assert second["model"] == "claude-opus-5-5"

    # Saved to disk and logged.
    reloaded = Store(tmp_path)
    assert len(reloaded.posts) == 3
    assert "generated" in (tmp_path / "log.jsonl").read_text()

    # Blocked posts can't be approved; clean ones can.
    with pytest.raises(ValueError):
        store.set_status(posts["hype"]["id"], "approved", by="Manager")
    store.set_status(posts["brsr-basics"]["id"], "approved", by="Manager")


def test_refusal_stops_planning(store):
    from hifuel.planner import PlanningError
    client = FakeClient({"pathvik": WeekPlan(summary="", questions_for_team=[], posts=[])}, stop_reason="refusal")
    with pytest.raises(PlanningError):
        plan_period(CFG, store, date(2026, 10, 26), 7, accounts=["pathvik"], client=client,
                    on_progress=lambda *_: None)


def _seed(store, **kw):
    post = make_post(**kw)
    post.update(id=store.new_id(post), time="10:00", account_name="Hi Fuel Advisory", account_type="company",
                approver="manager", slot_reason="Benchmark", issues=[], blocked=False, consent_confirmed=False)
    return store.add(post)


def test_hub_push_and_pull(store, tmp_path):
    clean = _seed(store, idea_id="a")
    other = _seed(store, idea_id="b", date="2026-10-28")
    files = hub.push(store, tmp_path / "outbox")
    assert len(files) == 2
    doc = json.loads((tmp_path / "outbox" / "posts" / f"{clean['id']}.json").read_text())
    assert doc["hook"] == clean["hook"] and doc["status"] == "draft"

    # Reviewer approves one post and edits another into something that breaks a rule.
    inbox = tmp_path / "inbox" / "posts"
    inbox.mkdir(parents=True)
    (inbox / f"{clean['id']}.json").write_text(json.dumps(
        {**doc, "status": "approved", "review": {"by": "u_1", "by_name": "Manager", "comment": "Good"}}))
    other_doc = {**json.loads((tmp_path / "outbox" / "posts" / f"{other['id']}.json").read_text())}
    other_doc.update(caption="The best ESG firm in India.", status="approved", review={"by_name": "Founder"})
    (inbox / f"{other['id']}.json").write_text(json.dumps({"data": other_doc, "version": 3}))

    changes = hub.pull(store, CFG, tmp_path / "inbox")
    assert store.posts[clean["id"]]["status"] == "approved"
    assert store.posts[other["id"]]["status"] == "draft"  # edit re-checked and now blocked
    assert store.posts[other["id"]]["blocked"]
    assert any("NOT approved" in c for c in changes)
    assert store.recent_edits("hifuel_advisory")[-1]["after"] == "The best ESG firm in India."


def test_exports(store, tmp_path):
    post = _seed(store, idea_id="a", caption="Fee: ₹4,999, incl. GST; new cohort.")
    post["status"] = "approved"
    posts = [post]
    csv_path = export.write_csv(posts, tmp_path / "c.csv")
    assert "₹4,999" in csv_path.read_text(encoding="utf-8-sig")
    ics = export.write_ics(posts, tmp_path / "c.ics").read_bytes().decode()
    assert "DTSTART;TZID=Asia/Kolkata:20261027T100000" in ics
    assert all(len(line.encode()) <= 75 for line in ics.split("\r\n"))
    assert "\\;" in ics and "\\," in ics
    md = export.write_captions(posts, tmp_path / "c.md").read_text()
    assert "Tuesday 27 October 2026" in md and "LinkedIn Page scheduler" in md
