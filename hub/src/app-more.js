// Ideas board, Quick Draft / Convert to Draft, Campaigns, Advocacy, Announcements, Reports, and start-up.

// ---------- ideas ----------
const voteCount = i => Object.values(i.votes || {}).filter(Boolean).length;
const canWriteIdeas = () => !!(state.me.canWrite || state.me.canEdit);
const ICEBOX = "Icebox";
function ideaLanes(list) {
  if (state.ideasBy === "pillar") {
    const acc = state.ideasAccount || [...accounts().keys()][0];
    const pillars = (accounts().get(acc) || {}).pillars || [];
    const mine = list.filter(i => (i.account || "") === acc);
    const lanes = pillars.map(p => ({ key: p, title: p, ideas: mine.filter(i => i.pillar === p) }));
    lanes.push({ key: "", title: "No pillar yet", ideas: mine.filter(i => !i.pillar || !pillars.includes(i.pillar)) });
    return { lanes, acc };
  }
  const names = new Set([ICEBOX, ...campaigns().filter(c => !c.upcoming || c.active || true).map(c => c.name), ...list.map(i => i.lane).filter(Boolean), ...(state.extraLanes || [])]);
  return { lanes: [...names].map(n => ({ key: n, title: n, ideas: list.filter(i => (i.lane || ICEBOX) === n) })) };
}
function viewIdeas() {
  const wait = notReady(); if (wait) return wait;
  const showDone = !!state.ideasShowDone;
  const live = state.ideas.filter(i => i.status !== "archived" && (showDone || i.status !== "converted"));
  const seg = el("div", { class: "seg", role: "group", "aria-label": "Group ideas by" }, [["lane", "Campaign ideas"], ["pillar", "Content pillars"]].map(([v, l]) =>
    el("button", { "aria-pressed": String(state.ideasBy === v), onclick: () => { state.ideasBy = v; savePrefs(); render(); }, text: l })));
  const { lanes, acc } = ideaLanes(live);
  const accSel = state.ideasBy === "pillar" ? el("select", { "aria-label": "Account", onchange: e => { state.ideasAccount = e.target.value; render(); } }, [...accounts()].map(([id, a]) => el("option", { value: id, text: a.name }))) : null;
  if (accSel) accSel.value = acc;
  const done = el("label", { class: "row small", style: "gap:6px" }, (() => { const c = el("input", { type: "checkbox", onchange: e => { state.ideasShowDone = e.target.checked; render(); } }); c.checked = showDone; return c; })(), "Show converted");
  const bar = el("div", { class: "toolbar" }, seg, accSel, done, el("span", { class: "grow" }),
    state.ideasBy === "lane" && canWriteIdeas() ? el("button", { class: "btn", onclick: addLane }, icon("plus"), "New lane") : null,
    canWriteIdeas() ? el("button", { class: "btn primary", onclick: () => openIdeaModal({ lane: state.ideasBy === "lane" ? ICEBOX : "", account: acc || "" }) }, icon("plus"), "Add idea") : null);
  if (!state.ideas.length) return [bar, emptyState("No ideas yet", "Ideas from anyone on the team land here. Vote on the ones you like; editors turn the best into briefs for Claude.", canWriteIdeas() ? el("button", { class: "btn primary", onclick: () => openIdeaModal({}) }, icon("plus"), "Add the first idea") : null)];
  const board = el("div", { class: "board", "data-keep": `ideas-${state.ideasBy}` }, lanes.map(l => {
    const lane = el("section", { class: "lane", "aria-label": `${l.title}: ${l.ideas.length} ideas` },
      el("div", { class: "kcol-head" }, el("h3", { class: "clamp2", text: l.title }), el("span", { class: "n", text: l.ideas.length })),
      l.ideas.sort((a, b) => voteCount(b) - voteCount(a) || (b.at || "").localeCompare(a.at || "")).map(ideaCard),
      canWriteIdeas() ? el("button", { class: "lane-add", onclick: () => openIdeaModal(state.ideasBy === "lane" ? { lane: l.key } : { account: acc, pillar: l.key }) }, "+ Add idea") : null);
    if (canWriteIdeas()) dropZoneIdea(lane, l.key);
    return lane;
  }));
  return [bar, el("p", { class: "hint", text: state.ideasBy === "lane" ? "Drag ideas between lanes to group them into campaigns. The Icebox holds ideas for later." : "Ideas grouped by the account's content pillars, so you can see which pillars need ideas." }), board];
}
function addLane() {
  const inp = el("input", { type: "text", placeholder: "e.g. ICLC school outreach", "aria-label": "Lane name", autofocus: true });
  openModal(() => [el("h2", { text: "New lane" }), el("p", { class: "small muted", text: "A lane groups ideas for a campaign or theme. It's saved when you add the first idea to it." }), inp,
    el("div", { class: "foot" }, el("button", { class: "btn", onclick: closeModal, text: "Cancel" }), el("button", { class: "btn primary", onclick: () => { const n = inp.value.trim(); if (!n) return; state.extraLanes = [...(state.extraLanes || []), n]; closeModal(); render(); }, text: "Add lane" }))], { label: "New lane" });
}
function dropZoneIdea(node, key) {
  node.addEventListener("dragover", e => { if (state.dragIdea) { e.preventDefault(); node.classList.add("drop-ok"); } });
  node.addEventListener("dragleave", e => { if (!node.contains(e.relatedTarget)) node.classList.remove("drop-ok"); });
  node.addEventListener("drop", e => {
    e.preventDefault(); node.classList.remove("drop-ok");
    const i = state.ideas.find(x => x.id === state.dragIdea); if (!i) return;
    const field = state.ideasBy === "lane" ? "lane" : "pillar";
    if ((i[field] || (field === "lane" ? ICEBOX : "")) === key) return;
    i[field] = key; render();
    guarded(() => db.doc(`ideas/${i.id}`).update({ [field]: key }), `Moved to ${key || "No pillar yet"}`);
  });
}
function ideaCard(i) {
  const mine = i.votes && i.votes[state.me.id];
  const n = voteCount(i);
  const card = el("article", { class: `idea${i.status === "converted" ? " done" : ""}`, draggable: canWriteIdeas() ? "true" : null },
    el("div", { class: "spread", style: "flex-wrap:nowrap" }, el("span", { class: "row", style: "gap:6px;min-width:0;flex-wrap:nowrap" }, personAva(i.by), el("span", { class: "xs muted ellipsis", text: `${nameOf(i.by)} · ${ago(i.at)}` })),
      canWriteIdeas() ? el("button", { class: "vote", "aria-pressed": String(!!mine), "aria-label": `${mine ? "Remove your vote" : "Vote for this idea"}, ${n} votes`, onclick: () => vote(i) }, icon("up"), n) : el("span", { class: "vote", text: `▲ ${n}` })),
    el("p", { text: i.text }),
    (i.links || []).length ? el("div", { class: "links" }, i.links.map(u => el("a", { href: u, target: "_blank", rel: "noopener noreferrer", title: u, text: u.replace(/^https?:\/\/(www\.)?/, "").slice(0, 40) }))) : null,
    (i.images || []).length ? el("div", { class: "shots" }, i.images.slice(0, 6).map(src => el("a", { href: imgUrl(src), target: "_blank", rel: "noopener" }, el("img", { src: imgUrl(src), alt: "Inspiration screenshot", loading: "lazy" })))) : null,
    el("div", { class: "spread" }, el("span", { class: "row", style: "gap:6px" }, i.account ? el("span", { class: "badge draft", text: accountName(i.account) }) : null, i.status === "converted" ? el("span", { class: "badge approved", text: "Brief created" }) : null),
      el("span", { class: "row", style: "gap:4px" },
        state.me.canEdit && i.status !== "converted" ? el("button", { class: "btn sm", onclick: () => openBriefModal({ idea: i }) }, "Convert to draft") : null,
        canWriteIdeas() && (i.by === state.me.id || state.me.canEdit) ? el("button", { class: "iconbtn", "aria-label": "Idea actions", "data-tip": "More", onclick: e => openMenu(e.currentTarget, [
          { label: "Edit", icon: "edit", fn: () => openIdeaModal({ idea: i }) },
          i.status === "converted" && i.post_ref && state.posts.get(i.post_ref) ? { label: "Open the brief", icon: "external", fn: () => openPost(i.post_ref) } : null,
          { label: "Archive", sub: "Hide it from the board", icon: "x", fn: () => guarded(() => db.doc(`ideas/${i.id}`).update({ status: "archived" }), "Idea archived") }]) }, icon("more")) : null)));
  card.addEventListener("dragstart", e => { state.dragIdea = i.id; e.dataTransfer.setData("text/plain", i.id); e.dataTransfer.effectAllowed = "move"; setTimeout(() => card.classList.add("dragging")); });
  card.addEventListener("dragend", () => { state.dragIdea = null; card.classList.remove("dragging"); });
  return card;
}
const imgUrl = src => /^(https?:|\/|data:)/.test(src) ? src : `/_blob/${src}`;
function vote(i) {
  const on = !(i.votes && i.votes[state.me.id]);
  i.votes = { ...(i.votes || {}), [state.me.id]: on }; render();
  guarded(() => db.doc(`ideas/${i.id}`).update({ votes: i.votes }), null);
}
function openIdeaModal({ idea, lane = "", account = "", pillar = "" }) {
  const editing = !!idea;
  const ta = el("textarea", { rows: 4, placeholder: "A post idea, a story from the field, a question students keep asking…", "aria-label": "Idea", autofocus: true }); ta.value = idea ? idea.text : "";
  const acc = el("select", { "aria-label": "Account" }, el("option", { value: "", text: "Any account" }), [...accounts()].map(([id, a]) => el("option", { value: id, text: a.name })));
  acc.value = idea ? idea.account || "" : account;
  const pil = el("select", { "aria-label": "Content pillar" });
  const fillPillars = () => { const ps = (accounts().get(acc.value) || {}).pillars || []; pil.replaceChildren(el("option", { value: "", text: ps.length ? "No pillar yet" : "Pick an account first" }), ps.map(p => el("option", { value: p, text: p }))); pil.value = idea ? idea.pillar || "" : pillar; };
  acc.addEventListener("change", fillPillars); fillPillars();
  const laneNames = ideaLanes([]).lanes ? [...new Set([ICEBOX, ...campaigns().map(c => c.name), ...state.ideas.map(x => x.lane).filter(Boolean), ...(state.extraLanes || [])])] : [ICEBOX];
  const ln = el("input", { type: "text", list: "laneList", "aria-label": "Lane" }); ln.value = idea ? idea.lane || ICEBOX : lane || ICEBOX;
  const links = el("textarea", { rows: 2, placeholder: "One link per line (articles, reference posts)", "aria-label": "Links" }); links.value = idea ? (idea.links || []).join("\n") : "";
  let images = idea ? [...(idea.images || [])] : [];
  const shots = el("div", { class: "shots" });
  const drawShots = () => shots.replaceChildren(...images.map(src => el("img", { src: imgUrl(src), alt: "Inspiration screenshot" })));
  drawShots();
  const file = el("input", { type: "file", accept: "image/*", multiple: true, class: "sr", id: "ideaFiles" });
  const upMsg = el("span", { class: "hint" });
  file.addEventListener("change", async () => {
    if (!assets) { upMsg.textContent = "Screenshots can't be uploaded here."; return; }
    for (const f of [...file.files].slice(0, 6 - images.length)) {
      if (f.size > 8e6) { upMsg.textContent = `${f.name} is over 8 MB; skipped.`; continue; }
      upMsg.textContent = `Uploading ${f.name}…`;
      try { const r = await assets.upload(f); images.push(r.url || r.id); drawShots(); upMsg.textContent = ""; } catch { upMsg.textContent = `Couldn't upload ${f.name}.`; }
    }
    file.value = "";
  });
  const save = async () => {
    const text = ta.value.trim(); if (!text) { toast("Write the idea first.", { warn: true }); return; }
    const doc = { text, account: acc.value, pillar: pil.value, lane: ln.value.trim() || ICEBOX, links: links.value.split(/\s+/).map(s => s.trim()).filter(s => /^https?:\/\//.test(s)).slice(0, 8), images };
    closeModal();
    if (editing) await guarded(() => db.doc(`ideas/${idea.id}`).update(doc), "Idea updated");
    else await guarded(() => db.collection("ideas").add({ ...doc, by: state.me.id, at: new Date().toISOString(), status: "new", votes: {} }), "Idea added. Claude reads new ideas when it plans");
  };
  openModal(() => [el("h2", { text: editing ? "Edit idea" : "New idea" }), ta,
    el("div", { class: "grid2" }, el("label", { class: "field" }, "Account", acc), el("label", { class: "field" }, "Content pillar", pil)),
    el("label", { class: "field" }, "Lane (campaign idea)", ln, el("datalist", { id: "laneList" }, laneNames.map(n => el("option", { value: n })))),
    el("label", { class: "field" }, "Quick links", links),
    el("div", { class: "sec" }, el("div", { class: "spread" }, el("span", { class: "label", text: "Inspiration screenshots" }), el("label", { class: "btn sm", for: "ideaFiles" }, icon("image"), "Add images"), file), shots, upMsg),
    el("div", { class: "foot" }, el("button", { class: "btn", onclick: closeModal, text: "Cancel" }), el("button", { class: "btn primary", onclick: save, text: editing ? "Save" : "Add idea" }))], { label: editing ? "Edit idea" : "New idea" });
}

// ---------- Quick Draft / Convert to Draft: creates a brief ("shell") that Claude writes at the next sync ----------
function nextFreeSlot(account, platform) {
  const probe = { id: "_new", account, account_name: accountName(account), platform };
  const times = [...new Set([DEFAULT_TIME[platform] || "10:00", "09:30", "12:30", "17:30", "19:30", "21:30"])];
  for (let i = 1; i < 30; i++) { const d = addDays(todayIST(), i); for (const t of times) if (!spacingProblems(probe, d, t).length) return [d, t]; }
  return [addDays(todayIST(), 1), DEFAULT_TIME[platform] || "10:00"];
}
function openBriefModal({ idea }) {
  if (!state.me.canEdit) { toast("Only editors can create briefs. Add it as an idea instead.", { warn: true }); return; }
  const accs = [...accounts()].filter(([, a]) => (a.platforms || []).length || allPosts().some(p => p.account === a.name));
  const acc = el("select", { "aria-label": "Account" }, accs.map(([id, a]) => el("option", { value: id, text: a.name })));
  acc.value = idea && idea.account && accounts().has(idea.account) ? idea.account : (accs.find(([id]) => id === "pathvik") || accs[0] || [""])[0];
  const plat = el("select", { "aria-label": "Platform" }), fmt = el("select", { "aria-label": "Format" }), pil = el("select", { "aria-label": "Content pillar" });
  const theme = el("select", { "aria-label": "Theme" }, Object.entries(THEMES).map(([k, v]) => el("option", { value: k, text: v })));
  const date = el("input", { type: "date", min: addDays(todayIST(), 0), "aria-label": "Date" }), time = el("input", { type: "time", "aria-label": "Time (IST)" });
  const camp = el("select", { "aria-label": "Campaign" }, el("option", { value: "", text: "No campaign" }), campaigns().filter(c => !c.upcoming || true).map(c => el("option", { value: c.id, text: c.name })));
  const hook = el("textarea", { rows: 2, placeholder: "The idea or angle, in a sentence", "aria-label": "Idea or working hook", autofocus: true }); hook.value = idea ? idea.text.split("\n")[0].slice(0, 200) : "";
  const notes = el("textarea", { rows: 3, placeholder: "Anything Claude should know: audience, facts to use, what to avoid", "aria-label": "Notes for Claude" });
  if (idea) notes.value = [idea.text.length > 200 || idea.text.includes("\n") ? idea.text : "", ...(idea.links || [])].filter(Boolean).join("\n");
  const warn = el("div");
  const fill = () => {
    const a = accounts().get(acc.value) || {};
    const pls = (a.platforms || []).length ? a.platforms : Object.keys(PLATFORMS);
    const keepP = plat.value; plat.replaceChildren(...pls.map(p => el("option", { value: p, text: PLATFORMS[p] }))); plat.value = pls.includes(keepP) ? keepP : pls[0];
    const ps = a.pillars || []; pil.replaceChildren(el("option", { value: "", text: "Let Claude pick" }), ps.map(p => el("option", { value: p, text: p }))); pil.value = idea && ps.includes(idea.pillar) ? idea.pillar : "";
    fillPlat();
  };
  const fillPlat = () => {
    const fs = FORMATS_BY_PLATFORM[plat.value] || ["text"]; fmt.replaceChildren(...fs.map(f => el("option", { value: f, text: FORMAT_LABEL[f] })));
    [date.value, time.value] = nextFreeSlot(acc.value, plat.value); check();
  };
  const check = () => { const pr = spacingProblems({ id: "_new", account: acc.value, account_name: accountName(acc.value), platform: plat.value }, date.value, time.value); warn.replaceChildren(pr.length ? el("div", { class: "callout warn", text: `Spacing: ${pr.join("; ")}.` }) : ""); };
  acc.addEventListener("change", fill); plat.addEventListener("change", fillPlat); date.addEventListener("input", check); time.addEventListener("input", check);
  fill();
  const create = async () => {
    const h = hook.value.trim(); if (!h) { toast("Add the idea or working hook.", { warn: true }); return; }
    if (`${date.value}T${time.value}` < nowIST()) { toast("Pick a time in the future.", { warn: true }); return; }
    const a = accounts().get(acc.value) || {};
    let id = `${date.value}-${acc.value}-${plat.value}-${slug(h)}`, k = 2; while (state.posts.has(id)) id = `${date.value}-${acc.value}-${plat.value}-${slug(h)}-${k++}`;
    const at = new Date().toISOString();
    const doc = { id, idea_id: idea ? `idea-${idea.id}` : id, status: "shell", account: acc.value, account_name: a.name || acc.value, account_type: a.type || "company", approver: a.approver || "manager",
      platform: plat.value, format: fmt.value, theme: theme.value, pillar: pil.value, date: date.value, time: time.value, hook: h, caption: "", cta: "", hashtags: [],
      internal_notes: notes.value.trim(), campaign: camp.value || null, idea_ref: idea ? idea.id : null, created_by: state.me.id, created_at: at, updated_at: at,
      slot_source: "manual", slot_reason: "Chosen on the hub", edits: [], review: {}, blocked: true,
      issues: [{ severity: "block", rule: 0, check: "not_written", message: "Not written yet. Claude writes and checks this brief at the next sync.", excerpt: "" }] };
    closeModal();
    const ok = await guarded(async () => {
      await db.doc(`posts/${id}`).set(doc);
      if (idea) await db.doc(`ideas/${idea.id}`).update({ status: "converted", post_ref: id });
    }, "Brief created. Claude writes it at the next sync", { action: { label: "Open", fn: () => openPost(id) } });
    if (ok) { state.posts.set(id, doc); render(); }
  };
  openModal(() => [el("div", {}, el("h2", { text: idea ? "Convert idea to a draft" : "Quick draft" }), el("p", { class: "small muted", text: "Creates a brief on the calendar. Claude writes the post, design brief and checks at the next sync, and it then goes to review like any other post." })),
    el("label", { class: "field" }, "Idea or working hook", hook),
    el("div", { class: "grid2" }, el("label", { class: "field" }, "Account", acc), el("label", { class: "field" }, "Platform", plat), el("label", { class: "field" }, "Format", fmt), el("label", { class: "field" }, "Theme", theme),
      el("label", { class: "field" }, "Date", date), el("label", { class: "field" }, "Time (IST)", time), el("label", { class: "field" }, "Content pillar", pil), el("label", { class: "field" }, "Campaign", camp)),
    warn, el("label", { class: "field" }, "Notes for Claude", notes),
    el("div", { class: "foot" }, el("button", { class: "btn", onclick: closeModal, text: "Cancel" }), el("button", { class: "btn primary", onclick: create }, icon("plus"), "Create brief"))], { label: idea ? "Convert idea to a draft" : "Quick draft" });
}

// ---------- campaigns ----------
function viewCampaigns() {
  const wait = notReady(); if (wait) return wait;
  const list = campaigns();
  if (!list.length) return emptyState("No campaigns yet", "Ask Claude to plan a campaign, such as a launch or a seasonal push.");
  const c = list.find(x => x.id === state.campaignId) || list[0];
  const posts = c.posts.filter(matches);
  const out = [];
  if (list.length > 1) out.push(el("div", { class: "seg" }, list.map(x => el("button", { "aria-pressed": String(x.id === c.id), onclick: () => { state.campaignId = x.id; render(); }, text: x.name }))));
  out.push(el("div", { class: "bento" },
    el("section", { class: "tile spot span-7" }, el("div", { class: "row", style: "align-items:flex-start;flex-wrap:nowrap;gap:12px" }, el("div", { class: "spot-badge", text: (c.name || "C")[0] }),
      el("div", { style: "min-width:0;flex:1;display:grid;gap:4px" }, el("span", { class: "label", text: c.active ? "Live campaign" : c.upcoming ? "Starts soon" : "Finished" }), el("h2", { style: "font-size:1.4rem", text: c.name }), el("p", { class: "small", text: c.goal || "" }))),
      campaignProgress(c), c.summary ? el("p", { class: "small muted", text: c.summary }) : null, statusBar(c.posts, `${plural(c.posts.length, "post")} by status`)),
    el("section", { class: "tile span-5" }, el("div", { class: "sec" }, el("span", { class: "label", text: "Where people go" }), el("div", { class: "tags" }, (c.ctas || []).map(t => el("span", { text: t })))),
      el("div", { class: "sec" }, el("span", { class: "label", text: "What we measure" }), el("div", { class: "tags" }, (c.kpis || []).map(t => el("span", { text: t })))),
      el("div", { class: "sec" }, el("span", { class: "label", text: "By platform" }), el("div", { class: "pcounts" }, Object.entries(countBy(c.posts, "platform")).sort((a, b) => b[1] - a[1]).map(([pl, n]) => el("span", { class: "pcount" }, pfBadge(pl), el("b", { text: n }), PLATFORM_SHORT[pl])))))));
  if (c.questions.length) out.push(el("section", { class: "card", style: "border-color:color-mix(in srgb, var(--alert) 40%, var(--line))" }, el("h2", { text: "Open questions for the team" }), el("ul", { class: "bullets" }, c.questions.map(q => el("li", { text: q })))));
  out.push(filterBar());
  const dates = [...new Set(posts.map(p => p.date))];
  out.push(dates.length ? el("div", { class: "stack" }, dates.map(d => el("section", { class: "card", style: "gap:6px" },
    el("div", { class: "spread" }, el("h3", { text: fmtDay(d, { weekday: "long", day: "numeric", month: "short" }) }), d === todayIST() ? el("span", { class: "badge approved", text: "Today" }) : dayTag(d)),
    el("div", { class: "list-rows" }, posts.filter(p => p.date === d).map(lrow))))) : emptyState("No posts match these filters", "Clear the filters to see the whole campaign."));
  return out;
}

// ---------- advocacy ----------
function viewKits() {
  const wait = notReady(); if (wait) return wait;
  const wk = state.kitWeek || thisWeek();
  const nav = el("div", { class: "datenav" }, el("button", { "aria-label": "Previous week", onclick: () => { state.kitWeek = addDays(wk, -7); render(); } }, icon("left")),
    el("strong", { text: `${fmtDay(wk, { day: "numeric", month: "short" })} – ${fmtDay(addDays(wk, 6), { day: "numeric", month: "short" })}` }),
    el("button", { "aria-label": "Next week", onclick: () => { state.kitWeek = addDays(wk, 7); render(); } }, icon("right")), el("button", { onclick: () => { state.kitWeek = null; render(); }, text: "This week" }));
  const kits = postsBetween(wk, addDays(wk, 6), false).filter(p => p.account_type === "person");
  const intro = el("div", { class: "callout", text: "Rewrite each draft in your own words and post it from your own profile. The hub never posts for you. After posting, open the draft and log your numbers so we can see what works." });
  if (!kits.length) return [el("div", { class: "toolbar" }, nav), intro, emptyState("No advocacy drafts this week", "Ask Claude to include the founder and team in the plan, or check another week.")];
  const byPerson = new Map();
  for (const p of kits) { if (!byPerson.has(p.account_name)) byPerson.set(p.account_name, []); byPerson.get(p.account_name).push(p); }
  return [el("div", { class: "toolbar" }, nav), intro, ...[...byPerson].map(([name, ps]) => el("section", { class: "card" },
    el("div", { class: "row" }, acctAva(ps[0]), el("h2", { text: name }), el("span", { class: "small muted", text: plural(ps.length, "draft") })),
    el("div", { class: "g-3 grid" }, ps.map(p => {
      const r = state.results.get(p.id);
      return el("article", { class: "tile", style: "box-shadow:none;background:var(--surface-2)" },
        el("div", { class: "spread" }, el("span", { class: "mono small", text: `${fmtDay(p.date, { weekday: "short", day: "numeric", month: "short" })} · ${p.time}` }), statusBadge(p)),
        el("b", { class: "clamp3", text: p.hook }),
        p.personalise_prompt ? el("p", { class: "small" }, el("b", { text: "Make it yours: " }), p.personalise_prompt) : null,
        r ? el("span", { class: "badge approved", text: `Results logged · ${fmtNum(r.impressions || 0)} impressions` }) : null,
        el("div", { class: "row" }, el("button", { class: "btn sm", onclick: () => openPost(p.id), text: "Open" }), el("button", { class: "btn sm ghost", onclick: () => copy(postText(p)) }, icon("copy"), "Copy text")));
    }))))];
}

// ---------- announcements ----------
function viewNews() {
  const wait = notReady(); if (wait) return wait;
  let form = null;
  if (state.me.canEdit) {
    const t = el("input", { type: "text", placeholder: "Title", "aria-label": "Title" });
    const b = el("textarea", { rows: 4, placeholder: "What the team needs to know", "aria-label": "Message" });
    form = el("section", { class: "card" }, el("h2", { text: "Post an announcement" }), el("form", { class: "edit", onsubmit: async e => {
      e.preventDefault(); if (!t.value.trim()) return;
      const doc = { title: t.value.trim(), body: b.value.trim(), by: state.me.id, at: new Date().toISOString() };
      t.value = ""; b.value = ""; document.activeElement?.blur();
      await guarded(() => db.collection("announcements").add(doc), "Posted to the team");
    } }, t, b, el("div", { class: "row" }, el("button", { class: "btn primary", type: "submit", text: "Post announcement" }))));
  }
  const list = state.news.length ? el("div", { class: "stack" }, state.news.map(n => el("article", { class: "card" },
    el("div", { class: "row" }, personAva(n.by, false), el("div", {}, el("b", { class: "small", text: nameOf(n.by) }), el("div", { class: "xs muted", text: ago(n.at) }))),
    el("h3", { style: "font-size:1.05rem", text: n.title }), n.body ? el("p", { class: "small", style: "white-space:pre-wrap", text: n.body }) : null)))
    : emptyState("No announcements yet", state.me.canEdit ? "Post the first one." : "Editors post updates here.");
  return form ? el("div", { class: "bento" }, el("div", { class: "span-7 stack" }, list), el("div", { class: "span-5 stack" }, form)) : list;
}

// ---------- reports ----------
const changeEl = x => x == null ? null : el("span", { class: `delta ${x >= 0 ? "up" : "down"}`, text: ` ${x >= 0 ? "▲" : "▼"}${Math.abs(x * 100).toFixed(0)}%` });
function reportLabel(r) { return r.kind === "monthly" ? fmtDay(r.start, { month: "long", year: "numeric" }) + " (monthly)" : `Week of ${fmtDay(r.start, { day: "numeric", month: "short", year: "numeric" })}`; }
function bullets(title, items, empty) {
  return el("div", { class: "sec" }, el("div", { class: "label", text: title }), items && items.length ? el("ul", { class: "bullets" }, items.map(t => el("li", { text: t }))) : el("p", { class: "small muted", text: empty }));
}
function reportSection() {
  if (!state.reports.length) return el("section", { class: "card" }, el("h2", { text: "Reports" }),
    emptyState("No reports yet", "Weekly and monthly reports appear here once results are imported. Send Claude this week's Instagram or LinkedIn export, follower counts and enquiries."));
  const r = state.reports.find(x => x.id === state.reportId) || state.reports[0];
  const sel = el("select", { "aria-label": "Report", style: "width:auto", onchange: e => { state.reportId = e.target.value; render(); } },
    state.reports.map(x => { const o = el("option", { value: x.id, text: reportLabel(x) }); if (x.id === r.id) o.selected = true; return o; }));
  const rows = r.rows || [];
  const tot = { posts: rows.reduce((a, k) => a + k.posts, 0), exp: rows.reduce((a, k) => a + (k.exposure || 0), 0), enq: Object.values(r.enquiries || {}).reduce((a, n) => a + n, 0) };
  const table = el("div", { class: "tablewrap" }, el("table", {},
    el("thead", {}, el("tr", {}, ["Account", "Platform", "Posts", "Reach / impr.", "Engagement / reach", "Shares / reach", "Saves / reach", "Non-followers", "Follower growth"].map((h, i) => el("th", { scope: "col", class: i > 1 ? "n" : null, text: h })))),
    el("tbody", {}, rows.map(k => el("tr", {},
      el("td", {}, el("span", { class: "row", style: "gap:6px;flex-wrap:nowrap" }, ava(k.account_name, acctColor(k.account, KNOWN_ACCOUNTS.includes(k.account) ? "company" : "person"), true), k.account_name)),
      el("td", {}, el("span", { class: "row", style: "gap:6px;flex-wrap:nowrap" }, pfBadge(k.platform), PLATFORM_SHORT[k.platform] || k.platform)), el("td", { class: "n", text: k.posts }),
      el("td", { class: "n" }, `${fmtNum(k.exposure)}${k.exposure_label === "impressions" ? " impr." : ""}`, changeEl((k.change || {}).exposure)),
      el("td", { class: "n" }, fmtPct(k.engagement_rate), changeEl((k.change || {}).engagement_rate)),
      el("td", { class: "n", text: fmtPct(k.share_rate) }), el("td", { class: "n", text: fmtPct(k.save_rate) }), el("td", { class: "n", text: fmtPct(k.non_follower_share) }),
      el("td", { class: "n", text: k.follower_growth == null ? "–" : signed(k.follower_growth) }))))));
  return el("section", { class: "card" },
    el("div", { class: "spread" }, el("h2", { text: r.kind === "monthly" ? "Monthly growth report" : "Weekly performance report" }), el("div", { class: "row" }, sel,
      r.markdown ? el("button", { class: "btn sm", onclick: () => saveFile(`hifuel-report-${r.start}.md`, r.markdown, "text/markdown") }, icon("download"), "Download") : null)),
    el("div", { class: "g-3 grid" }, [["Posts measured", tot.posts], ["Total reach / impressions", fmtNum(tot.exp)], ["Enquiries from social", tot.enq]].map(([k, v]) =>
      el("div", { class: "tile", style: "box-shadow:none;background:var(--surface-2);border-color:transparent" }, el("span", { class: "kk", text: k }), el("span", { class: "kv", style: "font-size:1.6rem", text: v })))),
    (r.priorities || []).length ? el("div", { class: "sec" }, el("div", { class: "label", text: "Next month's three priorities" }), el("ol", { class: "bullets" }, r.priorities.map(t => el("li", { text: t })))) : null,
    el("div", { class: "g-2 grid" }, bullets("What worked", r.worked, "Not enough data for a clear conclusion yet."), bullets("What didn't", r.didnt, "Nothing clearly underperformed.")),
    table,
    (r.top_posts || []).length ? el("div", { class: "sec" }, el("div", { class: "label", text: "Top posts" }), el("ul", { class: "bullets" },
      r.top_posts.map(t => el("li", {}, el("b", { text: `${fmtPct(t.engagement_rate)} ` }), `${t.account_name} · ${PLATFORMS[t.platform] || t.platform} · ${FORMAT_LABEL[t.format] || t.format}: ${t.text}`)))) : null,
    bullets("Data notes", r.notes, "None."),
    el("p", { class: "hint", text: "Engagement = likes + comments + shares + saves. Comparisons need at least 3 posts on each side." }));
}
function experimentSection() {
  const head = el("h2", { text: "Experiments" });
  if (!state.experiments.length) return el("section", { class: "card" }, head, el("p", { class: "small muted", text: "No experiments yet. Ask Claude to start one: change one thing (format, time of day, theme) for 2–4 weeks and compare." }));
  const verdict = { better: ["approved", "Better"], worse: ["blocked", "Worse"], no_difference: ["draft", "No clear difference"], pending: ["needs_changes", "Collecting data"] };
  const VAR = { format: "Format", hour_band: "Time of day", theme: "Theme", pillar: "Pillar", slot_source: "Time source" };
  return el("section", { class: "card" }, head, el("div", { class: "stack" }, state.experiments.map(e => {
    const v = verdict[e.verdict] || (e.status === "running" ? verdict.pending : ["draft", e.status]);
    return el("div", { class: "tile", style: "box-shadow:none;background:var(--surface-2);border-color:transparent" },
      el("div", { class: "spread" }, el("b", { text: e.name }), el("span", { class: `badge ${v[0]}`, text: e.status === "running" ? "Running" : v[1] })),
      el("div", { class: "xs muted", text: `${accountName(e.account)} · ${VAR[e.variable] || e.variable}: ${String(e.value).replace(/_/g, " ")} · ${fmtDay(e.start, { day: "numeric", month: "short" })} – ${fmtDay(e.end, { day: "numeric", month: "short" })}` }),
      el("p", { class: "small", text: `Hypothesis: ${e.hypothesis}` }), e.result ? el("p", { class: "small", text: e.result }) : null);
  })));
}
function mixSection() {
  const wk = thisWeek();
  const ps = postsBetween(wk, addDays(wk, 6), false).filter(p => p.status !== "rejected");
  const card = el("section", { class: "card" }, el("div", { class: "spread" }, el("h2", { text: "This week's content mix" }), el("span", { class: "xs muted", text: plural(ps.length, "post") })));
  if (!ps.length) { card.append(el("p", { class: "small muted", text: "The mix appears once a week is planned." })); return card; }
  const keys = Object.keys(THEMES);
  card.append(el("div", { class: "legend" }, keys.map((t, i) => el("span", {}, el("i", { style: `background:${THEME_COLORS[i]}` }), THEMES[t]))),
    el("div", { class: "stack", style: "gap:10px" }, [...new Map(ps.map(p => [p.account, p.account_name]))].map(([id, name]) => {
      const mine = ps.filter(p => p.account === id);
      return el("div", { class: "mixrow" }, el("span", { class: "ellipsis", text: name }),
        el("div", { class: "bar", style: "height:12px", role: "img", "aria-label": `${name}: ` + keys.map(t => `${mine.filter(p => p.theme === t).length} ${THEMES[t]}`).join(", ") },
          keys.map((t, i) => { const n = mine.filter(p => p.theme === t).length; return n ? el("span", { style: `width:${(n / mine.length) * 100}%;background:${THEME_COLORS[i]}` }) : null; })),
        el("span", { class: "mono", style: "text-align:right", text: mine.length }));
    })));
  return card;
}
function viewReports() {
  const wait = notReady(); if (wait) return wait;
  return [reportSection(), el("div", { class: "g-2 grid" }, experimentSection(), mixSection())];
}

// ---------- start-up ----------
{
  const [v, id] = (location.hash || "").slice(1).split("/");
  if (VIEWS.some(x => x.id === v)) state.view = v;
  if (v === "review" && id) state.review.id = decodeURIComponent(id);
  state.cal.anchor = todayIST();
  render();
}
window.addEventListener("hashchange", () => {
  const [v, id] = (location.hash || "").slice(1).split("/");
  if (!VIEWS.some(x => x.id === v)) return;
  const rid = v === "review" && id ? decodeURIComponent(id) : null;
  if (v === state.view && rid === (v === "review" ? state.review.id : null)) return;
  while (modals.length) modals.pop();
  renderModals(true);
  go(v, v === "review" ? { id: rid } : {});
});
function pickAnchor() {
  const dates = allPosts().map(p => p.date);
  const cur = thisWeek();
  if (!dates.length || dates.some(d => d >= cur && d <= addDays(cur, 6))) return todayIST();
  return dates.find(d => d >= cur) || dates[dates.length - 1];
}
async function start() {
  const claude = window.claude;
  if (!claude || !claude.use) { state.unavailable = true; state.conn = "offline"; render(); return; }
  const use = n => claude.use(n).catch(() => null);
  [db, user, downloads, assets] = await Promise.all([use("db"), use("user"), use("downloads"), use("assets")]);
  if (!db) { state.unavailable = true; state.conn = "offline"; render(); return; }
  if (user) {
    try {
      const me = await user.me();
      Object.assign(state.me, { id: me.id, name: me.name, avatar: me.avatarUrl, canEdit: !!me.canEdit });
      state.me.canWrite = await user.can("data.write");
      if (me.id && me.name) state.names[me.id] = me.name;
    } catch {}
  }
  const fail = () => { state.conn = "offline"; renderSync(); };
  const live = () => { if (navigator.onLine !== false) state.conn = "live"; };
  let first = true;
  db.collection("posts").onSnapshot(snap => {
    state.posts = new Map(snap.docs.map(d => [d.id, { ...d.data(), id: d.id }]));
    state.loaded = true; live();
    if (first) { first = false; state.cal.anchor = pickAnchor(); }
    render();
    resolveNames([...state.posts.values()].flatMap(p => [p.review && p.review.by, p.created_by, ...(p.edits || []).map(e => e.by)]));
  }, () => { if (!state.loaded) state.unavailable = true; fail(); render(); });
  const sub = (name, fn, q = c => c) => q(db.collection(name)).onSnapshot(snap => { fn(snap.docs.map(d => ({ ...d.data(), id: d.id }))); live(); render(); }, () => {});
  sub("plans", docs => { state.plans = docs; });
  sub("ideas", docs => { state.ideas = docs; resolveNames(docs.map(i => i.by)); }, c => c.orderBy("at", "desc").limit(300));
  sub("announcements", docs => { state.news = docs; resolveNames(docs.map(n => n.by)); }, c => c.orderBy("at", "desc").limit(50));
  sub("reports", docs => { state.reports = docs; }, c => c.orderBy("end", "desc").limit(30));
  sub("experiments", docs => { state.experiments = docs; }, c => c.orderBy("start", "desc").limit(50));
  sub("results", docs => { state.results = new Map(docs.map(d => [d.id, d])); });
  sub("comments", docs => { state.comments = docs; resolveNames(docs.map(c => c.by)); }, c => c.orderBy("at", "desc").limit(500));
  sub("meta", docs => { for (const d of docs) state.meta[d.id] = d; });
  sub("analytics", docs => { state.analytics = docs.find(d => d.id === "summary") || null; });
}
start().catch(() => { state.unavailable = true; state.conn = "offline"; render(); });
