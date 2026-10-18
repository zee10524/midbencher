"use strict";
// The page holds no numbers of its own: every figure and every sentence with a figure in it arrives from the server (app/ui/data.py), which reads
// notes/numbers.md, backtest/out/impact.csv, the register and the reader's stored results.

const $ = (id) => document.getElementById(id);
function el(tag, cls, text) {
  const e = document.createElement(tag);
  if (cls) e.className = cls;
  if (text !== undefined && text !== null) e.textContent = text;
  return e;
}
function add(parent, ...kids) { kids.forEach((k) => k && parent.appendChild(k)); return parent; }
async function api(path, opts) {
  const r = await fetch(path, opts);
  const j = await r.json();
  if (!r.ok || j.error) throw new Error(j.error || "Request failed");
  return j;
}
function showError(e) { const p = $("err"); p.hidden = !e; p.textContent = e ? String(e.message || e) : ""; if (e) reveal(p); }
function clear(node) { while (node.firstChild) node.removeChild(node.firstChild); }

// Presentation helpers: an icon cloned from the sprite in index.html, a loading line, and scrolling a fresh result into view.
function icon(name) {
  const src = $("icons").querySelector("[data-icon=" + name + "]");
  if (!src) return null;
  const svg = src.cloneNode(true);
  svg.removeAttribute("data-icon");
  svg.setAttribute("aria-hidden", "true");
  svg.setAttribute("focusable", "false");
  svg.classList.add("icon");
  return svg;
}
function loading(text, cls) {
  const p = el("div", "loading" + (cls ? " " + cls : ""));
  p.setAttribute("role", "status");
  return add(p, el("span", "spinner"), el("span", "", text));
}
const reduceMotion = () => window.matchMedia && window.matchMedia("(prefers-reduced-motion: reduce)").matches;
function reveal(node) {
  if (!node) return;
  const top = parseFloat(getComputedStyle(document.documentElement).scrollPaddingTop) || 0;
  const r = node.getBoundingClientRect();
  if (r.top < top || r.top > window.innerHeight * 0.7) node.scrollIntoView({ behavior: reduceMotion() ? "auto" : "smooth", block: "start" });
}

// ---------------------------------------------------------------- routing
const views = ["intake", "control", "impact"];
const loaded = {};
function route() {
  const v = views.includes(location.hash.slice(1)) ? location.hash.slice(1) : views[0];
  views.forEach((n) => { $("view-" + n).hidden = n !== v; });
  document.querySelectorAll("#nav a").forEach((a) => {
    const on = a.dataset.view === v;
    a.classList.toggle("on", on);
    if (on) a.setAttribute("aria-current", "page"); else a.removeAttribute("aria-current");
  });
  showError(null);
  window.scrollTo(0, 0);
  if (!loaded[v]) { loaded[v] = true; ({ intake: initIntake, control: () => loadControl(), impact: loadImpact })[v](); }
}
window.addEventListener("hashchange", route);
// a file dropped outside the drop zone must not make the browser leave the page
["dragover", "drop"].forEach((t) => window.addEventListener(t, (e) => e.preventDefault()));

// ---------------------------------------------------------------- intake
let tesseract = false;
let lastFile = null;   // {name, body} of the last dropped file, for the live reader
let busy = false;      // one reading at a time: a second drop or click is ignored until the first has answered

function setBusy(on) {
  busy = on;
  const d = $("drop");
  d.classList.toggle("is-busy", on);
  d.setAttribute("aria-busy", on ? "true" : "false");
  $("file").disabled = on;
  $("pickgo").disabled = on || !$("sample").options.length;
  $("card-area").setAttribute("aria-busy", on ? "true" : "false");
}

async function initIntake() {
  const sel = $("sample");
  try {
    const [meta, samples] = await Promise.all([api("/api/meta"), api("/api/samples")]);
    tesseract = meta.tesseract;
    samples.forEach((s) => sel.appendChild(el("option", "", s.file + "  (" + s.bill_type.replace("_", " ") + ")")));
    sel.dataset.files = JSON.stringify(samples.map((s) => s.file));
  } catch (e) { showError(e); }
  $("pickgo").disabled = !sel.options.length;
  $("pickgo").onclick = () => {
    if (busy) return;
    const files = JSON.parse($("sample").dataset.files || "[]");
    const f = files[$("sample").selectedIndex];
    if (f) intake({ sample: f });
  };
  $("file").onchange = (ev) => {
    const f = ev.target.files[0];
    ev.target.value = "";   // so choosing the same file again still counts
    if (f) dropped(f);
  };
  const d = $("drop");
  ["dragenter", "dragover"].forEach((t) => d.addEventListener(t, (e) => { e.preventDefault(); if (!busy) d.classList.add("over"); }));
  d.addEventListener("dragleave", (e) => { e.preventDefault(); if (!d.contains(e.relatedTarget)) d.classList.remove("over"); });
  d.addEventListener("drop", (e) => { e.preventDefault(); d.classList.remove("over"); if (e.dataTransfer.files[0]) dropped(e.dataTransfer.files[0]); });
  // the whole zone opens the file picker: a click on its background, or Enter or Space while it has focus
  const choose = () => { if (!busy) $("file").click(); };
  d.addEventListener("click", (e) => { if (!e.target.closest("label, input, button, select, a")) choose(); });
  d.addEventListener("keydown", (e) => { if (e.target === d && (e.key === "Enter" || e.key === " ")) { e.preventDefault(); choose(); } });
}

async function dropped(file) { if (busy) return; lastFile = { name: file.name, body: file }; intake({ file }); }

async function intake({ file, sample, live }) {
  if (busy) return;
  const area = $("card-area");
  clear(area);
  area.appendChild(loading(live ? "Reading the file with Tesseract. A packet can take several seconds." : "Reading the stored extraction.", "card"));
  showError(null);
  setBusy(true);
  try {
    let url = live ? "/api/intake/live" : "/api/intake", opts = { method: "POST", headers: {} };
    if (sample) url += "?sample=" + encodeURIComponent(sample);
    else if (file) { opts.headers["X-Filename"] = file.name; opts.body = file; }
    else if (lastFile) { opts.headers["X-Filename"] = lastFile.name; opts.body = lastFile.body; }
    const c = await api(url, opts);
    if (sample) lastFile = { name: sample, sample: true };
    renderCard(c);
    reveal(area);
  } catch (e) { clear(area); showError(e); }
  finally { setBusy(false); }
}

// How the verdict looks, by route: a tone, an icon and a short status word. The headline and the sentence under it come from the server.
const TONE = {
  "auto-clear": ["ok", "check-circle", "Cleared"],
  "human-look": ["info", "eye", "Needs human review"],
  "resend": ["warn", "alert", "Needs attention"],
  "fix-before-sending": ["warn", "alert", "Needs attention"],
  "fix-internal": ["warn", "alert", "Needs attention"],
};
const TONE_OTHER = ["neutral", "info", "Verdict"];
const SRC_ICON = { stored: "file", live: "refresh", human_review: "edit" };

function verdictBox(tone, ico, tag, headline, sub) {
  const box = el("div", "verdict-box tone-" + tone);
  return add(box, add(el("div", "verdict-ico"), icon(ico)), add(el("div", "verdict-text"), el("p", "verdict-tag", tag), el("div", "verdict", headline), el("p", "verdict-sub", sub)));
}

function renderCard(c) {
  const area = $("card-area");
  clear(area);
  const art = el("article", "card cols");
  const card = el("div", "col-main");
  const side = el("aside", "col-side");
  side.setAttribute("aria-label", "Messages for this bill");
  add(art, card, side);
  if (c.no_stored) {
    art.classList.remove("cols");
    const blk = add(el("div", "blk"), el("p", "reading", c.reading_label), verdictBox("neutral", "file", "No verdict", "No stored reading", c.message));
    if (c.tesseract) add(blk, add(el("div", "live-row"), liveButton()));
    card.appendChild(blk);
    return area.appendChild(art);
  }
  const srcWords = { stored: "Simulated reading, stored", live: "Live reading, Tesseract", human_review: "Typed by a person, then checked again" };
  const head = el("div", "blk");
  const how = el("div", "how");
  how.hidden = true;
  how.id = "how-read";
  add(how, el("p", "", c.reading_label), c.vision_label ? el("p", "", c.vision_label) : null, el("p", "", c.review_note),
    el("p", "", c.file + " · " + (c.doc_type === "credit_note" ? "credit note · " : "") + c.bill_type.replace("_", " ") + " · read in " + c.seconds + " s"));
  const howLink = el("button", "link-btn", "How was this read?");
  howLink.type = "button";
  howLink.setAttribute("aria-expanded", "false");
  howLink.setAttribute("aria-controls", how.id);
  howLink.onclick = () => { how.hidden = !how.hidden; howLink.setAttribute("aria-expanded", String(!how.hidden)); };
  const src = srcWords[c.source] ? c.source : "stored";
  const tone = TONE[c.route] || TONE_OTHER;
  add(head, add(el("div", "read-line"), add(el("span", "src"), icon(SRC_ICON[src]), el("span", "", srcWords[src])), el("span", "file", c.file), howLink), how,
    verdictBox(tone[0], tone[1], tone[2], c.headline, c.sub));
  card.appendChild(head);
  if (c.saved) card.appendChild(add(el("div", "blk"), add(el("p", "saved"), icon("check-circle"), el("span", "", c.saved.message))));

  const ib = el("section", "blk");
  ib.setAttribute("aria-labelledby", "h-issues");
  const h2a = el("h2", "", "The issues that matter");
  h2a.id = "h-issues";
  add(ib, add(el("div", "blk-title"), h2a, c.issues.length ? el("span", "count", nf.format(c.issues.length)) : null));
  if (!c.issues.length) ib.appendChild(add(el("p", c.route === "auto-clear" ? "empty tone-ok" : "empty"), icon("check-circle"), el("span", "", "Nothing to fix at intake.")));
  const ul = el("ol", "issues");
  c.issues.forEach((it, i) => {
    const li = el("li", "issue kind-" + (it.kind || "fail"));
    const n = el("div", "n", String(i + 1));
    n.setAttribute("aria-hidden", "true");
    add(li, n, add(el("div"), el("p", "t", it.title), add(el("span", "who"), icon("user"), el("span", "", "Who must fix: " + it.who)), el("p", "d", it.detail)));
    ul.appendChild(li);
  });
  if (c.issues.length) ib.appendChild(ul);
  if (c.more_issues) ib.appendChild(el("p", "muted small more", c.more_issues + " more flagged: see the checks."));
  card.appendChild(ib);

  if (c.not_run && c.not_run.length) {
    const nrd = el("details", "fold");
    nrd.appendChild(add(el("summary"), el("span", "", "Checks that could not run"), el("span", "count", nf.format(c.not_run.length))));
    const nl = el("ul", "rows");
    c.not_run.forEach((n) => add(nl, add(el("li", "row compact"), add(el("div"), el("div", "who", n.title), el("div", "meta", "Needs: " + n.needs.join(", "))))));
    nrd.appendChild(add(el("div", "fold-body"), nl));
    card.appendChild(nrd);
  }
  const det = el("details", "fold");
  const sum = add(el("summary"), el("span", "", "What was read"));
  det.appendChild(sum);
  let anyNeeds = false, needCount = 0;
  const grid = el("div", "fields");
  const typed = {};
  c.fields.forEach((f) => {
    const needsPerson = f.state === "unread" || f.state === "differ";
    if (needsPerson) { anyNeeds = true; needCount += 1; }
    const cell = el("div", "field st-" + f.state + (needsPerson ? " unread" : ""));
    const k = el(needsPerson ? "label" : "div", "k", f.name);
    if (f.state === "ok") k.insertBefore(icon("check"), k.firstChild);
    add(cell, k, el("div", "v", f.value));
    if (needsPerson) {
      const inp = el("input", "typein");
      inp.type = "text"; inp.placeholder = "type it here"; inp.setAttribute("aria-label", f.name);
      inp.id = "typein-" + f.key;
      k.htmlFor = inp.id;
      typed[f.key] = inp;
      add(cell, add(el("span", "flag"), icon("alert"), el("span", "", f.state === "differ" ? "the two readers differ: needs human review" : "not read: needs human review")));
      if (f.cross) {
        const side = el("div", "sidebyside");
        const pick = (who, val) => {
          const b = el("button", "pick", "Use this");
          b.type = "button";
          b.onclick = () => { inp.value = val; inp.focus(); };
          return add(el("div", "col"), el("div", "who", who), el("div", "val", val), val === "not read" ? el("span") : b);
        };
        if (f.cross.state === "differ") add(side, pick("Tesseract", f.cross.tesseract), pick("Stored vision reading", f.cross.vision));
        else add(side, pick("Stored vision reading (suggestion only)", f.cross.vision));
        cell.appendChild(side);
      }
      cell.appendChild(inp);
    } else if (f.state === "typed") add(cell, add(el("span", "flag"), icon("edit"), el("span", "", "typed by a person")));
    else if (f.state !== "ok") add(cell, add(el("span", "flag"), icon("eye"), el("span", "", f.note || "needs human review")));
    if (f.cross && f.cross.state === "agree" && !needsPerson) cell.appendChild(add(el("span", "agree"), icon("check"), el("span", "", "two readers agree")));
    if (f.cross && f.cross.state === "vision_confirms" && !needsPerson) cell.appendChild(add(el("span", "agree"), icon("check"), el("span", "", "vision reading matches the vendor master")));
    grid.appendChild(cell);
  });
  if (needCount) sum.appendChild(el("span", "count count-warn", "Needs review: " + nf.format(needCount)));
  det.appendChild(add(el("div", "fold-body"), grid));
  det.open = anyNeeds;
  card.appendChild(det);
  if (Object.keys(typed).length && c.key) {
    const rv = el("section", "blk review");
    rv.setAttribute("aria-labelledby", "h-review");
    const h = el("h2", "", "Run the checks again");
    h.id = "h-review";
    const form = el("form", "review-form");
    form.noValidate = true;
    const go = el("button", "btn", "Run the checks again with my entries");
    go.type = "submit";
    const who = el("input", "typein who");
    who.type = "text"; who.placeholder = "your name"; who.setAttribute("aria-label", "your name, so the entry can be traced");
    who.id = "reviewer";
    who.required = true;
    try { who.value = localStorage.getItem("reviewer") || ""; } catch (e) { /* storage may be blocked */ }
    const lab = add(el("label", "field-label", "Your name "), el("span", "req", "(required, so the entry can be traced)"));
    lab.htmlFor = who.id;
    const msg = el("p", "form-msg");
    msg.setAttribute("role", "status");
    const fail = (t) => { msg.textContent = t; msg.classList.add("is-error"); };
    form.onsubmit = async (ev) => {
      ev.preventDefault();
      if (go.disabled) return;
      msg.classList.remove("is-error");
      who.removeAttribute("aria-invalid");
      const values = {};
      Object.entries(typed).forEach(([k, i]) => { if (i.value.trim()) values[k] = i.value.trim(); });
      if (!Object.keys(values).length) { fail(" Type at least one value first."); det.open = true; Object.values(typed)[0].focus(); return; }
      if (!who.value.trim()) { fail(" Type your name first, so the entry can be traced."); who.setAttribute("aria-invalid", "true"); who.focus(); return; }
      try { localStorage.setItem("reviewer", who.value.trim()); } catch (e) { /* storage may be blocked */ }
      go.disabled = true;
      form.setAttribute("aria-busy", "true");
      try {
        msg.textContent = " Checking.";
        const r = await api("/api/intake/review", { method: "POST", body: JSON.stringify({ key: c.key, values, reviewer: who.value.trim() }) });
        renderCard(r);
        reveal(area);
      } catch (e) { fail(" " + e.message); }
      finally { go.disabled = false; form.removeAttribute("aria-busy"); }
    };
    // Enter in a typed field runs the checks, as it does in the name field
    Object.values(typed).forEach((i) => i.addEventListener("keydown", (e) => { if (e.key === "Enter") { e.preventDefault(); form.requestSubmit(); } }));
    add(form, add(el("div"), lab, who), go);
    add(rv, h, el("p", "muted small", "Type the values that were not read in the fields above, add your name, then run the checks again. The entry is saved with your name."), form, msg);
    card.appendChild(rv);
  }
  const toVendor = c.messages.filter((m) => m.channel.startsWith("WhatsApp"));
  const others = c.messages.filter((m) => !m.channel.startsWith("WhatsApp"));
  const s1 = add(el("section", "side-sec"), add(el("h2", "side-h"), icon("chat"), el("span", "", "Message to the vendor")), phone(c, toVendor));
  const ob = el("div", "outbox");
  ob.appendChild(add(el("p", "note"), icon("lock"), el("span", "", c.outbox_note)));
  if (!others.length) ob.appendChild(el("p", "muted small", "No task or other message is needed."));
  others.forEach((m) => {
    const wrap = el("div", "msg");
    add(wrap, el("div", "to", "To " + m.to + " · " + m.channel), el("div", "bubble", m.text));
    ob.appendChild(wrap);
  });
  const s2 = add(el("section", "side-sec"), add(el("h2", "side-h"), icon("send"), el("span", "", "Ready to send")), ob);
  add(side, s1, s2);
  if (c.source !== "live" && tesseract && lastFile) add(side, add(el("div", "live-row"), liveButton()));
  area.appendChild(art);
}

// A phone-style chat with the vendor. Simulated: nothing is sent. The drafted message is shown in English or Hindi; "Vendor replies with a photo" reads the photo
// (the stored reading, or Tesseract when it is installed), re-runs the checks, and the answer is posted back to the thread in plain words.
function phone(c, msgs) {
  let lang = "en";
  let sending = false;
  const items = msgs.map((m) => ({ who: "company", en: m.text, hi: m.hi || m.text }));
  const wrap = el("div", "phone");
  const name = (msgs[0] && msgs[0].to) || "Vendor";
  const avatar = el("div", "phone-avatar", name.trim().charAt(0).toUpperCase() || "V");
  avatar.setAttribute("aria-hidden", "true");
  const top = add(el("div", "phone-top"), avatar, add(el("div"), el("div", "phone-name", name), el("div", "phone-sim", c.chat_note)));
  const seg = el("div", "lang");
  seg.setAttribute("role", "group");
  seg.setAttribute("aria-label", "Language of the message");
  const bEn = el("button", "on", "English"), bHi = el("button", "", "हिन्दी");
  bHi.lang = "hi";
  [bEn, bHi].forEach((b) => { b.type = "button"; });
  add(seg, bEn, bHi);
  const log = el("div", "phone-log");
  log.setAttribute("role", "log");
  log.setAttribute("aria-label", "Simulated chat with the vendor");
  log.tabIndex = 0;
  const note = el("p", "phone-note");
  note.hidden = true;
  const render = () => {
    clear(log);
    if (!items.length) log.appendChild(el("p", "phone-empty", "No message to the vendor is needed."));
    items.forEach((it) => {
      const b = el("div", "chat " + it.who);
      if (lang === "hi") b.lang = "hi";
      if (it.thumb) { const im = el("img", "thumb"); im.src = it.thumb; im.alt = "the photo the vendor sent"; b.appendChild(im); }
      b.appendChild(el("div", "t", lang === "hi" ? it.hi : it.en));
      if (it.card) {
        const open = el("button", "pick", lang === "hi" ? "इस जवाब का पूरा कार्ड खोलें" : "Open the full card for this reply");
        open.type = "button";
        open.onclick = () => { renderCard(it.card); reveal($("card-area")); };
        b.appendChild(open);
      }
      log.appendChild(b);
    });
    if (sending) {
      const dots = add(el("div", "chat company typing"), el("span"), el("span"), el("span"));
      dots.setAttribute("aria-hidden", "true");
      log.appendChild(dots);
    }
    log.scrollTop = log.scrollHeight;
    bEn.classList.toggle("on", lang === "en");
    bHi.classList.toggle("on", lang === "hi");
    bEn.setAttribute("aria-pressed", String(lang === "en"));
    bHi.setAttribute("aria-pressed", String(lang === "hi"));
    note.hidden = lang !== "hi";
    note.textContent = c.hindi_note;
  };
  bEn.onclick = () => { lang = "en"; render(); };
  bHi.onclick = () => { lang = "hi"; render(); };
  add(top, seg);
  add(wrap, top, log, note);
  const msg = el("span", "small muted send-msg");
  msg.setAttribute("role", "status");
  const send = async (label, thumb, url, opts) => {
    if (sending) return;
    sending = true;
    go.disabled = true; sel.disabled = true;
    items.push({ who: "vendor", en: "Photo: " + label, hi: "फ़ोटो: " + label, thumb });
    render();
    msg.classList.remove("is-error");
    msg.textContent = " Reading the photo.";
    try {
      const r = await api(url, opts);
      items.push({ who: "company", en: r.reply.en, hi: r.reply.hi, card: r.card });
      msg.textContent = "";
    } catch (e) { msg.textContent = " " + e.message; msg.classList.add("is-error"); items.pop(); }
    sending = false;
    go.disabled = false; sel.disabled = false;
    render();
  };
  const file = el("input");
  file.type = "file"; file.accept = "image/*,.pdf"; file.hidden = true;
  file.onchange = () => {
    const f = file.files[0];
    if (!f) return;
    send(f.name, f.type.startsWith("image/") ? URL.createObjectURL(f) : null, "/api/intake/reply", { method: "POST", headers: { "X-Filename": f.name }, body: f });
    file.value = "";
  };
  const go = add(el("button", "btn quiet"), icon("camera"), el("span", "", "Vendor replies with a photo"));
  go.type = "button";
  go.onclick = () => file.click();
  const sel = el("select");
  sel.setAttribute("aria-label", "or reply with a sample bill");
  sel.appendChild(el("option", "", "or reply with a sample bill"));
  JSON.parse($("sample").dataset.files || "[]").forEach((f) => sel.appendChild(el("option", "", f)));
  sel.onchange = () => {
    if (sel.selectedIndex < 1) return;
    const f = sel.value;
    sel.selectedIndex = 0;
    send(f, null, "/api/intake/reply?sample=" + encodeURIComponent(f), { method: "POST" });
  };
  add(wrap, add(el("div", "phone-send"), go, sel, msg), file);
  render();
  return wrap;
}

function liveButton() {
  const b = add(el("button", "btn quiet"), icon("refresh"), el("span", "", "Run live reader"));
  b.type = "button";
  b.onclick = () => intake({ live: true, sample: lastFile && lastFile.sample ? lastFile.name : undefined });
  return b;
}

// ---------------------------------------------------------------- control tower
const nf = new Intl.NumberFormat("en-IN");
let cutoffNow = null;
let controlBusy = false;
async function loadControl(cutoff) {
  if (controlBusy) return;
  controlBusy = true;
  const body = $("control-body");
  const seg = $("cutoff");
  const refocus = seg.contains(document.activeElement);
  // the first load shows a loading line; a change of scenario keeps the current figures, dimmed, until the new ones arrive
  if (cutoffNow === null) { clear(body); body.appendChild(loading("Loading the register.")); }
  else { body.classList.add("is-updating"); seg.classList.add("is-loading"); }
  body.setAttribute("aria-busy", "true");
  try {
    const d = await api("/api/control" + (cutoff === undefined ? "" : "?cutoff=" + cutoff));
    cutoffNow = d.cutoff;
    $("control-as").textContent = "As of " + d.as_of + ".";
    clear(seg);
    d.scenarios.forEach((s) => {
      const on = s.cutoff === d.cutoff;
      const b = el("button", on ? "sc-opt on" : "sc-opt");
      b.type = "button";
      b.setAttribute("role", "radio");
      b.setAttribute("aria-checked", on ? "true" : "false");
      b.tabIndex = on ? 0 : -1;
      add(b, el("span", "sc-dot"), el("span", "sc-label", s.label), el("span", "sc-case", s.case));
      b.onclick = () => { if (s.cutoff !== cutoffNow) loadControl(s.cutoff); };
      seg.appendChild(b);
    });
    $("sc-effect").textContent = d.effect;
    renderControl(d);
    if (refocus) { const on = seg.querySelector("[aria-checked=true]"); if (on) on.focus(); }
  } catch (e) { clear(body); showError(e); }
  finally {
    controlBusy = false;
    body.classList.remove("is-updating");
    seg.classList.remove("is-loading");
    body.removeAttribute("aria-busy");
  }
}
// arrow keys move between the three cases, as in any radio group
$("cutoff").addEventListener("keydown", (e) => {
  const step = { ArrowRight: 1, ArrowDown: 1, ArrowLeft: -1, ArrowUp: -1 }[e.key];
  if (!step && e.key !== "Home" && e.key !== "End") return;
  const opts = [...e.currentTarget.querySelectorAll("[role=radio]")];
  if (!opts.length) return;
  e.preventDefault();
  const i = opts.indexOf(document.activeElement);
  const j = e.key === "Home" ? 0 : e.key === "End" ? opts.length - 1 : (i + step + opts.length) % opts.length;
  opts[j].focus();
  opts[j].click();
});

// A list that shows its first few rows and a "Show all" link for the rest. `preview` comes from the server (layout only).
function section(parent, title, id, items, build, preview, note) {
  const body = el("section", "sec");
  body.setAttribute("aria-labelledby", id);
  parent.appendChild(body);
  const h = el("h2", "", title);
  h.id = id;
  const head = add(el("div", "sec-head"), h);
  const list = el("ul", "rows");
  list.id = id + "-list";
  items.forEach((x, i) => { const li = build(x); li.hidden = i >= preview; list.appendChild(li); });
  if (items.length > preview) {
    const more = el("button", "chip-btn", "Show all " + nf.format(items.length));
    more.type = "button";
    more.setAttribute("aria-expanded", "false");
    more.setAttribute("aria-controls", list.id);
    let open = false;
    more.onclick = () => {
      open = !open;
      [...list.children].forEach((li, i) => { li.hidden = !open && i >= preview; });
      more.textContent = open ? "Show fewer" : "Show all " + nf.format(items.length);
      more.setAttribute("aria-expanded", String(open));
    };
    head.appendChild(more);
  }
  body.appendChild(head);
  if (note) body.appendChild(el("p", "muted small sec-note", note));
  if (!items.length) body.appendChild(el("p", "muted small empty-list", "Nothing in this list."));
  body.appendChild(list);
}

function stat(num, lab, miss, extra) { return add(el("div", miss ? "stat miss" : "stat"), el("div", miss ? "num miss" : "num", nf.format(num)), el("div", "lab", lab), extra ? el("div", "lab extra", extra) : null); }

function renderControl(d) {
  const body = $("control-body");
  clear(body);
  const h = d.headline;
  add(body, add(el("div", "stats"), stat(h.late, d.labels.late, true), stat(h.miss, d.labels.miss, true), stat(h.waiting, d.labels.waiting), stat(h.dry, d.labels.dry, false, d.labels.dry_extra)));
  const pv = d.preview;
  const lists = el("div", "lists-two");
  body.appendChild(lists);
  section(lists, "The oldest bills", "s-oldest", d.oldest, (b) => {
    const li = el("li", b.miss ? "row compact miss" : "row compact");
    const who = add(el("div", "who", b.vendor), el("span", "meta", " " + b.bill_id + " · " + b.amount));
    if (b.miss) who.appendChild(el("span", "tag tag-miss", "Misses its deadline"));
    const left = add(el("div"), who, el("div", "meta", "Stuck: " + b.stuck + (b.reason ? " (" + b.reason + ")" : "") + " · Next move: " + (b.owner || "none")));
    const right = el("div", "big", nf.format(b.days));
    right.appendChild(el("small", "", "days"));
    add(li, left, right);
    return li;
  }, pv);

  section(lists, "Micro and Small bills closest to the limit", "s-msme", d.msme, (b) => {
    const li = el("li", b.miss ? "row miss" : "row");
    const whoRow = add(el("div"), el("span", "who", b.vendor), el("span", "meta", " " + b.bill_id + " · " + b.amount));
    if (b.unknown) whoRow.appendChild(el("span", "tag", "status unknown"));
    if (b.miss) whoRow.appendChild(el("span", "tag tag-miss", "Will miss the limit"));
    const left = add(el("div"), whoRow, el("div", "meta", b.stage + " · next move: " + (b.owner || "none")),
      el("div", "meta", b.runs_left ? nf.format(b.runs_left) + " payment run(s) left" + (b.last_run ? ", the last on " + b.last_run : "") : "No payment run left before the limit"));
    const right = el("div", "big", nf.format(b.days_left));
    right.appendChild(el("small", "", "days left"));
    add(li, left, right);
    return li;
  }, pv);

  const pickBox = el("section", "sec");
  pickBox.setAttribute("aria-labelledby", "s-pick");
  lists.appendChild(pickBox);
  const h2p = el("h2", "", "Pick order across the AP clerks"); h2p.id = "s-pick"; pickBox.appendChild(add(el("div", "sec-head"), h2p));
  const cl = el("div", "clerks");
  d.clerks.forEach((c) => {
    add(cl, add(el("div", "clerk"), el("div", "name", c.clerk), el("div", "num", "+" + nf.format(c.new)), el("div", "cap", nf.format(c.after) + " in hand after, from " + nf.format(c.in_hand)),
      el("div", "cap", nf.format(c.queries) + " query follow-ups"), c.first ? el("div", "cap", "Starts with " + c.first) : null));
  });
  pickBox.appendChild(cl);
  pickBox.appendChild(el("p", "muted small sec-foot", d.spread_pct === null ? "" : "Highest load is " + d.spread_pct + " per cent above the lowest after the order. The live queue holds " + nf.format(d.live_waiting) + " waiting bills."));

  section(lists, "Work orders likely to run dry, biggest billing first", "s-dry", d.dry, (x) => {
    const li = el("li", "row");
    const right = el("div", "big", nf.format(x.days));
    right.appendChild(el("small", "", "days of balance left"));
    add(li, add(el("div"), el("div", "who", "Work order " + x.wo_id + " · " + x.vendor), el("div", "meta", x.property + " · bills about " + x.burn + " a month, last quarter · balance left " + x.balance + " · ends in " + nf.format(x.expires) + " days" + (x.vendor_waiting ? " · this vendor has a bill waiting" : ""))), right);
    return li;
  }, pv, d.labels.dry_note);
}

// ---------------------------------------------------------------- impact
// A small "?" beside a figure. Hover or focus shows where the figure comes from (the file and the ids in notes/numbers.md); the text is sent by the server.
// The tip is nudged sideways, or below, so it never runs off the window.
function sourceTip(text) {
  const q = el("span", "q", "?");
  q.tabIndex = 0;
  q.setAttribute("role", "note");
  q.setAttribute("aria-label", "Source: " + text);
  q.dataset.tip = "Source: " + text;
  const place = () => {
    const r = q.getBoundingClientRect();
    const vw = document.documentElement.clientWidth;
    const w = Math.min(300, vw - 32);
    const mid = r.left + r.width / 2;
    let shift = 0;
    if (mid - w / 2 < 16) shift = 16 - (mid - w / 2);
    else if (mid + w / 2 > vw - 16) shift = vw - 16 - (mid + w / 2);
    q.style.setProperty("--tip-w", w + "px");
    q.style.setProperty("--tip-shift", shift + "px");
    q.classList.toggle("below", r.top < 240);
  };
  q.addEventListener("mouseenter", place);
  q.addEventListener("focus", place);
  q.addEventListener("keydown", (e) => { if (e.key === "Escape") q.blur(); });
  return q;
}

async function loadImpact() {
  const body = $("impact-body");
  body.appendChild(loading("Loading the backtest."));
  try {
    const d = await api("/api/impact");
    $("impact-label").textContent = d.label + " " + d.reading_note;
    clear(body);
    const cases = el("details", "fold panel");
    add(cases, add(el("summary"), el("span", "", "How the best, middle and worst case are set")), add(el("div", "fold-body"), el("p", "muted small", d.low_middle_high)));
    body.appendChild(el("h2", "", "Before and after"));
    const metrics = el("div", "metrics");
    body.appendChild(metrics);
    d.headline.forEach((m) => {
      const box = el("article", "metric");
      const after = el("div", "after", m.after);
      after.appendChild(el("small", "", " " + m.unit + " after"));
      add(box, add(el("div", "name"), el("span", "", m.name), sourceTip(m.source)), after, el("div", "before", m.sentence.charAt(0).toUpperCase() + m.sentence.slice(1) + "."));
      const s = m.scale, span = s.max || 1;
      const track = el("div", "bar-track");
      track.setAttribute("aria-hidden", "true");
      const fill = el("div", "bar-fill");
      fill.style.left = (100 * Math.min(s.lo, s.hi) / span) + "%";
      fill.style.width = Math.max(1.2, 100 * Math.abs(s.hi - s.lo) / span) + "%";
      const mark = el("div", "bar-mark");
      mark.style.left = (100 * s.before / span) + "%";
      add(track, fill, mark);
      const cap = el("div", "bar-cap");
      cap.setAttribute("aria-hidden", "true");
      add(cap, el("span", "key key-fill", "with the changes"), el("span", "key key-mark", "today"));
      const cond = add(el("div", "cond"), add(el("div", "cond-label"), icon("info"), el("span", "", "Condition")), el("p", "", m.condition));
      add(box, add(el("div", "metric-foot"), track, cap, cond));
      metrics.appendChild(box);
    });
    body.appendChild(el("h2", "", "The three changes, one at a time"));
    const ul = el("ul", "levers");
    d.levers.forEach((l) => {
      const big = el("div", "big", l.days);
      big.appendChild(el("small", "", "days off the average, worst to best case"));
      add(ul, add(el("li", "lever"), add(el("div", "who"), el("span", "", l.title), sourceTip(l.source)), big, el("p", "says", l.sentence), el("div", "meta", l.condition)));
    });
    body.appendChild(ul);
    body.appendChild(add(el("div", "line-note"), icon("info"), el("p", "", d.intake_line)));
    body.appendChild(cases);
  } catch (e) { clear(body); showError(e); }
}

route();
