"""Hub sync for the v4 hub: briefs (shells), drag-and-drop moves, checklists, comments, analytics summary."""

import json

import pytest

from hifuel import hub
from hifuel.analytics import Analytics
from hifuel.config import load_config
from hifuel.planner import import_plan
from hifuel.reports import hub_analytics
from hifuel.store import Store
from tests.test_claims import make_post

CFG = load_config()


@pytest.fixture
def store(tmp_path):
    return Store(tmp_path)


def _seed(store, **kw):
    post = make_post(**kw)
    post.update(id=store.new_id(post), time="10:00", account_name=CFG.account(post["account"])["name"],
                account_type=CFG.account(post["account"])["type"], approver="manager", slot_reason="Benchmark",
                slot_source="benchmark", issues=[], blocked=False, consent_confirmed=False)
    return store.add(post)


def _inbox(tmp_path, collection, doc_id, doc):
    folder = tmp_path / "inbox" / collection
    folder.mkdir(parents=True, exist_ok=True)
    (folder / f"{doc_id}.json").write_text(json.dumps(doc))
    return tmp_path / "inbox"


def test_brief_from_hub_becomes_a_blocked_shell(store, tmp_path):
    inbox = _inbox(tmp_path, "posts", "shell-abc", {
        "status": "shell", "account": "pathvik", "platform": "instagram", "date": "2026-11-03", "time": "19:30",
        "format": "reel", "hook": "Reel: a day in the life of a product manager", "created_by": "u_1"})
    changes = hub.pull(store, CFG, inbox)
    shell = store.posts["shell-abc"]
    assert shell["status"] == "shell" and shell["blocked"] and shell["account_name"] == "Pathvik"
    assert shell["issues"][0]["check"] == "not_written"
    assert any("New brief" in c for c in changes)
    with pytest.raises(ValueError):
        store.set_status("shell-abc", "approved", by="Manager")


def test_written_post_replaces_the_shell(store, tmp_path):
    hub.pull(store, CFG, _inbox(tmp_path, "posts", "shell-abc", {
        "status": "shell", "account": "pathvik", "platform": "instagram", "date": "2026-11-03", "hook": "PM reel"}))
    post = make_post(account="pathvik", platform="instagram", date="2026-11-03", idea_id="pm-day",
                     hashtags=["#Pathvik", "#CareerClarity", "#ProductManagement"], caption="What a product manager does.")
    post["replaces"] = "shell-abc"
    import_plan(CFG, store, {"posts": [post]})
    assert "shell-abc" not in store.posts
    files = hub.push_meta(store, CFG, Analytics(store.dir), tmp_path / "out", "2026-10-19T12:00:00Z", "2026-10-19")
    assert json.loads((tmp_path / "out" / "_delete.json").read_text()) == ["posts/shell-abc"]
    assert any(f.name == "config.json" for f in files) and any(f.name == "sync.json" for f in files)


def test_drag_and_drop_move_is_applied_and_rechecked(store, tmp_path):
    post = _seed(store, theme="initiative_promo", date="2027-01-29")
    hub.push(store, tmp_path / "out")
    doc = json.loads((tmp_path / "out" / "posts" / f"{post['id']}.json").read_text())
    doc["date"], doc["time"] = "2027-01-30", "11:00"  # Martyrs' Day: no promo posts
    doc["edits"] = [{"field": "date", "old": "2027-01-29", "new": "2027-01-30", "by": "u_1", "at": "2099-01-01T10:00:00Z"},
                    {"field": "time", "old": "10:00", "new": "11:00", "by": "u_1", "at": "2099-01-01T10:00:00Z"}]
    doc["slot_reason"] = "Moved by hand on the hub"
    hub.pull(store, CFG, _inbox(tmp_path, "posts", post["id"], doc))
    moved = store.posts[post["id"]]
    assert (moved["date"], moved["time"], moved["slot_source"]) == ("2027-01-30", "11:00", "manual")
    assert moved["blocked"] and any(i["check"] == "sensitive_day" for i in moved["issues"])


def test_request_changes_keeps_the_checklist(store, tmp_path):
    post = _seed(store)
    doc = {**post, "status": "needs_changes",
           "review": {"by": "u_2", "at": "2099-01-01T10:00:00Z", "comment": "Close",
                      "checklist": ["Hook isn't strong enough", "Shorten the caption"]}}
    hub.pull(store, CFG, _inbox(tmp_path, "posts", post["id"], doc))
    assert store.posts[post["id"]]["status"] == "needs_changes"
    assert store.posts[post["id"]]["review"]["checklist"] == ["Hook isn't strong enough", "Shorten the caption"]


def test_comments_are_pulled_once_in_order(store, tmp_path):
    post = _seed(store)
    _inbox(tmp_path, "comments", "c2", {"post_id": post["id"], "by": "u_1", "at": "2026-10-19T11:00:00Z", "text": "Second"})
    inbox = _inbox(tmp_path, "comments", "c1", {"post_id": post["id"], "by": "u_2", "at": "2026-10-19T10:00:00Z", "text": "First"})
    hub.pull_extras(store, Analytics(store.dir), inbox)
    hub.pull_extras(store, Analytics(store.dir), inbox)
    assert [c["text"] for c in store.comments[post["id"]]] == ["First", "Second"]


def test_hub_analytics_summary(store, tmp_path):
    an = Analytics(tmp_path)
    row = lambda d, reach, likes, clicks: {"posted_at": f"2026-10-{d:02d}T19:00", "external_id": f"x{d}", "text": "t",
                                            "permalink": "", "format": "reel", "reach": reach, "likes": likes,
                                            "comments": 0, "shares": 0, "saves": 0, "link_clicks": clicks}
    an.add_rows([row(6, 1000, 50, 10), row(13, 2000, 60, None), row(14, 1000, 40, 20)], "pathvik", "instagram")
    an.add_followers("pathvik", "instagram", "2026-10-11", 1000)
    an.add_followers("pathvik", "instagram", "2026-10-18", 1060)
    s = hub_analytics(CFG, store, an, "2026-10-19")
    assert s["has_data"] and s["weeks"][-1] == "2026-10-19" and len(s["weeks"]) == 12
    wk = next(r for r in s["series"] if r["week"] == "2026-10-12")
    assert (wk["posts"], wk["impressions"], wk["engagements"], wk["clicks"], wk["click_base"]) == (2, 3000, 100, 20, 1000)
    assert wk["follower_change"] == 60
    top = s["posts"][0]
    assert top["date"] == "2026-10-14" and top["er"] == pytest.approx(0.04) and top["ctr"] == pytest.approx(0.02)
