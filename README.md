# Junk Facts

Shevi and Rupesh's junk-food tracker. It's one self-contained page, `index.html`, with no build step and no server.

## Tabs

### Today
- **This week's score:** who has eaten fewer junk items since Monday.
- **A nutrition label for each of you**, like the one on food packets:
  - today's item count against your daily limit (*Clean*, *Under limit*, *At limit*, *Over by N*)
  - calories, fat, sugar and sodium from junk, as a % of a full day's maximum
  - money spent today and this week, against an optional weekly budget
  - current and best within-limit streak, the last 7 days compared with the 7 before, and junk-free days
- **Logging:** tap an item (17 common Indian junk foods), your own saved quick items, or *Repeat* to log your last item again in one tap. You can change amount, time, nutrition and cost. You can also tag **where** you were and **why** you ate it. Every log has an **Undo**.
- **Logged today:** both of your entries, with edit and delete.

### Scan
Photograph a packaged food's **ingredients list** and **nutrition table**, and optionally the front of the pack. Claude reads them and writes a detailed report on that exact product:
- a health score out of 10, a plain-language verdict, and label warnings (high sodium, palm oil, MSG, ...)
- the full nutrition table, plus what *your portion* adds up to against a day's maximum
- effects on the **blood, heart and blood vessels, brain, liver, kidneys, pancreas, stomach, intestines and gut bacteria, teeth, and body fat**, for eating it once and for eating it often
- **diseases** it's linked to, with how strong the evidence is
- **cancer risk**: each substance, where it comes from in the product, its IARC group, and whether the label confirms it
- every ingredient and additive (INS numbers) explained, better Indian swaps, and a bottom line

One tap logs the item with the numbers from the scan, and reports are saved under *Past scans*. The scanner only works in the shared Claude version: it uses the viewer's own Claude account, which asks for permission the first time. The report can misread a label and isn't medical advice.

### Trends
- **Items per day** for 14 or 30 days, with daily limits and over-limit days marked. Tap a day to see what each of you ate.
- **Month calendar** for each of you, colored junk-free, within limit, or over limit. Earlier months are available.
- **Week by week table** for the last 8 weeks: items, junk-free days, over-limit days, calories, sugar and spend.
- **Weight check-in** with a trend line. Once a week is enough.

### Patterns (last 30 days)
- A written summary for each person:
  - items per day, and the change from the previous 30 days
  - favorite item, usual time and weekday, top reason and usual place
  - money, calories and the kg of body fat those calories equal, plus the yearly cost at this pace
  - the biggest day
- **When it happens:** a heatmap of weekday by time of day.
- **Why**, **what**, **what type** and **where**, split by person.
- **Nutrition from junk:** daily averages against daily maximums.

### History
All entries grouped by day with daily totals. Filter by person or type, or search items, notes and reasons. Every entry can be edited or deleted.

### Settings
Names, daily item limits, weekly budgets, currency, your saved quick items, and a note on how the numbers are calculated.

## Reference values

- Daily maximums: 2,000 kcal, 70 g fat, 50 g sugar (WHO; under 25 g is better), 2,000 mg sodium (WHO).
- 7,700 kcal ≈ 1 kg of body fat.
- Item nutrition values are rough per-serving estimates, and you can edit them when logging.
- A day with no entries counts as junk-free.

## Running it

- **Shared version:** the page is published as a Claude artifact with a shared database. Entries, settings and weights sync live between you, as long as the artifact is shared with the other person as a Contributor.
- **Standalone:** open `index.html` in a browser, or turn on GitHub Pages (Settings → Pages → deploy from branch, root folder). Data then stays in that browser. Use **Settings → Backup** to export it or import it on another device.

## Tips

1. **Log right away.** Logging from memory at night undercounts.
2. **Always tag why and where.** After two weeks, the Patterns tab shows your real triggers. Deal with the top one: no chips at home if it's *Bored at home*, a proper dinner if it's *Late night*.
3. **Set a limit you can hit**, then tighten it after a two-week streak.
4. **Look at the Trends tab together every Sunday**, and weigh in the same morning.
