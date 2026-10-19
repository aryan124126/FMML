# CLAUDE.md — Social Media Assistant (Hi Fuel group)

_Context brief for building an AI social media assistant. Prepared 19 Oct 2026 by Aryan Srivastava (Analyst, R&D, Hi Fuel Advisory). Read this fully before writing any code. Items marked **[CONFIRM]** are not settled; ask Aryan before assuming. Items marked **[INTERNAL]** must never appear in public posts until approved._

---

## 1. What we are building (and what we are not)

An AI **social media assistant** for the Hi Fuel group. It has two jobs:

- **A. Initiative content:** plan, write and time posts for the group's initiatives (Pathvik, Earth.OSAI, ICLC, Born Green and others).
- **B. Company growth:** grow the reach and engagement of the **company itself**, meaning Hi Fuel Advisory and Tranzent Foundation as organisations, separate from any single initiative (see §7).

It helps the team **plan, write and time** posts. It does **not** publish anything on its own.

**In scope**
1. **Content calendar:** a weekly/monthly plan per account and platform, with a theme mix (educational, impact story, initiative/promo, behind-the-scenes, founder/team voice, engagement).
2. **Post content:** hook (first line), caption, hashtags, call to action, alt text, platform variants (Instagram, LinkedIn, Facebook, WhatsApp).
3. **Design brief per post:** format (single image, carousel, Reel, story), slide-by-slide text, Reel script with shot list and on-screen text, layout notes, brand colours, and an image-generation prompt if AI imagery is used.
4. **Best-time-to-post engine:** a recommended date and time slot for each post, from the account's own data first (see §6).
5. **Review queue:** every post goes to a human for approval before anyone schedules or posts it.
6. **Learning loop:** after posts go live, pull performance numbers, report what worked, and adjust timing, formats and topics.
7. **Growth toolkit:** advocacy kits for founder/team LinkedIn posts, a repurposing engine (one idea → many formats), an experiment log, and a monthly growth report (see §7).
8. **Team Hub:** a polished, private web app for the team only. It shows what's lined up, collects reviews and ideas, carries announcements, and reports engagement and growth. Aryan controls it, through the agent in chat (see §8).

**Out of scope (for now)**
- Auto-publishing, auto-replying to comments or DMs, buying ads, buying followers.
- Posting on behalf of any person's personal profile. The agent only **drafts** posts for founders/team; they post themselves.
- Scheduling is **a plan + export** (calendar file, sheet, reminders). A human schedules in Meta Business Suite / LinkedIn or posts manually. Optional later phase: push approved drafts into a scheduler, still behind human approval.

---

## 2. The organisation

The company was formerly **Tranzent**. The advisory arm is now **Hi Fuel Advisory**; the impact arm is **Tranzent Foundation**. Spell it exactly **"Hi Fuel Advisory"** (space, no hyphen). Founder: **Ashish Srivastava**. Based in Noida (Logix Mall, Wave City Center, Sector 32), with an office in Okhla, New Delhi.

### 2.1 Company accounts (the organisations themselves)

| Account | What it is | Key facts | Colours |
|---|---|---|---|
| **Hi Fuel Advisory** (hifueladvisory.lovable.app) | Multidisciplinary, execution-oriented "growth ecosystem" for startups, MSMEs, enterprises, government, NGOs, CSR leaders, investors | Tagline: "Fueling businesses. Powering growth. Building legacies." Positioning: "Not reports. Not decks. Outcomes." 10 practices, incl. Sustainability & ESG and CSR & Social Impact. Hi Fuel Growth Framework™ = Hear → Identify → Fuel → Upgrade → Expand → Lead. O.L.I.V.E.R Framework (Outcome Led Integrated Value & Execution Roadmap). Process: Discover → Diagnose → Design → Deliver → Drive Growth. Upcoming insights: ESG Readiness Index, CSR & Social Impact Review, India Business Growth Outlook 2027 | Deep emerald #064e3b |
| **Tranzent Foundation** (tranzentfoundation.in, Instagram @tranzentfoundation) | Impact consulting for nonprofits, philanthropies and companies | Tagline: "Navigating Change, Creating Impact." Verticals: Advisors, Compound, Data Insights, Media (Impact Sandesh), Research, Design & Implement, Waste Management. Green Credits service: Carbon Footprint Assessment → Offset Strategy → Implementation → Monitoring & Reporting. Press coverage shown on site: Hindustan Times, Dainik Jagran, Amar Ujala, I-next and others | **[CONFIRM]** |
| **Hi Fuel Media** | Group PR/media arm (issued the Pathvik press release; runs the Digital PR-Media Movement) | | **[CONFIRM]** |

### 2.2 Initiatives, in priority order

**Major initiatives right now: Pathvik and Earth.OSAI.** ICLC is the next priority, because the company wants schools signed in the coming months.

**1. Pathvik** (formerly *Catalystra*, renamed 07 Oct 2026). **Major.**
- Live online, mentor-led career programmes for undergraduates and graduates. Tagline: **"Clarity before career."**
- Graduate Career Accelerator: 6 weeks, 12 live classes, ₹4,999 incl. GST. Consulting, Strategy & Product Mentorship: 8 weeks, 16 live classes, ₹14,999 incl. GST. Cohorts of 30. Placement assistance included, with **no job guarantee**.
- First-cohort pricing is **not decided** (a token ₹499–999 founding fee was suggested) **[CONFIRM before any price post]**.
- Planned but **not yet built**: week-1 diagnostic interview, verifiable certificate IDs. Don't advertise these as live.
- Website, pitch film and old email (hello@catalystra.in) still say Catalystra. **Use "Pathvik" only; domain/email/handles [CONFIRM].**
- Audiences: students aged about 19–24 (Instagram), their parents, and colleges/placement cells as institutional partners (LinkedIn).
- Colours: navy #140F2F, violet #8B7BFF, orange #FE6A3C.

**2. Earth.OSAI** (earthosai.lovable.app). **Major.**
- "Verified Reforestation Infrastructure": a platform to plant, track and verify environmental impact at scale, with geo-tagged trees, ESG reports and APIs.
- Suggested positioning (an earlier internal recommendation, **[CONFIRM]**): verified plantation monitoring for **corporate CSR**. Indian companies under Section 135 of the Companies Act must spend on CSR and report it, and tree-planting CSR is hard to verify. Large CSR projects also need independent impact assessment, and listed companies report under BRSR.
- Audiences: CSR heads, CSR implementing agencies/NGOs, ESG/BRSR teams, forest/environment officials. Mainly LinkedIn.
- Content angle: "proof, not photo albums": how verification works, survival tracking, dashboards and reports. **Never** claim it issues carbon credits (see §3).
- Site content is a JavaScript app and couldn't be read; product features, team and numbers are **[CONFIRM]**.

**3. ICLC: Sustainability Championship for schools.** **Next priority.**
- A sustainability championship for students in **Classes 6–9**. Per Aryan, the outline is ready. The goal now is to **pitch it to schools and publicise it widely**, aiming to sign **3–4 school clients in the coming months**.
- Full form of "ICLC": **Aryan is confirming it; don't guess or expand the acronym in any output until it's added here.** Launch date, format, price and prizes are also **[CONFIRM]**.
- Related internal work, all **[INTERNAL]** (don't post details until approved):
  - **RWLOS** (Real World Learning Operating System): a year-long, gamified edtech concept. Students solve real problems from village development and ecological restoration around the Loni river, Shankargarh block, Prayagraj district. Each class competes separately.
  - **"Shankargarh 11"**: a drafted 11-day championship spec (one problem domain a day, 5–10 minutes daily, live leaderboard, capstone). How it relates to ICLC is **[CONFIRM]**; it may be the same thing under a working name.
- Audiences and the message for each:
  - **Principals and school owners** (decision-makers): student outcomes, low teacher workload, a credible certificate, a safe and simple process.
  - **Eco Club teachers** (the internal champion): Indian schools run Eco Clubs under Mission LiFE / National Green Corps, so ICLC can make their reporting easier and give them ready content **[verify current figures before quoting]**.
  - **Parents:** certificate and recognition for the child's portfolio, real-world learning without extra study load.
  - **CSR funders:** sponsoring schools or districts, with measurable reach.
- Social media goals for ICLC: (a) a launch/teaser campaign, (b) credibility content for principals on LinkedIn, (c) a waitlist/expression-of-interest link, (d) during the championship, a public campaign layer such as daily themes, school shout-outs and a winners' showcase.
- **Child-safety rules apply in full** (§3, rules 13–14): no child names or faces without verifiable parental consent; leaderboards show handles only.

**4. Other Tranzent Foundation movements** (lower priority; include in the calendar as impact stories)
- **Born Green:** geo-tagged trees planted in a child's name, from ₹460 per tree. Native species; blockchain-based tracking claimed; gamified leaderboards for RWAs and schools.
- **Greenpreneur:** agri-waste micro-enterprises (biochar, vermicompost, biogas, pellets) with NSDC-certified training; MNNIT Allahabad incubator partnership claimed.
- **S.H.I.N.E** (Social Heroes Inspiring New Era): a changemaker programme.
- **Digital PR-Media Movement** (Hi Fuel Media).

**[CONFIRM] Which accounts and handles exist today, and which are in v1?** Build so accounts, initiatives and platforms are config, not code, because new initiatives will keep being added.

### 2.3 Voice per account
- **Hi Fuel Advisory:** confident, outcome-led, crisp business English for founders, CXOs, CSR and ESG heads. Specific, no fluff, no jargon stacking.
- **Tranzent Foundation and its movements:** warm, hopeful, community-driven, grounded in real people and places (RWAs, schools, villages). Hindi/Hinglish is fine for community posts **[CONFIRM]**.
- **Pathvik:** friendly, honest, student-first. Short sentences, relatable doubts. Its signature is honesty: **no job guarantees, just a real plan.**
- **Earth.OSAI:** precise, evidence-first, quietly technical. Data and maps over adjectives.
- **ICLC:** two registers. With schools and CSR funders: credible and outcome-focused. With students and parents: energetic and playful, never childish.
- **Founder/team personal posts:** first person, real experience, opinions in their own words. Never corporate copy pasted onto a person.

---

## 3. Hard content rules (the agent must enforce these)

These come from real accuracy problems already found on the group's sites. Treat them as validation checks that block a draft, not as style tips.

**Environmental claims (Tranzent / Born Green / Earth.OSAI / ICLC)**
1. CO₂ per tree: use **~22 kg CO₂ per tree per year**, labelled **"estimated sequestration."** Never use the "2 t per 10 trees" figure on the Born Green page (~9× higher; inconsistent).
2. Never call tree planting a **"carbon credit"** or **"offset"** unless a registry issuance exists (Verra, Gold Standard, or India's Green Credit Programme). Say "plantation impact" or "estimated sequestration."
3. Don't repeat the **"6M cars off the road"** equivalence (it mixes lifetime and annual tonnes).
4. Don't name partners (MoEFCC, SBI Foundation, etc.) based on logos on the site; the logo files are reused across names. Partner associations must be confirmed first.
5. Survival rate (95%), 2050 targets and other programme numbers: only as "target" or "claimed", never as verified results.

**General**
6. No **"India's first…"** or other superlatives, and no unsourced stats (e.g., Hi Fuel's "80% / 70%" figures).
7. Every statistic needs a source and year in the internal notes, so a reviewer can check it.
8. No engagement bait ("comment YES to win", "tag 10 friends"), no fake urgency, no bought followers, likes or reviews, no invented testimonials.

**Pathvik and ICLC (education ads; India's CCPA 2024 coaching guidelines)**
9. No "100% placement", "guaranteed job", rank or marks promises, or salary claims. Say what placement assistance actually includes, or leave it out.
10. No struck-through "original" prices and no fake scarcity ("only 2 seats left") unless true.
11. No outcomes or testimonials from cohorts or championships that haven't run. Scores in visuals must be marked "illustrative."
12. No named mentors, colleges, schools or companies unless confirmed in writing.

**Children and privacy (ICLC, Born Green, any school content)**
13. No child's name, face, school + class combination or location without **verifiable parental consent** (India's DPDP Act and Rules). Default to backs-of-heads, hands, group shots from a distance, illustrations, or anonymised handles.
14. No personal data of students or beneficiaries in captions, comments or the agent's own logs beyond what's needed.

**AI-generated media**
15. India's IT Rules amendment (in force 20 Feb 2026) covers synthetically generated content. Any post with an AI-generated or AI-edited image, video or voice of real people must carry an **"AI-assisted"** label in the caption, plus the platform's AI label where available. Example: the Pathvik team photo is an AI composite.

Every draft runs through a **claims check** that flags any number, superlative, partner or school name, guarantee, price, child image or AI media, and lists them for the reviewer.

---

## 4. Users and workflow

- **Users:** Aryan (builds and operates), his manager (assigns and approves), the founder (approves Pathvik, ICLC and his own posts). Non-developers will use it, so outputs must be readable without a terminal.
- **Weekly loop:**
  1. Input: accounts, period, goals/campaigns (e.g., "ICLC school outreach", "Pathvik applications open", "Earth.OSAI CSR season"), any fixed dates.
  2. The agent drafts the calendar, posts, design briefs, recommended times and the advocacy kit.
  3. The claims check runs; issues are listed per post.
  4. A human approves, edits or rejects each post.
  5. Approved posts are exported for scheduling.
  6. After posting, performance data comes back in; the agent reports what worked and adjusts.
- **Calendar awareness (India):**
  - Festivals and national days: Diwali, Holi, Independence Day, Republic Day, etc.
  - Environmental days: Earth Day 22 Apr, World Environment Day 5 Jun, Van Mahotsav in the first week of July.
  - **CSR budgeting season** (Earth.OSAI, Hi Fuel): companies plan CSR around the April–March financial year **[CONFIRM best pitch months]**.
  - **School calendar** (ICLC): admissions, exam periods, vacations, and when principals set the year's activity plan. Avoid launches during exams and major festivals.
  - **Academic/placement cycle** (Pathvik): placement season, semester exams, results.
  - Avoid tone-deaf promotional posts on sensitive days.

---

## 5. Content engine

For every account, the agent works from **content pillars** (topics) set in config, so the mix stays balanced and on-brand. Starting pillars (to be tuned with data):

| Account | Pillars |
|---|---|
| Hi Fuel Advisory | ESG and BRSR explainers · CSR law and practice (Section 135) · green credits vs carbon credits, India's carbon market (explainers, carefully sourced) · founder point of view · frameworks as carousels (HI-FUEL, O.L.I.V.E.R) · Insights launches (ESG Readiness Index, etc.) · client stories (only with written consent) · team and culture |
| Tranzent Foundation | Field stories (one person, one place, one change) · movement updates (Born Green, Greenpreneur, S.H.I.N.E) · calls to volunteer/partner (RWAs, schools, CSR) · press coverage (link to the article) · behind-the-scenes |
| Pathvik | Career-clarity tips · "a day in the life of" industry roles · mentor insights (named only when confirmed) · programme details and application steps · student doubts answered |
| Earth.OSAI | How verification works · why CSR plantations need proof · dashboard/map walkthroughs · field visuals · regulation explainers |
| ICLC | Why real-world sustainability learning matters · what the championship looks like · for principals/Eco Club teachers · teaser countdown · (live) daily themes and shout-outs |

**Repurposing engine:** one source idea (e.g., an ESG explainer) becomes a LinkedIn text post, a carousel, a 20–30 s Reel script, a WhatsApp/Channel message and a founder-voice version, each adapted, not copy-pasted (platforms penalise duplicates; see §7).

---

## 6. Best-time-to-post logic

Priority order. The agent must say which source each recommendation came from:

1. **The account's own audience activity.** Instagram's Graph API exposes an `online_followers` insight (hourly breakdown of when followers are online), available only for the **last 30 days**. Needs a professional (Business/Creator) account and the `instagram_manage_insights` permission. May return nothing for small accounts; handle that gracefully.
2. **The account's own past post performance:** reach and engagement rate by day-of-week × hour slot, normalised for follower count at the time and for format (Reel vs carousel vs image).
3. **Fallback benchmarks** for Indian audiences (IST), clearly labelled as **starting hypotheses**, to be replaced by real data after 4–6 weeks.
4. **Experimentation:** rotate slots deliberately (simple explore/exploit, e.g., ~20% of posts in untested slots) so the model keeps learning.

Also apply:
- All times in **IST (Asia/Kolkata)**.
- Spacing rules: max posts per account per day, a minimum gap between posts, and no two group accounts posting near-identical content in the same hour.
- Different audiences keep different clocks:
  - Students (Pathvik): evenings and late nights.
  - Founders, CSR heads and principals (Hi Fuel, Earth.OSAI, ICLC on LinkedIn): weekday business hours.
  - Parents and RWAs (Born Green, ICLC parent content): evenings and weekends.

---

## 7. Growing the company's own reach and engagement (Hi Fuel Advisory & Tranzent Foundation)

**Goal:** build the organisations' own audience, credibility and inbound interest, separately from any initiative. Every initiative's success should also strengthen the parent brand.

The platform facts below come from third-party industry reports (2026). Treat them as working assumptions to test against our own data, not as guarantees.

### 7.1 LinkedIn: lead with people, anchor with the page
- Industry studies in 2026 report that **company-page organic reach is very low** (often cited at roughly 2–5% of followers), while **posts from people** (founders, employees) get far more reach and engagement than identical page posts. Reports also say LinkedIn favours specific, expert, original posts and holds back generic, AI-sounding content.
- So the agent should run a **founder-led + team advocacy** model:
  - **Founder voice (Ashish Srivastava), confirmed:** the founder will post from his own LinkedIn. Draft 2–3 posts a week for him to edit and post himself: opinions, lessons, field visits, what the group is building. He approves every word; never post as him.
  - **Team advocacy kit, confirmed:** team members will also post themselves. Each week, 2–3 ready-to-personalise posts per team member (Aryan included), written in first person with a prompt for their own detail. Never identical text across people. Kits are delivered through the Team Hub (§8).
  - **Company page = hub:** official announcements, Insights reports, hiring, event recaps, client wins (with consent), and reshares of founder/team posts with a comment.
- Formats to favour: document/carousel posts (frameworks, explainers), short text posts with a clear point of view, polls used sparingly for genuine questions, and photos with real people.
- Use specifics (named projects, real numbers with sources, places). Hashtags help categorise, not reach: 3–5 relevant ones.
- Engagement routine (human-run, agent-prepared): reply to every comment within 24 hours; the agent drafts suggested replies and a daily list of 5–10 relevant posts (clients, partners, CSR/ESG voices) for the team to comment on thoughtfully.

### 7.2 Instagram: Reels for discovery, carousels for depth
- 2026 reports consistently say Instagram ranks Reels mainly on **watch time/completion**, then **sends per reach** (shares by DM, the strongest signal for reaching non-followers), then likes per reach. **Originality** matters: reposted, aggregated or watermarked cross-posted content gets reduced reach.
- So the agent should:
  - Plan Reels built to be **shared**: useful, surprising or relatable (e.g., "3 myths about carbon credits", "What a CSR plantation audit actually checks", a 20-second field story).
  - Write the **first 1–2 seconds** (hook) and the on-screen text for every Reel; keep discovery Reels around 15–30 s.
  - Use **carousels** for saveable explainers, and Stories for relationship (polls, Q&A, behind-the-scenes).
  - Put keywords in captions (Instagram search reads captions), with 3–5 specific hashtags.
  - Use **Trial Reels** (shown to non-followers first; reported to need 1,000+ followers **[verify for each account]**) to test hooks before showing a Reel to the main audience.
  - Use **Collab posts** between the parent and an initiative (e.g., Tranzent Foundation × Born Green, Hi Fuel × Pathvik) so both audiences see one post. Instagram's native scheduler reportedly doesn't support Collab posts, so mark these "post manually."

### 7.3 Ecosystem flywheel (parent ↔ initiatives)
- Every initiative post should carry a light **"An initiative of Tranzent Foundation / Hi Fuel"** signal where appropriate (bio, end card, Collab), so the parent brand gains from initiative reach. Pathvik's affiliation disclosure is **[CONFIRM]**.
- The parent accounts reshare initiative milestones with the **company's** angle: why we built it and what it says about our approach.
- Press coverage (via Hi Fuel Media) → posts on both parent accounts, linking to the original article.
- **Owned channels**, so reach isn't only rented from algorithms **[CONFIRM which to start]**: a LinkedIn newsletter from Hi Fuel Advisory (monthly ESG/CSR brief), a WhatsApp Channel for Tranzent Foundation, email capture via the website.

### 7.4 Measurement and experiments
- **KPIs per account, separately for company and initiative accounts:**
  - Reach to non-followers.
  - Engagement rate per reach.
  - Shares/sends per reach and saves per reach.
  - Reel watch time and completion.
  - Follower growth.
  - Profile visits and link clicks.
  - Inbound enquiries attributed to social, which is the metric that matters most to the business.
  - For LinkedIn advocacy: reach from team/founder posts vs page posts.
- **Experiment log:** one change at a time (hook style, format, time slot, topic), with a hypothesis, start date and result after 2–4 weeks.
- **Monthly growth report:** what worked, what didn't, the next month's three priorities, with numbers and plain-language takeaways for the manager.

---

## 8. Platform and API facts (checked Oct 2026; verify against current docs before coding)

**Instagram (Meta Graph API)**
- Publishing and insights work **only for professional accounts**.
- The content publishing endpoint has **no "schedule for later" field**; third-party schedulers hold the post and fire the publish call at the right time. Since we are **not** auto-publishing, we only need **read** access (insights) in v1.
- Meta caps API publishing at about **100 posts per account per rolling 24 h** (only relevant if publishing is added later).
- Instagram's app and Meta Business Suite can schedule posts natively; that is where a human will schedule approved posts.
- For the group's own accounts, a Meta developer app with the team as admins/testers may avoid full App Review. App Review/Business Verification is needed if outside accounts connect **[CONFIRM against Meta docs]**.

**LinkedIn**
- Company Page analytics (followers, page views, post impressions/engagement) and Page posting need the **Community Management API**, which requires a manual approval. A Development tier comes first; the Standard tier (production) needs a screencast demo.
- The person connecting must hold an admin/content role on the Page.
- Access tokens last about **60 days**, so build a re-authentication reminder.
- LinkedIn's API is versioned monthly (`Linkedin-Version` header).
- Personal-profile analytics via API are limited and need separate approval. For founder/team advocacy, track results via manual input or exports in v1.

**Practical consequence:** API approvals take time. **Build v1 so it works with no API access at all**: accept CSV exports from Meta Business Suite / Instagram Insights and LinkedIn Page analytics, plus manual entry for personal posts. Add live API connectors later.

---

## 9. Suggested phased build

**Phase 1: Planner MVP (no platform APIs)**
- Config files per account and initiative: voice, colours, audiences, pillars, rules, hashtags, banned phrases, priority level.
- The agent generates the calendar, post drafts, design briefs, time slots (benchmarks at first) and the weekly advocacy kit.
- Claims checker (rules in §3) as a separate, testable step.
- Approval status per post: draft → needs changes → approved → scheduled → posted.
- Exports: Google Sheet or CSV calendar, `.ics` calendar file, and a copy-ready caption doc.

**Phase 2: Learning from data**
- Import CSV analytics; compute best slots and best formats/topics per account; weekly performance and monthly growth reports; experiment log.
- Then Instagram Graph API (read-only insights) and the LinkedIn Community Management API once approved.

**Phase 3 (optional, needs manager sign-off)**
- Push approved posts into a scheduler, still human-triggered. Never auto-post unapproved content.

**Tech notes**
- Use the Claude API for generation, with structured outputs (a JSON schema per post) so drafts are parseable. Keep prompts and brand rules in versioned files, not hard-coded strings.
- Store secrets (API keys, tokens) in environment variables / `.env`, never in code or git.
- Log every generated draft and every human edit; edits are training signal for voice.
- Keep the UI simple. A small web app or a shared Google Sheet as the front end is fine for v1 **[CONFIRM preferred interface]**.
- Budget awareness: small team. Prefer free tiers and low running costs; estimate monthly API cost before scaling.

---

## 10. Open questions to ask Aryan before or during Phase 1

1. Which accounts and platforms are in v1? (Instagram, LinkedIn, Facebook, WhatsApp Channel, YouTube?) Which handles exist for Pathvik, Earth.OSAI and ICLC?
2. Who approves posts, and how do they want to review: web page, Google Sheet, WhatsApp?
3. Posting volume per account per week?
4. Do we have admin access to each account, and can we export past analytics? Current follower counts (Trial Reels needs 1,000+)?
5. Will the founder post on LinkedIn from his own profile? Which team members will join the advocacy kit?
6. **ICLC:** full form, launch date, format, price/prizes, and how it relates to the Shankargarh 11 / RWLOS drafts. What can be said publicly now?
7. **Earth.OSAI:** confirmed product features, positioning (CSR verification?) and any numbers we may publish.
8. Languages: English only, or Hindi/Hinglish variants too?
9. Design output: briefs only, or should the agent also produce images (Canva templates, AI images, HTML-to-image)?
10. Pathvik's live domain, email and handles (the old ones say Catalystra); whether Pathvik discloses its Hi Fuel/Tranzent affiliation.
11. Tranzent Foundation, Hi Fuel Media, Earth.OSAI and ICLC brand colours and logo files.
12. Budget ceiling for APIs/tools per month.

---

## 11. Working style expected

- Ask before making irreversible choices; flag assumptions clearly.
- Explain decisions in plain language (the operator is an analyst, not a full-time developer).
- Write tests for the claims checker and the time-slot scoring.
- Accuracy over volume: a smaller set of correct, on-brand posts beats a full calendar with risky claims.

---

## 12. Build status and how to operate (kept up to date by Claude)

- **Phase 1 is built**: `hifuel/` (planner, claims check, time slots, store, exports, hub sync), `config/`, `prompts/system.md`, tests in `tests/`. See README.md for commands.
- **Phase 2 is built**: `hifuel/analytics.py` (CSV import via `config/analytics_columns.yaml`, follower counts, audience hours, enquiries, stored in `data/analytics.json`), `hifuel/reports.py` (weekly/monthly reports, planner insights), `hifuel/experiments.py`. Analytics feed the slot engine (`own_history`, `own_audience`) and the planner request (`results_so_far`, running experiments, team ideas). Live platform APIs are not built (approvals pending).
- **v1 decisions (19 Oct 2026, from Aryan):** review in a private web page (Team Hub); platforms Instagram, LinkedIn, Facebook, WhatsApp Channel and X; English only; design briefs only (no image generation).
- **Team Hub (v4, 19 Oct 2026):** https://claude.ai/artifact/JoZnLiaiVKUBVYFB3TbNxM. Source lives in `hub/src/` (`shell.html`, `styles.css`, `app-*.js`); run `python hub/build.py` to rebuild `hub/team_hub.html`, then publish that file. Screens: Overview (bento), Calendar (month / week timeline / status pipeline, drag-to-reschedule with spacing warnings and undo, Editors only), Review (queue + full preview + checks + comments, "Approve to queue", "Request changes" checklist, shortcuts J/K/A/R), Analytics (KPIs with week-over-week change, one-axis small-multiple trend charts, sortable top content, CSV/report export), Ideas (lanes by campaign idea or content pillar, votes, links, screenshots, "Convert to draft"), Campaigns, Advocacy, Announcements, Reports. "Delayed" = approved/scheduled, past its time, not marked published. Quick draft / Convert to draft create a `shell` post that Claude writes at the next sync.
- **Hub collections and rules:** Editors only write `posts`, `plans`, `announcements`, `reports`, `experiments`, `meta` (`config`, `sync`), `analytics` (`summary`); Contributors write `ideas`, `results`, `comments`. Give the manager and founder Editor access; team members Contributor. Republish with those seven `db` rules plus `user: {scopes: ["profile"]}`, `downloads: true`, `assets: {upload: "interact"}` (verified 19 Oct 2026: Contributors can comment, can't write `meta`; Viewers can read `analytics`).
- **Sync loop:** `python -m hifuel hub-push` writes `data/hub_outbox/<collection>/<id>.json`; load them with the ArtifactData `batch` action (`file_path` per doc, `if_version` for docs that already exist). `hub-push` also writes `meta/config`, `meta/sync` (the hub's "Claude synced" stamp) and `analytics/summary`; push them every sync, and if it writes `_delete.json`, delete those post ids on the hub. To pull, ArtifactData `list` the `posts`, `ideas`, `results` and `comments` collections with the same `out_dir`, then `python -m hifuel hub-pull <out_dir>` (applies reviews and edits, stores ideas, imports logged results), then push again so the hub shows the re-checked issues. Reports (`python -m hifuel report ...`) and experiments go up with the same push. Reviewer ids in `review.by` are opaque; resolve names with ArtifactData `profiles`.
- **Pathvik launched (Oct 2026):** website live, registrations open, no prices in posts, no cohort dates (Aryan, 19 Oct 2026). Launch campaign 20 Oct – 1 Nov in `campaigns/pathvik-launch.yaml` (32 posts, tagged `campaign: pathvik-launch`; the plan record carries the campaign goal, KPIs and CTAs). Campaign files use the same `import` command. Affiliation disclosure is approved (19 Oct 2026). Open: Pathvik URL/handle, whether a Pathvik Facebook Page exists.
- **WhatsApp review packs:** `python -m hifuel review-pack` writes `data/exports/review-packs/<name>.pdf` (phone-sized, one post per page, codes like P01/W01), `<name>.whatsapp.txt` (message to paste) and `<name>.codes.json` (code → post id). Reviewers reply `P07 OK` / `P07 CHANGE ...` / `P07 DROP ...`; when Aryan pastes replies in chat, map codes with the codes file and apply them (edits, status, or a comment) the same way as hub reviews. First packs (19 Oct 2026): `pathvik-launch-review` (P01–P32) and `week-2026-10-26-review` (W01–W24).
- **Hub sync rule:** `hub-pull` applies only actions recorded on the hub (entries in a post's `edits` list, consent changes flagged `edited_since_check`, and status decisions whose `review.at` is newer than ours). A stale hub copy never overwrites local text. Always pull before pushing new content.
- **Spacing:** max 2 posts per account per platform per day, 3 h apart on one platform, 1 h apart across an account's platforms.
- **Weeks drafted in chat** (no API key yet) live in `weeks/<monday>.yaml` and are loaded with `python -m hifuel import`. The week of 26 Oct 2026 (31 posts) is the first real plan; the earlier sample was removed. `samples/sample_week.yaml` remains as a demo and test fixture.
- `data/` is git-ignored (posts, logs, exports). Back it up or move it to shared storage before more than one person runs the planner.
