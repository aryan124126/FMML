# Junk Facts

A junk-food tracker for two people (built for two brothers). It's one self-contained page, `index.html`, with no build step and no server.

## What it does

- **Two-tap logging.** Pick who you are, tap an item (chips, cold drink, pizza, samosa, ...) or "Something else", then hit **Log it**. You can change how many you ate, calories, cost and time, and optionally tag *why* you ate it (bored, stressed, with friends, late night, ...).
- **Daily limit and status.** Each person sets a daily limit (start at 1, lower it later). A nutrition-label-style card shows today's items, calories and spend, marked *Clean*, *At limit* or *Over by N*.
- **Streaks.** Consecutive days at or under your limit, junk-free days in the last 7, and this week vs last week.
- **14-day chart.** Both of you side by side, with your limits and over-limit days marked.
- **30-day insights.** Your most-eaten junk, your most common reasons, and what it costs. It also converts the calories into kg of body fat (≈7,700 kcal per kg) and shows the yearly spend at this pace.
- **History.** Recent entries grouped by day, with delete.

A day with no entries counts as junk-free, so you only log the junk.

## Running it

Open `index.html` in a browser, or turn on GitHub Pages for this repo (Settings → Pages → deploy from branch, root folder) and add the page to both phones' home screens.

In this mode, data is saved in the browser (`localStorage`) on each device. Use **Settings → Export backup / Import backup** to move data between devices.

The same page is also published as a Claude artifact with a shared database. There, both brothers' entries sync live, as long as the artifact is shared with the second person as a Contributor.

## Tips for using it well

1. **Log right away**, before or right after eating. Logging from memory at night undercounts.
2. **Always tag the reason.** After a couple of weeks, the "Why it happened" chart shows your real triggers. Deal with the top one: keep no chips at home if it's *Bored*, eat proper dinners if it's *Late night*.
3. **Set a limit you can hit**, then tighten it. A 20-day streak at 1/day beats failing at 0/day.
4. **Check the chart together once a week.**
