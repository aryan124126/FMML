// Overview (bento) and Calendar (month grid, week timeline, status pipeline) with drag-and-drop.

// ---------- post card ----------
function brandColors(p) {
  const cs = ((p.design_brief || {}).colours || []).filter(c => /^#[0-9a-f]{3,8}$/i.test(c));
  if (cs.length >= 2) return [cs[0], cs[1]];
  const base = cs[0] || acctVar(p);
  return [base, `color-mix(in srgb, ${base} 45%, #000)`];
}
function mediaText(p) {
  const b = p.design_brief || {};
  if ((b.slides || []).length) return b.slides[0].text;
  const reel = b.reel || {};
  if ((reel.shots || []).length && reel.shots[0].on_screen_text) return reel.shots[0].on_screen_text;
  return p.hook;
}
const VISUAL = ["single_image", "carousel", "reel", "story", "document"];
function pcard(p, opts = {}) {
  const ds = displayStatus(p);
  const visual = VISUAL.includes(p.format) && !isShell(p);
  const [c1, c2] = brandColors(p);
  const thumb = opts.compact ? null : visual
    ? el("div", { class: "thumb", style: `--c1:${c1};--c2:${c2}` }, el("span", { class: "clamp2", text: mediaText(p) }), el("span", { class: "fmt", text: (FORMAT_LABEL[p.format] || p.format).toUpperCase() }))
    : el("div", { class: "thumb text" }, el("span", { class: "clamp3", text: isShell(p) ? "Brief · Claude writes this at the next sync" : (p.caption || p.hook || "").slice(0, 160) }));
  const drag = opts.draggable && canMove(p);
  const card = el("div", { class: `pcard${opts.compact ? " compact" : ""}${isShell(p) ? " shellcard" : ""}${ds === "delayed" ? " is-delayed" : ""}${ds === "blocked" ? " is-blocked" : ""}`,
    role: "button", tabindex: "0", draggable: drag ? "true" : null, "data-id": p.id,
    "aria-label": `${p.account_name}, ${PLATFORMS[p.platform]} ${FORMAT_LABEL[p.format] || p.format}, ${fmtDay(p.date, { weekday: "long", day: "numeric", month: "short" })} at ${p.time || "no time"}. ${STATUS_LABEL[ds]}. ${p.hook}`,
    onclick: e => { if (!e.target.closest(".menu-btn")) openPost(p.id); },
    onkeydown: e => { if (e.key === "Enter" || e.key === " ") { e.preventDefault(); openPost(p.id); } } },
    el("div", { class: "top" }, pfBadge(p.platform), el("span", { class: "mono", text: p.time || "--:--" }), opts.compact ? null : el("span", { class: "ellipsis", text: FORMAT_LABEL[p.format] || p.format })),
    thumb,
    el("div", { class: `copy ${opts.compact ? "ellipsis" : "clamp2"}`, text: p.hook || "Untitled brief" }),
    opts.compact ? null : el("div", { class: "foot" }, el("span", { class: "row", style: "gap:6px;min-width:0;flex-wrap:nowrap" }, acctAva(p, true), el("span", { class: "xs muted ellipsis", text: p.account_name })), statusBadge(ds)));
  if (opts.compact) card.querySelector(".top").append(el("span", { style: "margin-left:auto" }, el("i", { class: "dot", title: STATUS_LABEL[ds], style: `background:${dotColor(ds)}` })));
  if (state.me.canEdit && !opts.compact) card.append(el("button", { class: "menu-btn", "aria-label": "Post actions", onclick: e => { e.stopPropagation(); postMenu(e.currentTarget, p); } }, icon("more")));
  if (drag) {
    card.addEventListener("dragstart", e => { state.dragId = p.id; e.dataTransfer.setData("text/plain", p.id); e.dataTransfer.effectAllowed = "move"; setTimeout(() => card.classList.add("dragging")); });
    card.addEventListener("dragend", () => { state.dragId = null; card.classList.remove("dragging"); document.querySelectorAll(".drop-ok").forEach(n => n.classList.remove("drop-ok")); });
  }
  return card;
}
function dotColor(ds) {
  return { shell: "var(--line-strong)", draft: "var(--muted)", needs_changes: "var(--alert)", blocked: "var(--error)", delayed: "var(--error)", approved: "var(--success)", scheduled: "var(--info)", posted: "var(--success)", rejected: "var(--line-strong)" }[ds] || "var(--muted)";
}
function postMenu(anchor, p) {
  openMenu(anchor, [
    { label: "Open", icon: "external", fn: () => openPost(p.id) },
    canMove(p) ? { label: "Move to another day or time", icon: "move", fn: () => openMoveModal(p) } : null,
    isPending(p) ? { label: "Review", sub: "Approve or request changes", icon: "review", fn: () => go("review", { id: p.id }) } : null,
    p.status === "approved" ? { label: "Mark scheduled", icon: "clock", fn: () => setStatus(p, "scheduled") } : null,
    p.status === "scheduled" ? { label: "Mark published", icon: "check", fn: () => setStatus(p, "posted") } : null,
    !isShell(p) ? { label: "Copy post text", icon: "copy", fn: () => copy(postText(p)) } : null
  ]);
}
const postText = p => (p.thread_parts || []).length ? p.thread_parts.join("\n\n") : publishText(p);

// ---------- drop targets ----------
function dropZone(node, accept, onDrop) {
  node.addEventListener("dragover", e => { const p = state.dragId && state.posts.get(state.dragId); if (p && accept(p)) { e.preventDefault(); e.dataTransfer.dropEffect = "move"; node.classList.add("drop-ok"); } });
  node.addEventListener("dragleave", e => { if (!node.contains(e.relatedTarget)) node.classList.remove("drop-ok"); });
  node.addEventListener("drop", e => { e.preventDefault(); node.classList.remove("drop-ok"); const p = state.posts.get(e.dataTransfer.getData("text/plain") || state.dragId); if (p) onDrop(p); });
  return node;
}

// ---------- overview ----------
function viewOverview() {
  const wait = notReady("bento"); if (wait) return wait;
  if (!state.posts.size) return emptyState("No posts yet", "Ask Claude in chat to plan a week, and the drafts appear here.", state.me.canEdit ? el("button", { class: "btn primary", onclick: () => openBriefModal({}) }, icon("plus"), "Create a brief") : null);
  const wk0 = thisWeek(), wk1 = addDays(wk0, 6);
  const all = allPosts();
  const pending = all.filter(p => isPending(p) && p.date >= addDays(todayIST(), -7));
  const blocked = pending.filter(isBlocked);
  const delayed = all.filter(isDelayed);
  const ready = all.filter(p => ["approved", "scheduled"].includes(p.status) && !isDelayed(p) && p.date >= todayIST());
  const hour = Number(nowIST().slice(11, 13));
  const first = (state.me.name || "").split(" ")[0];
  const greet = `${hour < 12 ? "Good morning" : hour < 17 ? "Good afternoon" : "Good evening"}${first ? ", " + first : ""}`;
  const tile = (cls, n, label, sub, onclick, span = 3) => el("button", { class: `tile ${cls} span-${span} half`, onclick }, el("span", { class: "kk", text: label }), el("span", { class: "kv", text: n }), el("span", { class: "xs muted", text: sub }));
  const out = [el("div", { class: "spread" }, el("div", {}, el("h2", { style: "font-size:1.25rem", text: greet }),
    el("p", { class: "small muted", text: `${fmtDay(todayIST(), { weekday: "long", day: "numeric", month: "long" })} · ${pending.length ? `${plural(pending.length, "post")} waiting for review` : "Nothing waiting for review"}` })))];
  const bento = el("div", { class: "bento" },
    tile("hero", pending.length, "Waiting for review", state.me.canEdit ? "Open the review queue" : "Editors approve these", () => { state.review.tab = "todo"; go("review"); }),
    tile(blocked.length ? "alert" : "", blocked.length, "Blocked by content checks", blocked.length ? "Fix before approving" : "All drafts pass the rules", () => { state.review.tab = "blocked"; go("review"); }),
    tile(delayed.length ? "alert" : "", delayed.length, "Delayed", delayed.length ? "Approved but not published on time" : "Nothing overdue", () => { state.filter = { account: "", platform: "", status: "delayed", q: "" }; state.cal.mode = "pipeline"; go("calendar"); }),
    tile("", ready.length, "Ready to post", "Approved or scheduled, upcoming", () => { state.filter = { account: "", platform: "", status: "approved", q: "" }; go("calendar"); }));
  const camps = campaigns();
  const camp = camps.find(c => c.active) || camps.find(c => c.upcoming) || camps[0];
  bento.append(camp ? campaignSpotlight(camp, "span-7") : weekMix(postsBetween(wk0, wk1, false), "span-7"), upNext("span-5"));
  bento.append(waitingOn(pending, "span-4"), recentActivity("span-4"), analyticsSnapshot("span-4"));
  bento.append(latestNews("span-6"), topIdeas("span-6"));
  out.push(bento);
  return out;
}
function campaignProgress(c) {
  const days = daysBetween(c.start, c.end) + 1;
  const dayN = Math.min(days, Math.max(0, daysBetween(c.start, todayIST()) + 1));
  const label = c.active ? `Day ${dayN} of ${days}` : c.upcoming ? `Starts ${fmtDay(c.start, { weekday: "long", day: "numeric", month: "short" })}` : `Ended ${fmtDay(c.end, { day: "numeric", month: "short" })}`;
  return el("div", { class: "sec" }, el("div", { class: "spread" }, el("span", { class: "small", text: label }), el("span", { class: "mono muted", text: `${fmtDay(c.start, { day: "numeric", month: "short" })} – ${fmtDay(c.end, { day: "numeric", month: "short" })}` })),
    el("div", { class: "progress", role: "progressbar", "aria-valuemin": "0", "aria-valuemax": String(days), "aria-valuenow": String(dayN), "aria-label": "Campaign progress" }, el("span", { style: `width:${(dayN / days) * 100}%` })));
}
const STATUS_BAR = ["posted", "scheduled", "approved", "needs_changes", "draft", "shell"];
function statusBar(list, title) {
  const c = countBy(list, p => { const d = displayStatus(p); return d === "blocked" ? "needs_changes" : d === "delayed" ? "approved" : d; });
  const total = list.length || 1;
  const col = { posted: "var(--success)", scheduled: "var(--info)", approved: "color-mix(in srgb, var(--success) 55%, var(--surface))", needs_changes: "var(--alert)", draft: "var(--line-strong)", shell: "var(--surface-3)" };
  return el("div", { class: "sec" }, title ? el("span", { class: "label", text: title }) : null,
    el("div", { class: "bar", role: "img", "aria-label": STATUS_BAR.filter(s => c[s]).map(s => `${c[s]} ${STATUS_LABEL[s].toLowerCase()}`).join(", ") }, STATUS_BAR.filter(s => c[s]).map(s => el("span", { style: `width:${(c[s] / total) * 100}%;background:${col[s]}` }))),
    el("div", { class: "legend" }, STATUS_BAR.filter(s => c[s]).map(s => el("span", {}, el("i", { style: `background:${col[s]}` }), `${STATUS_LABEL[s]} ${c[s]}`))));
}
function campaignSpotlight(c, span) {
  const plats = countBy(c.posts, "platform");
  const next = c.posts.filter(p => `${p.date}T${p.time || "00:00"}` >= nowIST() && p.status !== "rejected").slice(0, 3);
  return el("section", { class: `tile spot ${span}` },
    el("div", { class: "row", style: "align-items:flex-start;flex-wrap:nowrap;gap:12px" }, el("div", { class: "spot-badge", text: (c.name || "C")[0] }),
      el("div", { style: "min-width:0;flex:1;display:grid;gap:2px" }, el("span", { class: "label", text: c.active ? "Live campaign" : c.upcoming ? "Starts soon" : "Campaign" }),
        el("h2", { style: "font-size:1.25rem", text: c.name }), el("p", { class: "small muted clamp2", text: c.goal || "" })),
      el("button", { class: "btn sm", onclick: () => { state.campaignId = c.id; go("campaigns"); } }, "Open")),
    campaignProgress(c), statusBar(c.posts, `${plural(c.posts.length, "post")} by status`),
    el("div", { class: "pcounts" }, Object.entries(plats).sort((a, b) => b[1] - a[1]).map(([pl, n]) => el("span", { class: "pcount" }, pfBadge(pl), el("b", { text: n }), PLATFORM_SHORT[pl]))),
    next.length ? el("div", { class: "list-rows" }, el("div", { class: "grouphead", text: "Next in this campaign" }), next.map(lrow)) : null);
}
function weekMix(list, span) {
  return el("section", { class: `tile ${span}` }, el("h2", { text: "This week" }), list.length ? statusBar(list) : el("p", { class: "small muted", text: "Nothing planned this week yet." }));
}
function lrow(p) {
  return el("button", { class: "lrow", onclick: () => openPost(p.id) },
    el("span", { class: "mono", text: p.time || "--:--" }), pfBadge(p.platform),
    el("span", { style: "min-width:0" }, el("div", { class: "t ellipsis", text: p.hook || "Untitled brief" }), el("div", { class: "s ellipsis", text: `${p.account_name} · ${FORMAT_LABEL[p.format] || p.format}` })),
    statusBadge(p));
}
function upNext(span) {
  const now = nowIST();
  const list = allPosts().filter(p => `${p.date}T${p.time || "00:00"}` >= now && p.status !== "rejected").slice(0, 7);
  const card = el("section", { class: `tile ${span}` }, el("div", { class: "spread" }, el("h2", { text: "Up next" }), el("button", { class: "linkbtn small", onclick: () => go("calendar"), text: "Calendar" })));
  if (!list.length) { card.append(el("p", { class: "small muted", text: "Nothing planned ahead. Ask Claude to plan the next week." })); return card; }
  const rows = el("div", { class: "list-rows" });
  let day = null;
  const today = todayIST(), tomorrow = addDays(today, 1);
  for (const p of list) {
    if (p.date !== day) { day = p.date; rows.append(el("div", { class: "grouphead", text: day === today ? "Today" : day === tomorrow ? "Tomorrow" : fmtDay(day, { weekday: "long", day: "numeric", month: "short" }) })); }
    rows.append(lrow(p));
  }
  card.append(rows);
  return card;
}
function waitingOn(pending, span) {
  const by = countBy(pending, p => p.approver || "manager");
  const card = el("section", { class: `tile ${span}` }, el("h2", { text: "Waiting on" }));
  const keys = Object.keys(by);
  if (!keys.length) { card.append(el("div", { class: "okline" }, icon("check"), "Everyone is up to date")); return card; }
  const desc = { founder: "Pathvik, ICLC and his own posts", manager: "Company and initiative posts", self: "Their own advocacy drafts" };
  card.append(el("div", {}, keys.sort((a, b) => by[b] - by[a]).map(k => el("div", { class: "who" },
    ava(APPROVER[k] || k, "var(--a-other)"), el("div", { style: "min-width:0" }, el("b", { class: "small", text: APPROVER[k] || k }), el("div", { class: "xs muted", text: desc[k] || "" })),
    el("span", { class: "n", text: by[k] })))));
  return card;
}
function activityItems() {
  const items = [];
  for (const p of state.posts.values()) {
    if (p.review && p.review.at && p.review.by) items.push({ at: p.review.at, by: p.review.by, post: p, text: `marked it ${(STATUS_LABEL[p.status] || p.status).toLowerCase()}` });
    if (isShell(p) && p.created_by) items.push({ at: p.created_at || p.updated_at, by: p.created_by, post: p, text: "added a brief" });
  }
  for (const c of state.comments) { const p = state.posts.get(c.post_id); if (p) items.push({ at: c.at, by: c.by, post: p, text: c.kind === "change_request" ? "requested changes" : "commented" }); }
  for (const i of state.ideas) items.push({ at: i.at, by: i.by, idea: i, text: "added an idea" });
  return items.filter(x => x.at).sort((a, b) => b.at.localeCompare(a.at));
}
function recentActivity(span) {
  const items = activityItems().slice(0, 6);
  const card = el("section", { class: `tile ${span}` }, el("h2", { text: "Recent activity" }));
  if (!items.length) { card.append(el("p", { class: "small muted", text: "Approvals, comments and new ideas show up here." })); return card; }
  card.append(el("div", { class: "feed" }, items.map(it => el("div", { class: "ev" }, personAva(it.by),
    el("p", {}, el("b", { text: nameOf(it.by) }), ` ${it.text} `,
      it.post ? el("button", { class: "linkbtn", onclick: () => openPost(it.post.id), text: `“${(it.post.hook || "a brief").slice(0, 52)}${(it.post.hook || "").length > 52 ? "…" : ""}”` })
        : el("button", { class: "linkbtn", onclick: () => go("ideas"), text: `“${it.idea.text.slice(0, 52)}${it.idea.text.length > 52 ? "…" : ""}”` }),
      el("span", { class: "muted xs", text: ` · ${ago(it.at)}` }))))));
  return card;
}
function analyticsSnapshot(span) {
  const a = state.analytics;
  const card = el("button", { class: `tile ${span}`, onclick: () => go("analytics") }, el("h2", { text: "Reach last week" }));
  if (!a || !a.has_data) { card.append(el("div", { class: "ghost-chart", "aria-hidden": "true" }), el("p", { class: "small muted", text: "No results imported yet. Send Claude your Instagram or LinkedIn export to start tracking." })); return card; }
  const k = kpisFor(a.series, a.weeks[a.weeks.length - 2], a.weeks[a.weeks.length - 3]);
  card.append(el("div", { class: "row", style: "align-items:baseline" }, el("span", { class: "kv", text: fmtCompact(k.cur.impressions) }), deltaEl(k.cur.impressions, k.prev.impressions, "pct")),
    el("p", { class: "xs muted", text: `Engagement rate ${fmtPct(k.cur.er)} · Follower change ${k.cur.followers == null ? "–" : signed(k.cur.followers)}` }));
  return card;
}
function latestNews(span) {
  const n = state.news[0];
  const card = el("section", { class: `tile ${span}` }, el("div", { class: "spread" }, el("h2", { text: "Latest announcement" }), el("button", { class: "linkbtn small", onclick: () => go("news"), text: "All" })));
  if (!n) { card.append(el("p", { class: "small muted", text: state.me.canEdit ? "Post the first update for the team." : "Editors post team updates here." })); return card; }
  card.append(el("h3", { text: n.title }), n.body ? el("p", { class: "small muted clamp3", text: n.body }) : null, el("span", { class: "xs muted", text: `${nameOf(n.by)} · ${ago(n.at)}` }));
  return card;
}
function topIdeas(span) {
  const list = state.ideas.filter(i => !["converted", "archived"].includes(i.status)).sort((a, b) => voteCount(b) - voteCount(a)).slice(0, 4);
  const card = el("section", { class: `tile ${span}` }, el("div", { class: "spread" }, el("h2", { text: "Top ideas" }), el("button", { class: "linkbtn small", onclick: () => go("ideas"), text: "Idea board" })));
  if (!list.length) { card.append(el("p", { class: "small muted", text: "No ideas yet. Anyone on the team can add one." }), state.me.canWrite || state.me.canEdit ? el("button", { class: "btn sm", style: "justify-self:start", onclick: () => openIdeaModal({}) }, icon("plus"), "Add an idea") : null); return card; }
  card.append(el("div", { class: "list-rows" }, list.map(i => el("button", { class: "lrow", style: "grid-template-columns:44px minmax(0,1fr)", onclick: () => go("ideas") },
    el("span", { class: "vote", "aria-label": `${voteCount(i)} votes` }, icon("up"), voteCount(i)), el("span", { class: "t clamp2", text: i.text })))));
  return card;
}

// ---------- calendar ----------
function calRange() {
  const a = state.cal.anchor || todayIST();
  if (state.cal.mode === "month") { const first = a.slice(0, 7) + "-01"; const start = mondayOf(first); const last = addDays(addMonths(first, 1), -1); return { start, end: addDays(mondayOf(last), 6), first, last }; }
  const start = mondayOf(a); return { start, end: addDays(start, 6) };
}
function viewCalendar() {
  const wait = notReady(); if (wait) return wait;
  const mode = state.cal.mode;
  const r = calRange();
  const seg = el("div", { class: "seg", role: "group", "aria-label": "Calendar view" }, [["month", "Month"], ["week", "Week"], ["pipeline", "Pipeline"]].map(([m, l]) =>
    el("button", { "aria-pressed": String(mode === m), onclick: () => { state.cal.mode = m; savePrefs(); render(); }, text: l })));
  const step = d => { state.cal.anchor = mode === "month" ? addMonths(state.cal.anchor || todayIST(), d) : addDays(state.cal.anchor || todayIST(), 7 * d); state.cal.day = null; render(); };
  const label = mode === "month" ? fmtDay(r.first, { month: "long", year: "numeric" }) : `${fmtDay(r.start, { day: "numeric", month: "short" })} – ${fmtDay(r.end, { day: "numeric", month: "short", year: "numeric" })}`;
  const nav = el("div", { class: "datenav" }, el("button", { "aria-label": mode === "month" ? "Previous month" : "Previous week", onclick: () => step(-1) }, icon("left")),
    el("strong", { "aria-live": "polite", text: label }), el("button", { "aria-label": mode === "month" ? "Next month" : "Next week", onclick: () => step(1) }, icon("right")),
    el("button", { onclick: () => { state.cal.anchor = todayIST(); state.cal.day = null; render(); }, text: "Today" }));
  const bar = filterBar({ lead: el("div", { class: "row" }, seg, nav) });
  const ps = postsBetween(r.start, r.end);
  const hint = state.me.canEdit ? el("p", { class: "hint", text: mode === "pipeline" ? "Drag a card to the next stage: Approved → Scheduled → Published. Approvals happen in Review." : "Drag a post to another day" + (mode === "week" ? " or hour" : "") + " to reschedule. It saves straight away, and you can undo." }) : null;
  if (!state.posts.size) return [bar, emptyState("No posts planned yet", "Ask Claude in chat to plan a week, or create a brief.", state.me.canEdit ? el("button", { class: "btn primary", onclick: () => openBriefModal({}) }, icon("plus"), "Create a brief") : null)];
  const body = mode === "month" ? monthView(r, ps) : mode === "week" ? weekView(r, ps) : pipelineView(ps);
  const out = [bar, hint, body];
  if (!ps.length) out.push(emptyState(matchesActive() ? "No posts match these filters" : `Nothing planned ${mode === "month" ? "this month" : "this week"}`, matchesActive() ? "Clear the filters to see everything." : "Use the arrows to see another period, or ask Claude to plan it."));
  return out;
}
function dayTag(d) { const kd = KEY_DATES[d]; return kd ? el("span", { class: `dtag${kd[1] ? " sensitive" : ""}`, title: kd[1] ? "Sensitive day: no promotional posts" : kd[0], text: kd[0] }) : null; }
function monthView(r, ps) {
  const today = todayIST();
  const grid = el("div", { class: "month", role: "grid", "aria-label": fmtDay(r.first, { month: "long", year: "numeric" }) },
    ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"].map(d => el("div", { class: "dow", role: "columnheader", text: d })));
  const days = daysBetween(r.start, r.end) + 1;
  const sel = state.cal.day || (today >= r.first && today <= r.last ? today : (ps.find(p => p.date >= r.first) || {}).date || r.first);
  for (let i = 0; i < days; i++) {
    const d = addDays(r.start, i);
    const mine = ps.filter(p => p.date === d);
    const cell = el("div", { class: `mcell${d < r.first || d > r.last ? " out" : ""}${d === today ? " today" : ""}`, role: "gridcell", "aria-selected": String(d === sel),
      onclick: e => { if (!e.target.closest(".pcard, .more")) { state.cal.day = d; renderMain(); } } },
      el("div", { class: "dhead" }, el("span", { class: "dnum", text: fmtDay(d, { day: "numeric" }) }), dayTag(d)),
      mine.slice(0, 3).map(p => pcard(p, { compact: true, draggable: true })),
      mine.length > 3 ? el("button", { class: "more", onclick: () => { state.cal.day = d; renderMain(); setTimeout(() => $("#dayAgenda")?.scrollIntoView({ behavior: "smooth", block: "start" })); }, text: `+${mine.length - 3} more` }) : null,
      mine.length ? el("div", { class: "mdots", "aria-hidden": "true" }, mine.slice(0, 8).map(p => el("i", { style: `--pc:var(--p-${p.platform})` }))) : null);
    if (d === sel) cell.style.boxShadow = "inset 0 0 0 2px var(--line-strong)";
    dropZone(cell, p => canMove(p) && d >= today, p => movePost(p, d, p.time || DEFAULT_TIME[p.platform]));
    grid.append(cell);
  }
  const list = ps.filter(p => p.date === sel);
  const agenda = el("section", { class: "card", id: "dayAgenda" }, el("div", { class: "spread" }, el("h2", { text: fmtDay(sel, { weekday: "long", day: "numeric", month: "long" }) }), dayTag(sel)),
    list.length ? el("div", { class: "list-rows" }, list.map(lrow)) : el("p", { class: "small muted", text: "Nothing planned this day." }));
  return el("div", { class: "stack" }, grid, agenda);
}
function weekView(r, ps) {
  const today = todayIST(), now = nowIST();
  const days = [...Array(7)].map((_, i) => addDays(r.start, i));
  const tl = el("div", { class: "timeline", role: "grid", "aria-label": "Week timeline" }, el("div", { class: "tl-corner" }));
  for (const d of days) tl.append(el("div", { class: `tl-head${d === today ? " today" : ""}`, role: "columnheader" }, el("span", { text: fmtDay(d, { weekday: "short" }) }), el("span", { class: "dnum", text: fmtDay(d, { day: "numeric" }) }), dayTag(d)));
  for (let h = 0; h < 24; h++) {
    tl.append(el("div", { class: "tl-hour", "data-hour": String(h), text: `${String(h).padStart(2, "0")}:00` }));
    for (const d of days) {
      const mine = ps.filter(p => p.date === d && Math.floor(minutesOf(p.time) / 60) === h);
      const cell = el("div", { class: `tl-cell${d === today && Number(now.slice(11, 13)) === h ? " now" : ""}`, role: "gridcell" }, mine.map(p => pcard(p, { compact: true, draggable: true })));
      const slotOk = `${d}T${String(h).padStart(2, "0")}:59` >= now;
      dropZone(cell, p => canMove(p) && slotOk, p => { const mm = minutesOf(p.time) % 60; let t = hhmm(h * 60 + mm); if (`${d}T${t}` < now) t = hhmm(h * 60 + Math.min(59, Number(now.slice(14, 16)) + 5)); movePost(p, d, t); });
      tl.append(cell);
    }
  }
  const key = `tl-${r.start}`;
  const wrap = el("div", { class: "timeline-wrap", "data-keep": key, "data-needs-init": "1" }, tl);
  if (!scrollKeep.has(key)) setTimeout(() => {
    const w = main.querySelector(`[data-keep="${key}"]`); if (!w || scrollKeep.has(key)) return;
    const row = w.querySelector('[data-hour="7"]'), head = w.querySelector(".tl-head");
    if (row) w.scrollTop = row.offsetTop - (head ? head.offsetHeight : 40);
    scrollKeep.set(key, [w.scrollLeft, w.scrollTop]);
  }, 0);
  return wrap;
}
const PIPE = [["shell", "Briefs", "Claude writes these at the next sync"], ["draft", "Draft", "Waiting for review"], ["needs_changes", "Needs changes", "Sent back with a checklist"], ["approved", "Approved", "Ready to schedule"], ["scheduled", "Scheduled", "Set up in the platform's scheduler"], ["posted", "Published", ""]];
function pipelineView(ps) {
  const board = el("div", { class: "kanban", "data-keep": "pipeline" });
  for (const [s, label, hint] of PIPE) {
    const list = ps.filter(p => p.status === s);
    const col = el("section", { class: "kcol", "aria-label": `${label}: ${list.length}` },
      el("div", { class: "kcol-head" }, el("h3", {}, el("i", { class: "dot", style: `background:${dotColor(s)}` }), label), el("span", { class: "n", text: list.length })),
      hint ? el("div", { class: "hint", style: "padding:0 4px", text: hint }) : null,
      list.map(p => pcard(p, { draggable: true })));
    dropZone(col, p => p.status !== s, p => pipelineDrop(p, s));
    board.append(col);
  }
  return board;
}
function pipelineDrop(p, to) {
  const from = p.status;
  if (to === "approved" && isPending(p)) {
    if (isBlocked(p)) { toast("This post is blocked by content checks. Fix it in Review first.", { warn: true }); return; }
    toast("Approvals happen in Review, so someone reads the whole post first.");
    go("review", { id: p.id }); return;
  }
  if (to === "needs_changes" && ["draft", "approved", "scheduled"].includes(from)) { openChangesModal(p); return; }
  const ok = { approved: ["scheduled"], scheduled: ["posted", "approved"] }[from] || [];
  if (!ok.includes(to)) {
    const why = from === "shell" ? "Briefs move on once Claude writes them." : from === "posted" ? "Published posts stay published." : to === "shell" || to === "draft" ? "Posts can't go back to draft by dragging. Use Request changes in Review." : "That step isn't allowed by dragging.";
    toast(why, { warn: true }); return;
  }
  setStatus(p, to);
}
