import pytest

from hifuel.claims import check_post, is_blocked
from hifuel.config import load_config

CFG = load_config()


def make_post(**overrides):
    post = {
        "idea_id": "test",
        "account": "hifuel_advisory",
        "platform": "linkedin",
        "date": "2026-10-27",
        "theme": "educational",
        "pillar": "ESG and BRSR explainers",
        "format": "text",
        "hook": "BRSR is a reporting duty, not a branding exercise.",
        "caption": "Here is what a good first BRSR report gets right.",
        "cta": "What did your first report teach you?",
        "hashtags": ["#ESG", "#BRSR", "#CSR"],
        "alt_text": "",
        "thread_parts": [],
        "personalise_prompt": "",
        "design_brief": {"format_notes": "", "slides": [], "reel": {"duration_seconds": 0, "opening_hook": "", "shots": []},
                         "layout_notes": "", "colours": [], "image_prompt": ""},
        "claims_notes": [],
        "uses_ai_media": False,
        "shows_children": False,
        "collab_with": "",
        "key_date": "",
        "internal_notes": "",
    }
    post.update(overrides)
    return post


def checks(post, severity="block"):
    return {i["check"] for i in check_post(post, CFG) if i["severity"] == severity}


def test_clean_post_has_no_blocks():
    assert not is_blocked(check_post(make_post(), CFG))


@pytest.mark.parametrize("account,text,check", [
    ("tranzent_foundation", "Every tree you plant earns carbon credits.", "tree_carbon_credit"),
    ("tranzent_foundation", "Plant a sapling to offset your footprint.", "tree_carbon_credit"),
    ("earth_osai", "Earth.OSAI helps you get carbon credits fast.", "earth_osai_carbon_credit"),
    ("tranzent_foundation", "That's like taking 6M cars off the road.", "cars_equivalence"),
    ("tranzent_foundation", "Our plantations have a 95% survival rate.", "programme_numbers"),
    ("hifuel_advisory", "We are India's first growth ecosystem.", "superlatives"),
    ("hifuel_advisory", "We are the best partner for MSMEs.", "superlatives"),
    ("hifuel_advisory", "The best ESG firm in India.", "superlatives"),
    ("tranzent_foundation", "We're the largest tree-planting network.", "superlatives"),
    ("tranzent_foundation", "Comment YES to join the drive!", "engagement_bait"),
    ("tranzent_foundation", "Tag 3 friends who love trees.", "engagement_bait"),
    ("pathvik", "Get a guaranteed job after 6 weeks.", "education_guarantees"),
    ("pathvik", "Graduates earn 12 LPA.", "education_guarantees"),
    ("pathvik", "Only 2 seats left in this cohort.", "pricing_tricks"),
    ("pathvik", "Our students got placed at top firms.", "unrun_outcomes"),
    ("pathvik", "Learn from mentors from McKinsey.", "named_institutions"),
    ("iclc", "ICLC (Indian Climate Learning Championship) is here.", "iclc_acronym"),
    ("hifuel_advisory", "Hi-Fuel Advisory is hiring.", "company_spelling"),
    ("pathvik", "Every student gets a week-1 diagnostic interview.", "pathvik_not_built"),
    ("iclc", "Inspired by the Shankargarh 11 format.", "internal_term"),
    ("pathvik", "Pathvik, formerly Catalystra, is live.", "internal_term"),
    ("pathvik", "Register at [website link] today.", "placeholder"),
    ("pathvik", "Classes start on {{start_date}}.", "placeholder"),
    ("tranzent_foundation", "Proud to work with MoEFCC on this.", "unconfirmed_partner"),
])
def test_blocking_rules(account, text, check):
    assert check in checks(make_post(account=account, caption=text))


@pytest.mark.parametrize("account,text,check", [
    ("tranzent_foundation", "These trees are registered with Verra for carbon credits.", "tree_carbon_credit"),
    ("earth_osai", "Earth.OSAI does not issue carbon credits; it verifies plantations.", "earth_osai_carbon_credit"),
    ("tranzent_foundation", "Our target is a 95% survival rate.", "programme_numbers"),
])
def test_downgraded_to_flag(account, text, check):
    post = make_post(account=account, caption=text, claims_notes=[{"claim": "x", "source": "y", "year": "2026"}])
    assert check not in checks(post)
    assert check in checks(post, "flag")


@pytest.mark.parametrize("account,text", [
    ("pathvik", "No job guarantees. Just a real plan."),
    ("pathvik", "Neither comes with a job guarantee, and we say so up front."),
    ("pathvik", "What's your biggest doubt right now?"),
    ("founder_ashish", "What's the best question a field visit ever taught you?"),
    ("hifuel_advisory", "Poor data is leading to weak CSR reports."),
    ("hifuel_advisory", "Hi Fuel Advisory works with MSMEs."),
    ("earth_osai", "Carbon markets reward verified removals, not photo albums."),
])
def test_not_blocked(account, text):
    assert not is_blocked(check_post(make_post(account=account, caption=text), CFG))


def test_place_names_blocked_only_for_iclc():
    assert "internal_term" in checks(make_post(account="iclc", caption="Students near Prayagraj will compete."))
    assert "internal_term" not in checks(make_post(account="tranzent_foundation", caption="A farmer near Prayagraj."))


def test_hashtag_spelling_is_allowed():
    assert "company_spelling" not in checks(make_post(hashtags=["#HiFuelAdvisory", "#ESG", "#CSR"]))


def test_co2_per_tree():
    wrong = make_post(account="born_green", caption="Every 10 trees absorb 2 t CO2 per 10 trees each year.")
    assert "co2_per_tree" in checks(wrong)
    unlabelled = make_post(account="born_green", caption="A tree absorbs 22 kg CO2 per tree per year.")
    assert "co2_per_tree" in checks(unlabelled)
    ok = make_post(account="born_green", caption="Estimated sequestration: ~22 kg CO2 per tree per year.",
                   claims_notes=[{"claim": "22 kg", "source": "internal standard", "year": "2026"}])
    assert "co2_per_tree" not in checks(ok)


def test_statistics_need_sources():
    stat = make_post(caption="Only 40% of CSR spend is ever audited.")
    assert "statistic_source" in checks(stat)
    sourced = make_post(caption="Only 40% of CSR spend is ever audited.",
                        claims_notes=[{"claim": "40%", "source": "Example report", "year": "2025"}])
    assert "statistic_source" not in checks(sourced)
    assert "statistic_source" in checks(sourced, "flag")


def test_prices():
    assert "price" in checks(make_post(account="pathvik", caption="Founding cohort fee: ₹999."))
    # Pathvik posts carry no prices for now (19 Oct 2026), so even the standard price is blocked.
    assert "price" in checks(make_post(account="pathvik", caption="The Graduate Career Accelerator is ₹4,999."))
    confirmed = make_post(account="born_green", caption="Plant a tree from ₹460 per tree.")
    assert "price" not in checks(confirmed)
    assert "price" in checks(confirmed, "flag")


def test_large_amounts_are_statistics_not_prices():
    post = make_post(caption="Companies with a CSR obligation of ₹10 crore or more must commission an assessment.")
    assert "price" not in checks(post)
    assert "statistic_source" in checks(post)


def test_parent_account_may_quote_initiative_prices():
    post = make_post(account="tranzent_foundation", caption="Plant a Born Green tree from ₹460 per tree.")
    assert "price" not in checks(post)


def test_children_need_consent():
    post = make_post(account="iclc", shows_children=True)
    assert "children" in checks(post)
    assert "children" not in checks({**post, "consent_confirmed": True})


def test_ai_media_label():
    post = make_post(uses_ai_media=True)
    assert "ai_label" in checks(post)
    labelled = make_post(uses_ai_media=True, cta="Image: AI-assisted.")
    assert "ai_label" not in checks(labelled)


def test_length_limits():
    assert "length" in checks(make_post(platform="x", caption="a" * 300, hashtags=[]))
    thread = make_post(platform="x", format="thread", hashtags=[], thread_parts=["short", "b" * 290])
    assert "length" in checks(thread)
    assert "length" not in checks({**thread, "thread_parts": ["short", "fine"]})


def test_numbers_are_always_listed_for_reviewer():
    issues = check_post(make_post(caption="12 live classes over 6 weeks."), CFG)
    assert any(i["check"] == "numbers" and "12" in i["message"] for i in issues)


def test_no_promo_on_sensitive_days():
    promo = make_post(date="2027-01-30", theme="initiative_promo")
    assert "sensitive_day" in checks(promo)
    assert "sensitive_day" not in checks({**promo, "theme": "educational"})


def test_iclc_promo_in_exam_season_is_flagged():
    assert "season" in checks(make_post(account="iclc", date="2027-03-02", theme="initiative_promo"), "flag")
