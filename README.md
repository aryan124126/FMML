# Junk Facts

Shevi and Rupesh's junk-food tracker. It's one self-contained page, `index.html`, with no build step and no server.

## How it keeps you going

The app is built around what behavior-change research says actually works:
- **Your reason and identity:** a one-minute setup asks why you're changing and who you're becoming, and shows it back to you every day.
- **A daily coach and wellness score:** a 0–100 ring combining junk items with four healthy habits (water, fruit and veg, a 30-minute walk or workout, and 7+ hours of sleep), with a supportive message for where you are.
- **Wins, not just junk:** tap "I resisted one" whenever you beat a craving. Wins count toward milestones.
- **Craving SOS:** a 5-minute urge timer with a guided breathing circle, your reason, your if-then plans and quick things to try. It can also send your brother an alert to back you up.
- **Kind slip-ups:** going over your limit gets a "never miss twice" message instead of shame, and your total clean days and best streak stay visible.
- **Progress tab:**
  - money saved and body fat avoided, measured against your "before" habits, counting toward a reward you choose
  - 16 milestones with a celebration when you unlock one
  - a "what's changing in your body" timeline
  - a shared team goal for the week, and cheers you can send each other
  - your if-then plans

## Tabs

### Today
- **A nutrition label for each of you**, like the one on food packets:
  - today's item count against your daily limit (*Clean*, *Under limit*, *At limit*, *Over by N*)
  - calories, fat, sugar and sodium from junk, as a % of a full day's maximum
  - money spent today and this week, against an optional weekly budget
  - current and best within-limit streak, the last 7 days compared with the 7 before, and junk-free days
- **Logging:** tap an item (17 common Indian junk foods), your own saved quick items, or *Repeat* to log your last item again in one tap. You can change amount, time, nutrition and cost. You can also tag **where** you were and **why** you ate it. Every log has an **Undo**.
- **Logged today:** both of your entries, with edit and delete.

### Scan
Two modes:

**Meal photo.** For Zomato or Swiggy orders, restaurant food or anything without a label. Photograph the plate or delivery box from above, and optionally add a screenshot of the order and a line about what you ordered. Claude estimates:
- calories for what *you* ate, as a best guess and likely range, with a confidence level, plus the whole order
- protein, carbs, sugar, fibre, fat, saturated fat and sodium, and each as a % of a day's maximum
- a dish-by-dish breakdown and where the hidden oil, butter, cream, sugar and salt are
- how to order it healthier next time, what to eat for the rest of the day, and how much walking burns it off

Estimates from a photo can be off by 20–30% or more.

**Packet label.** Photograph a packaged food's **ingredients list** and **nutrition table**, and optionally the front of the pack. Claude reads them and writes a detailed report on that exact product:
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

### Patterns (on the Trends tab, last 30 days)
- A written summary for each person:
  - items per day, and the change from the previous 30 days
  - favorite item, usual time and weekday, top reason and usual place
  - money, calories and the kg of body fat those calories equal, plus the yearly cost at this pace
  - the biggest day
- **When it happens:** a heatmap of weekday by time of day.
- **Why**, **what**, **what type** and **where**, split by person.
- **Nutrition from junk:** daily averages against daily maximums.

### Health (private to each person)
Everything on this tab is stored in **your own private space** on your Claude account. Your brother can't see it, even though you share the tracker, and each of you fills in your own.
- **About you:** age, sex, height, diet, exercise, sleep, smoking and alcohol, family history, past and current medical issues, medicines, allergies and your goals.
- **Lab reports:** photograph each page (or screenshot a PDF) and Claude reads every value for you to check before saving, or type the key values in yourself.
- **Checkups:** when CBC, lipid profile, LFT, KFT, HbA1c, fasting sugar, thyroid, vitamin D, B12, uric acid and urine were last done, and which are due.
- **Key numbers over time:** HbA1c, fasting glucose, cholesterol (total, LDL, HDL), triglycerides, ALT/AST, haemoglobin, creatinine, uric acid, TSH, vitamin D and B12 across your reports, with out-of-range values marked.
- **Health analysis:** Claude reads your profile, reports, weight and junk-food log and writes:
  - where you stand, with your actual values
  - your tendencies, and what to take care of
  - concrete lifestyle changes, each with a first step for this week
  - **what's likely ahead if nothing changes**: the time frame, how likely it is and why, and how to prevent or delay it
  - which tests to get and when, warning signs that need a doctor, and questions to ask your doctor
- **Personal scans:** once your profile is filled in, label scans add a private "For you" section. It flags your allergens and ingredients that push your own lab values the wrong way.

The analysis is not a diagnosis. Take it and your reports to a doctor.

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
