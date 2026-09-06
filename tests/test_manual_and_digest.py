import csv

from freelance_agent.config import Profile
from freelance_agent.digest import to_csv, to_markdown
from freelance_agent.models import Listing
from freelance_agent.sources.manual import ManualSource

SAMPLE = """Title: Financial model for SaaS startup
URL: https://www.upwork.com/jobs/~1
Budget: $500 fixed
Build a 3-statement financial model.
---
Title: Weekly SEO blog posts
URL: https://www.upwork.com/jobs/~2
Budget: $40/hour
Ongoing content writing for a finance blog.
"""


def test_manual_source_parses_multiple_entries(tmp_path):
    path = tmp_path / "manual_jobs.txt"
    path.write_text(SAMPLE, encoding="utf-8")

    listings = ManualSource(str(path)).fetch([])

    assert len(listings) == 2
    assert listings[0].title == "Financial model for SaaS startup"
    assert listings[0].url == "https://www.upwork.com/jobs/~1"
    assert listings[0].budget_text == "$500 fixed"
    assert "3-statement" in listings[0].description
    assert listings[1].title == "Weekly SEO blog posts"


def test_manual_source_skips_blank_entries(tmp_path):
    path = tmp_path / "manual_jobs.txt"
    path.write_text("Title: Only one\nURL: http://x\nBudget: $1\nSomething.\n---\n\n---\n", encoding="utf-8")

    listings = ManualSource(str(path)).fetch([])
    assert len(listings) == 1


def _profile():
    return Profile(
        keywords=["financial modeling"],
        exclude_keywords=[],
        target_income_inr_month=(300000, 400000),
        inr_per_usd=89.0,
        min_project_usd=150.0,
        min_hourly_usd=20.0,
        sources_enabled=[],
        wwr_feeds=[],
        top_n=25,
    )


def test_to_markdown_includes_target_and_listing_fields():
    listing = Listing(
        source="manual",
        title="Financial model for SaaS startup",
        url="https://www.upwork.com/jobs/~1",
        description="Build a 3-statement financial model.",
        budget_text="$500 fixed",
        score=15.0,
        match_reasons=["financial modeling"],
    )
    md = to_markdown([listing], _profile())
    assert "300,000" in md
    assert "400,000" in md
    assert "Financial model for SaaS startup" in md
    assert "$500 fixed" in md
    assert "https://www.upwork.com/jobs/~1" in md


def test_to_markdown_handles_no_matches():
    md = to_markdown([], _profile())
    assert "No matches" in md


def test_to_csv_writes_expected_columns(tmp_path):
    listing = Listing(
        source="manual",
        title="Gig",
        url="http://x",
        budget_text="$500",
        score=12.5,
        match_reasons=["financial modeling"],
    )
    out = tmp_path / "out.csv"
    to_csv([listing], str(out))

    with open(out, newline="", encoding="utf-8") as f:
        rows = list(csv.reader(f))
    assert rows[0] == ["score", "source", "title", "budget", "url", "matched_keywords"]
    assert rows[1] == ["12.5", "manual", "Gig", "$500", "http://x", "financial modeling"]
