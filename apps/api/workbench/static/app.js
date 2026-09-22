"use strict";
const $ = (s, root = document) => root.querySelector(s);
const esc = value => String(value ?? "").replace(/[&<>"']/g, c => ({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[c]));
const state = {runs: [], assets: [], selected: new Set(), view: "focus", busy: false, urls: new Map(), timer: null};
let token = sessionStorage.getItem("sonic-token") || "";
const fragment = new URLSearchParams(location.hash.slice(1));
if (fragment.has("token")) {
  token = fragment.get("token"); sessionStorage.setItem("sonic-token", token);
  history.replaceState(null, "", location.pathname);
}
const savedInputs = JSON.parse(localStorage.getItem("sonic-inputs") || "{}");
for (const [id, values] of Object.entries(savedInputs)) {
  const form = document.getElementById(id);
  if (form) for (const [name, value] of Object.entries(values)) {
    const field = form.elements.namedItem(name);
    if (field && !["source_run_id", "pack_run_id"].includes(name)) field.value = value;
  }
}
function reportError(error) {
  const box = $("#error"); box.textContent = error.message || String(error); box.hidden = false;
}
function clearError() { $("#error").hidden = true; }
function showView(view) {
  state.view = view;
  document.querySelectorAll(".view").forEach(x => { x.hidden = x.id !== "view-" + view; });
  document.querySelectorAll("[data-view]").forEach(x => x.classList.toggle("active", x.dataset.view === view));
  $("#view-label").textContent = {focus:"A little direction goes a long way.",midi:"Your idea starts with a sound.",assets:"A clear inventory. A usable deliverable.",release:"An honest offer, backed by your work.",history:"Everything you made, ready to resume.",settings:"Your local engine and AI connection."}[view];
}
async function api(path, options = {}) {
  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), 120000);
  try {
    const headers = new Headers(options.headers || {});
    headers.set("Authorization", "Bearer " + token);
    if (options.body && !(options.body instanceof FormData)) headers.set("Content-Type", "application/json");
    const response = await fetch("/workbench/api" + path, {...options, headers, signal: controller.signal});
    if (!response.ok) {
      const body = await response.json().catch(() => ({}));
      const detail = Array.isArray(body.detail) ? body.detail.map(e => e.msg).join("; ") : body.detail;
      throw new Error(detail || `Sonic could not finish the request (${response.status}).`);
    }
    return options.binary ? await response.blob() : await response.json();
  } catch (e) {
    if (e.name === "AbortError") throw new Error("This is taking longer than expected. Refresh Your outputs before retrying; the work may have finished.");
    if (e instanceof TypeError) throw new Error("Sonic's local connection was interrupted. Reopen the app; saved outputs will remain available.");
    throw e;
  } finally { clearTimeout(timeout); }
}
async function busy(label, fn) {
  if (state.busy) return;
  state.busy = true; clearError(); $("#busy-text").textContent = label; $("#busy").hidden = false;
  const buttons = [...document.querySelectorAll("button")].filter(b => !b.disabled);
  buttons.forEach(b => b.disabled = true);
  try { return await fn(); } catch (e) { reportError(e); }
  finally { state.busy = false; $("#busy").hidden = true; buttons.forEach(b => b.disabled = false); }
}
function values(form) {
  const data = Object.fromEntries(new FormData(form));
  if (!["ai-form", "connection-form"].includes(form.id)) {
    savedInputs[form.id] = data; localStorage.setItem("sonic-inputs", JSON.stringify(savedInputs));
  }
  return data;
}
async function command(kind, payload) {
  const storageKey = "sonic-pending-" + kind, canonical = JSON.stringify(payload);
  let pending = JSON.parse(localStorage.getItem(storageKey) || "null");
  if (!pending || pending.canonical !== canonical) {
    pending = {canonical, id: crypto.randomUUID()};
    localStorage.setItem(storageKey, JSON.stringify(pending));
  }
  const run = await api("/" + kind, {method:"POST", body:JSON.stringify({...payload, request_id:pending.id})});
  localStorage.removeItem(storageKey);
  await refresh();
  if (run.status !== "succeeded") throw new Error(run.error || "The run did not finish. Start a new run.");
  return run;
}
function bytes(n) { return n > 1048576 ? (n / 1048576).toFixed(1) + " MB" : Math.max(1, Math.round(n / 1024)) + " KB"; }
function replaceOptions(element, list, empty) {
  const value = element.value;
  element.innerHTML = `<option value="">${esc(empty)}</option>` + list.map(r => `<option value="${r.id}">${esc(r.result.title)} · ${new Date(r.created_at).toLocaleDateString()}</option>`).join("");
  if (list.some(r => r.id === value)) element.value = value;
}
async function refresh() {
  const data = await api("/status");
  state.runs = data.runs; state.assets = data.assets;
  $("#connection-status").textContent = "● Local engine ready";
  $("#output-count").textContent = state.runs.filter(r => r.status === "succeeded").length;
  $("#cloud-state").textContent = data.cloud_ai === "not_configured" ? "Cloud AI is not connected. Local workflows are ready." : "AI is configured. A successful insight request verifies the connection.";
  $("#mcp-address").textContent = location.origin + "/mcp";
  renderAssets(); renderHistory();
  const finished = state.runs.filter(r => r.status === "succeeded");
  replaceOptions($("#pack-source"), finished.filter(r => r.kind === "midi"), "Imported assets only");
  replaceOptions($("#release-source"), finished.filter(r => r.kind === "pack"), "Choose a completed pack");
}
function renderAssets() {
  $("#asset-list").innerHTML = state.assets.length ? state.assets.map(a => `<div class="asset"><input aria-label="Select ${esc(a.name)}" type="checkbox" data-asset="${a.id}" ${state.selected.has(a.id) ? "checked" : ""}><div class="asset-info"><strong>${esc(a.name)}</strong><small>${esc(a.category)} · ${bytes(a.bytes)}${a.metadata.sample_rate ? " · " + a.metadata.sample_rate + " Hz" : ""}</small></div>${a.category !== "MIDI" ? `<button data-analyze="${a.id}">Analyze</button>` : ""}</div>`).join("") : `<div class="empty"><h2>Your sources belong here.</h2><p>Import files or a folder. Exact duplicates are detected by their contents.</p></div>`;
}
function renderHistory() {
  $("#history-list").innerHTML = state.runs.length ? state.runs.map(r => `<div class="history-row"><div><span class="history-kind">${esc(r.kind)} · ${esc(r.status)}</span><strong>${esc(r.result.title || r.request.title || "Sonic run")}</strong><small>${new Date(r.created_at).toLocaleString()} · ${(r.result.artifacts || []).length} files</small></div><button class="secondary" data-run="${r.id}">Open output →</button></div>`).join("") : `<div class="card empty"><h2>No finished work yet.</h2><p>Create one MIDI phrase or import an audio file to start your history.</p><button class="secondary" data-view="midi">Create your first MIDI</button></div>`;
}
function fileButtons(run) {
  return `<div class="artifact-list">${(run.result.artifacts || []).map(f => `<button class="file-button" data-file="${esc(f.name)}" data-run-id="${run.id}"><span>↓ ${esc(f.name)}</span><small>${bytes(f.bytes)}</small></button>`).join("")}</div>`;
}
function piano(canvas, result) {
  if (!canvas) return;
  const ctx = canvas.getContext("2d"), width = canvas.width = 900, height = canvas.height = 240;
  ctx.fillStyle = "#141819"; ctx.fillRect(0, 0, width, height);
  const notes = result.notes.filter(n => n.track !== "Drums");
  const min = Math.min(...notes.map(n => n.pitch)) - 1, max = Math.max(...notes.map(n => n.pitch)) + 1;
  const row = height / (max - min + 1);
  ctx.strokeStyle = "#29302c";
  for (let i = 0; i <= result.bars * 4; i++) { const x = i / (result.bars * 4) * width; ctx.beginPath(); ctx.moveTo(x, 0); ctx.lineTo(x, height); ctx.stroke(); }
  for (const n of notes) {
    ctx.fillStyle = {Melody:"#c1ee8c", Chords:"#556c76", Bass:"#bb9461"}[n.track];
    ctx.fillRect(n.start / (result.bars * 4) * width, (max - n.pitch) * row, Math.max(2, n.duration / (result.bars * 4) * width - 1), Math.max(2, row - 1));
  }
}
async function blobURL(runId, name) {
  const key = runId + "/" + name;
  if (!state.urls.has(key)) {
    const blob = await api(`/runs/${runId}/files/${encodeURIComponent(name)}`, {binary:true});
    if (state.urls.size >= 8) { const [old, url] = state.urls.entries().next().value; URL.revokeObjectURL(url); state.urls.delete(old); }
    state.urls.set(key, URL.createObjectURL(blob));
  }
  return state.urls.get(key);
}
async function showRun(run, container) {
  container.hidden = false;
  const r = run.result;
  if (run.status !== "succeeded") { container.innerHTML = `<h2>${esc(run.status)}</h2><p>${esc(run.error || "This run has not finished.")}</p>`; return; }
  let body = "";
  if (run.kind === "midi") body = `<div class="result-meta"><span>${r.bars} bars</span><span>${esc(r.key)} ${esc(r.scale.replaceAll("_", " "))}</span><span>${r.bpm} BPM</span><span>${r.note_count} notes</span></div><canvas class="piano" role="img" aria-label="Piano roll of generated melody, chords and bass"></canvas><div class="audio-row"><audio controls preload="none" aria-label="Audition the generated phrase"></audio><p class="fine">Synth audition · melody / chords / bass / drums</p></div>`;
  if (run.kind === "analysis") {
    const m = r.measurements;
    body = `<div class="metrics">${[["Sample peak", m.sample_peak_dbfs === null ? "Silent" : m.sample_peak_dbfs + " dBFS"],["RMS",m.rms_dbfs === null ? "Silent" : m.rms_dbfs + " dBFS"],["Duration",m.duration_seconds + "s"],["Stereo correlation",m.stereo_correlation ?? "Not defined"]].map(([name,value]) => `<div class="metric"><span>${esc(name)}</span><strong>${esc(value)}</strong></div>`).join("")}</div>` + m.observations.map(o => `<div class="next-step"><strong>${esc(o.fact)}</strong><p>${esc(o.action)}</p></div>`).join("");
  }
  if (run.kind === "release") body = `<pre class="report-copy">${esc(r.copy)}</pre>`;
  if (run.kind === "focus") body = `<p>${esc(r.message)}</p><div class="timer" data-minutes="${r.minutes}">${r.minutes}:00</div><p><strong>Done when:</strong> ${esc(r.done_when)}</p><div class="button-row"><button class="secondary" data-action="timer">Start focus timer</button><button class="secondary" data-view="${esc(r.target)}">Open this workflow →</button></div>`;
  if (run.kind === "pack") body = `<div class="result-meta">${Object.entries(r.manifest.category_counts).map(([category,count]) => `<span>${count} ${esc(category)}</span>`).join("")}</div><p class="fine">${r.manifest.license_status === "missing" ? "License not supplied." : "Operator-supplied license included; terms have not been legally validated."}</p>`;
  container.innerHTML = `<div class="rendered" data-output-id="${run.id}"><span class="eyebrow accent">${esc(run.kind)} · SAVED</span><h2 class="result-title">${esc(r.title)}</h2><p>${esc(r.summary)}</p>${body}<div class="next-step"><span class="eyebrow">NEXT USEFUL STEP</span><p>${esc(r.next_action)}</p></div><div class="button-row">${run.kind === "midi" ? `<button class="secondary" data-pack-midi="${run.id}">Package this MIDI set</button>` : ""}${run.kind === "pack" ? `<button class="secondary" data-release-pack="${run.id}">Prepare its release</button>` : ""}<button class="secondary" data-save-run="${run.id}">Export all files</button></div>${fileButtons(run)}${(r.warnings || []).map(w => `<p class="warning">${esc(w)}</p>`).join("")}${!["coach", "focus"].includes(run.kind) ? `<hr><label>Ask Sonic about this output<input data-question value="What is the most useful next step?" maxlength="2000"></label><button class="secondary" data-coach="${run.id}">Get a grounded insight</button>` : ""}<p class="fine">${esc(r.engine)} · ${esc(run.id.slice(0,8))}</p></div>`;
  if (run.kind === "midi") {
    piano($("canvas", container), r);
    try { $("audio", container).src = await blobURL(run.id, "Audition.wav"); } catch(e) { reportError(e); }
  }
}
async function download(runId, name) {
  if (window.pywebview?.api) {
    const result = await window.pywebview.api.save_artifact(runId, name);
    if (result.error) throw new Error(result.error);
  } else {
    const url = await blobURL(runId, name), a = document.createElement("a");
    a.href = url; a.download = name; a.click();
  }
}
document.addEventListener("click", e => {
  const button = e.target.closest("button"); if (!button) return;
  if (button.dataset.view) { clearError(); showView(button.dataset.view); }
  if (button.dataset.file) busy("Saving your file…", () => download(button.dataset.runId, button.dataset.file));
  if (button.dataset.run) busy("Opening saved output…", async () => { const run = await api("/runs/" + button.dataset.run); await showRun(run, $("#history-result")); });
  if (button.dataset.analyze) busy("Measuring the audio samples…", async () => showRun(await command("analysis", {asset_id:button.dataset.analyze}), $("#asset-result")));
  if (button.dataset.packMidi) { showView("assets"); $("#pack-source").value = button.dataset.packMidi; }
  if (button.dataset.releasePack) { showView("release"); $("#release-source").value = button.dataset.releasePack; }
  if (button.dataset.saveRun) busy("Exporting your output…", async () => {
    if (window.pywebview?.api) {
      const result = await window.pywebview.api.save_run(button.dataset.saveRun);
      if (result.error) throw new Error(result.error);
    } else {
      const blob = await api(`/runs/${button.dataset.saveRun}/archive`, {binary:true});
      const url = URL.createObjectURL(blob), a = document.createElement("a"); a.href = url; a.download = "Sonic_Output.zip"; a.click(); setTimeout(() => URL.revokeObjectURL(url), 60000);
    }
  });
  if (button.dataset.coach) busy("Sonic is reviewing this output…", async () => {
    const question = $("[data-question]", button.closest(".rendered")).value;
    const run = await command("coach", {run_id:button.dataset.coach,question}); showView("history"); await showRun(run,$("#history-result"));
  });
  if (button.dataset.action === "timer") {
    if (state.timer) { clearInterval(state.timer); state.timer = null; button.textContent = "Resume focus timer"; return; }
    const display = $(".timer", button.closest(".rendered"));
    const remaining = Number(display.dataset.remaining || Number(display.dataset.minutes) * 60), end = Date.now() + remaining * 1000;
    button.textContent = "Pause timer";
    state.timer = setInterval(() => {
      const seconds = Math.max(0, Math.ceil((end-Date.now()) / 1000)); display.dataset.remaining = seconds;
      display.textContent = `${Math.floor(seconds/60)}:${String(seconds%60).padStart(2,"0")}`;
      if (!seconds) { clearInterval(state.timer); state.timer = null; display.textContent = "Save your work. You're done for now."; button.textContent = "Session finished"; button.disabled = true; }
    },250);
  }
});
document.addEventListener("change", e => { if (e.target.dataset.asset) { e.target.checked ? state.selected.add(e.target.dataset.asset) : state.selected.delete(e.target.dataset.asset); } });
$("#midi-form").addEventListener("submit", e => { e.preventDefault(); busy("Composing your phrase and rendering the audition…", async () => {
  const p = values(e.target); for (const k of ["bpm","bars","seed"]) p[k] = Number(p[k]);
  await showRun(await command("midi",p),$("#midi-result"));
}); });
$("#variation").addEventListener("click", () => { $("#midi-form").elements.seed.value = Math.floor(Math.random()*2147483647); $("#midi-form").requestSubmit(); });
$("#focus-form").addEventListener("submit", e => { e.preventDefault(); busy("Choosing one useful next step…", async () => { const p = values(e.target); p.minutes = Number(p.minutes); if(state.timer){clearInterval(state.timer);state.timer=null;} await showRun(await command("focus",p),$("#focus-result")); }); });
$("#pack-form").addEventListener("submit", e => { e.preventDefault(); busy("Copying selected assets and building the pack…", async () => { const p = values(e.target); p.source_run_id ||= null; p.asset_ids = [...state.selected]; if (!p.asset_ids.length && !p.source_run_id) throw new Error("Select at least one imported asset or a generated MIDI set."); await showRun(await command("pack",p),$("#asset-result")); }); });
$("#release-form").addEventListener("submit", e => { e.preventDefault(); busy("Drafting from your pack inventory…", async () => { const p = values(e.target); p.price = Number(p.price); await showRun(await command("release",p),$("#release-result")); }); });
$("#refresh-history").onclick = () => busy("Refreshing saved work…",refresh);
$("#select-all").onclick = () => { const all = state.assets.every(a => state.selected.has(a.id)); state.selected = new Set(all ? [] : state.assets.map(a => a.id)); renderAssets(); };
$("#choose-files").onclick = () => $("#import-files").click();
$("#choose-folder").onclick = () => $("#import-folder").click();
for (const input of [$("#import-files"),$("#import-folder")]) input.addEventListener("change", () => busy("Importing your source files…",async () => {
  const files = [...input.files].filter(f => /\.(wav|flac|aiff?|mp3|ogg|midi?)$/i.test(f.name));
  if (!files.length) throw new Error("No supported audio or MIDI files were selected.");
  if (files.length > 200) throw new Error("Import up to 200 files at a time.");
  const errors = []; let added = 0, duplicates = 0;
  for (const [i, file] of files.entries()) {
    $("#busy-text").textContent = `Importing ${i+1}/${files.length}: ${file.name}`;
    try { const form = new FormData(); form.append("file",file); const asset = await api("/imports",{method:"POST",body:form}); state.selected.add(asset.id); asset.duplicate ? duplicates++ : added++; }
    catch(e) { errors.push(file.name + ": " + e.message); }
  }
  await refresh(); input.value = "";
  $("#asset-result").hidden = false; $("#asset-result").innerHTML = `<h2>${added} imported · ${duplicates} exact duplicates reused</h2><p>${state.selected.size} assets selected for your pack.</p>`;
  if(errors.length) reportError(new Error(errors.join("\n")));
}));
$("#connection-form").addEventListener("submit",e => { e.preventDefault();token=e.target.elements.token.value;sessionStorage.setItem("sonic-token",token);e.target.reset();busy("Connecting…",refresh); });
$("#ai-form").addEventListener("submit",e => { e.preventDefault(); busy("Saving the AI connection…", async () => {
  if (!window.pywebview?.api) throw new Error("Use the desktop app to save AI credentials, or configure SONIC_OPENAI_API_KEY on the API server.");
  const p=Object.fromEntries(new FormData(e.target));
  const result=await window.pywebview.api.configure_ai(p.api_key,p.model);e.target.elements.api_key.value="";
  if(result.error) throw new Error(result.error);await refresh();$("#cloud-state").textContent=result.message;
}); });
$("#mcp-config").onclick = () => busy("Preparing MCP connection details…", async () => {
  if(!window.pywebview?.api) throw new Error("Open Sonic Desktop to save its private MCP connection file.");
  const result=await window.pywebview.api.save_mcp_config();if(result.error) throw new Error(result.error);
});
refresh().then(async () => {
  const midiRun=state.runs.find(r=>r.kind==="midi" && r.status==="succeeded");if(midiRun) await showRun(midiRun,$("#midi-result"));
}).catch(e => { $("#connection-status").textContent="Connection needed";reportError(e);if(!token) showView("settings"); });
