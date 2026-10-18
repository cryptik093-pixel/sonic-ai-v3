"use strict";
// Extends the existing Workbench and its authenticated api()/busy() helpers.
const forge = { pack: null, selected: new Set(), pending: new Map(), dirty: false };
const forgeRoot = "/forge/packs";

async function forgeRefresh() {
  const packs = await api(forgeRoot);
  $("#forge-packs").innerHTML = packs.map(p => `<button class="secondary" data-forge-open="${esc(p.id)}">${esc(p.title)} · ${esc(p.status)}</button>`).join("") || "No ZIP packs imported yet.";
}
async function forgeLoad(id) {
  forge.pack = await api(`${forgeRoot}/${id}`);
  forge.selected.clear(); forge.dirty = false;
  forgeRender();
}
function forgeRender() {
  const p = forge.pack, target = $("#forge-review");
  if (!p) { target.hidden = true; return; }
  target.hidden = false;
  const approved = p.approved_revision === p.manifest_revision;
  target.innerHTML = `<h2>${esc(p.manifest.title)}</h2><p>Revision ${p.manifest_revision} · ${esc(p.status)} · ${p.manifest.assets.length} assets</p>
    <p class="fine mono">Original ZIP SHA-256: ${esc(p.manifest.source_zip_sha256)}</p>
    <p class="fine">BPM and key estimates are undetermined. Optional manual entries are recorded as operator overrides. Blank override fields preserve existing values.</p>
    <div class="button-row"><button class="secondary" data-forge-select>Select all</button><button class="secondary" data-forge-reload>Reload saved revision (discard edits)</button></div>
    <div class="form-row"><label>Batch taxonomy<input id="forge-batch-taxonomy" maxlength="120"></label><div class="button-row"><button class="secondary" data-forge-taxonomy>Apply to selected</button><button class="secondary" data-forge-rights>Confirm selected rights cleared</button></div></div>
    <div class="forge-scroll"><table class="forge-table"><caption>Review every asset. Rights clearance is your explicit declaration.</caption><thead><tr><th>Select</th><th>Original / type / checksum</th><th>Export path</th><th>Taxonomy</th><th>Rights</th><th>Tags</th><th>Manual BPM</th><th>Manual key</th></tr></thead><tbody>
    ${p.manifest.assets.map(a => `<tr data-forge-asset="${esc(a.asset_id)}"><td><input type="checkbox" data-forge-check="${esc(a.asset_id)}" aria-label="Select ${esc(a.original_path)}"></td>
      <td><strong>${esc(a.original_path)}</strong><small>${esc(a.asset_type)} · ${a.bytes} bytes · ${esc(a.review_state)}</small><small class="mono">${esc(a.sha256)}</small></td>
      <td><input data-forge-field="proposed_path" aria-label="Export path ${esc(a.original_path)}" maxlength="240" value="${esc(a.proposed_path)}"></td>
      <td><input data-forge-field="taxonomy" aria-label="Taxonomy ${esc(a.original_path)}" maxlength="120" value="${esc(a.taxonomy)}"></td>
      <td><select data-forge-field="rights_state" aria-label="Rights ${esc(a.original_path)}">${["unverified","cleared","restricted"].map(s => `<option ${a.rights_state === s ? "selected" : ""}>${s}</option>`).join("")}</select></td>
      <td><input data-forge-field="tags" aria-label="Tags ${esc(a.original_path)}" value="${esc(a.tags.join(", "))}"></td>
      <td><input data-forge-field="bpm_override" aria-label="Manual BPM ${esc(a.original_path)}" type="number" min="30" max="300" step="any" placeholder="Unknown" value="${a.bpm.method === "operator_override" ? esc(a.bpm.value) : ""}"><small>${esc(a.bpm.method)} · ${esc(a.bpm.value ?? "undetermined")}</small></td>
      <td><input data-forge-field="key_override" aria-label="Manual key ${esc(a.original_path)}" placeholder="C minor" value="${a.key.method === "operator_override" ? esc(a.key.value) : ""}"><small>${esc(a.key.method)} · ${esc(a.key.value ?? "undetermined")}</small></td></tr>`).join("")}
    </tbody></table></div><div class="button-row"><button class="primary" data-forge-save>Save and review all assets</button><button class="secondary" data-forge-approve ${approved || p.manifest.assets.some(a => a.review_state !== "approved") ? "disabled" : ""}>Approve revision ${p.manifest_revision}</button><button class="primary" data-forge-export ${!approved ? "disabled" : ""}>Export reviewed ZIP</button></div>
    <hr><h2>Offline Shopify draft</h2><p class="fine">All assets must have cleared rights. This saves an unpublished CSV; no store operation occurs.</p><div class="form-row"><label>Draft price<input id="forge-price" inputmode="decimal"></label><label>SKU<input id="forge-sku" maxlength="64"></label></div><button class="secondary" data-forge-draft ${!approved || p.manifest.assets.some(a => a.rights_state !== "cleared") ? "disabled" : ""}>Download unpublished CSV draft</button>
    <hr><h2>Saved exports</h2>${(p.artifacts || []).map(a => `<p><button class="secondary" data-forge-download="${esc(a.id)}">Download ${esc(a.kind)} revision ${a.revision}</button><small class="mono">SHA-256 ${esc(a.sha256)}</small></p>`).join("") || "No exports yet."}
    <hr><h2>Review history</h2>${(p.events || []).map(e => `<p class="fine">${esc(e.timestamp)} · ${esc(e.action)} · revision ${e.revision} · ${esc(e.actor)} · ${esc(e.correlation_id)}</p>`).join("")}`;
}
async function forgeCommand(action, extra = {}) {
  const p = forge.pack;
  if (!p) throw new Error("Choose a ZIP pack first.");
  if (forge.dirty && action !== "review") throw new Error("Save your review before approving or exporting.");
  const canonical = JSON.stringify({id:p.id, revision:p.manifest_revision, action, extra});
  if (!forge.pending.has(canonical)) forge.pending.set(canonical, crypto.randomUUID());
  const result = await api(`${forgeRoot}/${p.id}/${action}`, {method:action === "review" ? "PATCH" : "POST",
    body:JSON.stringify({request_id:forge.pending.get(canonical), expected_revision:p.manifest_revision, ...extra})});
  forge.pending.delete(canonical);
  await forgeLoad(p.id); await forgeRefresh();
  if (result.artifact) await forgeDownload(result.artifact);
}
async function forgeDownload(artifact) {
  const blob = await api(`/forge/exports/${artifact.id}`, {binary:true});
  const hash = Array.from(new Uint8Array(await crypto.subtle.digest("SHA-256", await blob.arrayBuffer())))
    .map(x => x.toString(16).padStart(2,"0")).join("");
  if (hash !== artifact.sha256) throw new Error("Downloaded artifact failed its checksum check.");
  const url = URL.createObjectURL(blob), link = document.createElement("a");
  link.href = url; link.download = `forge-${artifact.id}.${artifact.kind === "export" ? "zip" : "csv"}`;
  link.click(); setTimeout(() => URL.revokeObjectURL(url),60000);
}
function forgeSave() {
  const updates = {};
  for (const row of document.querySelectorAll("[data-forge-asset]")) {
    const change = {};
    for (const input of row.querySelectorAll("[data-forge-field]")) {
      const field = input.dataset.forgeField;
      if (field === "tags") change[field] = input.value.split(",").map(s => s.trim()).filter(Boolean);
      else if (field === "bpm_override") { if (input.value) change[field] = Number(input.value); }
      else if (field === "key_override") { if (input.value) change[field] = input.value; }
      else change[field] = input.value;
    }
    updates[row.dataset.forgeAsset] = change;
  }
  return forgeCommand("review", {updates});
}
document.addEventListener("input", e => {
  if (e.target.matches("[data-forge-field]")) forge.dirty = true;
});
document.addEventListener("change", e => {
  if (e.target.matches("[data-forge-field]")) forge.dirty = true;
  const id = e.target.dataset.forgeCheck;
  if (id) e.target.checked ? forge.selected.add(id) : forge.selected.delete(id);
});
document.addEventListener("click", e => {
  const b = e.target.closest("button"); if (!b) return;
  if (b.dataset.view === "forge" || b.hasAttribute("data-forge-refresh")) busy("Loading ZIP packs…", forgeRefresh);
  if (b.dataset.forgeOpen) busy("Opening ZIP review…", async () => {
    if (forge.dirty) throw new Error("Save your review or reload the saved revision before switching packs.");
    await forgeLoad(b.dataset.forgeOpen);
  });
  if (b.hasAttribute("data-forge-reload")) busy("Reloading saved review…", () => forgeLoad(forge.pack.id));
  if (b.hasAttribute("data-forge-select")) {
    document.querySelectorAll("[data-forge-check]").forEach(x => { x.checked = true; forge.selected.add(x.dataset.forgeCheck); });
  }
  if (b.hasAttribute("data-forge-taxonomy") || b.hasAttribute("data-forge-rights")) {
    const field = b.hasAttribute("data-forge-rights") ? "rights_state" : "taxonomy";
    const value = field === "rights_state" ? "cleared" : $("#forge-batch-taxonomy").value.trim();
    if (!value || !forge.selected.size) { reportError(new Error("Select assets and enter a batch value first.")); return; }
    document.querySelectorAll("[data-forge-asset]").forEach(row => {
      if (forge.selected.has(row.dataset.forgeAsset)) row.querySelector(`[data-forge-field="${field}"]`).value = value;
    }); forge.dirty = true;
  }
  if (b.hasAttribute("data-forge-save")) busy("Saving revision and operator review…", forgeSave);
  if (b.hasAttribute("data-forge-approve")) busy("Approving this revision…", () => forgeCommand("approve"));
  if (b.hasAttribute("data-forge-export")) busy("Verifying source hashes and exporting…", () => forgeCommand("export"));
  if (b.hasAttribute("data-forge-draft")) busy("Creating unpublished CSV…", () => forgeCommand("shopify-draft", {price:$("#forge-price").value,sku:$("#forge-sku").value}));
  if (b.dataset.forgeDownload) busy("Verifying saved export…", () => forgeDownload(forge.pack.artifacts.find(a => a.id === b.dataset.forgeDownload)));
});
$("#forge-upload").addEventListener("submit", e => {
  e.preventDefault(); busy("Validating and inventorying the ZIP…", async () => {
    if (forge.dirty) throw new Error("Save your current review before importing another pack.");
    const form = e.target, file = form.elements.source.files[0];
    if (!file || file.size > 32 * 1024 * 1024) throw new Error("Choose a ZIP up to 32 MiB.");
    const bytes = await file.arrayBuffer();
    const digest = Array.from(new Uint8Array(await crypto.subtle.digest("SHA-256", bytes))).map(x => x.toString(16).padStart(2,"0")).join("");
    const payload = {title:form.elements.title.value, taxonomy:form.elements.taxonomy.value};
    const canonical = JSON.stringify({...payload, digest});
    if (!forge.pending.has(canonical)) forge.pending.set(canonical, crypto.randomUUID());
    const query = new URLSearchParams({...payload, request_id:forge.pending.get(canonical)});
    const created = await api(`${forgeRoot}?${query}`, {method:"POST", body:bytes, headers:{"Content-Type":"application/zip"}});
    forge.pending.delete(canonical);
    await forgeLoad(created.id); await forgeRefresh(); form.reset();
  });
});
