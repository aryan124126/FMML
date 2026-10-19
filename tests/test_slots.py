import copy
from datetime import datetime

from hifuel.config import load_config
from hifuel.slots import assign_slots, history_scores

CFG = load_config()
NO_EXPLORE = copy.deepcopy(CFG)
NO_EXPLORE.slots["spacing"]["explore_share"] = 0

MON, SUN = "2026-10-26", "2026-11-01"  # Monday 26 Oct 2026, Sunday 1 Nov 2026


def post(id, account="pathvik", platform="instagram", day=MON, idea="i1"):
    return {"id": id, "account": account, "platform": platform, "date": day, "idea_id": idea}


def minutes(t):
    h, m = t.split(":")
    return int(h) * 60 + int(m)


def test_benchmark_for_students_on_weekday():
    [r] = assign_slots([post("p1")], NO_EXPLORE)
    assert r["slot_source"] == "benchmark"
    assert r["time"] in {"19:30", "21:30"}
    assert "starting hypothesis" in r["slot_reason"]


def test_business_audience_on_sunday_falls_back_with_warning():
    [r] = assign_slots([post("p1", account="earth_osai", platform="linkedin", day=SUN)], NO_EXPLORE)
    assert "consider moving" in r["slot_reason"]


def test_same_account_posts_are_spaced():
    results = assign_slots([post("p1", idea="a"), post("p2", idea="b")], NO_EXPLORE)
    assert abs(minutes(results[0]["time"]) - minutes(results[1]["time"])) >= 180


def test_daily_limit_warns():
    results = assign_slots([post(f"p{i}", idea=f"i{i}") for i in range(3)], NO_EXPLORE)
    assert "WARNING" in results[2]["slot_reason"]


def test_same_idea_across_accounts_is_spaced():
    results = assign_slots([
        post("a", account="hifuel_advisory", platform="linkedin", idea="esg"),
        post("b", account="earth_osai", platform="linkedin", idea="esg"),
    ], NO_EXPLORE)
    assert abs(minutes(results[0]["time"]) - minutes(results[1]["time"])) >= 120


def test_already_placed_posts_are_respected():
    existing = [{"account": "pathvik", "platform": "instagram", "idea_id": "x", "date": MON, "time": "19:30"}]
    [r] = assign_slots([post("p1")], NO_EXPLORE, already_placed=existing)
    assert abs(minutes(r["time"]) - minutes("19:30")) >= 180


def test_own_audience_data_wins():
    data = {"pathvik": {"instagram": {"22": 900, "20": 400, "9": 999}}}
    [r] = assign_slots([post("p1")], NO_EXPLORE, audience_data=data)
    assert r["slot_source"] == "own_audience"
    assert r["time"] == "22:00"  # 9:00 is outside the students' active hours


def _hist(weekday, hour, reach, eng, fmt="image", followers=1000):
    return {"account": "pathvik", "platform": "instagram", "weekday": weekday, "hour": hour,
            "reach": reach, "engagements": eng, "followers": followers, "format": fmt}


def test_history_scores_normalise_for_format_and_need_enough_posts():
    history = (
        [_hist(0, 18, 500, 50) for _ in range(3)]          # images at 18:00, good for images
        + [_hist(0, 20, 300, 30) for _ in range(3)]        # images at 20:00, weaker
        + [_hist(0, 21, 5000, 500, "reel") for _ in range(3)]  # reels: big reach, but average for reels
        + [_hist(0, 12, 9000, 900)]                        # one lucky post: not enough data
    )
    scores = history_scores(history, "pathvik", "instagram", min_posts=3)
    assert (0, 12) not in scores
    assert scores[(0, 18)] > scores[(0, 20)]
    assert abs(scores[(0, 21)] - 1.0) < 1e-9


def test_history_used_before_benchmark():
    history = [_hist(0, 18, 500, 50) for _ in range(3)]
    [r] = assign_slots([post("p1")], NO_EXPLORE, history=history)
    assert r["slot_source"] == "own_history"
    assert r["time"] == "18:00"


def test_explore_share_is_about_twenty_percent_and_stable():
    posts = [post(f"post-{i}", day="2026-10-2" + str(6 + i % 4), idea=f"i{i}") for i in range(400)]
    sources = [assign_slots([p], CFG)[0]["slot_source"] for p in posts]
    share = sources.count("explore") / len(sources)
    assert 0.12 < share < 0.28
    assert sources == [assign_slots([p], CFG)[0]["slot_source"] for p in posts]


def test_explore_stays_in_active_hours():
    for i in range(200):
        r = assign_slots([post(f"x{i}")], CFG)[0]
        if r["slot_source"] == "explore":
            assert 12 <= int(r["time"][:2]) <= 23


def test_higher_priority_account_gets_first_pick():
    # ICLC (priority 2) and Tranzent Foundation (priority 1) share an idea on the same evening slot.
    results = assign_slots([
        post("iclc", account="iclc", platform="facebook", idea="same"),
        post("tf", account="tranzent_foundation", platform="facebook", idea="same"),
    ], NO_EXPLORE)
    assert results[1]["time"] == "19:00"
    assert results[0]["time"] != "19:00"


def test_times_are_valid():
    for r in assign_slots([post(f"p{i}", idea=f"i{i}") for i in range(2)], CFG):
        datetime.strptime(r["time"], "%H:%M")


def test_other_platforms_only_need_an_hour_apart():
    results = assign_slots([post("ig", idea="a"), post("x", platform="x", idea="b")], NO_EXPLORE)
    gap = abs(minutes(results[0]["time"]) - minutes(results[1]["time"]))
    assert gap >= 60
    assert all("WARNING" not in r["slot_reason"] for r in results)
