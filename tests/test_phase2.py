"""Phase 2: analytics import, reports, experiments, and the learning loop."""

import json
from datetime import date

import pytest
import yaml

from hifuel import experiments as exps
from hifuel import hub, reports
from hifuel.analytics import Analytics, AnalyticsError, detect_date_order, load_columns, parse_datetime, read_export
from hifuel.config import ROOT, load_config
from hifuel.planner import build_request, import_plan
from hifuel.slots import assign_slots
from hifuel.store import Store

CFG = load_config()
COLS = load_columns()

META_CSV = """Instagram content export
Post ID,Account username,Description,Publish time,Post type,Reach,Views,Likes,Shares,Comments,Saves,Follows
101,pathvik,"Job offer, MBA prep, or a gap year? You don't have to guess.",10/27/2026 19:34,IG carousel,"1,200",1500,90,30,12,40,5
102,pathvik,We won't promise you a job. Here's what we do promise.,10/29/2026 19:31,IG reel,3000,4000,150,60,20,10,12
103,pathvik,What does a strategy analyst actually do all day?,10/31/2026 12:05,IG carousel,900,1000,80,20,6,45,2
"""

LINKEDIN_CSV = """Post title,Post link,Content Type,Created date,Impressions,Clicks,Likes,Comments,Reposts
A CSR plantation report full of photos tells you trees were planted.,https://lnkd.in/a,Document,27/10/2026 18:02,2400,40,60,9,5
Three questions to ask a CSR plantation partner before you sign.,https://lnkd.in/b,Text,29/10/2026 11:00,1800,22,30,4,2
"""


@pytest.fixture
def setup(tmp_path):
    store, an = Store(tmp_path), Analytics(tmp_path)
    data = yaml.safe_load((ROOT / "weeks" / "2026-10-26.yaml").read_text(encoding="utf-8"))
    import_plan(CFG, store, data)
    return store, an, tmp_path


def _write(tmp_path, name, text):
    p = tmp_path / name
    p.write_text(text, encoding="utf-8")
    return p


def test_date_order_detection():
    assert detect_date_order(["10/27/2026 19:34", "10/5/2026 10:00"]) == "mdy"
    assert detect_date_order(["27/10/2026 18:02"]) == "dmy"
    assert detect_date_order(["2026-10-27 18:02"]) == "iso"
    with pytest.raises(AnalyticsError):
        detect_date_order(["05/06/2026 10:00"])


def test_timezones_convert_to_ist():
    assert parse_datetime("2026-10-27T14:00:00Z", "iso").strftime("%H:%M") == "19:30"
    assert parse_datetime("10/27/2026 14:00", "mdy", file_offset_hours=0).strftime("%H:%M") == "19:30"


def test_meta_export_import_and_matching(setup):
    store, an, tmp = setup
    rows = read_export(_write(tmp, "meta.csv", META_CSV), COLS)
    assert rows[0]["reach"] == 1200 and rows[0]["format"] == "carousel" and rows[1]["format"] == "reel"
    result = an.add_rows(rows, "pathvik", "instagram", store)
    assert result == {"added": 3, "updated": 0, "matched": 3}
    rec = next(r for r in an.posts.values() if r["external_id"] == "101")
    assert rec["post_id"] == "2026-10-27-pathvik-instagram-career-choice-check"
    assert rec["theme"] == "educational"
    assert an.add_rows(rows, "pathvik", "instagram", store)["updated"] == 3  # re-import doesn't duplicate


def test_linkedin_export_uses_impressions(setup):
    store, an, tmp = setup
    rows = read_export(_write(tmp, "li.csv", LINKEDIN_CSV), COLS)
    assert rows[0]["posted_at"] == "2026-10-27T18:02" and rows[0]["reach"] is None and rows[0]["impressions"] == 2400
    assert an.add_rows(rows, "earth_osai", "linkedin", store)["matched"] == 2


def test_missing_columns_explain_the_fix(tmp_path):
    with pytest.raises(AnalyticsError, match="analytics_columns.yaml"):
        read_export(_write(tmp_path, "bad.csv", "Foo,Bar\n1,2\n"), COLS)


def test_history_feeds_slot_engine(tmp_path):
    an = Analytics(tmp_path)
    rows = [{"posted_at": f"2026-10-{d:02d}T18:00", "external_id": f"x{d}", "text": "", "permalink": "",
             "format": "single_image", "reach": 1000, "likes": 100, "comments": 0, "shares": 0, "saves": 0}
            for d in (5, 12, 19)]
    an.add_rows(rows, "pathvik", "instagram")
    an.add_followers("pathvik", "instagram", "2026-10-01", 1000)
    no_explore = load_config()
    no_explore.slots["spacing"]["explore_share"] = 0
    post = {"id": "p", "account": "pathvik", "platform": "instagram", "date": "2026-10-26", "idea_id": "i"}
    [r] = assign_slots([post], no_explore, history=an.history())
    assert r["slot_source"] == "own_history" and r["time"] == "18:00"


def test_audience_data_expires(tmp_path):
    an = Analytics(tmp_path)
    an.set_audience("pathvik", "instagram", {21: 500, 9: 100}, "2026-09-01")
    assert an.audience_data("2026-09-20") == {"pathvik": {"instagram": {"21": 500, "9": 100}}}
    assert an.audience_data("2026-12-01") == {}


def _seed_results(store, an, tmp):
    an.add_rows(read_export(_write(tmp, "meta.csv", META_CSV), COLS), "pathvik", "instagram", store)
    an.add_rows(read_export(_write(tmp, "li.csv", LINKEDIN_CSV), COLS), "earth_osai", "linkedin", store)


def test_weekly_report(setup):
    store, an, tmp = setup
    _seed_results(store, an, tmp)
    an.add_followers("pathvik", "instagram", "2026-10-25", 1800)
    an.add_followers("pathvik", "instagram", "2026-11-01", 1840)
    an.add_enquiry("earth_osai", "2026-10-30", 2, "CSR head via LinkedIn")
    store.set_status("2026-10-28-hifuel_advisory-linkedin-green-vs-carbon-credits", "posted", by="test")
    r = reports.build_report(CFG, store, an, "2026-10-26", "2026-11-01")
    pathvik = next(k for k in r["rows"] if k["account"] == "pathvik")
    assert pathvik["posts"] == 3 and pathvik["exposure"] == 5100
    assert pathvik["engagement_rate"] == pytest.approx((172 + 240 + 151) / 5100)
    assert pathvik["follower_growth"] == 40
    earth = next(k for k in r["rows"] if k["account"] == "earth_osai")
    assert earth["exposure_label"] == "impressions" and earth["save_rate"] is None
    assert r["enquiries"] == {"earth_osai": 2}
    assert any("no results imported" in n for n in r["notes"])
    assert r["top_posts"] and r["worked"] == []  # 3 posts can't support a format comparison
    md = reports.render_markdown(r)
    assert "| Pathvik | Instagram | 3 |" in md


def test_takeaways_need_three_posts_each(tmp_path):
    store, an = Store(tmp_path), Analytics(tmp_path)

    def row(i, fmt, eng):
        return {"posted_at": f"2026-11-{i + 2:02d}T19:00", "external_id": f"{fmt}{i}", "text": "", "permalink": "",
                "format": fmt, "reach": 1000, "likes": eng, "comments": 0, "shares": 0, "saves": 0}
    an.add_rows([row(i, "carousel", 80) for i in range(3)] + [row(i + 3, "single_image", 30) for i in range(3)],
                "pathvik", "instagram")
    r = reports.build_report(CFG, store, an, "2026-11-01", "2026-11-30", "monthly")
    assert any("carousels earned 2.7x" in w for w in r["worked"])
    assert r["priorities"] and r["priorities"][0].startswith("Do more of what worked")
    assert len(r["priorities"]) <= 3


def test_experiment_evaluation(tmp_path):
    store, an = Store(tmp_path), Analytics(tmp_path)
    exp = exps.add(an, "Carousels vs images", "Carousels get more saves", "pathvik", "format", "carousel",
                   start="2026-11-02", weeks=4)
    assert exps.evaluate(an, exp, {})["verdict"] == "pending"

    def row(i, fmt, eng):
        return {"posted_at": f"2026-11-{i + 2:02d}T19:00", "external_id": f"{fmt}{i}", "text": "", "permalink": "",
                "format": fmt, "reach": 1000, "likes": eng, "comments": 0, "shares": 0, "saves": 0}
    an.add_rows([row(i, "carousel", 80) for i in range(3)] + [row(i + 3, "reel", 40) for i in range(3)],
                "pathvik", "instagram")
    result = exps.evaluate(an, exp, {})
    assert result["verdict"] == "better" and "2.0x" in result["summary"]
    closed = exps.close(an, exp["id"], {}, note="Keep carousels for explainers")
    assert closed["status"] == "done" and "Keep carousels" in closed["result"]


def test_planner_request_includes_results_experiments_and_ideas(setup):
    store, an, tmp = setup
    _seed_results(store, an, tmp)
    exps.add(an, "Night slot", "Students engage more late", "pathvik", "hour_band", "night", start="2026-11-02")
    store.ideas["i1"] = {"text": "Reel: a day in the life of a product manager", "account": "pathvik", "status": "new"}
    store.ideas["i2"] = {"text": "Earth.OSAI map walkthrough", "account": "earth_osai", "status": "new"}
    req = build_request(CFG, store, "pathvik", "2026-11-02", "2026-11-08", [], "", [], an)
    assert "posts_with_results: 3" in req
    assert "Night slot" in req
    assert "a day in the life of a product manager" in req and "map walkthrough" not in req


def test_hub_pull_ideas_and_logged_results(setup):
    store, an, tmp = setup
    inbox = tmp / "inbox"
    (inbox / "ideas").mkdir(parents=True)
    (inbox / "results").mkdir()
    (inbox / "ideas" / "abc.json").write_text(json.dumps({"text": "Field visit video", "account": "", "by": "u_1",
                                                          "at": "2026-10-20T10:00:00Z", "status": "new"}))
    pid = "2026-10-28-founder_ashish-linkedin-proof-in-a-year"
    (inbox / "results" / f"{pid}.json").write_text(json.dumps(
        {"post_id": pid, "posted_at": "2026-10-29T08:45", "impressions": 3100, "reactions": 120, "comments": 18,
         "reposts": 6, "link": "https://lnkd.in/x"}))
    changes = hub.pull_extras(store, an, inbox)
    assert "New idea: Field visit video" in changes
    rec = next(r for r in Analytics(tmp).posts.values() if r.get("post_id") == pid)
    assert rec["impressions"] == 3100 and rec["date"] == "2026-10-29" and rec["theme"] == "founder_team_voice"
    assert Store(tmp).ideas["abc"]["text"] == "Field visit video"
