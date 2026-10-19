// Analytics: KPI cards with week-over-week deltas, one-axis trend charts (small multiples), sortable top content, export menu.

const fmtCompact = n => n == null ? "–" : Math.abs(n) >= 1e5 ? new Intl.NumberFormat("en-IN", { notation: "compact", maximumFractionDigits: 1 }).format(n) : fmtNum(n);
const signed = n => n == null ? "–" : `${n > 0 ? "+" : ""}${fmtNum(n)}`;
function anRows(series) {
  const a = state.an;
  return (series || []).filter(r => (!a.account || r.account === a.account) && (!a.platform || r.platform === a.platform));
}
function weekTotals(rows, week) {
  const w = rows.filter(r => r.week === week);
  const sum = k => w.reduce((s, r) => s + (r[k] || 0), 0);
  const imp = sum("impressions"), eng = sum("engagements"), clk = sum("clicks"), base = sum("click_base");
  const fc = w.filter(r => r.follower_change != null);
  return { posts: sum("posts"), impressions: w.some(r => r.posts) ? imp : null, er: imp ? eng / imp : null, ctr: base ? clk / base : null, followers: fc.length ? fc.reduce((s, r) => s + r.follower_change, 0) : null };
}
function kpisFor(series, week, prevWeek) { const rows = anRows(series); return { cur: weekTotals(rows, week), prev: weekTotals(rows, prevWeek) }; }
function deltaEl(cur, prev, kind) {
  if (cur == null || prev == null) return el("span", { class: "delta flat", text: "no comparison" });
  let d, text;
  if (kind === "pct") { if (!prev) return el("span", { class: "delta flat", text: "new" }); d = (cur - prev) / Math.abs(prev); text = `${Math.abs(d * 100).toFixed(0)}%`; }
  else if (kind === "pts") { d = cur - prev; text = `${Math.abs(d * 100).toFixed(1)} pts`; }
  else { d = cur - prev; text = fmtNum(Math.abs(d)); }
  const dir = Math.abs(d) < 1e-9 ? "flat" : d > 0 ? "up" : "down";
  return el("span", { class: `delta ${dir}`, title: "Change vs the week before" }, dir === "flat" ? "→ " : dir === "up" ? "▲ " : "▼ ", text, el("span", { class: "sr", text: dir === "up" ? " up" : dir === "down" ? " down" : " no change" }), el("span", { class: "muted", style: "font-weight:500", text: " vs prior week" }));
}
const METRICS = [
  { key: "impressions", label: "Impressions", fmt: fmtCompact, delta: "pct", hint: "Reach where the platform gives it, impressions otherwise" },
  { key: "ctr", label: "Click-through rate", fmt: fmtPct, delta: "pts", hint: "Link clicks ÷ impressions, for exports that include clicks" },
  { key: "er", label: "Engagement rate", fmt: fmtPct, delta: "pts", hint: "Likes, comments, shares and saves ÷ impressions" },
  { key: "followers", label: "Net follower growth", fmt: signed, delta: "abs", hint: "From follower counts you send Claude" }
];
function analyticsActions() {
  if (!state.analytics || !state.analytics.has_data) return null;
  return el("button", { class: "btn", "aria-haspopup": "menu", onclick: e => openMenu(e.currentTarget, [
    { label: "Top content (CSV)", sub: "The table below, with your filters", icon: "download", fn: exportPostsCsv },
    { label: "Weekly trend (CSV)", sub: "12 weeks, with your filters", icon: "download", fn: exportSeriesCsv },
    state.reports[0] && state.reports[0].markdown ? { label: "Latest report (Markdown)", sub: reportLabel(state.reports[0]), icon: "reports", fn: () => saveFile(`hifuel-report-${state.reports[0].start}.md`, state.reports[0].markdown, "text/markdown") } : null,
    { label: "Copy summary", sub: "KPIs for the selected week, as text", icon: "copy", fn: copySummary }
  ]) }, icon("download"), "Export", icon("more"));
}
async function saveFile(filename, data, type = "text/csv") {
  if (downloads) {
    try { await downloads.save({ filename, data }); toast(`Saved ${filename}`); }
    catch (e) { if (!e || e.code !== "declined") toast(e && e.code === "rate_limited" ? "A download prompt is already open. Try again in a moment." : "Couldn't save the file here. Ask Claude in chat for it.", { warn: true }); }
    return;
  }
  try { const url = URL.createObjectURL(new Blob([data], { type })); const a = el("a", { href: url, download: filename }); document.body.append(a); a.click(); a.remove(); setTimeout(() => URL.revokeObjectURL(url), 2000); toast(`Downloading ${filename}`); }
  catch { toast("Couldn't download here. Ask Claude in chat for the file.", { warn: true }); }
}
const csvCell = v => v == null ? "" : /[",\n]/.test(String(v)) ? `"${String(v).replace(/"/g, '""')}"` : String(v);
const toCsv = (head, rows) => [head, ...rows].map(r => r.map(csvCell).join(",")).join("\n");
function exportPostsCsv() {
  const rows = topPosts(true);
  saveFile(`hifuel-top-content-${todayIST()}.csv`, toCsv(["date", "time", "account", "platform", "format", "post", "impressions", "engagements", "engagement_rate", "clicks", "ctr", "shares", "saves", "link"],
    rows.map(r => [r.date, r.time, r.account_name, PLATFORMS[r.platform] || r.platform, r.format, r.text, r.impressions, r.engagements, r.er == null ? "" : r.er.toFixed(4), r.clicks, r.ctr == null ? "" : r.ctr.toFixed(4), r.shares, r.saves, r.permalink])));
}
function exportSeriesCsv() {
  const a = state.analytics, rows = anRows(a.series);
  saveFile(`hifuel-weekly-trend-${todayIST()}.csv`, toCsv(["week_starting", "posts", "impressions", "engagement_rate", "ctr", "net_follower_growth"],
    a.weeks.map(w => { const t = weekTotals(rows, w); return [w, t.posts, t.impressions, t.er == null ? "" : t.er.toFixed(4), t.ctr == null ? "" : t.ctr.toFixed(4), t.followers]; })));
}
function selectedWeeks() { const a = state.analytics; const w = state.an.week && a.weeks.includes(state.an.week) ? state.an.week : a.weeks[a.weeks.length - 2]; const i = a.weeks.indexOf(w); return { week: w, prev: a.weeks[i - 1] }; }
function copySummary() {
  const { week, prev } = selectedWeeks(); const k = kpisFor(state.analytics.series, week, prev);
  copy([`Social results, week of ${fmtDay(week, { day: "numeric", month: "short", year: "numeric" })}${state.an.account ? ` · ${accountName(state.an.account)}` : ""}${state.an.platform ? ` · ${PLATFORMS[state.an.platform]}` : ""}`,
    ...METRICS.map(m => `${m.label}: ${m.fmt(k.cur[m.key])} (prior week ${m.fmt(k.prev[m.key])})`)].join("\n"));
}
function topPosts(all = false) {
  const a = state.an, an = state.analytics;
  const { week } = selectedWeeks();
  const from = a.period === "1w" ? week : a.period === "4w" ? addDays(week, -21) : an.weeks[0];
  const to = addDays(week, 6);
  const rows = (an.posts || []).filter(r => (!a.account || r.account === a.account) && (!a.platform || r.platform === a.platform) && r.date >= from && r.date <= to);
  const k = a.sort, dir = a.dir;
  rows.sort((x, y) => { const vx = x[k], vy = y[k]; if (vx == null && vy == null) return 0; if (vx == null) return 1; if (vy == null) return -1; return (typeof vx === "string" ? vx.localeCompare(vy) : vx - vy) * dir; });
  return all || a.showAll ? rows : rows.slice(0, 15);
}

// ---------- chart (one axis, thin line, crosshair, tooltip) ----------
const chartGroup = [];
function lineChart(points, metric, height = 150) {
  const box = el("div", { class: "chart", role: "img", "aria-label": `${metric.label} by week: ` + points.map(p => `${fmtDay(p.week, { day: "numeric", month: "short" })} ${metric.fmt(p.value)}`).join(", ") });
  const tip = el("div", { class: "tooltip", hidden: true });
  let draw = () => {}, setHover = () => {};
  const ro = new ResizeObserver(() => draw());
  draw = () => {
    if (!box.isConnected && box.dataset.drawn) { ro.disconnect(); return; }
    box.dataset.drawn = "1";
    const W = Math.max(240, box.clientWidth), H = height, padL = 46, padR = 10, padT = 10, padB = 22;
    const vals = points.map(p => p.value).filter(v => v != null);
    let lo = Math.min(0, ...vals), hi = Math.max(...vals, 0);
    if (hi === lo) hi = lo + (metric.key === "er" || metric.key === "ctr" ? 0.01 : 1);
    hi = niceCeil(hi * 1.08); if (lo < 0) lo = -niceCeil(-lo * 1.08);
    const x = i => padL + (i * (W - padL - padR)) / Math.max(1, points.length - 1);
    const y = v => padT + (1 - (v - lo) / (hi - lo)) * (H - padT - padB);
    const ticks = [lo, lo + (hi - lo) / 2, hi].map(t => Math.abs(t) < 1e-12 ? 0 : t);
    let s = `<svg viewBox="0 0 ${W} ${H}" width="${W}" height="${H}" aria-hidden="true">`;
    for (const t of ticks) s += `<line class="gridline" x1="${padL}" x2="${W - padR}" y1="${y(t)}" y2="${y(t)}"/><text class="axis" x="${padL - 6}" y="${y(t) + 4}" text-anchor="end">${esc(metric.fmt(t))}</text>`;
    points.forEach((p, i) => { if (i % 2 === (points.length - 1) % 2) s += `<text class="axis" x="${x(i)}" y="${H - 4}" text-anchor="middle">${esc(fmtDay(p.week, { day: "numeric", month: "short" }))}</text>`; });
    let path = "", area = "", started = false, segStart = 0;
    points.forEach((p, i) => {
      if (p.value == null) { if (started) { area += `L${x(i - 1)},${y(Math.max(lo, 0))}L${x(segStart)},${y(Math.max(lo, 0))}Z`; } started = false; return; }
      if (!started) { path += `M${x(i)},${y(p.value)}`; area += `M${x(i)},${y(p.value)}`; segStart = i; started = true; } else { path += `L${x(i)},${y(p.value)}`; area += `L${x(i)},${y(p.value)}`; }
    });
    if (started) area += `L${x(points.length - 1)},${y(Math.max(lo, 0))}L${x(segStart)},${y(Math.max(lo, 0))}Z`;
    s += `<path class="area" d="${area}"/><path class="line" d="${path}"/>`;
    points.forEach((p, i) => { if (p.value != null && (points[i - 1] || {}).value == null && (points[i + 1] || {}).value == null) s += `<circle class="pt" cx="${x(i)}" cy="${y(p.value)}" r="4"/>`; });
    s += `<line class="xhair" x1="0" x2="0" y1="${padT}" y2="${H - padB}" visibility="hidden"/><circle class="pt hov" r="5" visibility="hidden"/><rect class="hit" x="${padL}" y="0" width="${W - padL - padR}" height="${H}"/></svg>`;
    box.innerHTML = s; box.append(tip);
    const svgEl = box.querySelector("svg"), xh = svgEl.querySelector(".xhair"), dot = svgEl.querySelector(".hov");
    setHover = i => {
      if (i == null) { xh.setAttribute("visibility", "hidden"); dot.setAttribute("visibility", "hidden"); tip.hidden = true; return; }
      const p = points[i]; xh.setAttribute("x1", x(i)); xh.setAttribute("x2", x(i)); xh.setAttribute("visibility", "visible");
      if (p.value != null) { dot.setAttribute("cx", x(i)); dot.setAttribute("cy", y(p.value)); dot.setAttribute("visibility", "visible"); } else dot.setAttribute("visibility", "hidden");
      tip.hidden = false; tip.replaceChildren(el("div", { class: "xs muted", text: `Week of ${fmtDay(p.week, { day: "numeric", month: "short" })}` }), el("div", {}, `${metric.label}: `, el("b", { text: metric.fmt(p.value) })));
      tip.style.left = Math.min(Math.max(x(i), 80), W - 80) + "px"; tip.style.top = (p.value != null ? y(p.value) - 10 : padT) + "px";
    };
    const pick = e => { const r = svgEl.getBoundingClientRect(); const px = e.clientX - r.left; const i = Math.round(((px - padL) / (W - padL - padR)) * (points.length - 1)); return Math.max(0, Math.min(points.length - 1, i)); };
    svgEl.addEventListener("pointermove", e => chartGroup.forEach(c => c.isConnected() && c.setHover(pick(e))));
    svgEl.addEventListener("pointerleave", () => chartGroup.forEach(c => c.isConnected() && c.setHover(null)));
  };
  chartGroup.push({ setHover: i => setHover(i), isConnected: () => box.isConnected });
  while (chartGroup.length > 12) chartGroup.shift();
  ro.observe(box);
  return box;
}
function niceCeil(v) { const p = Math.pow(10, Math.floor(Math.log10(v))); const m = v / p; return (m <= 1 ? 1 : m <= 2 ? 2 : m <= 2.5 ? 2.5 : m <= 5 ? 5 : 10) * p; }
const esc = s => String(s).replace(/[&<>"]/g, c => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]));

// ---------- the screen ----------
function viewAnalytics() {
  const wait = notReady(); if (wait) return wait;
  const an = state.analytics;
  const a = state.an;
  if (!an || !an.has_data) {
    const req = "Please import our social analytics. Attached: the Instagram Insights export, the LinkedIn Page analytics export, current follower counts per account, and enquiries from social this week.";
    return [el("div", { class: "kpis" }, METRICS.map(m => el("div", { class: "tile" }, el("span", { class: "kk", text: m.label }), el("span", { class: "kv muted", text: "–" }), el("span", { class: "xs muted", text: "No data yet" })))),
      el("section", { class: "card" }, el("div", { class: "empty", style: "border:0" }, icon("analytics"), el("strong", { text: "No results imported yet" }),
        el("ol", {}, el("li", { text: "Download the last 4–6 weeks of results: Instagram Insights (Meta Business Suite → Insights → Export) and LinkedIn Page analytics (Analytics → Export)." }),
          el("li", { text: "Note each account's follower count today, and any enquiries that came from social." }),
          el("li", { text: "Send the files to Claude in chat. Claude imports them, and this screen fills in at the next sync." })),
        el("div", { class: "row", style: "justify-content:center" }, el("button", { class: "btn primary", onclick: () => copy(req) }, icon("copy"), "Copy the request for Claude")),
        el("p", { class: "hint", text: "Founder and team LinkedIn results come from the Advocacy screen: each person logs their own numbers." })))];
  }
  const { week, prev } = selectedWeeks();
  const acc = el("select", { "aria-label": "Account", onchange: e => { a.account = e.target.value; render(); } }, el("option", { value: "", text: "All accounts" }),
    [...new Map(an.series.map(r => [r.account, accountName(r.account)]))].map(([id, n]) => el("option", { value: id, text: n })));
  acc.value = a.account;
  const plats = el("div", { class: "pchips", role: "group", "aria-label": "Platform" }, [...new Set(an.series.map(r => r.platform))].map(pl =>
    el("button", { class: "pchip", style: `--pc:var(--p-${pl})`, "aria-pressed": String(a.platform === pl), "aria-label": `Only ${PLATFORMS[pl]}`, title: PLATFORMS[pl], onclick: () => { a.platform = a.platform === pl ? "" : pl; render(); } }, pfBadge(pl))));
  const wk = el("select", { "aria-label": "Week", onchange: e => { a.week = e.target.value; render(); } }, an.weeks.slice(1).reverse().map(w => el("option", { value: w, text: `Week of ${fmtDay(w, { day: "numeric", month: "short" })}${w === an.weeks[an.weeks.length - 1] ? " (in progress)" : ""}` })));
  wk.value = week;
  const bar = el("div", { class: "toolbar" }, acc, plats, wk, el("span", { class: "grow" }), el("span", { class: "xs muted", text: `Updated ${ago(an.generated_at)}` }));
  const k = kpisFor(an.series, week, prev);
  const kpis = el("div", { class: "kpis" }, METRICS.map(m => el("div", { class: "tile", title: m.hint }, el("span", { class: "kk", text: m.label }), el("span", { class: "kv", text: m.fmt(k.cur[m.key]) }), deltaEl(k.cur[m.key], k.prev[m.key], m.delta))));
  const rows = anRows(an.series);
  const totals = an.weeks.map(w => ({ week: w, ...weekTotals(rows, w) }));
  const tableToggle = el("div", { class: "seg", role: "group", "aria-label": "Trend view" }, [[false, "Charts"], [true, "Table"]].map(([v, l]) => el("button", { "aria-pressed": String(a.chartTable === v), onclick: () => { a.chartTable = v; render(); }, text: l })));
  const trend = el("section", { class: "card" }, el("div", { class: "spread" }, el("div", {}, el("h2", { text: "12-week trend" }), el("p", { class: "xs muted", text: "One chart per measure, same weeks across. Hover to compare a week." })), tableToggle),
    a.chartTable ? el("div", { class: "tablewrap" }, el("table", {}, el("thead", {}, el("tr", {}, el("th", { scope: "col", text: "Week of" }), el("th", { scope: "col", class: "n", text: "Posts" }), METRICS.map(m => el("th", { scope: "col", class: "n", text: m.label })))),
      el("tbody", {}, totals.slice().reverse().map(t => el("tr", {}, el("td", { text: fmtDay(t.week, { day: "numeric", month: "short" }) }), el("td", { class: "n", text: t.posts }), METRICS.map(m => el("td", { class: "n", text: m.fmt(t[m.key]) })))))))
      : el("div", { class: "small-multiple" }, METRICS.map(m => el("div", {}, el("div", { class: "sm-title" }, m.label, el("span", { text: `Week of ${fmtDay(week, { day: "numeric", month: "short" })}: ${m.fmt(k.cur[m.key])}` })), lineChart(totals.map(t => ({ week: t.week, value: t[m.key] })), m)))));
  // top content
  const head = [["text", "Post", false], ["platform", "Platform", false], ["date", "Date", false], ["impressions", "Impressions", true], ["er", "Eng. rate", true], ["ctr", "CTR", true], ["shares", "Shares", true], ["saves", "Saves", true]];
  const sortBtn = (key, label) => el("button", { onclick: () => { if (a.sort === key) a.dir *= -1; else { a.sort = key; a.dir = key === "text" || key === "platform" ? 1 : -1; } render(); } }, label, a.sort === key ? (a.dir < 0 ? " ↓" : " ↑") : "");
  const list = topPosts();
  const allN = topPosts(true).length;
  const period = el("div", { class: "seg", role: "group", "aria-label": "Period" }, [["1w", "Selected week"], ["4w", "4 weeks"], ["12w", "12 weeks"]].map(([v, l]) => el("button", { "aria-pressed": String(a.period === v), onclick: () => { a.period = v; render(); }, text: l })));
  const table = el("section", { class: "card" }, el("div", { class: "spread" }, el("h2", { text: "Top content" }), period),
    list.length ? el("div", { class: "tablewrap" }, el("table", {}, el("thead", {}, el("tr", {}, head.map(([key, label, n]) => el("th", { scope: "col", class: n ? "n" : null, "aria-sort": a.sort === key ? (a.dir < 0 ? "descending" : "ascending") : null }, sortBtn(key, label))))),
      el("tbody", {}, list.map(r => el("tr", {},
        el("td", { style: "white-space:normal;min-width:220px;max-width:360px" }, el("div", { class: "row", style: "flex-wrap:nowrap;gap:8px" }, ava(r.account_name, acctColor(r.account), true),
          r.post_id && state.posts.get(r.post_id) ? el("button", { class: "linkbtn clamp2", style: "color:var(--fg);font-weight:500", onclick: () => openPost(r.post_id), text: r.text || "(no text)" }) : r.permalink ? el("a", { href: r.permalink, target: "_blank", rel: "noopener", class: "clamp2", style: "color:var(--fg)", text: r.text || "(no text)" }) : el("span", { class: "clamp2", text: r.text || "(no text)" }))),
        el("td", {}, el("span", { class: "row", style: "gap:6px;flex-wrap:nowrap" }, pfBadge(r.platform), FORMAT_LABEL[r.format] || r.format)),
        el("td", { class: "mono", text: fmtDay(r.date, { day: "numeric", month: "short" }) }),
        el("td", { class: "n", text: fmtNum(r.impressions) }), el("td", { class: "n", text: fmtPct(r.er) }), el("td", { class: "n", text: fmtPct(r.ctr) }),
        el("td", { class: "n", text: fmtNum(r.shares) }), el("td", { class: "n", text: fmtNum(r.saves) })))))) : el("p", { class: "small muted", text: "No posts with results in this period." }),
    allN > 15 ? el("button", { class: "btn ghost sm", style: "justify-self:start", onclick: () => { a.showAll = !a.showAll; render(); }, text: a.showAll ? "Show top 15" : `Show all ${allN}` }) : null,
    el("p", { class: "hint", text: an.note || "" }));
  return [bar, kpis, trend, table];
}
