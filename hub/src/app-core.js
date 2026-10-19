// Core: constants, helpers, state, chrome (sidebar, header, sync pill), overlays, writes, render loop.

// ---------- constants ----------
const PLATFORMS = { instagram: "Instagram", linkedin: "LinkedIn", facebook: "Facebook", whatsapp_channel: "WhatsApp Channel", x: "X" };
const PLATFORM_SHORT = { instagram: "Instagram", linkedin: "LinkedIn", facebook: "Facebook", whatsapp_channel: "WhatsApp", x: "X" };
const LIMITS = { instagram: 2200, linkedin: 3000, facebook: 63206, whatsapp_channel: 1000, x: 280 };
const STATUS_LABEL = { shell: "Brief", draft: "Draft", needs_changes: "Needs changes", approved: "Approved", scheduled: "Scheduled", posted: "Published", rejected: "Rejected", blocked: "Blocked", delayed: "Delayed" };
const STATUS_ORDER = ["shell", "draft", "needs_changes", "approved", "scheduled", "posted", "rejected"];
const THEMES = { educational: "Educational", impact_story: "Impact story", initiative_promo: "Initiative / promo", behind_the_scenes: "Behind the scenes", founder_team_voice: "Founder / team voice", engagement: "Engagement" };
const THEME_COLORS = ["var(--a-earth_osai)", "var(--a-tranzent_foundation)", "var(--a-iclc)", "var(--a-other)", "var(--a-pathvik)", "var(--a-person)"];
const FORMAT_LABEL = { text: "Text", single_image: "Image", carousel: "Carousel", reel: "Reel", story: "Story", document: "Document", poll: "Poll", channel_message: "Channel message", thread: "Thread" };
const FORMATS_BY_PLATFORM = { instagram: ["reel", "carousel", "single_image", "story"], linkedin: ["text", "document", "single_image", "poll"], x: ["text", "thread"], facebook: ["text", "single_image", "reel"], whatsapp_channel: ["channel_message"] };
const DEFAULT_TIME = { linkedin: "09:30", instagram: "19:30", x: "21:30", facebook: "19:00", whatsapp_channel: "18:30" };
const APPROVER = { founder: "Founder", manager: "Manager", self: "Post author" };
const KNOWN_ACCOUNTS = ["hifuel_advisory", "tranzent_foundation", "pathvik", "earth_osai", "iclc"];
const SPACING = { perDay: 2, gapHours: 3, gapAccountMin: 60 };
const KEY_DATES = {
  "2026-11-08": ["Diwali", ""], "2026-11-14": ["Children's Day", ""], "2026-11-24": ["Guru Nanak Jayanti", ""],
  "2026-11-26": ["Constitution Day", ""], "2026-12-05": ["World Soil Day", ""], "2026-12-25": ["Christmas", ""],
  "2027-01-26": ["Republic Day", ""], "2027-01-30": ["Martyrs' Day", "sensitive"], "2027-03-21": ["Intl Day of Forests", ""],
  "2027-03-22": ["World Water Day", ""], "2027-03-26": ["Good Friday", "sensitive"], "2027-04-22": ["Earth Day", ""], "2027-06-05": ["World Environment Day", ""],
  "2027-07-01": ["Van Mahotsav", ""], "2027-08-15": ["Independence Day", ""], "2027-10-02": ["Gandhi Jayanti", ""]
};
const CHANGE_REASONS = ["The hook doesn't stop the scroll", "Tone is off-brand for this account", "A fact or number needs a source", "Too long for the platform", "Design brief is unclear", "Wrong day or time", "Call to action is unclear"];

const ICONS = {
  overview: '<rect x="3" y="3" width="7" height="9" rx="1.5"/><rect x="14" y="3" width="7" height="5" rx="1.5"/><rect x="14" y="12" width="7" height="9" rx="1.5"/><rect x="3" y="16" width="7" height="5" rx="1.5"/>',
  calendar: '<rect x="3" y="5" width="18" height="16" rx="2"/><path d="M3 10h18M8 3v4M16 3v4"/>',
  review: '<circle cx="12" cy="12" r="9"/><path d="M8.5 12.5l2.5 2.5 4.5-5"/>',
  analytics: '<path d="M4 20V10M10 20V4M16 20v-7M22 20H2"/>',
  ideas: '<path d="M9 18h6M10 21h4M12 3a6 6 0 0 0-3.6 10.8c.7.5 1.1 1.3 1.1 2.1V16h5v-.1c0-.8.4-1.6 1.1-2.1A6 6 0 0 0 12 3z"/>',
  campaigns: '<path d="M4 10v4a1 1 0 0 0 1 1h2l6 4V5L7 9H5a1 1 0 0 0-1 1z"/><path d="M17 9.5a3.5 3.5 0 0 1 0 5M19.5 7a7 7 0 0 1 0 10"/>',
  kits: '<circle cx="9" cy="8" r="3.5"/><path d="M2.5 20a6.5 6.5 0 0 1 13 0"/><path d="M16 4.6a3.5 3.5 0 0 1 0 6.8M18 14.3a6.5 6.5 0 0 1 3.5 5.7"/>',
  news: '<path d="M6 16v-5a6 6 0 1 1 12 0v5l1.5 2h-15z"/><path d="M10 20.5a2 2 0 0 0 4 0"/>',
  reports: '<path d="M7 3h7l5 5v13H7z"/><path d="M14 3v5h5M10 13h6M10 17h6"/>',
  more: '<circle cx="5" cy="12" r="1.3"/><circle cx="12" cy="12" r="1.3"/><circle cx="19" cy="12" r="1.3"/>',
  copy: '<rect x="9" y="9" width="11" height="11" rx="2"/><path d="M5 15V5a1 1 0 0 1 1-1h10"/>',
  check: '<path d="M5 12.5l4.5 4.5L19 7.5"/>',
  x: '<path d="M6 6l12 12M18 6L6 18"/>',
  plus: '<path d="M12 5v14M5 12h14"/>',
  left: '<path d="M15 6l-6 6 6 6"/>',
  right: '<path d="M9 6l6 6-6 6"/>',
  up: '<path d="M12 19V5M6 11l6-6 6 6"/>',
  heart: '<path d="M12 20s-7-4.4-7-10a4 4 0 0 1 7-2.6A4 4 0 0 1 19 10c0 5.6-7 10-7 10z"/>',
  comment: '<path d="M20 12a8 8 0 0 1-11.8 7L4 20l1.1-4A8 8 0 1 1 20 12z"/>',
  send: '<path d="M21 3L10 14M21 3l-7 18-4-7-7-4z"/>',
  save: '<path d="M6 3h12v18l-6-4.5L6 21z"/>',
  repost: '<path d="M17 2l3 3-3 3M20 5H8a4 4 0 0 0-4 4v1M7 22l-3-3 3-3M4 19h12a4 4 0 0 0 4-4v-1"/>',
  like: '<path d="M7 11v9H4v-9zM7 11l4-8a2 2 0 0 1 2 2v4h6a2 2 0 0 1 2 2.3l-1.2 7A2 2 0 0 1 17.8 20H7"/>',
  play: '<path d="M8 5v14l11-7z" fill="currentColor" stroke="none"/>',
  clock: '<circle cx="12" cy="12" r="9"/><path d="M12 7v5l3 2"/>',
  sun: '<circle cx="12" cy="12" r="4"/><path d="M12 2v2M12 20v2M4.9 4.9l1.4 1.4M17.7 17.7l1.4 1.4M2 12h2M20 12h2M4.9 19.1l1.4-1.4M17.7 6.3l1.4-1.4"/>',
  moon: '<path d="M20 14.5A8 8 0 0 1 9.5 4a8 8 0 1 0 10.5 10.5z"/>',
  auto: '<circle cx="12" cy="12" r="9"/><path d="M12 3v18" /><path d="M12 3a9 9 0 0 1 0 18z" fill="currentColor"/>',
  sidebar: '<rect x="3" y="4" width="18" height="16" rx="2"/><path d="M9 4v16"/>',
  download: '<path d="M12 4v11M7 10l5 5 5-5M5 20h14"/>',
  link: '<path d="M10 14a4 4 0 0 0 5.7 0l3-3a4 4 0 0 0-5.7-5.7l-1 1M14 10a4 4 0 0 0-5.7 0l-3 3a4 4 0 0 0 5.7 5.7l1-1"/>',
  image: '<rect x="3" y="4" width="18" height="16" rx="2"/><circle cx="9" cy="10" r="2"/><path d="M21 16l-5-5-9 9"/>',
  move: '<path d="M12 3v18M3 12h18M12 3l-3 3M12 3l3 3M12 21l-3-3M12 21l3-3M3 12l3-3M3 12l3 3M21 12l-3-3M21 12l-3 3"/>',
  edit: '<path d="M4 20h4L19 9l-4-4L4 16z"/><path d="M13.5 6.5l4 4"/>',
  table: '<rect x="3" y="4" width="18" height="16" rx="2"/><path d="M3 10h18M3 15h18M9 4v16"/>',
  chart: '<path d="M3 17l6-6 4 4 8-8"/>',
  external: '<path d="M14 4h6v6M20 4l-9 9M18 14v5a1 1 0 0 1-1 1H5a1 1 0 0 1-1-1V7a1 1 0 0 1 1-1h5"/>',
  alert: '<path d="M12 3l9.5 17h-19z"/><path d="M12 10v4M12 17.5v.1"/>',
  sparkle: '<path d="M12 3l1.8 5.2L19 10l-5.2 1.8L12 17l-1.8-5.2L5 10l5.2-1.8z"/>',
  grip: '<circle cx="9" cy="6" r="1.2"/><circle cx="15" cy="6" r="1.2"/><circle cx="9" cy="12" r="1.2"/><circle cx="15" cy="12" r="1.2"/><circle cx="9" cy="18" r="1.2"/><circle cx="15" cy="18" r="1.2"/>'
};
const PF_SVG = {
  instagram: '<svg viewBox="0 0 24 24" aria-hidden="true"><rect x="3" y="3" width="18" height="18" rx="5" fill="none" stroke="currentColor" stroke-width="2"/><circle cx="12" cy="12" r="4" fill="none" stroke="currentColor" stroke-width="2"/><circle cx="17.4" cy="6.6" r="1.3" fill="currentColor"/></svg>',
  linkedin: '<svg viewBox="0 0 24 24" aria-hidden="true"><rect x="2.5" y="2.5" width="19" height="19" rx="4" fill="currentColor"/><path d="M7.5 10.5v6.5M7.5 7.3v.1M11.2 17v-6.5M11.2 13.4c0-1.7 1-2.9 2.6-2.9s2.6 1.1 2.6 2.9V17" stroke="var(--surface)" stroke-width="2" stroke-linecap="round" fill="none"/></svg>',
  facebook: '<svg viewBox="0 0 24 24" aria-hidden="true"><circle cx="12" cy="12" r="10" fill="currentColor"/><path d="M13.4 21.5v-7.2h2.3l.4-2.8h-2.7V9.8c0-.8.3-1.4 1.4-1.4h1.4V5.9a17 17 0 0 0-2-.1c-2 0-3.4 1.2-3.4 3.5v2.2H8.6v2.8h2.2v7.2" fill="var(--surface)"/></svg>',
  x: '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M4.5 4h4.2l10.8 16h-4.2z" fill="currentColor"/><path d="M19 4l-6 6.9M5 20l6-6.9" stroke="currentColor" stroke-width="2" stroke-linecap="round"/></svg>',
  whatsapp_channel: '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M12 3a9 9 0 0 0-7.7 13.6L3 21l4.5-1.2A9 9 0 1 0 12 3z" fill="none" stroke="currentColor" stroke-width="2" stroke-linejoin="round"/><path d="M9 8.2c0 3.6 3 6.8 6.8 6.8" stroke="currentColor" stroke-width="2" fill="none" stroke-linecap="round"/></svg>'
};
const VIEWS = [
  { id: "overview", label: "Overview", group: "Workspace", sub: "What's happening across the group this week" },
  { id: "calendar", label: "Calendar", group: "Workspace", sub: "Every planned post. Drag a post to move it. Times are IST" },
  { id: "review", label: "Review", group: "Workspace", sub: "Every post needs a human yes before anyone schedules it" },
  { id: "analytics", label: "Analytics", group: "Workspace", sub: "Reach, engagement and follower growth from imported results" },
  { id: "ideas", label: "Ideas", group: "Workspace", sub: "The team's idea board. Vote, group, and turn the best into briefs" },
  { id: "campaigns", label: "Campaigns", group: "Team", sub: "Launches and pushes, tracked end to end" },
  { id: "kits", label: "Advocacy", group: "Team", sub: "Drafts for founder and team LinkedIn posts" },
  { id: "news", label: "Announcements", group: "Team", sub: "Updates for the whole team" },
  { id: "reports", label: "Reports", group: "Results", sub: "Weekly and monthly reports, experiments and the content mix" }
];
const TAB_VIEWS = ["overview", "calendar", "review", "analytics"];

// ---------- state ----------
const state = {
  posts: new Map(), plans: [], ideas: [], news: [], reports: [], experiments: [], results: new Map(), comments: [],
  meta: { config: null, sync: null }, analytics: null,
  view: "overview", loaded: false, unavailable: false, conn: "connecting", saving: 0,
  me: { id: null, name: "", avatar: "", canEdit: false, canWrite: null }, names: {}, pendingRender: false,
  filter: { account: "", platform: "", status: "", q: "" },
  cal: { mode: "week", anchor: null, day: null },
  review: { tab: "todo", id: null },
  an: { account: "", platform: "", week: null, period: "4w", sort: "impressions", dir: -1, chartTable: false, showAll: false },
  ideasBy: "lane", ideasAccount: "", campaignId: null, reportId: null, kitWeek: null,
  prefs: { mini: false, theme: "auto" }
};
try {
  const saved = JSON.parse(localStorage.getItem("hub-prefs-v4") || "{}");
  if (saved.calMode) state.cal.mode = saved.calMode;
  if (typeof saved.mini === "boolean") state.prefs.mini = saved.mini;
  if (saved.theme) state.prefs.theme = saved.theme;
  if (saved.ideasBy) state.ideasBy = saved.ideasBy;
} catch {}
function savePrefs() { try { localStorage.setItem("hub-prefs-v4", JSON.stringify({ calMode: state.cal.mode, mini: state.prefs.mini, theme: state.prefs.theme, ideasBy: state.ideasBy })); } catch {} }
let db = null, user = null, downloads = null, assets = null;
const $ = (sel, root = document) => root.querySelector(sel);
const main = $("#main");

// ---------- helpers ----------
function el(tag, attrs = {}, ...kids) {
  const n = document.createElement(tag);
  for (const [k, v] of Object.entries(attrs)) {
    if (v == null || v === false) continue;
    if (k === "class") n.className = v;
    else if (k === "style") n.setAttribute("style", v);
    else if (k.startsWith("on")) n.addEventListener(k.slice(2), v);
    else if (k === "text") n.textContent = v;
    else n.setAttribute(k, v === true ? "" : v);
  }
  for (const kid of kids.flat(Infinity)) if (kid != null && kid !== false) n.append(kid.nodeType ? kid : document.createTextNode(String(kid)));
  return n;
}
function svg(markup, cls = "icon") { const t = document.createElement("template"); t.innerHTML = `<svg class="${cls}" viewBox="0 0 24 24" aria-hidden="true">${markup}</svg>`; return t.content.firstChild; }
const icon = name => svg(ICONS[name]);
function pfBadge(platform, lg = false) { const s = el("span", { class: `pf${lg ? " lg" : ""}`, style: `--pc:var(--p-${platform})`, title: PLATFORMS[platform] || platform }); s.innerHTML = PF_SVG[platform] || ""; return s; }
const iso = d => d.toISOString().slice(0, 10);
function mondayOf(dateStr) { const d = new Date(dateStr + "T00:00:00Z"); d.setUTCDate(d.getUTCDate() - (d.getUTCDay() + 6) % 7); return iso(d); }
function addDays(dateStr, n) { const d = new Date(dateStr + "T00:00:00Z"); d.setUTCDate(d.getUTCDate() + n); return iso(d); }
function addMonths(dateStr, n) { const d = new Date(dateStr.slice(0, 7) + "-01T00:00:00Z"); d.setUTCMonth(d.getUTCMonth() + n); return iso(d); }
function daysBetween(a, b) { return Math.round((new Date(b + "T00:00:00Z") - new Date(a + "T00:00:00Z")) / 864e5); }
function fmtDay(dateStr, opts) { return new Date(dateStr + "T00:00:00Z").toLocaleDateString("en-IN", { timeZone: "UTC", ...opts }); }
function nowIST() { return new Date(Date.now() + 5.5 * 3600e3).toISOString().slice(0, 16); }
const todayIST = () => nowIST().slice(0, 10);
function ago(isoStr) {
  if (!isoStr) return "";
  const m = Math.round((Date.now() - new Date(isoStr).getTime()) / 6e4);
  if (m < 1) return "just now"; if (m < 60) return `${m} min ago`; const h = Math.round(m / 60); if (h < 24) return `${h} h ago`;
  const d = Math.round(h / 24); return d < 7 ? `${d} d ago` : new Date(isoStr).toLocaleDateString("en-IN", { day: "numeric", month: "short" });
}
const minutesOf = t => { const [h, m] = (t || "00:00").split(":").map(Number); return h * 60 + (m || 0); };
const hhmm = mins => `${String(Math.floor(mins / 60)).padStart(2, "0")}:${String(mins % 60).padStart(2, "0")}`;
const slug = s => (s || "").toLowerCase().replace(/[^a-z0-9]+/g, "-").replace(/^-|-$/g, "").slice(0, 40) || "brief";
const plural = (n, w) => `${n} ${w}${n === 1 ? "" : "s"}`;
const fmtNum = n => n == null ? "–" : Math.round(n).toLocaleString("en-IN");
const fmtPct = x => x == null || !isFinite(x) ? "–" : `${(x * 100).toFixed(1)}%`;
const acctColor = (account, type) => type === "person" ? "var(--a-person)" : (KNOWN_ACCOUNTS.includes(account) ? `var(--a-${account})` : "var(--a-other)");
const acctVar = p => acctColor(p.account, p.account_type);
const initials = name => (name || "?").replace(/\(.*?\)/g, "").split(/[\s.]+/).filter(Boolean).slice(0, 2).map(w => w[0]).join("").toUpperCase();
function publishText(p) { return [p.hook, p.caption, p.cta, (p.hashtags || []).join(" ")].map(s => (s || "").trim()).filter(Boolean).join("\n\n"); }
const blocks = p => (p.issues || []).filter(i => i.severity === "block");
const isShell = p => p.status === "shell";
const isBlocked = p => !isShell(p) && blocks(p).length > 0 && ["draft", "needs_changes"].includes(p.status);
const isDelayed = p => ["approved", "scheduled"].includes(p.status) && `${p.date}T${p.time || "23:59"}` < nowIST();
const isPending = p => ["draft", "needs_changes"].includes(p.status);
function displayStatus(p) { if (isShell(p)) return "shell"; if (isDelayed(p)) return "delayed"; if (isBlocked(p)) return "blocked"; return p.status; }
const allPosts = () => [...state.posts.values()].sort((a, b) => (a.date + (a.time || "")).localeCompare(b.date + (b.time || "")));
const matchesActive = () => { const f = state.filter; return !!(f.account || f.platform || f.status || f.q); };
function matches(p) {
  const f = state.filter;
  if (f.account && p.account !== f.account) return false;
  if (f.platform && p.platform !== f.platform) return false;
  if (f.status) { const ds = displayStatus(p); if (f.status !== ds && f.status !== p.status) return false; }
  if (f.q) { const q = f.q.toLowerCase(); if (![p.hook, p.caption, p.account_name, p.pillar, p.campaign].join(" ").toLowerCase().includes(q)) return false; }
  return true;
}
const postsBetween = (a, b, filtered = true) => allPosts().filter(p => p.date >= a && p.date <= b && (!filtered || matches(p)));
const thisWeek = () => mondayOf(todayIST());
const nameOf = id => (id && state.names[id]) || (id && id === state.me.id ? "You" : id === "claude" ? "Claude" : "A teammate");
function accounts() {
  const cfg = state.meta.config && state.meta.config.accounts;
  const fromPosts = new Map(allPosts().map(p => [p.account, { name: p.account_name, type: p.account_type, pillars: [], platforms: [], approver: p.approver, enabled: true }]));
  const out = new Map();
  if (cfg) for (const [id, a] of Object.entries(cfg)) if (a.enabled || fromPosts.has(id)) out.set(id, a);
  for (const [id, a] of fromPosts) if (!out.has(id)) out.set(id, a);
  return out;
}
const accountName = id => (accounts().get(id) || {}).name || id;
function statusBadge(p) { const s = typeof p === "string" ? p : displayStatus(p); return el("span", { class: `badge ${s}`, text: STATUS_LABEL[s] || s }); }
function ava(name, color, sm = false, img = "") {
  const a = el("span", { class: `ava${sm ? " sm" : ""}`, style: `--acct:${color}`, "aria-hidden": "true" });
  if (img) a.append(el("img", { src: img, alt: "" })); else a.textContent = initials(name);
  return a;
}
const acctAva = (p, sm = false) => ava(p.account_name, acctVar(p), sm);
const personAva = (id, sm = true) => ava(nameOf(id), "var(--a-other)", sm, id === state.me.id ? state.me.avatar : "");
function countBy(list, key) { const c = {}; for (const p of list) { const k = typeof key === "function" ? key(p) : p[key]; c[k] = (c[k] || 0) + 1; } return c; }
function emptyState(title, body, ...actions) { return el("div", { class: "empty" }, icon("sparkle"), el("strong", { text: title }), body ? el("span", { text: body }) : null, actions.length ? el("div", { class: "row", style: "justify-content:center" }, actions) : null); }
function skeleton(kind = "cards") {
  if (kind === "bento") return el("div", { class: "bento" }, [3, 3, 3, 3, 7, 5, 4, 4, 4].map(s => el("div", { class: `skel span-${s}${s === 3 ? " half" : ""}`, style: `height:${s === 3 ? 108 : 240}px` })));
  return el("div", { class: "stack" }, [1, 2, 3].map(() => el("div", { class: "skel", style: "height:120px" })));
}
function notReady(kind) {
  if (state.unavailable) return emptyState("The hub can't load here", "Open this page from claude.ai while signed in to see the team's plan.");
  if (!state.loaded) return skeleton(kind);
  return null;
}
async function resolveNames(ids) {
  const need = [...new Set(ids.filter(Boolean))].filter(id => !state.names[id] && id !== "claude");
  if (!user || !need.length) return;
  try {
    const ps = await user.profiles(need);
    let changed = false;
    for (const id of need) { const n = ps[id] && ps[id].name; if (n) { state.names[id] = n; changed = true; } }
    if (changed) render();
  } catch {}
}

// ---------- toasts, menus, modals ----------
function toast(msg, opts = {}) {
  const root = $("#toastRoot");
  const t = el("div", { class: `toast${opts.warn ? " warn" : ""}`, role: "status" }, opts.saving ? el("span", { class: "saving" }, el("i")) : null, el("span", { text: msg }),
    opts.action ? el("button", { class: "linkbtn", onclick: () => { t.remove(); opts.action.fn(); }, text: opts.action.label }) : null);
  root.append(t);
  while (root.children.length > 3) root.firstChild.remove();
  setTimeout(() => t.remove(), opts.ms || (opts.action ? 6500 : 3400));
  return t;
}
async function copy(text) {
  try { await navigator.clipboard.writeText(text); toast("Copied to clipboard"); }
  catch { openModal(() => [el("h2", { text: "Copy this text" }), (() => { const ta = el("textarea", { rows: 10, "aria-label": "Text to copy" }); ta.value = text; setTimeout(() => ta.select(), 30); return ta; })(), el("div", { class: "foot" }, el("button", { class: "btn", onclick: closeModal, text: "Done" }))]); }
}
function errMsg(e) {
  if (e && (e.code === "invalid_argument" || e.code === "permission_denied")) return "You don't have permission to change this. Ask Aryan for Editor access.";
  if (e && e.code === "quota_exceeded") return "The hub's storage is full. Ask Aryan to archive old weeks.";
  return "That didn't save. Check your connection and try again.";
}
function openMenu(anchor, items) {
  const root = $("#menuRoot");
  const r = anchor.getBoundingClientRect();
  const close = () => { root.replaceChildren(); document.removeEventListener("pointerdown", outside, true); };
  const outside = e => { if (!root.contains(e.target)) close(); };
  const menu = el("div", { class: "menu", role: "menu" }, items.filter(Boolean).map(it => el("button", { role: "menuitem", disabled: it.disabled || null, onclick: () => { close(); it.fn(); } },
    it.icon ? icon(it.icon) : null, el("span", {}, it.label, it.sub ? el("small", { text: it.sub }) : null))));
  root.replaceChildren(menu);
  const w = Math.max(menu.offsetWidth, 220);
  const left = Math.min(window.scrollX + r.right - w, window.scrollX + document.documentElement.clientWidth - w - 12);
  menu.style.left = Math.max(window.scrollX + 12, left) + "px";
  menu.style.top = (window.scrollY + r.bottom + 6) + "px";
  setTimeout(() => document.addEventListener("pointerdown", outside, true), 0);
  menu.querySelector("button:not([disabled])")?.focus();
  menu.addEventListener("keydown", e => {
    const bs = [...menu.querySelectorAll("button:not([disabled])")], i = bs.indexOf(document.activeElement);
    if (e.key === "ArrowDown") { e.preventDefault(); bs[(i + 1) % bs.length].focus(); }
    if (e.key === "ArrowUp") { e.preventDefault(); bs[(i - 1 + bs.length) % bs.length].focus(); }
    if (e.key === "Escape") { close(); anchor.focus(); }
  });
}
const modals = [];
function openModal(renderFn, opts = {}) { modals.push({ renderFn, opts, opener: document.activeElement }); renderModals(true); }
function closeModal() { const m = modals.pop(); renderModals(true); if (m && m.opener && m.opener.isConnected) m.opener.focus(); if (state.pendingRender) render(); }
function renderModals(fresh = false) {
  const root = $("#modalRoot");
  const top = modals[modals.length - 1];
  if (!top) { root.replaceChildren(); document.body.style.overflow = ""; return; }
  const old = root.querySelector(".modal");
  if (!fresh && old && old.contains(document.activeElement) && document.activeElement.matches("textarea, input, select")) return;
  const scroll = old && !fresh ? old.scrollTop : 0;
  const box = el("div", { class: `modal${top.opts.wide ? " wide" : ""}`, role: "dialog", "aria-modal": "true", "aria-label": top.opts.label || "Dialog" }, top.renderFn());
  root.replaceChildren(el("div", { class: "scrim", onclick: closeModal }), box);
  document.body.style.overflow = "hidden";
  box.scrollTop = scroll;
  if (fresh) setTimeout(() => (box.querySelector("[autofocus]") || box.querySelector("input, textarea, select, button"))?.focus(), 20);
}
document.addEventListener("keydown", e => {
  if (e.key === "Escape" && modals.length && !$("#menuRoot").children.length) { e.preventDefault(); closeModal(); }
  if (e.key === "Tab" && modals.length) {
    const box = $("#modalRoot .modal"); if (!box) return;
    const f = [...box.querySelectorAll("button:not([disabled]), input, textarea, select, a[href], summary")].filter(x => x.offsetParent !== null);
    if (!f.length) return;
    if (e.shiftKey && document.activeElement === f[0]) { e.preventDefault(); f[f.length - 1].focus(); }
    else if (!e.shiftKey && document.activeElement === f[f.length - 1]) { e.preventDefault(); f[0].focus(); }
  }
});

// ---------- writes ----------
async function guarded(fn, okMsg, opts = {}) {
  state.saving++; renderSync();
  try { await fn(); if (okMsg) toast(okMsg, opts); return true; }
  catch (e) { console.warn("hub write failed", e); toast(errMsg(e), { warn: true }); return false; }
  finally { state.saving--; renderSync(); }
}
function writePost(p, fields, okMsg, opts) {
  return guarded(() => db.doc(`posts/${p.id}`).update({ ...fields, updated_at: new Date().toISOString() }), okMsg, opts);
}
function setStatus(p, status, comment = "", checklist = []) {
  return writePost(p, { status, review: { by: state.me.id, at: new Date().toISOString(), comment, checklist } }, `${STATUS_LABEL[status]}${status === "approved" ? ". It's in the queue to schedule" : ""}`);
}
function addComment(p, text, kind = "comment", checklist = []) {
  return guarded(() => db.collection("comments").add({ post_id: p.id, text, kind, checklist, by: state.me.id, at: new Date().toISOString() }), kind === "comment" ? "Comment added" : null);
}

// ---------- chrome ----------
function navCounts() {
  return {
    review: allPosts().filter(p => isPending(p) && p.date >= addDays(todayIST(), -7)).length,
    ideas: state.ideas.filter(i => (i.status || "new") === "new").length,
    campaigns: campaigns().filter(c => c.active).length
  };
}
const role = () => state.me.canEdit ? "Editor" : state.me.canWrite ? "Contributor" : state.me.id ? "Viewer" : "";
function renderChrome() {
  const app = $("#app");
  app.classList.toggle("mini", state.prefs.mini);
  const counts = navCounts();
  const navBtn = v => el("button", { class: "nav-item", "aria-current": state.view === v.id ? "page" : null, "data-tip": v.label + (counts[v.id] ? ` (${counts[v.id]})` : ""), onclick: () => go(v.id) },
    icon(v.id), el("span", { class: "txt", text: v.label }), counts[v.id] ? el("span", { class: `count${v.id === "review" ? " hot" : ""}`, text: counts[v.id] }) : null);
  const groups = [...new Set(VIEWS.map(v => v.group))];
  $("#sideNav").replaceChildren(...groups.flatMap(g => [el("div", { class: "nav-label", text: g }), ...VIEWS.filter(v => v.group === g).map(navBtn)]));
  const cb = $("#collapseBtn");
  cb.setAttribute("data-tip", state.prefs.mini ? "Expand sidebar" : "Collapse sidebar");
  cb.setAttribute("aria-label", state.prefs.mini ? "Expand sidebar" : "Collapse sidebar");
  $("#collapseIcon").replaceChildren(icon("sidebar"));
  const tab = id => { const v = VIEWS.find(x => x.id === id); return el("button", { "aria-current": state.view === id ? "page" : null, onclick: () => go(id) }, icon(id), v.label, counts[id] ? el("span", { class: "badge-n", text: counts[id] }) : null); };
  const moreActive = !TAB_VIEWS.includes(state.view);
  $("#tabBar").replaceChildren(...TAB_VIEWS.map(tab), el("button", { "aria-current": moreActive ? "page" : null, onclick: e => openMenu(e.currentTarget, VIEWS.filter(v => !TAB_VIEWS.includes(v.id)).map(v => ({ label: v.label, icon: v.id, fn: () => go(v.id) }))) }, icon("more"), moreActive ? VIEWS.find(v => v.id === state.view).label : "More"));
  // breadcrumbs
  const v = VIEWS.find(x => x.id === state.view);
  const crumbs = [el("button", { onclick: () => go("overview"), text: "Hub" }), el("span", { class: "sep", text: "/" })];
  const sub = crumbSub();
  if (sub) crumbs.push(el("button", { onclick: () => { if (state.view === "review") state.review.id = null; go(state.view); }, text: v.label }), el("span", { class: "sep", text: "/" }), el("b", { class: "ellipsis", style: "max-width:38ch", text: sub }));
  else crumbs.push(el("b", { text: v.label }));
  $("#crumbs").replaceChildren(...crumbs);
  // theme + quick action
  const th = state.prefs.theme;
  const tb = $("#themeBtn");
  tb.replaceChildren(icon(th === "dark" ? "moon" : th === "light" ? "sun" : "auto"));
  tb.setAttribute("data-tip", `Theme: ${th === "auto" ? "match device" : th}`);
  tb.setAttribute("aria-label", `Theme: ${th === "auto" ? "match device" : th}. Change theme`);
  const qb = $("#quickBtn");
  qb.hidden = !state.loaded || (!state.me.canEdit && !state.me.canWrite);
  qb.replaceChildren(icon("plus"), el("span", { text: state.me.canEdit ? "Quick draft" : "New idea" }));
  // page head
  $("#pageHead").replaceChildren(el("div", { class: "spread", style: "align-items:flex-end" },
    el("div", {}, el("h1", { text: v.label }), el("p", { text: v.sub })), pageActions()));
  if (state.me.id) {
    const box = $("#meBox"); box.hidden = false;
    box.replaceChildren(personAva(state.me.id, false), el("div", { style: "min-width:0" }, el("b", { class: "ellipsis", style: "display:block", text: state.me.name || "You" }), el("small", { text: state.me.canEdit ? "Editor · can approve" : role() })));
  }
  renderSync();
}
function crumbSub() {
  if (state.view === "review" && state.review.id) { const p = state.posts.get(state.review.id); return p ? (p.hook || "Untitled") : null; }
  if (state.view === "calendar") return state.cal.mode === "month" ? "Month" : state.cal.mode === "week" ? "Week" : "Pipeline";
  if (state.view === "campaigns") { const c = campaigns().find(x => x.id === state.campaignId) || campaigns()[0]; return c ? c.name : null; }
  return null;
}
function pageActions() {
  if (state.view === "analytics") return analyticsActions();
  return null;
}
function renderSync() {
  const pill = $("#syncPill");
  let cls = state.conn, text;
  if (state.conn === "offline") text = "Offline · changes won't save";
  else if (state.conn === "connecting") text = "Connecting…";
  else if (state.saving > 0) { cls = "live"; text = "Saving…"; }
  else { const at = state.meta.sync && state.meta.sync.at; text = at ? `Live · Claude synced ${ago(at)}` : "Live · waiting for Claude's first sync"; }
  pill.className = `sync ${cls}`;
  pill.replaceChildren(state.saving > 0 ? el("span", { class: "saving" }, el("i")) : el("i"), el("span", { text }));
  pill.title = "Live: teammates' changes appear here instantly. Claude sync: when Claude last pushed drafts and re-checked edits. Edits made here are re-checked at the next sync.";
}
setInterval(() => { renderSync(); }, 60e3);
window.addEventListener("offline", () => { state.conn = "offline"; renderSync(); });
window.addEventListener("online", () => { state.conn = state.loaded ? "live" : "connecting"; renderSync(); });

function applyTheme() { const t = state.prefs.theme; if (t === "auto") document.documentElement.removeAttribute("data-theme"); else document.documentElement.setAttribute("data-theme", t); }
$("#themeBtn").addEventListener("click", () => { const order = ["auto", "light", "dark"]; state.prefs.theme = order[(order.indexOf(state.prefs.theme) + 1) % 3]; applyTheme(); savePrefs(); renderChrome(); toast(`Theme: ${state.prefs.theme === "auto" ? "matches your device" : state.prefs.theme}`); });
$("#collapseBtn").addEventListener("click", () => { state.prefs.mini = !state.prefs.mini; savePrefs(); renderChrome(); });
$("#quickBtn").addEventListener("click", () => state.me.canEdit ? openBriefModal({}) : openIdeaModal({}));
applyTheme();

function go(view, opts = {}) {
  state.view = view;
  if (view === "review" && opts.id !== undefined) state.review.id = opts.id;
  try { history.replaceState(null, "", "#" + view + (view === "review" && state.review.id ? "/" + state.review.id : "")); } catch {}
  if (!opts.keepScroll) window.scrollTo({ top: 0 });
  render();
}
function openPost(id) {
  if (state.view === "review") { state.review.id = id; render(); return; }
  openModal(() => postModal(id), { wide: true, label: "Post details" });
}

// ---------- render loop ----------
function editingNow() { const a = document.activeElement; return !!a && a.matches("textarea, input:not([type=search]):not([type=checkbox]), select") && (main.contains(a) || $("#modalRoot").contains(a)); }
function render() {
  if (editingNow()) { state.pendingRender = true; return; }
  state.pendingRender = false;
  renderMain();
  renderChrome();
  renderModals();
}
const scrollKeep = new Map();
function renderMain() {
  const views = { overview: viewOverview, calendar: viewCalendar, review: viewReview, analytics: viewAnalytics, ideas: viewIdeas, campaigns: viewCampaigns, kits: viewKits, news: viewNews, reports: viewReports };
  // keep horizontal/vertical scroll of inner scrollers (timeline, kanban, board) across live updates
  main.querySelectorAll("[data-keep]").forEach(n => { if (!n.dataset.needsInit || scrollKeep.has(n.dataset.keep)) scrollKeep.set(n.dataset.keep, [n.scrollLeft, n.scrollTop]); });
  let nodes;
  try { nodes = [].concat(views[state.view]()).filter(Boolean); }
  catch (e) { console.error("hub render failed", e); nodes = [emptyState("This screen hit a problem", "Reload the page. If it keeps happening, tell Aryan which screen it was.", el("button", { class: "btn", onclick: () => location.reload(), text: "Reload" }))]; }
  main.replaceChildren(...nodes);
  main.querySelectorAll("[data-keep]").forEach(n => { const s = scrollKeep.get(n.dataset.keep); if (s) { n.scrollLeft = s[0]; n.scrollTop = s[1]; } else if (n.dataset.initTop) n.scrollTop = Number(n.dataset.initTop); });
}
document.addEventListener("focusout", () => setTimeout(() => { if (state.pendingRender && !editingNow()) render(); }, 300));

// ---------- filters toolbar (shared by calendar, review, campaigns) ----------
function filterBar(opts = {}) {
  const f = state.filter;
  const acc = el("select", { "aria-label": "Account", onchange: e => { f.account = e.target.value; render(); } },
    el("option", { value: "", text: "All accounts" }), [...accounts()].map(([id, a]) => el("option", { value: id, text: a.name })));
  acc.value = f.account;
  const statuses = ["shell", "draft", "needs_changes", "blocked", "approved", "scheduled", "delayed", "posted", "rejected"];
  const st = opts.noStatus ? null : el("select", { "aria-label": "Status", onchange: e => { f.status = e.target.value; render(); } },
    el("option", { value: "", text: "Any status" }), statuses.map(s => el("option", { value: s, text: STATUS_LABEL[s] })));
  if (st) st.value = f.status;
  const plats = el("div", { class: "pchips", role: "group", "aria-label": "Platform" }, Object.keys(PLATFORMS).map(pl =>
    el("button", { class: "pchip", style: `--pc:var(--p-${pl})`, "aria-pressed": String(f.platform === pl), title: PLATFORMS[pl], "aria-label": `Only ${PLATFORMS[pl]}`, onclick: () => { f.platform = f.platform === pl ? "" : pl; render(); } }, pfBadge(pl))));
  const q = el("input", { type: "search", placeholder: "Search posts", "aria-label": "Search posts" });
  q.value = f.q;
  let t; q.addEventListener("input", () => { clearTimeout(t); t = setTimeout(() => { f.q = q.value.trim(); renderMain(); setTimeout(() => { const n = main.querySelector("input[type=search]"); if (n) { n.focus(); n.setSelectionRange(n.value.length, n.value.length); } }); }, 220); });
  return el("div", { class: "toolbar", role: "search" }, opts.lead || null, acc, plats, st, q,
    matchesActive() ? el("button", { class: "btn ghost sm", onclick: () => { state.filter = { account: "", platform: "", status: "", q: "" }; render(); }, text: "Clear filters" }) : null,
    el("span", { class: "grow" }), opts.trail || null);
}

// ---------- campaigns (used by several screens) ----------
function campaigns() {
  const out = [];
  const today = todayIST();
  for (const pl of state.plans) {
    if (!pl.campaign) continue;
    const c = pl.campaign;
    out.push({ ...c, posts: allPosts().filter(p => p.campaign === c.id), active: today >= c.start && today <= c.end, upcoming: today < c.start,
      summary: pl.summaries && pl.summaries._overview, questions: pl.questions_for_team || [] });
  }
  return out.sort((a, b) => b.start.localeCompare(a.start));
}

// ---------- spacing guardrail (mirrors config/time_slots.yaml) ----------
function spacingProblems(p, date, time) {
  const others = allPosts().filter(x => x.id !== p.id && x.account === p.account && x.date === date && x.status !== "rejected");
  const t = minutesOf(time), out = [];
  const samePlat = others.filter(x => x.platform === p.platform);
  if (samePlat.length >= SPACING.perDay) out.push(`${p.account_name} already has ${samePlat.length} ${PLATFORM_SHORT[p.platform]} posts that day (max ${SPACING.perDay})`);
  const close = samePlat.find(x => Math.abs(minutesOf(x.time) - t) < SPACING.gapHours * 60);
  if (close) out.push(`another ${PLATFORM_SHORT[p.platform]} post is at ${close.time} (keep ${SPACING.gapHours} h apart)`);
  const cross = others.find(x => x.platform !== p.platform && Math.abs(minutesOf(x.time) - t) < SPACING.gapAccountMin);
  if (cross) out.push(`a ${PLATFORM_SHORT[cross.platform]} post from the same account is at ${cross.time} (keep 1 h apart)`);
  return out;
}
const canMove = p => state.me.canEdit && !["posted", "rejected"].includes(p.status);
async function movePost(p, date, time, opts = {}) {
  if (!canMove(p)) { toast(p.status === "posted" ? "Published posts can't be moved." : "Only editors can move posts.", { warn: true }); return; }
  if (date === p.date && time === p.time) return;
  if (`${date}T${time}` < nowIST()) { toast("That time has already passed. Pick a later slot.", { warn: true }); return; }
  const old = { date: p.date, time: p.time };
  const at = new Date().toISOString();
  const edits = [...(p.edits || [])];
  if (date !== p.date) edits.push({ field: "date", old: p.date, new: date, by: state.me.id, at });
  if (time !== p.time) edits.push({ field: "time", old: p.time, new: time, by: state.me.id, at });
  const problems = spacingProblems(p, date, time);
  // optimistic: show the move straight away; the live snapshot confirms it
  state.posts.set(p.id, { ...p, date, time, edits, slot_source: "manual" });
  render();
  const label = `${fmtDay(date, { weekday: "short", day: "numeric", month: "short" })}, ${time}`;
  const extra = p.status === "scheduled" ? " Reschedule it in Meta Business Suite / LinkedIn too." : "";
  const ok = await writePost(p, { date, time, edits, slot_source: "manual", slot_reason: `Moved by ${nameOf(state.me.id)} on the hub` }, null);
  if (!ok) { state.posts.set(p.id, p); render(); return; }
  if (opts.silent) return;
  toast(problems.length ? `Moved to ${label}. Heads up: ${problems[0]}.${extra}` : `Saved · moved to ${label}.${extra}`,
    { warn: problems.length > 0, action: { label: "Undo", fn: () => movePost(state.posts.get(p.id), old.date, old.time, { silent: false }) } });
}
function openMoveModal(p) {
  const d = el("input", { type: "date", value: p.date, min: todayIST(), "aria-label": "Date" });
  const t = el("input", { type: "time", value: p.time || "10:00", "aria-label": "Time (IST)" });
  const warn = el("div");
  const check = () => { const pr = spacingProblems(p, d.value, t.value); warn.replaceChildren(pr.length ? el("div", { class: "callout warn", text: `Spacing: ${pr.join("; ")}.` }) : ""); };
  d.addEventListener("input", check); t.addEventListener("input", check);
  openModal(() => [el("h2", { text: "Move post" }), el("p", { class: "small muted", text: p.hook }),
    el("div", { class: "grid2" }, el("label", { class: "field" }, "Date", d), el("label", { class: "field" }, "Time (IST)", t)), warn,
    p.status === "scheduled" ? el("div", { class: "callout warn", text: "This post is already scheduled. After moving it, reschedule it in Meta Business Suite / LinkedIn too." }) : null,
    el("div", { class: "foot" }, el("button", { class: "btn", onclick: closeModal, text: "Cancel" }), el("button", { class: "btn primary", onclick: () => { closeModal(); movePost(p, d.value, t.value); }, text: "Move" }))], { label: "Move post" });
  setTimeout(check, 30);
}
