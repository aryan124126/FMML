# Freelance work search agent — setup

## What this is

A small Python tool that pulls freelance/remote-contract listings from a few
sources, scores them against your skills, and ranks them so you're not
manually scrolling job boards every day. It does **not** scrape Upwork,
Fiverr, or similar platforms directly — those forbid automated scraping in
their terms of service. For those, you paste job posts in by hand (see
"Upwork / Fiverr / PeoplePerHour" below) and they get scored the same way as
everything else.

**Important:** this was built and tested from an environment whose outbound
network access is restricted to a small allowlist (pypi, npm, github,
anthropic's API) — remoteok.com, weworkremotely.com, freelancer.com, and
similar sites were all blocked there. So the parsing logic is verified with
offline fixtures and unit tests (`pytest`, all passing), but **not** against
each platform's live response right now. Run it once on your own machine
(normal internet access) and check the output looks sane before trusting it
day to day — schemas drift and a source may need a small fix.

## Install

```bash
cd FMML
python3 -m pip install -r requirements.txt
```

## Tune it to you

Edit `freelance_agent/config.yaml`:
- `keywords` — phrases that must appear in a listing for it to count as a
  match. Defaults cover content writing, data/analytics, and financial
  analysis — trim or add to match what you actually want to do.
- `exclude_keywords` — kills a listing outright even if a keyword matches
  (e.g. "unpaid", "equity only").
- `target_income_inr_month` / `min_project_usd` / `min_hourly_usd` — used to
  filter out listings too small to matter and to weight scoring. Adjust
  `inr_per_usd` if the exchange rate has moved a lot.
- `sources_enabled` — which sources to query.

## Run it

```bash
python3 -m freelance_agent.cli
```

Useful flags:
- `--out digest.md` — write the markdown digest to a file instead of stdout
- `--csv results.csv` — also export a spreadsheet-friendly CSV
- `--top 10` — only keep the top 10 by score
- `--manual-file manual_jobs.txt` — include pasted-in listings (see below)
- `--email` — send the digest by email (see "Email digest" below)

## Upwork / Fiverr / PeoplePerHour (manual paste-in)

These sites don't have a public search API, and automating around their
bot protection would violate their terms of service, so this tool doesn't do
that. Instead:

1. Copy `freelance_agent/manual_jobs.example.txt` to `manual_jobs.txt`.
2. When you're browsing Upwork etc., paste each job's title, URL, budget,
   and full description into that file, separated by a line containing just
   `---`.
3. Run with `--manual-file manual_jobs.txt` — those entries get scored and
   ranked exactly like everything else.

`manual_jobs.txt` is gitignored so your pasted job text never gets committed.

## Freelancer.com

Freelancer.com's API needs a personal OAuth token even for read-only
searches:

1. Go to https://developers.freelancer.com, sign in, and generate a personal
   access token (Manage Apps → create a token for your own account).
2. `export FREELANCER_OAUTH_TOKEN=your_token_here`

Without the token this source just logs a notice and contributes nothing —
it won't break the rest of the run.

## Email digest

Uses Gmail SMTP with an **App Password** (not your normal Gmail password —
Google requires this for third-party SMTP access):

1. Turn on 2-Step Verification on the Google account, then create an App
   Password at https://myaccount.google.com/apppasswords.
2. Set:
   ```bash
   export GMAIL_ADDRESS=your_address@gmail.com
   export GMAIL_APP_PASSWORD=the_16_char_app_password
   export EMAIL_TO=where_you_want_the_digest_sent@gmail.com   # optional, defaults to GMAIL_ADDRESS
   ```
3. Run with `--email`.

## Running it daily

Simplest option is a cron job on any machine that's on most of the time:

```cron
0 8 * * * cd /path/to/FMML && /usr/bin/python3 -m freelance_agent.cli --manual-file manual_jobs.txt --email >> agent.log 2>&1
```

(On Windows, use Task Scheduler with the same command.) Environment
variables for the email/API tokens need to be available to that cron
session — either export them in the crontab itself or source a `.env`-style
file from a wrapper script before invoking the CLI.

## A note on the income target

₹3–4L/month (~$3,400–4,500) is realistic on freelance platforms, but rarely
from one-off small gigs — it usually comes from landing 1-3 recurring
retainer clients (a weekly content package, an ongoing data/reporting
contract) rather than a stream of $50 tasks. The financial-analysis and
data-work keywords in the default config tend to carry higher per-project
budgets than generic writing work, which is worth keeping in mind when you
prioritize which matches to actually apply to.

## Running the tests

```bash
python3 -m pytest
```

All source-parsing tests run against saved fixture data (no network calls),
so they'll pass in any environment.
