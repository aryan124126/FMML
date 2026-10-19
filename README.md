# Hi Fuel Social Planner

An AI assistant that **plans, writes and times** social media posts for the Hi Fuel group (Hi Fuel Advisory, Tranzent Foundation, Pathvik, Earth.OSAI, ICLC and the founder/team advocacy kits). It never publishes anything. Every post goes to a human for approval. The full brief is in [`CLAUDE.md`](CLAUDE.md).

## What it does (Phase 1)

| Part | What you get |
|---|---|
| **Planner** | Drafts a week of posts per account and platform (Instagram, LinkedIn, Facebook, WhatsApp Channel, X): hook, caption, CTA, hashtags, alt text, and a design brief (slides, Reel script, layout, colours). |
| **Claims check** | Every draft is checked against the hard content rules (CO2 figures, carbon-credit wording, superlatives, unsourced stats, job guarantees, prices, partner names, children, AI media, internal terms). "Must fix" items block approval; "Check" items are listed for the reviewer. |
| **Best time to post** | Each post gets a time in IST, and it says where the time came from: your own audience data, your own past posts, or a benchmark (a starting guess until real data exists). About 20% of posts test new time slots. It also spaces posts out so the same account doesn't post too close together. |
| **Team Hub** | A private web page for the team: the week's board, review queue (approve / needs changes / reject / edit), advocacy kits, ideas box, announcements, and the week's content mix. |
| **Exports** | Approved posts as a spreadsheet (CSV for Google Sheets/Excel), a calendar file with reminders (.ics), and a copy-ready caption document. |

Not built yet (Phase 2): importing analytics exports, performance reports, the experiment log and monthly growth report, and live Instagram/LinkedIn connections.

## How a week works

You can do all of this by chatting with Claude in this project. Claude runs the commands for you.

1. **Plan:** "Plan next week. Campaigns: ICLC school outreach, Pathvik applications open."
2. **Review:** your manager and the founder open the Team Hub, approve, edit or send back each post. Blocked posts can't be approved until fixed.
3. **Sync:** "Pull the approvals from the hub." Claude applies the decisions, re-checks any edited text, and pushes the updated checks back to the hub.
4. **Export:** "Export the approved posts." You get the spreadsheet, calendar file and caption doc to schedule in Meta Business Suite / LinkedIn.

## Setup (only needed to run it yourself)

```bash
pip install -r requirements.txt
export ANTHROPIC_API_KEY=your-key   # from console.anthropic.com; never commit it
```

## Commands

```bash
python -m hifuel plan --start 2026-10-26 --campaign "ICLC school outreach"   # needs an API key
python -m hifuel import samples/sample_week.yaml --sample   # load drafts written in chat (no API key needed)
python -m hifuel list --start 2026-10-26
python -m hifuel show <post-id>
python -m hifuel status <post-id> approved --by "Manager"
python -m hifuel check                       # re-run the claims check (after changing rules or facts)
python -m hifuel export --start 2026-10-26   # approved posts -> data/exports/
python -m hifuel hub-push                    # prepare files for the Team Hub
python -m hifuel hub-pull <folder>           # apply reviewers' decisions downloaded from the hub
python -m pytest                             # run the tests
```

## Changing things without code

Everything about accounts, brands and rules lives in `config/`:

- `accounts.yaml`: accounts, initiatives and people: voice, colours, pillars, hashtags, confirmed facts, things not to say, allowed prices, posts per week. **Add a new initiative by copying a block.**
- `claims_rules.yaml`: the content rules as patterns.
- `time_slots.yaml`: benchmark times per audience and spacing rules.
- `key_dates.yaml`: festivals, national and environmental days, sensitive days, and seasons.
- `platforms.yaml`: character limits, hashtag counts and formats.
- `prompts/system.md`: the instructions Claude follows when writing.

## Cost

Planning uses Claude Opus 5.5 ($4 per million input tokens, $20 per million output tokens). Each run prints its cost. A full week across all accounts should cost roughly $1–3; check the first real run before relying on that.
