from freelance_agent.config import Profile
from freelance_agent.models import Listing
from freelance_agent.scoring import rank, score_listing


def make_profile(**overrides):
    base = dict(
        keywords=["financial modeling", "data analysis"],
        exclude_keywords=["unpaid"],
        target_income_inr_month=(300000, 400000),
        inr_per_usd=89.0,
        min_project_usd=150.0,
        min_hourly_usd=20.0,
        sources_enabled=[],
        wwr_feeds=[],
        top_n=25,
    )
    base.update(overrides)
    return Profile(**base)


def test_matches_on_keyword_in_description():
    profile = make_profile()
    listing = Listing(
        source="test",
        title="Need help with a spreadsheet",
        url="http://example.com/1",
        description="Looking for financial modeling expertise for a startup.",
    )
    result = score_listing(listing, profile)
    assert result is not None
    assert "financial modeling" in result.match_reasons
    assert result.score > 0


def test_no_keyword_match_is_dropped():
    profile = make_profile()
    listing = Listing(source="test", title="Dog walker needed", url="http://example.com/2")
    assert score_listing(listing, profile) is None


def test_excluded_keyword_drops_listing_even_with_match():
    profile = make_profile()
    listing = Listing(
        source="test",
        title="Unpaid data analysis internship",
        url="http://example.com/3",
        description="Great learning opportunity, unpaid.",
    )
    assert score_listing(listing, profile) is None


def test_budget_below_minimum_is_dropped():
    profile = make_profile(min_project_usd=150.0)
    listing = Listing(
        source="test",
        title="Quick data analysis task",
        url="http://example.com/4",
        budget_usd_max=20.0,
    )
    assert score_listing(listing, profile) is None


def test_budget_above_minimum_scores_higher_than_no_budget():
    profile = make_profile(min_project_usd=150.0)
    with_budget = Listing(
        source="test",
        title="data analysis project",
        url="http://example.com/5",
        budget_usd_max=2000.0,
    )
    without_budget = Listing(
        source="test",
        title="data analysis project",
        url="http://example.com/6",
    )
    scored_with = score_listing(with_budget, profile)
    scored_without = score_listing(without_budget, profile)
    assert scored_with.score > scored_without.score


def test_rank_sorts_descending_and_filters_none():
    profile = make_profile()
    listings = [
        Listing(source="a", title="dog walker", url="http://example.com/7"),
        Listing(
            source="b",
            title="financial modeling gig",
            url="http://example.com/8",
            budget_usd_max=5000.0,
        ),
        Listing(
            source="c",
            title="data analysis and financial modeling",
            url="http://example.com/9",
        ),
    ]
    ranked = rank(listings, profile)
    assert len(ranked) == 2
    assert ranked[0].score >= ranked[1].score
    assert ranked[0].url == "http://example.com/8"
