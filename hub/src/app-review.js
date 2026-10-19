// Review: split screen (queue + full preview + checks + comments), post detail modal, request-changes checklist.

// ---------- platform previews ----------
function clampBlock(nodes) {
  const box = el("div", { class: "pv-text clamp" }, nodes);
  const more = el("button", { class: "pv-more", text: "…see more", onclick: () => { box.classList.remove("clamp"); more.remove(); } });
  return [box, more];
}
function media(p, kind) {
  const [c1, c2] = brandColors(p);
  const m = el("div", { class: `pv-media ${kind}`, style: `--c1:${c1};--c2:${c2}` }, el("p", { text: mediaText(p) }));
  const b = p.design_brief || {};
  if (p.format === "reel") m.append(el("span", { class: "tag", text: `REEL${b.reel && b.reel.duration_seconds ? " · " + b.reel.duration_seconds + "s" : ""}` }), el("span", { class: "play" }, icon("play")));
  if (p.format === "carousel" || p.format === "document") { const k = Math.min((b.slides || []).length || 1, 8); m.append(el("span", { class: "tag", text: `1 / ${k}` }), el("span", { class: "dots" }, [...Array(k)].map(() => el("i")))); }
  return m;
}
function preview(p) {
  if (isShell(p)) return el("div", { class: "pv", style: "padding:22px;display:grid;gap:10px;text-align:center;justify-items:center" }, icon("sparkle"),
    el("b", { text: "Brief · not written yet" }), el("p", { class: "small muted", text: "Claude writes the post, design brief and checks at the next sync. The preview appears then." }));
  const [c1, c2] = brandColors(p);
  const head = sub => el("div", { class: "pv-head" }, acctAva(p), el("div", { style: "min-width:0" }, el("b", { text: p.account_name }), el("small", { text: sub })), pfBadge(p.platform));
  const text = publishText(p);
  const parts = p.thread_parts || [];
  const n = parts.length ? Math.max(...parts.map(t => t.length)) : text.length;
  const lim = LIMITS[p.platform] || 2200;
  const counter = el("span", { class: `chars${n > lim ? " over" : ""}`, text: `${n.toLocaleString("en-IN")} / ${lim.toLocaleString("en-IN")}${parts.length ? " (longest part)" : ""}` });
  const tags = (p.hashtags || []).join(" ");
  const bodyText = () => [[p.hook, p.caption, p.cta].filter(Boolean).join("\n\n"), tags ? "\n\n" : "", tags ? el("span", { class: "pv-tags", text: tags }) : null];
  let body;
  if (p.platform === "instagram" && p.format === "story") {
    const slides = (p.design_brief || {}).slides || [];
    const sticker = slides.find(s => /sticker/i.test(s.visual || ""));
    body = el("div", { class: "pv-story", style: `--c1:${c1};--c2:${c2}` },
      el("div", { class: "bars" }, [...Array(Math.max(1, slides.length))].map(() => el("i"))),
      el("div", { class: "whos" }, acctAva(p, true), p.account_name),
      el("p", { text: slides[0] ? slides[0].text : p.hook }), sticker ? el("div", { class: "sticker", text: sticker.visual }) : null);
  } else if (p.platform === "instagram") {
    const handle = p.account_name.toLowerCase().replace(/\(.*?\)/g, "").replace(/[^a-z0-9.]+/g, "");
    body = el("div", { class: "pv" }, head(FORMAT_LABEL[p.format] || p.format), media(p, p.format === "reel" ? "reel" : ""),
      el("div", { class: "pv-icons" }, icon("heart"), icon("comment"), icon("send"), el("span", { class: "spacer" }), icon("save")),
      clampBlock([el("b", { text: handle + " " }), bodyText()]));
  } else if (p.platform === "linkedin" || p.platform === "facebook") {
    const showMedia = ["single_image", "document", "carousel", "reel"].includes(p.format);
    const acts = p.platform === "linkedin" ? [["like", "Like"], ["comment", "Comment"], ["repost", "Repost"], ["send", "Send"]] : [["like", "Like"], ["comment", "Comment"], ["send", "Share"]];
    body = el("div", { class: "pv" }, head(`${p.account_type === "person" ? "Personal profile" : "Page"} · ${fmtDay(p.date, { day: "numeric", month: "short" })}`),
      clampBlock(bodyText()), showMedia ? media(p, "doc") : null, el("div", { class: "pv-actions" }, acts.map(([i, l]) => el("span", {}, icon(i), l))));
  } else if (p.platform === "x") {
    const list = parts.length ? parts : [text];
    body = el("div", { class: "pv" }, list.map(t => el("div", { class: "pv-x" }, acctAva(p),
      el("div", { style: "min-width:0;display:grid;gap:4px" }, el("div", { class: "xs" }, el("b", { text: p.account_name }), el("span", { class: "muted", text: ` · ${fmtDay(p.date, { day: "numeric", month: "short" })}` })),
        el("div", { style: "white-space:pre-wrap;overflow-wrap:anywhere", text: t }), el("span", { class: `chars${t.length > 280 ? " over" : ""}`, text: `${t.length}/280` })))));
  } else {
    body = el("div", { class: "pv" }, head("WhatsApp Channel"), el("div", { class: "pv-wa" }, el("div", { class: "bubble" }, el("span", { text }), el("small", { class: "muted", text: p.time || "" }))));
  }
  return el("div", { class: "frame", style: "display:grid;gap:8px;min-width:0" }, body,
    el("div", { class: "spread" }, el("span", { class: "xs muted", text: p.format === "story" ? `Story · ${((p.design_brief || {}).slides || []).length || 1} frames` : "Preview, not exact" }), counter));
}

// ---------- detail blocks ----------
function issueList(p) {
  const is = (p.issues || []).filter(i => i.check !== "not_written");
  if (isShell(p)) return el("div", { class: "callout", text: "Claude checks the content rules when it writes this brief." });
  if (!is.length) return el("div", { class: "okline" }, icon("check"), "Passes every content rule");
  return el("ul", { class: "issues" }, is.map(i => el("li", { class: `issue ${i.severity}` },
    el("span", {}, el("b", { text: i.severity === "block" ? "Must fix" : "Check" }), i.rule ? ` · rule ${i.rule}` : "", ` · ${i.message}`),
    i.excerpt ? el("q", { text: i.excerpt }) : null)));
}
function designBrief(p) {
  const b = p.design_brief || {};
  const reel = b.reel || {};
  const parts = [];
  if (b.format_notes) parts.push(el("p", { text: b.format_notes }));
  if ((b.slides || []).length) parts.push(el("div", {}, el("div", { class: "label", text: p.format === "story" ? "Frames" : "Slides" }), el("ol", {}, b.slides.map(s => el("li", {}, s.text, el("span", { class: "muted", text: ` · ${s.visual}` }))))));
  if ((reel.shots || []).length) parts.push(el("div", { class: "sec" }, el("div", { class: "label", text: `Reel script · ${reel.duration_seconds}s` }), el("p", {}, el("b", { text: "Opening: " }), reel.opening_hook),
    el("div", { class: "tablewrap" }, el("table", {}, el("thead", {}, el("tr", {}, ["Time", "Shot", "On screen", "Voiceover"].map(h => el("th", { scope: "col", text: h })))),
      el("tbody", {}, reel.shots.map(s => el("tr", {}, el("td", { class: "mono", text: `${s.seconds}s` }), el("td", { style: "white-space:normal;min-width:150px", text: s.shot }), el("td", { style: "white-space:normal;min-width:140px", text: s.on_screen_text }), el("td", { style: "white-space:normal;min-width:140px", text: s.voiceover || "–" }))))))));
  if (b.layout_notes) parts.push(el("p", {}, el("b", { text: "Layout: " }), b.layout_notes));
  if ((b.colours || []).length) parts.push(el("div", { class: "swatches" }, b.colours.map(c => el("span", { class: "swatch" }, el("i", { style: `background:${/^#[0-9a-f]{3,8}$/i.test(c) ? c : "transparent"}` }), c))));
  if (b.image_prompt) parts.push(el("p", {}, el("b", { text: "AI image prompt: " }), b.image_prompt));
  if (p.alt_text) parts.push(el("p", {}, el("b", { text: "Alt text: " }), p.alt_text));
  if (!parts.length) return null;
  return el("details", { class: "fold" }, el("summary", { text: "Design brief" }), el("div", { class: "brief" }, parts));
}
function notesBlock(p) {
  const needs = p.internal_notes && /CONFIRM/.test(p.internal_notes);
  const items = [];
  if (p.internal_notes) items.push(el("p", {}, el("b", { text: "Notes for reviewer: " }), p.internal_notes));
  if ((p.claims_notes || []).length) items.push(el("div", {}, el("b", { text: "Sources" }), el("ul", {}, p.claims_notes.map(c => el("li", { text: `${c.claim}: ${c.source} (${c.year})` })))));
  items.push(el("p", {}, el("b", { text: "Why this time: " }), p.slot_reason || "not set"));
  return el("details", { class: "fold", open: needs ? true : null }, el("summary", { text: needs ? "Notes, sources and timing · needs confirmation" : "Notes, sources and timing" }), el("div", { class: "brief" }, items));
}
function editBlock(p) {
  if (!state.me.canEdit || isShell(p) || ["posted", "rejected"].includes(p.status)) return null;
  const inputs = {};
  const box = el("div", { class: "edit", style: "margin-top:10px" });
  for (const [f, label, rows] of [["hook", "Hook (first line)", 2], ["caption", "Caption", 7], ["cta", "Call to action", 2]]) {
    const t = el("textarea", { id: `${p.id}-${f}`, rows }); t.value = p[f] || ""; inputs[f] = t; box.append(el("label", { for: t.id }, label, t));
  }
  const tags = el("input", { type: "text", id: `${p.id}-hashtags` }); tags.value = (p.hashtags || []).join(" "); inputs.hashtags = tags;
  box.append(el("label", { for: tags.id }, "Hashtags (space-separated)", tags), el("div", { class: "row" }, el("button", { class: "btn", onclick: () => saveEdits(p, inputs), text: "Save text" }), el("span", { class: "hint", text: "Claude re-checks edited text at the next sync." })));
  return el("details", { class: "fold" }, el("summary", { text: "Edit text" }), box);
}
function saveEdits(p, inputs) {
  const next = { hook: inputs.hook.value.trim(), caption: inputs.caption.value.trim(), cta: inputs.cta.value.trim(), hashtags: inputs.hashtags.value.split(/\s+/).filter(Boolean) };
  const at = new Date().toISOString();
  const changes = Object.entries(next).filter(([k, v]) => JSON.stringify(v) !== JSON.stringify(p[k] || (k === "hashtags" ? [] : "")))
    .map(([field, v]) => ({ field, old: p[field] ?? null, new: v, by: state.me.id, at }));
  if (!changes.length) { toast("No changes to save"); return; }
  document.activeElement?.blur();
  writePost(p, { ...next, edits: [...(p.edits || []), ...changes], edited_since_check: true }, "Saved. Claude re-checks it at the next sync");
}
function consentBlock(p) {
  if (!p.shows_children) return null;
  const cb = el("input", { type: "checkbox", id: `${p.id}-consent`, disabled: !state.me.canEdit }); cb.checked = !!p.consent_confirmed;
  cb.addEventListener("change", () => writePost(p, { consent_confirmed: cb.checked, edited_since_check: true }, cb.checked ? "Consent recorded" : "Consent removed"));
  return el("label", { class: "check", for: cb.id }, cb, el("span", {}, "Verifiable parental consent is on file for the children shown"));
}
function resultForm(p) {
  if (p.account_type !== "person" || !["approved", "scheduled", "posted"].includes(p.status) || !(state.me.canWrite || state.me.canEdit)) return null;
  const r = state.results.get(p.id) || {};
  const f = (id, label, type = "number", value = "") => { const i = el("input", { type, id: `${p.id}-r-${id}`, min: type === "number" ? "0" : null }); i.value = value ?? ""; return [i, el("label", { class: "field", for: i.id }, label, i)]; };
  const [when, whenL] = f("when", "Posted at (IST)", "datetime-local", r.posted_at || `${p.date}T${p.time || "10:00"}`);
  const [imp, impL] = f("imp", "Impressions", "number", r.impressions);
  const [rea, reaL] = f("rea", "Reactions", "number", r.reactions);
  const [com, comL] = f("com", "Comments", "number", r.comments);
  const [rep, repL] = f("rep", "Reposts", "number", r.reposts);
  const [lnk, lnkL] = f("lnk", "Link to your post", "url", r.link);
  const num = i => i.value === "" ? null : Math.max(0, Number(i.value));
  return el("details", { class: "fold" }, el("summary", { text: r.at ? `Results logged · ${fmtNum(r.impressions || 0)} impressions · update` : "Posted it? Log your results" }),
    el("form", { class: "edit", style: "margin-top:10px", onsubmit: e => {
      e.preventDefault(); document.activeElement?.blur();
      guarded(() => db.doc(`results/${p.id}`).set({ post_id: p.id, posted_at: when.value, impressions: num(imp), reactions: num(rea), comments: num(com), reposts: num(rep), link: lnk.value.trim(), by: state.me.id, at: new Date().toISOString() }), "Results saved. Thank you!");
    } }, el("div", { class: "grid2" }, whenL, impL, reaL, comL, repL, lnkL),
      el("p", { class: "hint", text: "Check the numbers about 3 days after posting, from the post's analytics on LinkedIn." }),
      el("div", { class: "row" }, el("button", { class: "btn primary", type: "submit", text: "Save results" }))));
}

// ---------- comments thread ----------
function threadFor(p) {
  const items = [];
  for (const c of state.comments.filter(c => c.post_id === p.id)) items.push({ at: c.at, by: c.by, kind: c.kind || "comment", text: c.text, checklist: c.checklist || [] });
  for (const e of p.edits || []) items.push({ at: e.at, by: e.by, kind: "sys", text: e.field === "date" || e.field === "time" ? `moved it (${e.field} ${e.old || "–"} → ${e.new})` : `edited the ${e.field === "cta" ? "call to action" : e.field}` });
  if (p.review && p.review.at && p.review.by && !state.comments.some(c => c.post_id === p.id && c.kind === "change_request" && c.at === p.review.at))
    items.push({ at: p.review.at, by: p.review.by, kind: "sys", text: `marked it ${(STATUS_LABEL[p.status] || p.status).toLowerCase()}${p.review.comment ? `: “${p.review.comment}”` : ""}` });
  if (p.created_by && p.created_at) items.push({ at: p.created_at, by: p.created_by, kind: "sys", text: "created this brief" });
  return items.filter(x => x.at).sort((a, b) => a.at.localeCompare(b.at));
}
function commentsBlock(p) {
  const items = threadFor(p);
  const box = el("section", { class: "sec" }, el("div", { class: "spread" }, el("h3", { text: "Comments and history" }), el("span", { class: "xs muted", text: items.length ? plural(items.filter(i => i.kind !== "sys").length, "comment") : "" })));
  box.append(items.length ? el("div", { class: "thread" }, items.map(it => el("div", { class: `msg${it.kind === "sys" ? " sys" : it.kind === "change_request" ? " change" : ""}` }, personAva(it.by),
    el("div", { style: "min-width:0" }, it.kind === "sys" ? null : el("div", { class: "meta" }, el("b", { style: "color:var(--fg)", text: nameOf(it.by) }), ` · ${ago(it.at)}${it.kind === "change_request" ? " · requested changes" : ""}`),
      el("div", { class: "bubble" }, it.kind === "sys" ? [el("b", { text: nameOf(it.by) }), ` ${it.text} · ${ago(it.at)}`] : it.text,
        (it.checklist || []).length ? el("ul", {}, it.checklist.map(c => el("li", { text: c }))) : null)))))
    : el("p", { class: "small muted", text: "No comments yet. Questions and notes for the team go here." }));
  if (state.me.canWrite || state.me.canEdit) {
    const ta = el("textarea", { rows: 2, placeholder: "Write a comment for the team", "aria-label": "Comment" });
    const send = el("button", { class: "btn", type: "submit" }, icon("send"), "Send");
    box.append(el("form", { class: "composer", onsubmit: async e => { e.preventDefault(); const t = ta.value.trim(); if (!t) return; ta.value = ""; ta.blur(); await addComment(p, t); } }, ta, send));
    ta.addEventListener("keydown", e => { if (e.key === "Enter" && (e.metaKey || e.ctrlKey)) { e.preventDefault(); send.click(); } });
  }
  return box;
}

// ---------- detail panel + action bar ----------
function panelHead(p) {
  const camp = p.campaign ? campaigns().find(c => c.id === p.campaign) : null;
  return el("div", { class: "panel-head" },
    el("div", { class: "row" }, acctAva(p), el("b", { text: p.account_name }), statusBadge(p), camp ? el("span", { class: "badge campaign", text: camp.name }) : null, p.sample ? el("span", { class: "badge draft", text: "Sample" }) : null),
    el("h2", { text: p.hook || "Untitled brief" }),
    el("div", { class: "metaline" }, el("span", {}, icon("clock"), el("span", { class: "mono", text: `${fmtDay(p.date, { weekday: "short", day: "numeric", month: "short" })} · ${p.time || "--:--"} IST` }),
      canMove(p) ? el("button", { class: "linkbtn", onclick: () => openMoveModal(p), text: "Move" }) : null),
      el("span", {}, pfBadge(p.platform), `${PLATFORMS[p.platform]} · ${FORMAT_LABEL[p.format] || p.format}`), el("span", { text: THEMES[p.theme] || p.theme }), p.pillar ? el("span", { text: p.pillar }) : null),
    isDelayed(p) ? el("div", { class: "callout warn", text: `This was due ${fmtDay(p.date, { day: "numeric", month: "short" })} at ${p.time} and isn't marked published. Post it, move it, or mark it published if it already went out.` }) : null);
}
function detailPanel(p) {
  return el("div", { class: "panel" }, panelHead(p),
    p.personalise_prompt ? el("div", { class: "callout good" }, el("b", { text: "Make it yours: " }), p.personalise_prompt) : null,
    isShell(p) && p.internal_notes ? el("div", { class: "callout" }, el("b", { text: "Brief notes: " }), p.internal_notes) : null,
    el("section", { class: "sec" }, el("h3", { text: "Content checks" }), issueList(p), p.edited_since_check ? el("p", { class: "hint", text: "Edited since the last check. Claude re-checks it at the next sync." }) : null),
    consentBlock(p), editBlock(p), designBrief(p), isShell(p) ? null : notesBlock(p), resultForm(p),
    commentsBlock(p), actionBar(p));
}
function actionBar(p) {
  const bar = el("div", { class: "actionbar" });
  const copyBtn = !isShell(p) ? el("button", { class: "iconbtn", "data-tip": "Copy post text", "aria-label": "Copy post text", onclick: () => copy(postText(p)) }, icon("copy")) : null;
  if (!state.me.canEdit) { bar.append(el("span", { class: "small muted grow", text: "Editors (Aryan, the manager, the founder) approve posts. You can comment above." }), copyBtn); return bar; }
  const blocked = isBlocked(p);
  if (isShell(p)) {
    bar.append(el("span", { class: "small muted grow", text: "Claude writes this brief at the next sync." }), el("button", { class: "btn danger", onclick: () => setStatus(p, "rejected", "Brief dropped"), text: "Drop brief" }));
    return bar;
  }
  if (["draft", "needs_changes", "rejected"].includes(p.status)) {
    bar.append(el("button", { class: "btn primary", disabled: blocked, title: blocked ? "Fix the Must-fix items first" : null, onclick: () => approve(p) }, icon("check"), "Approve to queue"),
      el("button", { class: "btn", onclick: () => openChangesModal(p) }, "Request changes"),
      el("span", { class: "grow" }), copyBtn,
      el("button", { class: "iconbtn", "data-tip": "More", "aria-label": "More actions", onclick: e => openMenu(e.currentTarget, [p.status !== "rejected" ? { label: "Reject", sub: "Drop this post from the plan", icon: "x", fn: () => setStatus(p, "rejected") } : null, canMove(p) ? { label: "Move", icon: "move", fn: () => openMoveModal(p) } : null]) }, icon("more")));
    if (blocked) bar.append(el("p", { class: "hint", style: "flex-basis:100%", text: "Blocked: fix the “Must fix” items (edit the text above), then Claude re-checks at the next sync." }));
  } else if (p.status === "approved") {
    bar.append(el("button", { class: "btn primary", onclick: () => setStatus(p, "scheduled") }, icon("clock"), "Mark scheduled"), el("button", { class: "btn", onclick: () => openChangesModal(p), text: "Send back" }), el("span", { class: "grow" }), copyBtn);
  } else if (p.status === "scheduled") {
    bar.append(el("button", { class: "btn primary", onclick: () => setStatus(p, "posted") }, icon("check"), "Mark published"), el("button", { class: "btn", onclick: () => setStatus(p, "approved"), text: "Unschedule" }), el("span", { class: "grow" }), copyBtn);
  } else {
    bar.append(el("span", { class: "small muted grow", text: p.status === "posted" ? "Published. Log results from Analytics or Advocacy." : "Rejected." }), copyBtn);
  }
  return bar;
}
async function approve(p) {
  if (isBlocked(p)) { toast("Fix the Must-fix items first.", { warn: true }); return; }
  const next = state.view === "review" ? nextInQueue(p.id) : null;
  const ok = await setStatus(p, "approved");
  if (ok && next && state.view === "review") { state.review.id = next; render(); }
}
function openChangesModal(p) {
  const auto = (p.issues || []).filter(i => i.check !== "not_written" && i.severity === "block").map(i => i.message);
  const items = [...new Set([...auto, ...CHANGE_REASONS])];
  const boxes = items.map((t, i) => { const cb = el("input", { type: "checkbox", id: `chg-${i}` }); cb.checked = auto.includes(t); return [cb, t]; });
  const extra = el("input", { type: "text", placeholder: "Add another item", "aria-label": "Add another checklist item" });
  const list = el("div", { class: "stack", style: "gap:6px" }, boxes.map(([cb, t]) => el("label", { class: `check${auto.includes(t) ? " auto" : ""}`, for: cb.id }, cb, el("span", {}, t, auto.includes(t) ? el("span", { class: "xs muted", text: " · from content checks" }) : null))));
  const note = el("textarea", { rows: 3, placeholder: "What should change? (optional)", "aria-label": "Note" });
  const submit = async () => {
    const checklist = boxes.filter(([cb]) => cb.checked).map(([, t]) => t);
    if (extra.value.trim()) checklist.push(extra.value.trim());
    const comment = note.value.trim();
    if (!checklist.length && !comment) { toast("Tick at least one item or add a note.", { warn: true }); return; }
    closeModal();
    const at = new Date().toISOString();
    const next = state.view === "review" ? nextInQueue(p.id) : null;
    const ok = await guarded(async () => {
      await db.doc(`posts/${p.id}`).update({ status: "needs_changes", review: { by: state.me.id, at, comment, checklist }, updated_at: at });
      await db.collection("comments").add({ post_id: p.id, text: comment || "Changes requested", kind: "change_request", checklist, by: state.me.id, at });
    }, "Changes requested. Claude rewrites it at the next sync");
    if (ok && next && state.view === "review" && state.review.tab === "todo") { state.review.id = next; render(); }
  };
  openModal(() => [el("h2", { text: "Request changes" }), el("p", { class: "small muted", text: p.hook }),
    el("div", { class: "label", text: "Checklist" }), list, extra, note,
    el("p", { class: "hint", text: "Claude works through this checklist when it rewrites the post, and the team sees it in the comments." }),
    el("div", { class: "foot" }, el("button", { class: "btn", onclick: closeModal, text: "Cancel" }), el("button", { class: "btn primary", onclick: submit, text: "Send back with checklist" }))], { label: "Request changes" });
}
function postModal(id) {
  const p = state.posts.get(id);
  if (!p) return [el("p", { text: "This post was removed." }), el("div", { class: "foot" }, el("button", { class: "btn", onclick: closeModal, text: "Close" }))];
  return [el("div", { class: "spread" }, el("span", { class: "label", text: "Post" }), el("div", { class: "row" },
      isPending(p) && state.me.canEdit ? el("button", { class: "btn sm", onclick: () => { closeModal(); go("review", { id: p.id }); } }, icon("review"), "Open in Review") : null,
      el("button", { class: "iconbtn", "aria-label": "Close", "data-tip": "Close", onclick: closeModal }, icon("x")))),
    el("div", { class: "detail" }, el("div", { class: "stage" }, preview(p)), detailPanel(p))];
}

// ---------- review screen ----------
const REVIEW_TABS = [["todo", "To review"], ["blocked", "Blocked"], ["approved", "Approved"], ["all", "All upcoming"]];
function reviewQueue() {
  const from = addDays(todayIST(), -7);
  const base = allPosts().filter(p => matches(p) && !isShell(p));
  const t = state.review.tab;
  let q = t === "todo" ? base.filter(p => isPending(p) && p.date >= from)
    : t === "blocked" ? base.filter(p => isBlocked(p) && p.date >= from)
      : t === "approved" ? base.filter(p => ["approved", "scheduled"].includes(p.status) && p.date >= from)
        : base.filter(p => p.date >= from && p.status !== "rejected");
  if (t === "todo") q.sort((a, b) => (isBlocked(a) - isBlocked(b)) || (a.date + a.time).localeCompare(b.date + b.time));
  return q;
}
function nextInQueue(id) { const q = reviewQueue(); const i = q.findIndex(p => p.id === id); const rest = q.filter((p, j) => j !== i && (state.review.tab !== "todo" || isPending(p))); return (rest[i] || rest[i - 1] || rest[0] || {}).id || null; }
function viewReview() {
  const wait = notReady(); if (wait) return wait;
  const q = reviewQueue();
  const counts = Object.fromEntries(REVIEW_TABS.map(([t]) => { const keep = state.review.tab; state.review.tab = t; const n = reviewQueue().length; state.review.tab = keep; return [t, n]; }));
  const tabs = el("div", { class: "seg", role: "tablist", "aria-label": "Queue" }, REVIEW_TABS.map(([t, l]) => el("button", { role: "tab", "aria-selected": String(state.review.tab === t), "aria-pressed": String(state.review.tab === t), onclick: () => { state.review.tab = t; state.review.id = null; render(); } }, l, el("span", { class: "xs muted num", text: counts[t] }))));
  const bar = filterBar({ lead: tabs, noStatus: true });
  let open = state.review.id && state.posts.get(state.review.id);
  const wide = window.matchMedia("(min-width: 901px)").matches;
  if (!open && wide && q.length) { open = q[0]; state.review.id = open.id; }
  if (!q.length && !open) return [bar, emptyState(state.review.tab === "todo" ? "All caught up" : "Nothing here", state.review.tab === "todo" ? "No posts are waiting for review. Approved posts are on the calendar." : matchesActive() ? "Nothing matches these filters." : "", el("button", { class: "btn", onclick: () => go("calendar"), text: "Open calendar" }))];
  const queue = el("div", { class: "queue", role: "listbox", "aria-label": "Posts in the queue" }, q.length ? q.map(p => el("button", { class: "qitem", role: "option", "aria-selected": String(open && p.id === open.id), "aria-current": String(!!open && p.id === open.id), onclick: () => { state.review.id = p.id; go("review", { keepScroll: !wide }); } },
    acctAva(p), el("span", { style: "min-width:0;display:grid;gap:3px" }, el("span", { class: "t clamp2", text: p.hook }),
      el("span", { class: "row", style: "gap:6px" }, pfBadge(p.platform), el("span", { class: "s mono", text: `${fmtDay(p.date, { day: "numeric", month: "short" })} · ${p.time || "--:--"}` }), statusBadge(p)))))
    : el("p", { class: "small muted", style: "padding:10px", text: "Queue is empty." }));
  const detail = open ? el("div", { class: "detail-wrap stack" },
    el("button", { class: "btn ghost sm backbtn", style: "justify-self:start", onclick: () => { state.review.id = null; go("review"); } }, icon("left"), "Back to queue"),
    el("div", { class: "detail" }, el("div", { class: "stage" }, preview(open)), detailPanel(open)),
    wide && state.me.canEdit ? el("p", { class: "hint", style: "text-align:right" }, "Shortcuts: ", el("span", { class: "kbd", text: "J" }), " next · ", el("span", { class: "kbd", text: "K" }), " previous · ", el("span", { class: "kbd", text: "A" }), " approve · ", el("span", { class: "kbd", text: "R" }), " request changes") : null) : el("div", { class: "detail-wrap" });
  return [bar, el("div", { class: `review${state.review.id ? " has-open" : ""}` }, queue, detail)];
}
document.addEventListener("keydown", e => {
  if (state.view !== "review" || modals.length || e.metaKey || e.ctrlKey || e.altKey) return;
  if (document.activeElement && document.activeElement.matches("input, textarea, select")) return;
  const q = reviewQueue(), i = q.findIndex(p => p.id === state.review.id), p = state.posts.get(state.review.id);
  if (e.key === "j" || e.key === "k") { const t = q[i + (e.key === "j" ? 1 : -1)]; if (t) { state.review.id = t.id; render(); main.querySelector(".qitem[aria-current=true]")?.scrollIntoView({ block: "nearest" }); } }
  else if (e.key === "a" && p && state.me.canEdit && ["draft", "needs_changes", "rejected"].includes(p.status)) approve(p);
  else if (e.key === "r" && p && state.me.canEdit && ["draft", "needs_changes", "approved", "scheduled"].includes(p.status)) openChangesModal(p);
});
