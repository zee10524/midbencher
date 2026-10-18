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
function showError(e) { const p = $("err"); p.hidden = !e; p.textContent = e ? String(e.message || e) : ""; }
function clear(node) { while (node.firstChild) node.removeChild(node.firstChild); }

// ---------------------------------------------------------------- routing
const views = ["intake", "control", "impact"];
const loaded = {};
function route() {
  const v = views.includes(location.hash.slice(1)) ? location.hash.slice(1) : views[0];
  views.forEach((n) => { $("view-" + n).hidden = n !== v; });
  document.querySelectorAll("#nav a").forEach((a) => a.classList.toggle("on", a.dataset.view === v));
  showError(null);
  window.scrollTo(0, 0);
  if (!loaded[v]) { loaded[v] = true; ({ intake: initIntake, control: () => loadControl(), impact: loadImpact })[v](); }
}
window.addEventListener("hashchange", route);

// ---------------------------------------------------------------- intake
let tesseract = false;
let lastFile = null;   // {name, body} of the last dropped file, for the live reader

async function initIntake() {
  try {
    const [meta, samples] = await Promise.all([api("/api/meta"), api("/api/samples")]);
    tesseract = meta.tesseract;
    const sel = $("sample");
    samples.forEach((s) => sel.appendChild(el("option", "", s.file + "  (" + s.bill_type.replace("_", " ") + ")")));
    sel.dataset.files = JSON.stringify(samples.map((s) => s.file));
  } catch (e) { showError(e); }
  $("pickgo").onclick = () => {
    const files = JSON.parse($("sample").dataset.files || "[]");
    const f = files[$("sample").selectedIndex];
    if (f) intake({ sample: f });
  };
  $("file").onchange = (ev) => { if (ev.target.files[0]) dropped(ev.target.files[0]); };
  const d = $("drop");
  ["dragenter", "dragover"].forEach((t) => d.addEventListener(t, (e) => { e.preventDefault(); d.classList.add("over"); }));
  ["dragleave", "drop"].forEach((t) => d.addEventListener(t, (e) => { e.preventDefault(); d.classList.remove("over"); }));
  d.addEventListener("drop", (e) => { if (e.dataTransfer.files[0]) dropped(e.dataTransfer.files[0]); });
}

async function dropped(file) { lastFile = { name: file.name, body: file }; intake({ file }); }

async function intake({ file, sample, live }) {
  const area = $("card-area");
  clear(area);
  area.appendChild(el("p", "muted card", live ? "Reading the file with Tesseract. A packet can take several seconds." : "Reading the stored extraction."));
  showError(null);
  try {
    let url = live ? "/api/intake/live" : "/api/intake", opts = { method: "POST", headers: {} };
    if (sample) url += "?sample=" + encodeURIComponent(sample);
    else if (file) { opts.headers["X-Filename"] = file.name; opts.body = file; }
    else if (lastFile) { opts.headers["X-Filename"] = lastFile.name; opts.body = lastFile.body; }
    const c = await api(url, opts);
    if (sample) lastFile = { name: sample, sample: true };
    renderCard(c);
  } catch (e) { clear(area); showError(e); }
}

function renderCard(c) {
  const area = $("card-area");
  clear(area);
  const art = el("article", "card cols");
  const card = el("div", "col-main");
  const side = el("aside", "col-side");
  add(art, card, side);
  if (c.no_stored) {
    art.classList.remove("cols");
    add(card, el("p", "reading", c.reading_label), el("div", "verdict", "No stored reading"), el("p", "verdict-sub", c.message));
    if (c.tesseract) add(card, liveButton());
    return area.appendChild(art);
  }
  const srcWords = { stored: "Simulated reading, stored", live: "Live reading, Tesseract", human_review: "Typed by a person, then checked again" };
  const how = el("div", "how");
  how.hidden = true;
  add(how, el("p", "", c.reading_label), c.vision_label ? el("p", "", c.vision_label) : null, el("p", "", c.review_note),
    el("p", "", c.file + " · " + (c.doc_type === "credit_note" ? "credit note · " : "") + c.bill_type.replace("_", " ") + " · read in " + c.seconds + " s"));
  const howLink = el("button", "link-btn", "How was this read?");
  howLink.type = "button";
  howLink.onclick = () => { how.hidden = !how.hidden; };
  add(card, add(el("div", "read-line"), el("span", "src", srcWords[c.source] || srcWords.stored), el("span", "", c.file), howLink), how,
    el("div", "verdict", c.headline), el("p", "verdict-sub", c.sub));
  const h2a = el("h2", "", "The issues that matter");
  card.appendChild(h2a);
  if (!c.issues.length) card.appendChild(el("p", "muted", "Nothing to fix at intake."));
  const ul = el("ol", "issues");
  c.issues.forEach((it, i) => {
    const li = el("li", "issue");
    add(li, el("div", "n", String(i + 1)), add(el("div"), el("p", "t", it.title), el("span", "who", "Who must fix: " + it.who), el("p", "d", it.detail)));
    ul.appendChild(li);
  });
  card.appendChild(ul);
  if (c.more_issues) card.appendChild(el("p", "muted small", c.more_issues + " more flagged: see the checks."));
  if (c.not_run && c.not_run.length) {
    const nrd = el("details", "fold");
    nrd.appendChild(el("summary", "", "Checks that could not run: " + nf.format(c.not_run.length)));
    const nl = el("ul", "rows");
    c.not_run.forEach((n) => add(nl, add(el("li", "row compact"), add(el("div"), el("div", "who", n.title), el("div", "meta", "Needs: " + n.needs.join(", "))))));
    nrd.appendChild(nl);
    card.appendChild(nrd);
  }
  const det = el("details", "fold");
  det.appendChild(el("summary", "", "What was read"));
  let anyNeeds = false;
  const grid = el("div", "fields");
  const typed = {};
  c.fields.forEach((f) => {
    const needsPerson = f.state === "unread" || f.state === "differ";
    if (needsPerson) anyNeeds = true;
    const cell = el("div", needsPerson ? "unread" : "");
    add(cell, el("div", "k", f.name), el("div", "v", f.value));
    if (needsPerson) {
      const inp = el("input", "typein");
      inp.type = "text"; inp.placeholder = "type it here"; inp.setAttribute("aria-label", f.name);
      typed[f.key] = inp;
      add(cell, el("span", "flag", f.state === "differ" ? "the two readers differ: needs human review" : "not read: needs human review"));
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
    } else if (f.state === "typed") add(cell, el("span", "flag", "typed by a person"));
    else if (f.state !== "ok") add(cell, el("span", "flag", f.note || "needs human review"));
    if (f.cross && f.cross.state === "agree" && !needsPerson) cell.appendChild(el("span", "agree", "two readers agree"));
    if (f.cross && f.cross.state === "vision_confirms" && !needsPerson) cell.appendChild(el("span", "agree", "vision reading matches the vendor master"));
    grid.appendChild(cell);
  });
  det.appendChild(grid);
  det.open = anyNeeds;
  card.appendChild(det);
  if (Object.keys(typed).length && c.key) {
    const go = el("button", "btn quiet", "Run the checks again with my entries");
    const who = el("input", "typein who");
    who.type = "text"; who.placeholder = "your name"; who.setAttribute("aria-label", "your name, so the entry can be traced");
    try { who.value = localStorage.getItem("reviewer") || ""; } catch (e) { /* storage may be blocked */ }
    const msg = el("span", "small muted");
    go.onclick = async () => {
      const values = {};
      Object.entries(typed).forEach(([k, i]) => { if (i.value.trim()) values[k] = i.value.trim(); });
      if (!Object.keys(values).length) { msg.textContent = " Type at least one value first."; return; }
      if (!who.value.trim()) { msg.textContent = " Type your name first, so the entry can be traced."; return; }
      try { localStorage.setItem("reviewer", who.value.trim()); } catch (e) { /* storage may be blocked */ }
      try {
        msg.textContent = " Checking.";
        const r = await api("/api/intake/review", { method: "POST", body: JSON.stringify({ key: c.key, values, reviewer: who.value.trim() }) });
        renderCard(r);
      } catch (e) { msg.textContent = " " + e.message; }
    };
    add(card, add(el("div", "live-row"), who, go, msg));
  }
  if (c.saved) card.appendChild(el("p", "saved", c.saved.message));
  const toVendor = c.messages.filter((m) => m.channel.startsWith("WhatsApp"));
  const others = c.messages.filter((m) => !m.channel.startsWith("WhatsApp"));
  side.appendChild(el("h2", "", "Message to the vendor"));
  side.appendChild(phone(c, toVendor));
  side.appendChild(el("h2", "", "Ready to send"));
  const ob = el("div", "outbox");
  ob.appendChild(el("p", "note", c.outbox_note));
  if (!others.length) ob.appendChild(el("p", "muted", "No task or other message is needed."));
  others.forEach((m) => {
    const wrap = el("div", "msg");
    add(wrap, el("div", "to", "To " + m.to + " · " + m.channel), el("div", "bubble", m.text));
    ob.appendChild(wrap);
  });
  side.appendChild(ob);
  if (c.source !== "live" && tesseract && lastFile) add(side, add(el("div", "live-row"), liveButton()));
  area.appendChild(art);
}

// A phone-style chat with the vendor. Simulated: nothing is sent. The drafted message is shown in English or Hindi; "Vendor replies with a photo" reads the photo
// (the stored reading, or Tesseract when it is installed), re-runs the checks, and the answer is posted back to the thread in plain words.
function phone(c, msgs) {
  let lang = "en";
  const items = msgs.map((m) => ({ who: "company", en: m.text, hi: m.hi || m.text }));
  const wrap = el("div", "phone");
  const top = add(el("div", "phone-top"), el("div", "phone-name", (msgs[0] && msgs[0].to) || "Vendor"), el("div", "phone-sim", c.chat_note));
  const seg = el("div", "lang");
  const bEn = el("button", "on", "English"), bHi = el("button", "", "हिन्दी");
  [bEn, bHi].forEach((b) => { b.type = "button"; });
  add(seg, bEn, bHi);
  const log = el("div", "phone-log");
  const note = el("p", "muted small");
  note.hidden = true;
  const render = () => {
    clear(log);
    if (!items.length) log.appendChild(el("p", "phone-empty", "No message to the vendor is needed."));
    items.forEach((it) => {
      const b = el("div", "chat " + it.who);
      if (it.thumb) { const im = el("img", "thumb"); im.src = it.thumb; im.alt = "the photo the vendor sent"; b.appendChild(im); }
      b.appendChild(el("div", "t", lang === "hi" ? it.hi : it.en));
      if (it.card) {
        const open = el("button", "pick", lang === "hi" ? "इस जवाब का पूरा कार्ड खोलें" : "Open the full card for this reply");
        open.type = "button";
        open.onclick = () => renderCard(it.card);
        b.appendChild(open);
      }
      log.appendChild(b);
    });
    log.scrollTop = log.scrollHeight;
    bEn.className = lang === "en" ? "on" : "";
    bHi.className = lang === "hi" ? "on" : "";
    note.hidden = lang !== "hi";
    note.textContent = c.hindi_note;
  };
  bEn.onclick = () => { lang = "en"; render(); };
  bHi.onclick = () => { lang = "hi"; render(); };
  add(top, seg);
  add(wrap, top, log, note);
  const msg = el("span", "small muted");
  const send = async (label, thumb, url, opts) => {
    items.push({ who: "vendor", en: "Photo: " + label, hi: "फ़ोटो: " + label, thumb });
    render();
    msg.textContent = " Reading the photo.";
    try {
      const r = await api(url, opts);
      items.push({ who: "company", en: r.reply.en, hi: r.reply.hi, card: r.card });
      msg.textContent = "";
    } catch (e) { msg.textContent = " " + e.message; items.pop(); }
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
  const go = el("button", "btn quiet", "Vendor replies with a photo");
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
  const b = el("button", "btn quiet", "Run live reader");
  b.onclick = () => intake({ live: true, sample: lastFile && lastFile.sample ? lastFile.name : undefined });
  return b;
}

// ---------------------------------------------------------------- control tower
const nf = new Intl.NumberFormat("en-IN");
let cutoffNow = null;
async function loadControl(cutoff) {
  const body = $("control-body");
  clear(body);
  body.appendChild(el("p", "muted", "Loading the register."));
  try {
    const d = await api("/api/control" + (cutoff === undefined ? "" : "?cutoff=" + cutoff));
    cutoffNow = d.cutoff;
    $("control-as").textContent = "As of " + d.as_of + ".";
    const seg = $("cutoff");
    clear(seg);
    d.scenarios.forEach((s) => {
      const on = s.cutoff === d.cutoff;
      const b = el("button", on ? "sc-opt on" : "sc-opt");
      b.type = "button";
      b.setAttribute("role", "radio");
      b.setAttribute("aria-checked", on ? "true" : "false");
      add(b, el("span", "sc-dot"), el("span", "sc-label", s.label), el("span", "sc-case", s.case));
      b.onclick = () => loadControl(s.cutoff);
      seg.appendChild(b);
    });
    $("sc-effect").textContent = d.effect;
    renderControl(d);
  } catch (e) { clear(body); showError(e); }
}

// A list that shows its first few rows and a "Show all" link for the rest. `preview` comes from the server (layout only).
function section(parent, title, id, items, build, preview, note) {
  const body = el("div", "sec");
  parent.appendChild(body);
  const head = add(el("div", "sec-head"), el("h2", "", title));
  const list = el("ul", "rows");
  items.forEach((x, i) => { const li = build(x); li.hidden = i >= preview; list.appendChild(li); });
  if (items.length > preview) {
    const more = el("button", "link-btn", "Show all " + nf.format(items.length));
    more.type = "button";
    let open = false;
    more.onclick = () => {
      open = !open;
      [...list.children].forEach((li, i) => { li.hidden = !open && i >= preview; });
      more.textContent = open ? "Show fewer" : "Show all " + nf.format(items.length);
    };
    head.appendChild(more);
  }
  body.appendChild(head);
  if (note) body.appendChild(el("p", "muted small sec-note", note));
  body.appendChild(list);
}

function stat(num, lab, miss, extra) { return add(el("div", "stat"), el("div", miss ? "num miss" : "num", nf.format(num)), el("div", "lab", lab), extra ? el("div", "lab extra", extra) : null); }

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
    const left = add(el("div"), add(el("div", "who", b.vendor), el("span", "meta", " " + b.bill_id + " · " + b.amount)), el("div", "meta", "Stuck: " + b.stuck + (b.reason ? " (" + b.reason + ")" : "") + " · Next move: " + (b.owner || "none")));
    const right = el("div", "big", nf.format(b.days));
    right.appendChild(el("small", "", "days"));
    add(li, left, right);
    return li;
  }, pv);

  section(lists, "Micro and Small bills closest to the limit", "s-msme", d.msme, (b) => {
    const li = el("li", b.miss ? "row miss" : "row");
    const whoRow = add(el("div"), el("span", "who", b.vendor), el("span", "meta", " " + b.bill_id + " · " + b.amount));
    if (b.unknown) whoRow.appendChild(el("span", "tag", "status unknown"));
    const left = add(el("div"), whoRow, el("div", "meta", b.stage + " · next move: " + (b.owner || "none")),
      el("div", "meta", b.runs_left ? nf.format(b.runs_left) + " payment run(s) left" + (b.last_run ? ", the last on " + b.last_run : "") : "No payment run left before the limit"));
    const right = el("div", "big", nf.format(b.days_left));
    right.appendChild(el("small", "", "days left"));
    add(li, left, right);
    return li;
  }, pv);

  const pickBox = el("div", "sec");
  lists.appendChild(pickBox);
  const h2p = el("h2", "", "Pick order across the AP clerks"); h2p.id = "s-pick"; pickBox.appendChild(h2p);
  const cl = el("div", "clerks");
  d.clerks.forEach((c) => {
    add(cl, add(el("div", "clerk"), el("div", "name", c.clerk), el("div", "num", "+" + nf.format(c.new)), el("div", "cap", nf.format(c.after) + " in hand after, from " + nf.format(c.in_hand)),
      el("div", "cap", nf.format(c.queries) + " query follow-ups"), c.first ? el("div", "cap", "Starts with " + c.first) : null));
  });
  pickBox.appendChild(cl);
  pickBox.appendChild(el("p", "muted small", d.spread_pct === null ? "" : "Highest load is " + d.spread_pct + " per cent above the lowest after the order. The live queue holds " + nf.format(d.live_waiting) + " waiting bills."));

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
function sourceTip(text) {
  const q = el("span", "q", "?");
  q.tabIndex = 0;
  q.setAttribute("role", "note");
  q.setAttribute("aria-label", "Source: " + text);
  q.dataset.tip = "Source: " + text;
  return q;
}

async function loadImpact() {
  const body = $("impact-body");
  body.appendChild(el("p", "muted", "Loading the backtest."));
  try {
    const d = await api("/api/impact");
    $("impact-label").textContent = d.label + " " + d.reading_note;
    clear(body);
    const cases = el("details", "fold");
    add(cases, el("summary", "", "How the best, middle and worst case are set"), el("p", "muted small", d.low_middle_high));
    const metrics = el("div", "metrics");
    body.appendChild(metrics);
    d.headline.forEach((m) => {
      const box = el("div", "metric");
      const after = el("div", "after", m.after);
      after.appendChild(el("small", "", " " + m.unit + " after"));
      add(box, add(el("div", "name"), el("span", "", m.name), sourceTip(m.source)), after, el("div", "before", m.sentence.charAt(0).toUpperCase() + m.sentence.slice(1) + "."));
      const s = m.scale, span = s.max || 1;
      const track = el("div", "bar-track");
      const fill = el("div", "bar-fill");
      fill.style.left = (100 * Math.min(s.lo, s.hi) / span) + "%";
      fill.style.width = Math.max(1.2, 100 * Math.abs(s.hi - s.lo) / span) + "%";
      const mark = el("div", "bar-mark");
      mark.style.left = (100 * s.before / span) + "%";
      add(track, fill, mark);
      const cap = el("div", "bar-cap");
      add(cap, el("span", "key key-fill", "with the changes"), el("span", "key key-mark", "today"));
      add(box, track, cap, el("p", "cond", m.condition));
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
    body.appendChild(el("div", "line-note", d.intake_line));
    body.appendChild(cases);
  } catch (e) { clear(body); showError(e); }
}

route();
