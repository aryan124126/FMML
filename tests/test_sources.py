from unittest.mock import MagicMock, patch

import requests

from freelance_agent.sources.remoteok import RemoteOKSource
from freelance_agent.sources.remotive import RemotiveSource
from freelance_agent.sources.weworkremotely import WeWorkRemotelySource


def _mock_response(json_data=None, content=None, status_ok=True):
    resp = MagicMock()
    if status_ok:
        resp.raise_for_status = MagicMock()
    else:
        resp.raise_for_status.side_effect = Exception("boom")
    if json_data is not None:
        resp.json = MagicMock(return_value=json_data)
    if content is not None:
        resp.content = content
    return resp


def test_remoteok_skips_legal_notice_and_filters_by_keyword():
    fixture = [
        {"legal": "notice, not a job"},
        {
            "position": "Senior Data Analyst",
            "url": "https://remoteok.com/remote-jobs/1",
            "description": "<p>We need data analysis skills.</p>",
            "tags": ["data", "analytics"],
            "salary_min": 60000,
            "salary_max": 90000,
            "date": "2026-01-01",
        },
        {
            "position": "Warehouse Forklift Operator",
            "url": "https://remoteok.com/remote-jobs/2",
            "description": "Drive a forklift.",
            "tags": ["logistics"],
        },
    ]
    with patch("freelance_agent.sources.remoteok.requests.get", return_value=_mock_response(json_data=fixture)):
        source = RemoteOKSource()
        listings = source.fetch(["data analysis"])

    assert len(listings) == 1
    assert listings[0].title == "Senior Data Analyst"
    assert listings[0].budget_usd_min == 60000
    assert "data analysis" in listings[0].description.lower()


def test_remotive_dedupes_by_url_across_keywords():
    fixture = {
        "jobs": [
            {
                "title": "Financial Analyst",
                "url": "https://remotive.com/job/1",
                "description": "Build financial models.",
                "salary": "$4000/mo",
                "publication_date": "2026-01-01",
                "category": "Finance",
            }
        ]
    }
    with patch("freelance_agent.sources.remotive.requests.get", return_value=_mock_response(json_data=fixture)):
        source = RemotiveSource()
        listings = source.fetch(["financial modeling", "financial analysis"])

    # same URL returned for both keyword queries -> deduped to one listing
    assert len(listings) == 1
    assert listings[0].url == "https://remotive.com/job/1"


def test_remotive_survives_one_keyword_failing():
    good = _mock_response(json_data={"jobs": []})
    with patch(
        "freelance_agent.sources.remotive.requests.get",
        side_effect=[requests.exceptions.RequestException("network error"), good],
    ):
        source = RemotiveSource()
        listings = source.fetch(["bad query", "ok query"])
    assert listings == []


RSS_FIXTURE = b"""<?xml version="1.0"?>
<rss><channel>
<item>
  <title>Remote Copywriter</title>
  <link>https://weworkremotely.com/jobs/1</link>
  <description>Need someone for content writing and copywriting.</description>
  <pubDate>Mon, 01 Jan 2026 00:00:00 +0000</pubDate>
</item>
<item>
  <title>Remote Plumber</title>
  <link>https://weworkremotely.com/jobs/2</link>
  <description>Fix pipes remotely somehow.</description>
  <pubDate>Mon, 01 Jan 2026 00:00:00 +0000</pubDate>
</item>
</channel></rss>
"""


def test_weworkremotely_filters_by_keyword_across_feeds():
    with patch(
        "freelance_agent.sources.weworkremotely.requests.get",
        return_value=_mock_response(content=RSS_FIXTURE),
    ):
        source = WeWorkRemotelySource(feed_urls=["https://weworkremotely.com/categories/x.rss"])
        listings = source.fetch(["copywriting"])

    assert len(listings) == 1
    assert listings[0].title == "Remote Copywriter"


def test_weworkremotely_skips_failing_feed_without_raising():
    with patch(
        "freelance_agent.sources.weworkremotely.requests.get",
        side_effect=requests.exceptions.RequestException("404"),
    ):
        source = WeWorkRemotelySource(feed_urls=["https://weworkremotely.com/categories/missing.rss"])
        listings = source.fetch(["copywriting"])
    assert listings == []
