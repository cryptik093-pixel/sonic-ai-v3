"use strict";
// UI contracts only. All musical behavior lives in shared Python services.
const studio = {proposal:null, explicit:new Set(), editingRun:null};
const studioTracks = ["Melody","Chords","Bass","Drums","Countermelody"];
const studioFields = [
 ["cadence","Final harmony",["resolve","loop"],"resolve"],
 ["max_melodic_leap","Maximum melodic leap · semitones",[3,12],7,"number"],
 ["counter_mode","Counter-melody mode",["response","parallel"],"response"],
 ["progression_rate","Harmonic rate · bars",[1,2,4],2],
 ["chord_type","Chord type",["triad","seventh","ninth"],"triad"],
 ["voicing","Voicing",["close","open"],"close"],
 ["contour","Melody contour",["balanced","ascending","descending","arch"],"balanced"],
 ["motif_variation","Motif variation · %",[0,100],25,"number"],
 ["syncopation","Syncopation · %",[0,100],30,"number"],
 ["swing","Swing · % (50 = straight)",[50,67],50,"number"],
 ["timing_ms","Timing humanization · ms",[0,30],8,"number"],
 ["velocity_variation","Velocity variation",[0,20],6,"number"],
 ["chord_spread_ms","Chord strum spread · ms",[0,40],15,"number"],
 ["bass_mode","Bass mode",["sustained","rhythmic"],"rhythmic"],
 ["drum_feel","Drum feel",["half-time","backbeat"],"half-time"],
 ["hat_subdivision","Hat subdivisions",["eighth","sixteenth"],"eighth"],
 ["phrase_ending","Phrase ending",["tonic","open"],"tonic"]
];
const controls=document.getElementById("studio-controls");
controls.innerHTML=`<div class="studio-tracks">${studioTracks.map(t=>`<label class="check-label"><input type="checkbox" name="track_${t}" ${t==="Countermelody"?"":"checked"}>${t}</label>`).join("")}</div>
<details class="studio-advanced"><summary>Advanced musical controls</summary>
<label>Progression · scale degrees 1–7<input name="settings.progression" placeholder="Style default, or 1, 6, 3, 7"></label>
<label class="check-label"><input type="checkbox" name="settings.drum_fills" checked>Phrase-end drum fills</label>
<label class="check-label"><input type="checkbox" name="settings.smooth_voice_leading" checked>Smooth voice leading</label>
${studioFields.map(([name,label,options,value,type])=>type==="number"?`<label>${label}<input name="settings.${name}" type="number" min="${options[0]}" max="${options[1]}" value="${value}" required></label>`:`<label>${label}<select name="settings.${name}">${options.map(v=>`<option value="${v}" ${v===value?"selected":""}>${v}</option>`).join("")}</select></label>`).join("")}
${[["melody",60,88,80],["chords",45,79,65],["bass",24,47,88],["countermelody",60,79,62]].map(([t,low,high,vel])=>`<fieldset><legend>${t[0].toUpperCase()+t.slice(1)} performance</legend><div class="form-row"><label>Lowest MIDI pitch<input type="number" name="settings.${t}_range.low" min="0" max="127" value="${low}" required></label><label>Highest MIDI pitch<input type="number" name="settings.${t}_range.high" min="0" max="127" value="${high}" required></label></div><label>Base velocity<input type="number" name="settings.${t}_velocity" min="1" max="127" value="${vel}" required></label></fieldset>`).join("")}
<label>Drum base velocity<input type="number" name="settings.drums_velocity" min="1" max="127" value="75" required></label></details>`;

function readStudioCommand(form) {
  const p={};
  for(const k of ["title","style","key","scale","density","prompt","interpretation_method"]) p[k]=form.elements.namedItem(k).value;
  for(const k of ["bpm","bars","seed"]) p[k]=Number(form.elements.namedItem(k).value);
  if(form.elements.engine_mode.value==="legacy") {
    delete p.prompt;delete p.interpretation_method;return p;
  }
  p.settings={version:2,enabled_tracks:studioTracks.filter(t=>form.elements.namedItem("track_"+t).checked)};
  for(const field of form.querySelectorAll('[name^="settings."]')) {
    const keys=field.name.split(".").slice(1);
    let value=field.type==="checkbox"?field.checked:field.type==="number"?Number(field.value):field.value;
    if(keys[0]==="progression") { value=field.value.trim()?field.value.split(/[ ,]+/).map(Number):null; }
    if(keys[0]==="progression_rate") value=Number(value);
    if(keys.length===2) (p.settings[keys[0]]??={})[keys[1]]=value;
    else p.settings[keys[0]]=value;
  }
  return p;
}
function applyStudioSettings(command) {
  const form=document.getElementById("midi-form");
  form.elements.engine_mode.value=command.settings?"studio":"legacy";
  for(const k of ["title","style","key","scale","density","prompt","interpretation_method","bpm","bars","seed"]) {
    if(command[k]!==undefined) form.elements.namedItem(k).value=command[k];
  }
  const s=command.settings;
  if(s) {
    for(const t of studioTracks) form.elements.namedItem("track_"+t).checked=s.enabled_tracks.includes(t);
    for(const field of form.querySelectorAll('[name^="settings."]')) {
      const keys=field.name.split(".").slice(1);const value=keys.reduce((v,k)=>v?.[k],s);
      if(value!==undefined) { if(field.type==="checkbox") field.checked=value;else field.value=keys[0]==="progression"?(value||[]).join(", "):value; }
    }
  }
}
function studioResult(run) {
  const r=run.result;
  if(!r.resolved_settings)return `<p class="fine">Legacy v1. Reuse settings and select MIDI Studio to create an upgraded generation.</p><button class="secondary" data-reuse-midi="${run.id}">Reuse settings</button>`;
  const measurements=r.quality?.measurements||{};
  return `<div class="studio-report"><span class="eyebrow">GENERATION STATE</span><p>${r.quality?.technical?.passed?"Technical MIDI checks passed":"Review technical checks"} · musical acceptance pending</p>
  ${r.parent_run_id?`<p>Parent ${esc(r.parent_run_id.slice(0,8))} · preserved ${esc((r.revision?.preserved_tracks||[]).join(", "))}</p>`:""}
  <p>${esc(r.resolved_settings.prompt||"Manual musical settings")}</p>
  <details><summary>Resolved settings and measurements</summary><pre>${esc(JSON.stringify({settings:r.resolved_settings,measurements},null,2))}</pre></details>
  <p class="fine">Reuse settings to edit this run. Edit controls or the displayed seed, then choose tracks to regenerate; other notes are preserved exactly. Global key, scale, tempo and length changes require unlocking all parent tracks.</p>
  <div class="button-row"><button class="secondary" data-reuse-midi="${run.id}">Reuse settings</button><button class="secondary" data-regenerate-midi="${run.id}">Regenerate all</button></div>
  <div class="studio-tracks">${studioTracks.map(t=>`<label class="check-label"><input type="checkbox" data-revise-track="${t}" ${r.tracks.includes(t)?"":"disabled"}>${t}</label>`).join("")}</div>
  <button class="secondary" data-revise="${run.id}">Revise selected tracks</button></div>`;
}
function settingsDiff(before,after) {
  const patch={};
  for(const [key,value] of Object.entries(after)) {
    if(["request_id","project_id","seed"].includes(key)) continue;
    if(JSON.stringify(before[key])===JSON.stringify(value))continue;
    if(key==="settings") {
      patch.settings={};
      for(const [k,v] of Object.entries(value)) if(JSON.stringify(before.settings?.[k])!==JSON.stringify(v)) patch.settings[k]=v;
    } else patch[key]=value;
  }
  return patch;
}
const midiForm=document.getElementById("midi-form");
midiForm.addEventListener("change",e=>{
  const name=e.target.name;
  if(!name||["prompt","use_cloud","engine_mode","interpretation_method"].includes(name))return;
  studio.explicit.add(name.startsWith("track_")?"settings.enabled_tracks":name.includes("_range.")?name.slice(0,name.lastIndexOf(".")):name);
  midiForm.elements.interpretation_method.value="manual";
  updateRevisionSelectors();
});
document.getElementById("interpret-midi").addEventListener("click",()=>busy("Interpreting your musical direction…",async()=>{
  const current=readStudioCommand(midiForm);
  if(!current.settings) throw new Error("Select MIDI Studio before interpreting.");
  const result=await api("/midi/interpret",{method:"POST",body:JSON.stringify({prompt:current.prompt,current,use_cloud:midiForm.elements.use_cloud.checked,explicit_fields:[...studio.explicit]})});
  studio.proposal={...result, baseline:current};
  const box=document.getElementById("midi-proposal");box.hidden=false;box.className="studio-proposal";
  box.innerHTML=`<strong>${esc(result.method)} · ${esc(result.status)}</strong><p>Review the proposal. Generation uses the controls you apply and edit.</p><pre class="report-copy">${esc(JSON.stringify(result.proposed_settings,null,2))}</pre>${result.unresolved.map(x=>`<p>Unhandled: ${esc(x)}</p>`).join("")}${result.warnings.map(x=>`<p>${esc(x)}</p>`).join("")}<button type="button" id="apply-midi-proposal" class="secondary">Apply proposed settings</button>`;
}));
document.addEventListener("click",e=>{
  const button=e.target.closest("button");if(!button)return;
  if(button.id==="apply-midi-proposal"&&studio.proposal) {
    const current=readStudioCommand(midiForm);
    if(!current.settings) { reportError(new Error("Select MIDI Studio to apply the proposal.")); return; }
    const proposal=structuredClone(studio.proposal.proposed_settings), baseline=studio.proposal.baseline;
    for(const [k,v] of Object.entries(current)) {
      if(k==="settings") {
        for(const [name,value] of Object.entries(v)) if(JSON.stringify(baseline.settings?.[name])!==JSON.stringify(value)) proposal.settings[name]=value;
      } else if(JSON.stringify(baseline[k])!==JSON.stringify(v)) proposal[k]=v;
    }
    applyStudioSettings(proposal);updateRevisionSelectors();document.getElementById("midi-proposal").hidden=true;values(midiForm);
  }
  const id=button.dataset.reuseMidi||button.dataset.regenerateMidi||button.dataset.revise;
  if(!id)return;
  busy("Preparing your MIDI generation…",async()=>{
    const run=await api("/runs/"+id);
    const base=run.result.resolved_settings||run.request;
    if(button.dataset.reuseMidi) {applyStudioSettings(base);studio.explicit.clear();studio.editingRun=id;showView("midi");values(midiForm);return;}
    let child;
    if(button.dataset.regenerateMidi) {
      const template={action:"regenerate",parent_run_id:id,base};
      child=await pendingStudioAction("regenerate",template,"midi",()=>{
        const p={...base,seed:Math.floor(Math.random()*2147483647)};delete p.request_id;return p;
      });
    } else {
      const selected=[...button.closest(".rendered").querySelectorAll("[data-revise-track]:checked")].map(x=>x.dataset.reviseTrack);
      if(!selected.length)throw new Error("Select at least one track to revise.");
      const after=studio.editingRun===id?readStudioCommand(midiForm):base;
      if(!after.settings)throw new Error("Revisions require MIDI Studio settings.");
      const payload={parent_run_id:id,regenerate_tracks:selected,seed:after.seed,settings_patch:settingsDiff(base,after)};
      child=await command("midi/revise",payload);
    }
    applyStudioSettings(child.result.resolved_settings||child.request);studio.editingRun=child.id;showView("midi");
    await showRun(child,document.getElementById("midi-result"));values(midiForm);
  });
});

function updateRevisionSelectors() {
  if(!studio.editingRun)return;
  const form=document.getElementById("midi-form");
  for(const rendered of document.querySelectorAll(".rendered")) {
    if(rendered.dataset.outputId!==studio.editingRun)continue;
    for(const box of rendered.querySelectorAll("[data-revise-track]")) {
      box.disabled=!form.elements.namedItem("track_"+box.dataset.reviseTrack).checked;
      if(box.disabled)box.checked=false;
    }
  }
}
async function pendingStudioAction(name, template, kind, createPayload) {
  const key="sonic-action-"+name, canonical=JSON.stringify(template);
  let pending=storedJSON(key,null);
  if(!plainObject(pending)||pending.canonical!==canonical||!plainObject(pending.payload)||!Number.isInteger(pending.payload.seed)) {
    pending={canonical,payload:createPayload()};localStorage.setItem(key,JSON.stringify(pending));
  }
  const run=await command(kind,pending.payload);
  localStorage.removeItem(key);
  return run;
}
