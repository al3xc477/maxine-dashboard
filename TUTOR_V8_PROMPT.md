# Tutor v8 — Observer profile, baseline sweep, micro-missions, narrative upgrade

You are implementing improvements to the Tutor tab in `Maxine_Dashboard.html`.
**Workstreams A → H are already applied and verified** (file at 1 182 775 bytes, parse-clean).
**All workstreams complete — no further implementation needed.**
Do NOT re-apply A–G. Do NOT modify any code outside the targeted functions/sections
unless explicitly instructed.

---

## GUARD RAILS

- NO REMOTE COMMIT — the user commits manually after review.
- Do NOT touch `state.children.Maxine` or any existing mastery data.
- `saveState(state)` takes one argument; never call `saveState()` without it.
- Cross-child guard pattern (required in every new async function):
  ```
  if (typeof getActiveChildId === "function" && getActiveChildId() !== childId) return;
  ```
- Every new state key added to the working set MUST also be added to `PER_CHILD_KEYS`.
- Follow the existing `escapeHtml()` pattern for all user-generated strings in HTML.
- Do not remove or rename any existing function.

---

## ⚠️ FILE RECONCILIATION NOTES — read before touching any workstream

These were discovered during Workstream A implementation. Apply them everywhere the
affected patterns appear — not just in the workstream that first introduces them.

**R1 — `skill.age_min` does not exist in this codebase.**
Use `skillAgeMinMonths(skill)` (already a helper in the file) everywhere the spec
writes `skill.age_min` or `sk.age_min`. This applies in `_estimateEarlyTs` (already
corrected in A) and anywhere else age-based estimates appear.

**R2 — `_installMmHook` is NOT an IIFE in this file.**
The v10 meta-milestone hook is a bare `addObservation = function(args){…}` reassignment,
not wrapped in `(function _installMmHook(){…})()`. When D3b says "append IMMEDIATELY
AFTER the closing `})();` of the existing `_installMmHook` IIFE", instead append after
the bare addObservation reassignment block. `_installMissionsHook` re-wraps the already-
wrapped addObservation — that chaining is intentional and fine; verify chain is intact.

**R3 — Verify these HTML/JS anchors exist before using them as FIND targets:**
Before each workstream, grep for its key anchors:
- `v7TutorTitle`, `v7TutorNarrative`, `v7TutorSnapshot`, `v7TutorPriorities`,
  `v7TutorHorizons` — expected inside `<section id="tutorView">`
- `// Horizons` comment — expected inside `renderTutorTab()`
- Helper functions: `getActiveDomainKeys`, `pickDomainSpotlight`, `getKeystoneGaps`,
  `getStalledSkills`, `pendingMasteryConfirmations`, `currentTier`, `activeEra`, `ERAS`
If any anchor is missing or named differently, grep variants and adjust the FIND target.
Do NOT assume the spec's exact string is present — always confirm first.

**R4 — ERA_TRANSITION_QUESTIONS keys must match the actual ERAS array.**
C+2 uses keys `"infant_late"`, `"toddler"`, `"preschool"` as guesses. Before writing
the constant, run:
```bash
grep -o '"key":"[^"]*"' Maxine_Dashboard.html | head -30
```
and grep for the ERAS array definition. Adjust keys to match exactly what's in the file.
Verification checklist item 13 covers this.

**R5 — PER_CHILD_KEYS current state (post-A).**
The line currently ends: `"metaMilestones","masteredAt"`. B3 must expand this. Use the
exact replacement string in B3 — do not attempt to append; replace the whole line.

**R6 — File uses CRLF line endings (OneDrive).**
After each workstream: check byte count and run `node --check`. If the file is
unexpectedly smaller, OneDrive may have re-truncated it. Stop and report before
continuing.

**R7 — `skill.keystone` DOES exist.** Confirmed ✓ — no substitution needed.

**R8 — ERA keys confirmed (from B–G run).**
Actual ERAS keys are `"infant"`, `"early_childhood"`, `"school_age"` (not `infant_late` /
`toddler` / `preschool`). The C+ workstream mapped toddler-stage questions under `"infant"`
(0–36m) and preschool under `"early_childhood"` (36–72m). Do not re-introduce the old keys.

**R9 — `_installMmHook` IS an IIFE (R2 was wrong).**
In the actual file it IS `(function _installMmHook(){…})()`. R2's note was incorrect.
`_installMissionsHook` was appended after `})();` — chain is intact. No action needed.

**R10 — z-index ceiling: floating chat FAB is at 9 000.**
The Horizon chat button (`#hz-btn`) is `z-index:9000`, panel `9001`, toast `9100`.
All new overlays and modals MUST use z-index ≥ 9200. The F6 fix already raised modals to
overlay:9200 / sheet:9201 / close:9202 / info-popup:9500. Workstream H must stay above 9200.

**R11 — Push-chip label: `k.label || k.t || k.id`.**
`getKeystoneGaps()` returns objects with a `.label` field, not `.t`. Always use
`k.label || k.t || k.id` when rendering skill names from keystone-gap objects.

**R12 — Verified function/element names (from B–G run).**
These names are confirmed present in the post-G file:
- `renderTutorTab()` — main tutor render function
- `isSkillMastered(id)` ✓
- `classifySkillFrontier(id)` ✓ (returns "mastered","verify","ready","stretch","locked","below")
- `buildZPDPoolV10()` ✓
- `_calcXP()` ✓ (added by F2)
- `_openSkillPopup(skillId)` ✓ (added by F3)
- `addObservation({…})` ✓
- `escapeHtml(str)` ✓
- `currentChild()` ✓
- `state.masteredAt` ✓ (added by A)
- `state.skillStatus[id].ts` ✓
- `state.weeklyMissions.missions` ✓ (added by D)
- `SKILLS` array ✓
- `state.skillsCustom` array ✓
- `state.observations[]` ✓

---

---

## ✅ WORKSTREAM A — ALREADY APPLIED (do not re-apply)
### `_estimateEarlyTs` + skip time-picker for below-frontier skills
*Verified at 1 107 854 bytes, parse-clean, node --check passes. Uses `skillAgeMinMonths(skill)` — see R1.*

### A1: Add `_estimateEarlyTs(skill)` helper

Insert IMMEDIATELY BEFORE `function setSkillStatus(id, status)` (FIND: that exact
function signature):

```javascript
/* _estimateEarlyTs(skill) — best-guess "when the child probably mastered this"
   for below-frontier skills where the parent didn't observe it live.
   Uses skill.age_min (months) + child's dob; floors at dob + 90 days (so we
   never produce a ts before birth). Returns an integer timestamp (ms).         */
function _estimateEarlyTs(skill){
  const child = (typeof currentChild === "function") ? currentChild() : null;
  const dobTs = child && child.dob ? new Date(child.dob).getTime() : 0;
  const MONTH_MS = 30.5 * 86400000;
  const ageMin = (skill && typeof skill.age_min === "number" && skill.age_min > 0)
    ? skill.age_min : 12;                          // fallback to 12m if unset
  const estimated = dobTs + ageMin * MONTH_MS;
  const floor    = dobTs + 90 * 86400000;          // at least 90 days after birth
  const cap      = Date.now() - 7 * 86400000;      // no later than 1 week ago
  return Math.min(cap, Math.max(floor, estimated));
}
```

### A2: Modify `setSkillStatus` to skip picker for below-frontier

Replace the existing `function setSkillStatus(id, status)` body with:

```javascript
function setSkillStatus(id, status){
  // v10: when marking mastered for the FIRST time, ask WHEN it became reliable
  // (velocity correction — retroactive discoveries shouldn't inflate recent pace).
  if (status === "mastered" && typeof isSkillMastered === "function" && !isSkillMastered(id)){
    // v8: below-frontier skills — skip the modal; auto-estimate from age_min.
    const pool = [...SKILLS, ...(SKILLS_CUSTOM_SEED||[]), ...(Array.isArray(state.skillsCustom) ? state.skillsCustom : [])];
    const sk = pool.find(s => s.id === id);
    if (sk && typeof classifySkillFrontier === "function" && classifySkillFrontier(sk) === "below"){
      addObservation({ skillId:id, status, source:"manual", estimated_ts: _estimateEarlyTs(sk) });
    } else {
      _showMasteryTimePicker(id, (estimated_ts) => {
        addObservation({ skillId:id, status, source:"manual", estimated_ts });
      });
    }
  } else {
    addObservation({ skillId:id, status, source:"manual" });
  }
}
```

---

## WORKSTREAM B — Baseline sweep card

### B1: Add CSS for baseline sweep (inside the existing `/* v7 — Tutor tab` CSS block)

Insert after the line `.v7-tutor-horizons li{ margin-bottom:6px; }` and before
the `@media (max-width:640px)` block:

```css
/* v8 — Baseline sweep */
.v8-sweep-domain{
  background:#F0FDF4; border:1px solid #BBF7D0; border-radius:10px;
  padding:10px 12px; margin-bottom:8px;
}
.v8-sweep-domain-h{
  display:flex; justify-content:space-between; align-items:center;
  font-weight:700; font-size:13px; color:#14532D; margin-bottom:6px; flex-wrap:wrap; gap:6px;
}
.v8-sweep-chips{
  display:flex; flex-wrap:wrap; gap:4px; margin-bottom:8px;
}
.v8-sweep-chip{
  font-size:11px; background:#fff; border:1px solid #BBF7D0; border-radius:6px;
  padding:2px 7px; color:var(--ink);
}
.v8-sweep-dismiss{
  font-size:11px; color:var(--muted); background:none; border:none;
  cursor:pointer; padding:0; text-decoration:underline;
}
```

### B2: Add HTML `div` for baseline sweep in the Tutor section

Inside `<section id="tutorView">`, INSERT the following block IMMEDIATELY AFTER
the `</div>` that closes the hero card (the card containing `v7TutorNarrative`),
and BEFORE the Snapshot card (`<div class="card v7-tutor-section"` that has
`v7TutorSnapshot` inside it):

```html
    <!-- v8 — Baseline sweep (below-frontier bulk mastery) -->
    <div id="v8TutorBaseline" style="display:none; margin-bottom:14px"></div>
```

### B3: Add `state.baselineSweepDismissed` to `PER_CHILD_KEYS`

FIND the line:
```
  "metaMilestones","masteredAt"
```
Replace it with:
```
  "metaMilestones","masteredAt","baselineSweepDismissed","observerProfile","weeklyMissions"
```

(This also covers the new keys from workstreams C and D.)

### B4: Add `defaultForKey` entries for the new keys

FIND the `function defaultForKey(k)` body. After the existing lines, add before
the `return _PCK_ARRAY.has(k)` line:

```javascript
  if (k === "baselineSweepDismissed") return {};
  if (k === "observerProfile") return { answers:{}, answered_at:{}, skipped:[] };
  if (k === "weeklyMissions")  return null;
```

### B5: Add `bulkBaselineSweep(domKey)` helper

Insert IMMEDIATELY BEFORE `function renderTutorTab()` (FIND: that exact function
declaration):

```javascript
/* bulkBaselineSweep — marks all unmastered `below`-class skills in a domain as
   already_mastered with an auto-estimated ts. No modal. Persists immediately.  */
function bulkBaselineSweep(domKey){
  const pool = [...SKILLS, ...(SKILLS_CUSTOM_SEED||[]), ...(Array.isArray(state.skillsCustom) ? state.skillsCustom : [])];
  const targets = pool.filter(s =>
    s && s.dom === domKey &&
    !isSkillMastered(s.id) &&
    (typeof classifySkillFrontier === "function") && classifySkillFrontier(s) === "below"
  );
  if (!targets.length){ if (typeof showToast==="function") showToast("Nothing to sweep"); return; }
  targets.forEach(sk => {
    addObservation({ skillId:sk.id, status:"already_mastered", source:"baseline_sweep",
                     estimated_ts: _estimateEarlyTs(sk) });
  });
  if (typeof showToast==="function") showToast(`✓ ${targets.length} skill${targets.length===1?"":"s"} marked as already known`);
  try { renderTutorTab(); } catch(e){}
}

/* renderTutorBaseline — populates #v8TutorBaseline.
   Shows when ≥1 domain has unmastered below-class skills (and hasn't been dismissed). */
function renderTutorBaseline(){
  const el = document.getElementById("v8TutorBaseline");
  if (!el) return;
  state.baselineSweepDismissed = state.baselineSweepDismissed || {};
  const pool = [...SKILLS, ...(SKILLS_CUSTOM_SEED||[]), ...(Array.isArray(state.skillsCustom) ? state.skillsCustom : [])];
  const active = (typeof getActiveDomainKeys==="function") ? getActiveDomainKeys() : DOMAINS.map(d=>d.key);

  // Collect below-class unmastered skills per domain, excluding dismissed domains.
  const byDomain = {};
  active.forEach(dk => {
    if (state.baselineSweepDismissed[dk]) return;
    const belowSkills = pool.filter(s =>
      s && s.dom===dk && !isSkillMastered(s.id) &&
      (typeof classifySkillFrontier==="function") && classifySkillFrontier(s)==="below"
    );
    if (belowSkills.length) byDomain[dk] = belowSkills;
  });

  if (!Object.keys(byDomain).length){ el.style.display="none"; return; }

  const childName = ((typeof currentChild==="function" ? currentChild() : null)||{}).name || "the child";
  let html = `<div class="card v7-tutor-section">
    <h3 class="v7-tutor-h">🗂️ Baseline sweep</h3>
    <p style="font-size:13px; color:var(--muted); margin:0 0 10px">
      These skills are below ${escapeHtml(childName)}'s current level — does ${escapeHtml(childName)} already know them?
      Marking them avoids clutter and improves velocity accuracy.
    </p>`;

  Object.entries(byDomain).forEach(([dk, skills]) => {
    const dom = DOMAINS.find(d=>d.key===dk) || { emoji:"·", label:dk };
    const chips = skills.slice(0,8).map(s =>
      `<span class="v8-sweep-chip">${escapeHtml(s.t||s.id)}</span>`
    ).join("") + (skills.length>8 ? `<span class="v8-sweep-chip" style="color:var(--muted)">+${skills.length-8} more</span>` : "");
    html += `<div class="v8-sweep-domain">
      <div class="v8-sweep-domain-h">
        <span>${dom.emoji} ${escapeHtml(dom.label)} — ${skills.length} skill${skills.length===1?"":"s"}</span>
        <div style="display:flex; gap:8px; align-items:center; flex-wrap:wrap">
          <button class="small primary" data-v8-sweep-domain="${escapeHtml(dk)}">✓ Already known</button>
          <button class="v8-sweep-dismiss" data-v8-sweep-dismiss="${escapeHtml(dk)}">Dismiss</button>
        </div>
      </div>
      <div class="v8-sweep-chips">${chips}</div>
    </div>`;
  });

  html += `</div>`;
  el.innerHTML = html;
  el.style.display = "";
}
```

### B6: Wire baseline sweep click handlers

FIND the click delegation block for tutor pending confirmations:
```
/* Pending-confirmation click delegation (✓ Mastered / ⏳ Still working). */
document.addEventListener("click", (e) => {
```

REPLACE the entire block (up to and including its closing `});`) with this
extended version (which keeps the existing pending handlers and adds sweep
handlers):

```javascript
/* Pending-confirmation + baseline sweep click delegation. */
document.addEventListener("click", (e) => {
  // Pending: ✓ Mastered
  const conf = e.target.closest("[data-v7-tutor-confirm]");
  if (conf){
    const id = conf.dataset.v7TutorConfirm;
    if (typeof addObservation === "function"){
      addObservation({ skillId: id, status: "mastered", source: "tutor_pending_confirm" });
    }
    if (typeof showToast === "function") showToast("✓ Declared mastered");
    try { renderTutorTab(); } catch(err){ console.warn("tutor re-render failed", err); }
    return;
  }
  // Pending: ⏳ Still working
  const sup = e.target.closest("[data-v7-tutor-suppress]");
  if (sup){
    const id = sup.dataset.v7TutorSuppress;
    state.suppressedConfirmations = state.suppressedConfirmations || {};
    state.suppressedConfirmations[id] = Date.now();
    if (typeof saveState === "function") saveState(state);
    if (typeof showToast === "function") showToast("⏳ Suppressed for 14 days");
    try { renderTutorTab(); } catch(err){ console.warn("tutor re-render failed", err); }
    return;
  }
  // Baseline sweep: ✓ Already known
  const sweepBtn = e.target.closest("[data-v8-sweep-domain]");
  if (sweepBtn){
    const dk = sweepBtn.dataset.v8SweepDomain;
    bulkBaselineSweep(dk);
    return;
  }
  // Baseline sweep: Dismiss
  const dismissBtn = e.target.closest("[data-v8-sweep-dismiss]");
  if (dismissBtn){
    const dk = dismissBtn.dataset.v8SweepDismiss;
    state.baselineSweepDismissed = state.baselineSweepDismissed || {};
    state.baselineSweepDismissed[dk] = Date.now();
    if (typeof saveState === "function") saveState(state);
    try { renderTutorTab(); } catch(err){}
    return;
  }
  // Observer Q&A: Save answer
  const saveQBtn = e.target.closest("[data-v8-profile-save]");
  if (saveQBtn){
    const qId = saveQBtn.dataset.v8ProfileSave;
    const input = document.getElementById(`v8-profile-input-${qId}`);
    const answer = (input && input.value) ? input.value.trim() : "";
    if (!answer){ if (typeof showToast==="function") showToast("Type an answer first"); return; }
    state.observerProfile = state.observerProfile || { answers:{}, answered_at:{}, skipped:[] };
    state.observerProfile.answers[qId]     = answer;
    state.observerProfile.answered_at[qId] = Date.now();
    if (typeof saveState === "function") saveState(state);
    if (typeof showToast==="function") showToast("💾 Saved");
    try { renderTutorTab(); } catch(err){}
    return;
  }
  // Observer Q&A: Skip question
  const skipQBtn = e.target.closest("[data-v8-profile-skip]");
  if (skipQBtn){
    const qId = skipQBtn.dataset.v8ProfileSkip;
    state.observerProfile = state.observerProfile || { answers:{}, answered_at:{}, skipped:[] };
    if (!state.observerProfile.skipped.includes(qId)) state.observerProfile.skipped.push(qId);
    if (typeof saveState === "function") saveState(state);
    try { renderTutorTab(); } catch(err){}
    return;
  }
  // Weekly missions: Done today!
  const missionBtn = e.target.closest("[data-v8-mission-skill]");
  if (missionBtn){
    const sid = missionBtn.dataset.v8MissionSkill;
    if (typeof addObservation==="function"){
      addObservation({ skillId:sid, status:"working_on_it", source:"weekly_mission" });
    }
    missionBtn.textContent = "✓ Logged!";
    missionBtn.disabled = true;
    missionBtn.style.opacity = "0.5";
    if (typeof showToast==="function") showToast("📝 Logged — keep at it!");
    return;
  }
  // Weekly missions: Refresh
  const refreshMissionsBtn = e.target.closest("[data-v8-missions-refresh]");
  if (refreshMissionsBtn){
    state.weeklyMissions = null;
    if (typeof saveState==="function") saveState(state);
    try { renderTutorTab(); } catch(err){}
    return;
  }
});
```

### B7: Call `renderTutorBaseline()` inside `renderTutorTab()`

FIND the line at the top of `renderTutorTab()`:
```javascript
  if (!narr) return;
```

INSERT immediately AFTER that line:
```javascript
  // v8 — Baseline sweep card
  renderTutorBaseline();
```

---

## WORKSTREAM C — Observer Q&A system

### C1: Add `OBSERVER_QUESTIONS` constant

Insert IMMEDIATELY BEFORE `function renderTutorTab()` (just before the block
added in B5 — i.e., before `_estimateEarlyTs`):

```javascript
/* OBSERVER_QUESTIONS — the tutor asks these one at a time to build a
   `state.observerProfile` for this child. 10 questions total.
   {text} uses {name} as a template variable — replaced at render time.      */
const OBSERVER_QUESTIONS = [
  { id:"q_learning_style", text:"How does {name} learn best — by watching, by doing, or by hearing/talking through things?",      category:"learning",  example:"e.g. \"she copies everything she sees\" / \"needs to touch it\" / \"talks to herself while practising\"" },
  { id:"q_attention_span", text:"How long can {name} typically stay focused on a chosen activity before losing interest?",         category:"energy",    example:"e.g. \"5 minutes\" / \"20+ minutes if it's her idea\"" },
  { id:"q_motivators",     text:"What does {name} love most right now?",                                                           category:"interests", example:"e.g. books, running outdoors, music, drawing, pretend play, puzzles, water" },
  { id:"q_social_context", text:"Does {name} engage better one-on-one with an adult, or with other children around?",             category:"social",    example:"e.g. \"needs one adult\" / \"thrives with 1-2 peers\" / \"fine either way\"" },
  { id:"q_languages",      text:"Which languages does {name} hear daily, and which does she produce most?",                       category:"language",  example:"e.g. \"hears French and English; mostly speaks English\"" },
  { id:"q_sensory",        text:"Any sensory sensitivities worth knowing about?",                                                  category:"sensory",   example:"e.g. loud sounds, certain textures, bright lights, or no sensitivities at all" },
  { id:"q_best_time",      text:"What time of day is {name} most alert and receptive to new things?",                             category:"energy",    example:"e.g. \"mid-morning 9–11 am\" / \"after her nap\"" },
  { id:"q_challenge",      text:"What's the one thing you'd most like to see improve for {name} over the next 3 months?",         category:"goals",     example:"e.g. \"more independence\" / \"better focus\" / \"catch up on language\" / \"social confidence\"" },
  { id:"q_caregiver_style",text:"How would you describe your approach with {name} in one or two words?",                          category:"context",   example:"e.g. \"playful, low-pressure\" / \"structured routines\" / \"child-led\" / \"busy household\"" },
  { id:"q_context",        text:"Any other context the tutor should know? (siblings, big routine changes, life events, etc.)",    category:"context",   example:"e.g. \"new baby sibling\" / \"just moved house\" / \"attends Montessori 3×/week\"" }
];
```

### C2: Add HTML `div` for observer profile in the Tutor section

INSERT the following IMMEDIATELY AFTER `<div id="v8TutorBaseline" style="display:none; margin-bottom:14px"></div>` (added in B2):

```html
    <!-- v8 — Observer Q&A -->
    <div id="v8TutorProfile" style="display:none; margin-bottom:14px"></div>
```

### C3: Add CSS for observer Q&A (inside the `/* v7 — Tutor tab` CSS block)

Insert AFTER the `.v8-sweep-dismiss` block (added in B1), still before `@media (max-width:640px)`:

```css
/* v8 — Observer profile Q&A */
.v8-profile-card{
  background:linear-gradient(135deg, #FFF7ED, #FFFBEB);
  border:1px solid #FDE68A; border-radius:12px; padding:14px 16px;
}
.v8-profile-progress{
  font-size:11px; color:#92400E; font-weight:700; margin-bottom:8px;
}
.v8-profile-q{
  font-size:14px; font-weight:700; color:var(--ink); margin-bottom:4px;
}
.v8-profile-example{
  font-size:11px; color:var(--muted); margin-bottom:10px; font-style:italic;
}
.v8-profile-input{
  width:100%; box-sizing:border-box; border:1px solid #FCD34D; border-radius:8px;
  padding:8px 10px; font-size:13px; resize:none; min-height:48px;
  font-family:inherit; margin-bottom:8px;
}
.v8-profile-input:focus{ outline:none; border-color:#F59E0B; }
.v8-profile-actions{ display:flex; gap:8px; align-items:center; flex-wrap:wrap; }
.v8-profile-complete{
  background:#F0FDF4; border:1px solid #BBF7D0; border-radius:10px;
  padding:10px 14px; font-size:13px; color:#14532D;
  display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; gap:8px;
}
```

### C4: Add `renderObserverProfile()` function

Insert IMMEDIATELY BEFORE `function renderTutorTab()` (after the `OBSERVER_QUESTIONS`
constant, before `_estimateEarlyTs`):

```javascript
/* renderObserverProfile — shows the next unanswered question, or completion badge. */
function renderObserverProfile(){
  const el = document.getElementById("v8TutorProfile");
  if (!el) return;
  const child = (typeof currentChild==="function") ? currentChild() : null;
  const cName = (child && child.name) || "the child";
  state.observerProfile = state.observerProfile || { answers:{}, answered_at:{}, skipped:[] };
  const prof = state.observerProfile;
  const total = OBSERVER_QUESTIONS.length;
  const answered = OBSERVER_QUESTIONS.filter(q => prof.answers[q.id]).length;
  // Find next unanswered, non-skipped question (cycle: skipped ones shown after all answered)
  const unanswered = OBSERVER_QUESTIONS.filter(q => !prof.answers[q.id] && !prof.skipped.includes(q.id));
  const skippedOnly = !unanswered.length && prof.skipped.length > 0;
  const next = unanswered[0] || (skippedOnly ? OBSERVER_QUESTIONS.find(q => prof.skipped.includes(q.id)) : null);

  if (answered >= total){
    el.innerHTML = `<div class="v8-profile-complete">
      <span>✅ Profile complete — ${total}/${total} questions answered</span>
      <button class="small ghost" data-v8-profile-reset style="font-size:11px">✏️ Edit</button>
    </div>`;
    el.style.display = "";
    return;
  }
  if (!next){ el.style.display = "none"; return; }

  const qText = next.text.replace(/\{name\}/g, escapeHtml(cName));
  el.innerHTML = `<div class="v8-profile-card">
    <div class="v8-profile-progress">💬 Help me understand ${escapeHtml(cName)} · ${answered}/${total} answered</div>
    <div class="v8-profile-q">${qText}</div>
    <div class="v8-profile-example">${escapeHtml(next.example)}</div>
    <textarea class="v8-profile-input" id="v8-profile-input-${next.id}"
      placeholder="Your answer…"
      rows="2">${escapeHtml(prof.answers[next.id]||"")}</textarea>
    <div class="v8-profile-actions">
      <button class="small primary" data-v8-profile-save="${next.id}">💾 Save</button>
      <button class="small ghost"   data-v8-profile-skip="${next.id}">Skip for now</button>
    </div>
  </div>`;
  el.style.display = "";
}
```

Also add a profile-reset handler. FIND the line in the click delegation block:
```
  // Weekly missions: Refresh
```
INSERT before it:
```javascript
  // Observer Q&A: Reset / edit profile
  const resetQBtn = e.target.closest("[data-v8-profile-reset]");
  if (resetQBtn){
    if (!confirm("Clear all profile answers and start over?")) return;
    state.observerProfile = { answers:{}, answered_at:{}, skipped:[] };
    if (typeof saveState==="function") saveState(state);
    try { renderTutorTab(); } catch(err){}
    return;
  }
```

### C5: Call `renderObserverProfile()` inside `renderTutorTab()`

FIND (inside `renderTutorTab()`):
```javascript
  // v8 — Baseline sweep card
  renderTutorBaseline();
```
INSERT immediately AFTER that line:
```javascript
  // v8 — Observer Q&A
  renderObserverProfile();
```

---

## WORKSTREAM D — Weekly micro-missions (replaces Horizons)

### D1: Add CSS for missions (in the `/* v7 — Tutor tab` CSS block)

Insert AFTER the `.v8-profile-complete` block, still before `@media (max-width:640px)`:

```css
/* v8 — Weekly micro-missions */
.v8-mission-card{
  background:#F8FAFC; border:1px solid var(--line); border-radius:12px;
  padding:12px 14px; margin-bottom:8px;
  display:flex; gap:10px; align-items:flex-start;
}
.v8-mission-num{
  font-size:20px; line-height:1; flex-shrink:0; margin-top:1px;
}
.v8-mission-body{ flex:1; min-width:0; }
.v8-mission-title{ font-weight:700; font-size:14px; color:var(--ink); margin-bottom:2px; }
.v8-mission-how{ font-size:12px; color:var(--ink); line-height:1.5; margin-bottom:6px; }
.v8-mission-meta{ font-size:11px; color:var(--muted); margin-bottom:6px; }
.v8-mission-why{
  font-size:11px; color:var(--muted); padding:4px 8px;
  background:var(--bg); border-radius:6px; margin-bottom:8px; line-height:1.4;
}
```

### D2: Add HTML `div` for missions in the Tutor section

FIND the existing Horizons HTML block:
```html
    <div class="card v7-tutor-section" style="margin-bottom:14px">
      <h3 class="v7-tutor-h">🗓️ Horizons</h3>
      <div id="v7TutorHorizons"></div>
    </div>
```
REPLACE it with:
```html
    <!-- v8 — Weekly micro-missions (replaces Horizons) -->
    <div class="card v7-tutor-section" style="margin-bottom:14px">
      <div style="display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; gap:6px; margin-bottom:8px">
        <h3 class="v7-tutor-h" style="margin:0">🎯 This week's missions</h3>
        <button class="small ghost" style="font-size:11px" data-v8-missions-refresh>↺ Refresh</button>
      </div>
      <div id="v7TutorHorizons"></div>
    </div>
```

(Note: keep `id="v7TutorHorizons"` unchanged so existing references don't break.)

### D3: Add `_missionsAlgorithmicFallback()` and `generateMissionsViaHaiku()` helpers

Insert IMMEDIATELY BEFORE `function renderTutorTab()`:

```javascript
/* _missionsAlgorithmicFallback — fast, offline, no API call.
   Picks 3 frontier `ready` skills (keystones > high-downstream > difficulty)
   and returns minimal mission objects. Used while Haiku is loading or if the
   API key is absent.                                                          */
function _missionsAlgorithmicFallback(){
  const allPool = [...SKILLS, ...(SKILLS_CUSTOM_SEED||[]), ...(Array.isArray(state.skillsCustom)?state.skillsCustom:[])];
  const readySkills = allPool.filter(s =>
    s && !isSkillMastered(s.id) &&
    (typeof classifySkillFrontier==="function") && classifySkillFrontier(s)==="ready"
  );
  if (!readySkills.length) return [];

  const downstream = (id) => allPool.filter(x => Array.isArray(x.prereqs) && x.prereqs.includes(id)).length;
  const scored = readySkills.map(s => ({
    s,
    score: (s.keystone?100:0) + downstream(s.id)*5 + (s.difficulty||5)
  }));
  scored.sort((a,b)=>b.score-a.score);

  const picked = [];
  const used = new Set();
  for (const {s} of scored){ if (picked.length>=3) break; if (!used.has(s.dom)){ picked.push(s); used.add(s.dom); } }
  for (const {s} of scored){ if (picked.length>=3) break; if (!picked.includes(s)) picked.push(s); }

  const NUMS = ["1️⃣","2️⃣","3️⃣"];
  return picked.map((sk,i) => {
    const dom = DOMAINS.find(d=>d.key===sk.dom)||{emoji:"✨",label:sk.dom||""};
    return {
      num: NUMS[i]||`${i+1}.`,
      skillId: sk.id,
      title: sk.t||sk.id,
      domain: `${dom.emoji} ${dom.label}`,
      how: sk.how||sk.what||"",
      duration: sk.difficulty<=3?10:sk.difficulty<=6?15:20,
      why: sk.why||"",
      best_moment: "",
      keystone: !!sk.keystone,
      downstream: downstream(sk.id),
      _ai: false
    };
  });
}

/* generateMissionsViaHaiku(childId) — async; sends frontier + observer profile +
   meta-milestones to Haiku and saves a personalised 3-mission plan to
   state.weeklyMissions. Falls back silently to algorithmic missions on error.
   Triggered every MISSIONS_MASTERY_TRIGGER mastery events (see _installMissionsHook).
   Cross-child guard: exits immediately if the active child has changed.        */
let _missionsMasteryCount = 0;
const MISSIONS_MASTERY_TRIGGER = 10;

async function generateMissionsViaHaiku(childId){
  if (typeof getActiveChildId === "function" && getActiveChildId() !== childId) return;
  const key = (typeof _hzKeySilent === "function") ? _hzKeySilent() : null;
  if (!key){ /* no key — silently skip; algorithmic fallback already shown */ return; }

  const child  = (typeof currentChild==="function") ? currentChild() : { name:"the child" };
  const ageM   = (typeof chronoAgeMonths==="function") ? chronoAgeMonths(child) : null;
  const prof   = state.observerProfile || { answers:{} };
  const mm     = (state.metaMilestones && state.metaMilestones._childId===childId) ? state.metaMilestones : null;

  // Build frontier context (up to 15 ready/stretch skills)
  const frontierSkills = (typeof buildZPDPoolV10==="function") ? buildZPDPoolV10().slice(0,15) : [];
  const allPool = [...SKILLS, ...(SKILLS_CUSTOM_SEED||[]), ...(Array.isArray(state.skillsCustom)?state.skillsCustom:[])];
  const downstream = (id) => allPool.filter(x => Array.isArray(x.prereqs)&&x.prereqs.includes(id)).length;
  const frontierText = frontierSkills.map(s =>
    `  ${s.id}: "${s.t}" [${s.dom}${s.keystone?" KEYSTONE":""}] diff:${s.difficulty||5} unlocks:${downstream(s.id)} how:"${(s.how||"").slice(0,80)}"`
  ).join("\n") || "  (no frontier skills)";

  // Build profile text
  const profileText = Object.entries(prof.answers||{}).length
    ? Object.entries(prof.answers).map(([qId, ans]) => {
        const q = (typeof OBSERVER_QUESTIONS!=="undefined") ? OBSERVER_QUESTIONS.find(x=>x.id===qId) : null;
        return `  - ${q ? q.text.replace(/\{name\}/g, child.name||"the child") : qId}: "${ans}"`;
      }).join("\n")
    : "  (no profile answers yet — use defaults)";

  const prompt = `You are a paediatric developmental specialist designing a personalised weekly learning plan.

CHILD: ${child.name||"the child"}, ${ageM ? ageM + " months old" : "age unknown"}

OBSERVER PROFILE:
${profileText}
${mm && mm.summary ? `\nAI DEVELOPMENTAL INSIGHT: ${mm.summary}` : ""}
${mm && mm.specialisation ? `\nSPECIALISATION SIGNAL: ${mm.specialisation}` : ""}

ELIGIBLE FRONTIER SKILLS (ready/stretch class — these are the right challenge level now):
${frontierText}

YOUR TASK:
Design exactly 3 weekly micro-missions. Each should:
1. Pick one skill from the frontier list above (use its exact id)
2. Adapt the activity to THIS child's learning style, motivators and goal (from profile)
3. Prioritise keystones and high-downstream skills (unlocks most future skills)
4. Keep sessions achievable: respect the child's age and attention span
5. Be specific and joyful — not generic developmental advice

For each mission return a JSON object with:
- skill_id: exact id from the frontier list
- title: short action-title (joyful, specific — NOT just the skill name)
- how: 2-3 sentences of concrete activity description adapted to this child
- duration_min: integer (5-20)
- why_brief: one sentence developmental rationale
- best_moment: when in the day (adapt from profile q_best_time if answered, else omit)

Respond with ONLY valid JSON:
{"missions":[{"skill_id":"...","title":"...","how":"...","duration_min":15,"why_brief":"...","best_moment":""},...],"_note":"optional brief note for the parent"}`;

  try {
    const resp = await fetch("https://api.anthropic.com/v1/messages", {
      method:"POST",
      headers:{
        "content-type":"application/json",
        "x-api-key": key,
        "anthropic-version":"2023-06-01",
        "anthropic-dangerous-direct-browser-access":"true"
      },
      body: JSON.stringify({
        model:"claude-haiku-4-5-20251001",
        max_tokens:900,
        messages:[{ role:"user", content:prompt }]
      })
    });
    if (typeof getActiveChildId==="function" && getActiveChildId()!==childId) return; // child switched while waiting
    const data = await resp.json();
    const textBlock = (data.content||[]).find(c=>c.type==="text");
    if (!textBlock) throw new Error("no text block");
    const jsonMatch = textBlock.text.match(/\{[\s\S]*\}/);
    if (!jsonMatch) throw new Error("no JSON in response");
    const parsed = JSON.parse(jsonMatch[0]);

    const NUMS = ["1️⃣","2️⃣","3️⃣"];
    const missions = (parsed.missions||[]).slice(0,3).map((m,i) => {
      const sk = allPool.find(s=>s.id===m.skill_id);
      const dom = sk ? (DOMAINS.find(d=>d.key===sk.dom)||{emoji:"✨",label:sk.dom||""}) : {emoji:"✨",label:""};
      return {
        num: NUMS[i]||`${i+1}.`,
        skillId: m.skill_id,
        title: m.title||(sk&&sk.t)||m.skill_id,
        domain: `${dom.emoji} ${dom.label}`,
        how: m.how||"",
        duration: typeof m.duration_min==="number" ? m.duration_min : 15,
        why: m.why_brief||"",
        best_moment: m.best_moment||"",
        keystone: !!(sk&&sk.keystone),
        downstream: downstream(m.skill_id),
        _ai: true,
        _note: parsed._note||""
      };
    });

    if (!missions.length) throw new Error("empty missions array");

    if (typeof getActiveChildId==="function" && getActiveChildId()!==childId) return;
    state.weeklyMissions = { missions, _ts: Date.now(), _childId: childId };
    if (typeof _v31Bump==="function") _v31Bump();
    if (typeof saveState==="function") saveState(state);
    // Re-render missions section if Tutor tab is visible
    const tv = document.getElementById("tutorView");
    if (tv && tv.style.display!=="none"){
      try { renderTutorTab(); } catch(e){ console.warn("tutor re-render after missions failed", e); }
    }
  } catch(err){
    console.warn("generateMissionsViaHaiku failed — keeping algorithmic fallback", err);
  }
}
```

### D3b: Add `_installMissionsHook` IIFE

Append IMMEDIATELY AFTER the closing `})();` of the existing `_installMmHook` IIFE
(which is near the end of the file, before `</script></body></html>`):

```javascript
/* _installMissionsHook — wraps addObservation (already wrapped by _installMmHook)
   to count mastery events and trigger generateMissionsViaHaiku every
   MISSIONS_MASTERY_TRIGGER masteries. Separate from _installMmHook so the two
   counters stay independent.                                                    */
(function _installMissionsHook(){
  const _origAddM = addObservation;
  addObservation = function(args){
    _origAddM(args);
    if (args && (args.status === "mastered" || args.status === "already_mastered")){
      _missionsMasteryCount = (_missionsMasteryCount || 0) + 1;
      if (_missionsMasteryCount >= MISSIONS_MASTERY_TRIGGER){
        _missionsMasteryCount = 0;
        const cid = (typeof getActiveChildId==="function") ? getActiveChildId() : null;
        if (cid) Promise.resolve().then(() => generateMissionsViaHaiku(cid).catch(()=>{}));
      }
    }
  };
})();
```

### D4: Replace `renderTutorTab` Horizons section with missions renderer

FIND inside `renderTutorTab()` the entire `// Horizons` block (from `// Horizons`
comment to the closing `}`  of the `if (horz){...}` block):

```javascript
  // Horizons
  if (horz){
    const spotlight = pickDomainSpotlight();
    const spotDom = DOMAINS.find(d => d.key === spotlight) || { label: spotlight };
    const child = (typeof currentChild === "function") ? currentChild() : null;
    const era = (child && typeof activeEra === "function") ? activeEra(child) : null;
    const eraIdx = era && typeof ERAS !== "undefined" ? ERAS.findIndex(e => e.key === era.key) : -1;
    const nextEra = (eraIdx >= 0 && eraIdx < (typeof ERAS !== "undefined" ? ERAS.length - 1 : -1)) ? ERAS[eraIdx + 1] : null;
    const ks = getKeystoneGaps()[0];
    horz.innerHTML = `<ul class="v7-tutor-list v7-tutor-horizons">
      <li><strong>This week:</strong> ${spotDom.emoji || "✨"} ${escapeHtml(spotDom.label)} spotlight${ks ? " + push toward keystone " + escapeHtml(ks.label) : ""}.</li>
      <li><strong>This month:</strong> Consolidate Active 10 mastery across foundation domains; declare any pending confirmations decisively.</li>
      <li><strong>Next quarter:</strong> ${nextEra ? "Approach " + escapeHtml(nextEra.label) + " transition — surface new domains (e.g. pre-writing, numeracy)." : "Continue era-current focus; refresh sub-domain coverage."}</li>
    </ul>`;
  }
```

REPLACE it with:

```javascript
  // Weekly micro-missions (v8 — replaces Horizons)
  if (horz){
    const childId = (typeof getActiveChildId==="function") ? getActiveChildId() : null;
    const cached = state.weeklyMissions;
    const cacheValid = cached && cached._ts && cached.missions && cached.missions.length &&
                       (Date.now() - cached._ts) < 7 * 86400000 &&
                       (!cached._childId || cached._childId === childId);

    // Use cached AI missions if fresh; otherwise generate algorithmic immediately
    // and trigger Haiku in background.
    let missions = cacheValid ? cached.missions : _missionsAlgorithmicFallback();
    const isAI = cacheValid && (missions[0]||{})._ai;

    if (!cacheValid && childId){
      // Fire-and-forget background Haiku generation; re-renders when done.
      Promise.resolve().then(() => generateMissionsViaHaiku(childId).catch(()=>{}));
    }

    const prof = state.observerProfile || {};
    const ansCount = Object.keys((prof.answers||{})).length;
    const aiLabel = isAI
      ? `<span style="font-size:10px; background:#EDE9FE; color:#5B21B6; border-radius:4px; padding:1px 6px; margin-left:6px">✨ personalised</span>`
      : `<span style="font-size:10px; color:var(--muted); margin-left:6px">(${ansCount < 3 ? "answer 3+ profile questions to unlock AI personalisation" : "generating…"})</span>`;

    // Carry-over AI note from Haiku response if present
    const aiNote = isAI && (missions[0]||{})._note
      ? `<div style="font-size:11px; color:#5B21B6; background:#EDE9FE; border-radius:8px; padding:6px 10px; margin-bottom:10px">${escapeHtml(missions[0]._note)}</div>`
      : "";
    // Goal hint from profile
    const goalHint = (prof.answers && prof.answers.q_challenge)
      ? `<div style="font-size:11px; color:var(--muted); margin-bottom:8px">Goal: <em>${escapeHtml(prof.answers.q_challenge)}</em></div>`
      : "";

    if (!missions.length){
      horz.innerHTML = `<div class="v7-tutor-empty">No ready-class skills in the frontier right now — check back after a few more masteries, or use the Skills catalogue.</div>`;
    } else {
      const cards = missions.map(m => `
        <div class="v8-mission-card">
          <div class="v8-mission-num">${m.num}</div>
          <div class="v8-mission-body">
            <div class="v8-mission-title">${escapeHtml(m.title)}${m.keystone ? " <span style='font-size:10px;background:#FCD34D;border-radius:4px;padding:1px 5px;color:#7C2D12'>keystone</span>" : ""}</div>
            <div class="v8-mission-meta">${escapeHtml(m.domain)} · ~${m.duration} min${m.downstream > 0 ? ` · unlocks ${m.downstream} skill${m.downstream===1?"":"s"}` : ""}${m.best_moment ? ` · ${escapeHtml(m.best_moment)}` : ""}</div>
            ${m.how  ? `<div class="v8-mission-how">↪ ${escapeHtml(m.how)}</div>` : ""}
            ${m.why  ? `<div class="v8-mission-why">${escapeHtml(m.why)}</div>` : ""}
            <button class="small" data-v8-mission-skill="${escapeHtml(m.skillId)}">✓ Did this today!</button>
          </div>
        </div>`).join("");
      horz.innerHTML = `<div style="display:flex; align-items:center; margin-bottom:4px; flex-wrap:wrap">${aiLabel}</div>` + goalHint + aiNote + cards;
    }
  }
```

---

## WORKSTREAM E — Narrative upgrade

### E1: Replace `computeTutorNarrative()` body

FIND the entire `function computeTutorNarrative()` (from its opening line to its
closing `}`). REPLACE it with:

```javascript
function computeTutorNarrative(){
  const child = (typeof currentChild === "function" ? currentChild() : null) || { name: "Maxine" };
  const ct = (typeof currentTier === "function") ? currentTier() : 0;
  const spotlightKey = pickDomainSpotlight();
  const spotlightDom = DOMAINS.find(d => d.key === spotlightKey) || { label: spotlightKey, emoji: "✨" };
  const potential = getGreatestPotential();
  const keys = getKeystoneGaps().length;
  const pending = pendingMasteryConfirmations().length;
  const stalled = getStalledSkills().length;
  const ageM = (typeof chronoAgeMonths === "function" && child) ? chronoAgeMonths(child) : null;
  const ageBit = ageM ? ` (age ${ageM}m)` : "";
  const _prN = (typeof getChildPronouns === "function") ? getChildPronouns(getActiveChildId()) : { Possessive:"Her" };

  // P1 — tier + spotlight
  const p1 = `${child.name || "Maxine"}${ageBit} is at developmental tier T${ct}. This week's spotlight domain is ${spotlightDom.emoji} ${spotlightDom.label} — lean play, reading, and one-on-one time toward it.`;

  // P2 — momentum or Haiku-inferred summary (v10 meta-milestones)
  let p2 = "";
  const mm = state.metaMilestones;
  if (mm && mm.summary && mm._childId && mm._childId === getActiveChildId()){
    p2 = mm.summary;                               // use AI-generated insight
  } else if (potential){
    p2 = `${_prN.Possessive} greatest current momentum is ${potential.domain_emoji} ${potential.domain_label} (${potential.obs_count_30d} observations in the last 30 days). Amplify what's already pulling.`;
  } else {
    p2 = "Not enough recent observations to detect momentum — log a few activities to surface the trend.";
  }

  // P2b — velocity (30-day mastery count)
  const now = Date.now();
  const masteries30 = (state.observations||[]).filter(o => o &&
    (o.status==="mastered"||o.status==="already_mastered") &&
    ((o.estimated_ts||o.ts)||0) >= now - 30*86400000
  ).length;
  const velBit = masteries30 > 0 ? ` ${masteries30} masteri${masteries30===1?"y":"es"} logged in the last 30 days.` : "";

  // P3 — flags
  const fragments = [];
  if (pending > 0) fragments.push(`${pending} skill${pending === 1 ? "" : "s"} look${pending === 1 ? "s" : ""} ready to declare mastered — see "Pending confirmations" below`);
  if (keys > 0)    fragments.push(`${keys} keystone${keys === 1 ? "" : "s"} still open — prioritise these`);
  if (stalled > 0) fragments.push(`${stalled} stalled skill${stalled === 1 ? "" : "s"} need a fresh look`);
  const p3 = fragments.length ? fragments.join(". ") + "." : "Nothing flagged — keep playing.";

  // P_profile — personalisation line if observer profile has learning style
  const prof = state.observerProfile || {};
  const ls = (prof.answers && prof.answers.q_learning_style) || "";
  const goalText = (prof.answers && prof.answers.q_challenge) || "";
  let pProfile = "";
  if (ls) pProfile += ` Since ${child.name||"she"} learns best ${ls.toLowerCase().replace(/^(by\s)?/,"by ")}, this week's missions lean that way.`;
  if (goalText) pProfile += ` Current focus: ${goalText}.`;

  return [p1, p2 + velBit, p3 + pProfile].join(" ");
}
```

---

---

## WORKSTREAM C+ — Dynamic observer questions (supersedes parts of C1 and C4)

C+ extends the observer profile from a one-time form into a living dialogue.
As the child's frontier moves, the tutor asks new contextual questions and re-asks
stale answers. Apply C+ AFTER completing workstreams A–E.

---

### C+1: Replace `OBSERVER_QUESTIONS` (supersedes C1)

Replace the entire `OBSERVER_QUESTIONS` constant (FIND: `const OBSERVER_QUESTIONS = [`)
with this version that adds `expires_after_days` to each entry:

```javascript
const OBSERVER_QUESTIONS = [
  { id:"q_learning_style",  expires_after_days:180, text:"How does {name} learn best — by watching, by doing, or by hearing/talking through things?",        category:"learning",  example:"e.g. \"she copies everything she sees\" / \"needs to touch it\" / \"talks to herself while practising\"" },
  { id:"q_attention_span",  expires_after_days:120, text:"How long can {name} typically stay focused on a chosen activity before losing interest?",           category:"energy",    example:"e.g. \"5 minutes\" / \"20+ minutes if it's her idea\"" },
  { id:"q_motivators",      expires_after_days:90,  text:"What does {name} love most right now?",                                                             category:"interests", example:"e.g. books, running outdoors, music, drawing, pretend play, puzzles, water" },
  { id:"q_social_context",  expires_after_days:180, text:"Does {name} engage better one-on-one with an adult, or with other children around?",               category:"social",    example:"e.g. \"needs one adult\" / \"thrives with 1-2 peers\" / \"fine either way\"" },
  { id:"q_languages",       expires_after_days:365, text:"Which languages does {name} hear daily, and which does she produce most?",                         category:"language",  example:"e.g. \"hears French and English; mostly speaks English\"" },
  { id:"q_sensory",         expires_after_days:365, text:"Any sensory sensitivities worth knowing about?",                                                    category:"sensory",   example:"e.g. loud sounds, certain textures, bright lights, or no sensitivities at all" },
  { id:"q_best_time",       expires_after_days:120, text:"What time of day is {name} most alert and receptive to new things?",                               category:"energy",    example:"e.g. \"mid-morning 9–11 am\" / \"after her nap\"" },
  { id:"q_challenge",       expires_after_days:60,  text:"What's the one thing you'd most like to see improve for {name} over the next 3 months?",           category:"goals",     example:"e.g. \"more independence\" / \"better focus\" / \"catch up on language\" / \"social confidence\"" },
  { id:"q_caregiver_style", expires_after_days:365, text:"How would you describe your approach with {name} in one or two words?",                            category:"context",   example:"e.g. \"playful, low-pressure\" / \"structured routines\" / \"child-led\" / \"busy household\"" },
  { id:"q_context",         expires_after_days:60,  text:"Any other context the tutor should know? (siblings, big routine changes, life events, etc.)",       category:"context",   example:"e.g. \"new baby sibling\" / \"just moved house\" / \"attends Montessori 3×/week\"" }
];
```

---

### C+2: Add `ERA_TRANSITION_QUESTIONS` and `DOMAIN_UNLOCK_QUESTIONS`

Insert IMMEDIATELY AFTER the `OBSERVER_QUESTIONS` constant (before `renderObserverProfile`):

```javascript
/* ERA_TRANSITION_QUESTIONS — keyed by era.key. One or two questions per era transition.
   Asked once when the child first enters that era. Check actual ERAS array keys in the
   file and adjust keys below if they differ (grep for "ERAS = [" to find them).         */
const ERA_TRANSITION_QUESTIONS = {
  "infant_late": [
    { id:"era_inf_late_imitation", text:"Is {name} starting to copy simple gestures or actions you make (clapping, waving, banging)?", category:"social",    example:"e.g. 'yes, mirrors everything' / 'sometimes' / 'not yet'" }
  ],
  "toddler": [
    { id:"era_tod_opinions",  text:"Now that {name} is entering the toddler stage, is she showing strong preferences or 'mine!' moments?", category:"social",    example:"e.g. 'yes, lots lately' / 'not yet' / 'occasionally with certain toys'" },
    { id:"era_tod_pretend",   text:"Is {name} starting to use objects pretend-style — feeding a doll, talking into a toy phone, stirring an empty pot?",        category:"cognitive", example:"e.g. 'yes daily' / 'only if I model it' / 'not yet'" }
  ],
  "preschool": [
    { id:"era_pre_peers",  text:"Does {name} get regular playtime with peers her age outside the home?",                                   category:"social",    example:"e.g. 'nursery 3×/week' / 'weekend playdates occasionally' / 'rarely'" },
    { id:"era_pre_books",  text:"How often does {name} look at books independently (not just when read to)?",                               category:"cognitive", example:"e.g. 'daily, 10+ min on her own' / 'only if prompted' / 'prefers other things'" }
  ]
};

/* DOMAIN_UNLOCK_QUESTIONS — keyed by domain key (gross/fine/sensory/cognitive/vocab/social).
   One question per domain, asked once when that domain first enters the active ZPD.
   Use exact domain keys from the DOMAINS array (grep for "DOMAINS = [" to verify).       */
const DOMAIN_UNLOCK_QUESTIONS = {
  "fine":      { id:"dom_fine_tools",    text:"Fine motor skills are coming into {name}'s range — does she have drawing tools (crayons, chalk, fat pencils) accessible at home?",         category:"cognitive", example:"e.g. 'yes, uses daily' / 'we have some but she ignores them' / 'not yet'" },
  "cognitive": { id:"dom_cog_puzzles",   text:"Problem-solving and matching games are opening up — does {name} have simple puzzles or shape-sorters she can access independently?",        category:"cognitive", example:"e.g. 'yes, loves them' / 'a few' / 'none yet'" },
  "vocab":     { id:"dom_vocab_reading", text:"Vocabulary is expanding fast for {name} right now — roughly how many books or stories does she encounter per week?",                        category:"language",  example:"e.g. '20+ per week' / '5–10' / 'very few'" },
  "social":    { id:"dom_social_peers",  text:"Social play is emerging for {name} — does she have regular contact with other children her age?",                                           category:"social",    example:"e.g. 'yes, at nursery / playgroup' / 'mainly adults around' / 'occasional'" }
};
```

---

### C+3: Add `_getContextualQuestions()` helper

Insert IMMEDIATELY AFTER the `DOMAIN_UNLOCK_QUESTIONS` constant (before `renderObserverProfile`):

```javascript
/* _getContextualQuestions — returns an array of pending contextual question objects.
   Sources: (1) era-transition questions for the current era,
            (2) domain-unlock questions for newly active domains,
            (3) keystone-stall questions for keystones stuck >28 days.
   Each returned question has _context_label and _trigger for the render layer.     */
function _getContextualQuestions(){
  const result = [];
  const prof = state.observerProfile || {};
  const dismissed = prof.contextual_dismissed || {};
  const child = (typeof currentChild==="function") ? currentChild() : null;

  // 1. Era-transition questions
  const era = (child && typeof activeEra==="function") ? activeEra(child) : null;
  if (era && ERA_TRANSITION_QUESTIONS[era.key]){
    ERA_TRANSITION_QUESTIONS[era.key].forEach(q => {
      if (!prof.answers[q.id] && !dismissed[q.id]){
        result.push({ ...q, _context_label:"🌱 New milestone — help me understand", _trigger:"era" });
      }
    });
  }

  // 2. Domain-unlock questions — for domains now active but whose question hasn't been answered/dismissed
  const activeDoms = (typeof getActiveDomainKeys==="function") ? getActiveDomainKeys() :
                     (typeof DOMAINS!=="undefined") ? DOMAINS.map(d=>d.key) : [];
  activeDoms.forEach(dk => {
    const q = DOMAIN_UNLOCK_QUESTIONS[dk];
    if (q && !prof.answers[q.id] && !dismissed[q.id]){
      const dom = (typeof DOMAINS!=="undefined") ? DOMAINS.find(d=>d.key===dk)||{emoji:"✨",label:dk} : {emoji:"✨",label:dk};
      result.push({ ...q, _context_label:`${dom.emoji} ${dom.label} just entered focus`, _trigger:"domain" });
    }
  });

  // 3. Keystone-stall questions — keystone in ready/stretch class with no observation in last 28 days
  const now = Date.now();
  const ks = (typeof getKeystoneGaps==="function") ? getKeystoneGaps() : [];
  ks.slice(0, 2).forEach(sk => {
    const qid = `ks_stall_${sk.id}`;
    if (dismissed[qid] || prof.answers[qid]) return;
    const recentObs = (state.observations||[]).filter(o => o && o.skillId===sk.id && (o.ts||0) > now - 28*86400000);
    if (!recentObs.length){
      result.push({
        id: qid,
        text: `"${sk.t||sk.id}" has been on the horizon for a while. Any barriers? (illness, limited opportunity, or just not quite there yet)`,
        category: "goals",
        example: "e.g. \"she tries but can't quite do it\" / \"haven't had opportunity\" / \"seems very close\"",
        _context_label: "⏳ Stalled keystone — help me understand",
        _trigger: "keystone"
      });
    }
  });

  return result;
}
```

---

### C+4: Add `_getNextObserverQuestion()` helper

Insert IMMEDIATELY AFTER `_getContextualQuestions()` (before `renderObserverProfile`):

```javascript
/* _getNextObserverQuestion — unified priority-ordered question picker.
   Priority: (1) expired core answers  →  (2) contextual (era > domain > keystone)
           → (3) unanswered core       →  (4) skipped questions recycled after 30 days
   Returns a question object extended with optional _context_label, _prev_answer,
   _trigger fields. Returns null when nothing is pending.                             */
function _getNextObserverQuestion(){
  const prof = state.observerProfile || {};
  const now = Date.now();

  // 1. Expired core answers (answered but stale — most important to refresh)
  const expired = OBSERVER_QUESTIONS.filter(q => {
    if (!prof.answers[q.id]) return false;
    const expMs = (q.expires_after_days || 365) * 86400000;
    return (prof.answered_at[q.id] || 0) + expMs < now;
  });
  if (expired.length){
    const eq = expired[0];
    const daysAgo = Math.round((now - (prof.answered_at[eq.id]||0)) / 86400000);
    return { ...eq, _context_label:`🔄 Check-in (answered ${daysAgo} days ago — things may have changed)`, _prev_answer: prof.answers[eq.id], _trigger:"refresh" };
  }

  // 2. Contextual questions (era → domain → keystone)
  const contextual = _getContextualQuestions();
  if (contextual.length) return contextual[0];

  // 3. Unanswered core questions
  const unanswered = OBSERVER_QUESTIONS.filter(q => !prof.answers[q.id] && !(prof.skipped||[]).includes(q.id));
  if (unanswered.length) return unanswered[0];

  // 4. Recycled skipped questions (skipped >30 days ago)
  const recyclable = OBSERVER_QUESTIONS.filter(q =>
    (prof.skipped||[]).includes(q.id) &&
    ((prof.skipped_at && prof.skipped_at[q.id]) || 0) < now - 30*86400000
  );
  if (recyclable.length) return recyclable[0];

  return null; // profile is fully current
}
```

---

### C+5: Replace `renderObserverProfile()` body (supersedes C4)

FIND the entire `function renderObserverProfile()` body (from opening `{` to closing `}`)
and REPLACE just the body (keep the function declaration line) with:

```javascript
function renderObserverProfile(){
  const el = document.getElementById("v8TutorProfile");
  if (!el) return;
  const child = (typeof currentChild==="function") ? currentChild() : null;
  const cName = (child && child.name) || "the child";
  // Ensure all new sub-keys exist (backward-compat with older state)
  state.observerProfile = Object.assign(
    { answers:{}, answered_at:{}, skipped:[], skipped_at:{}, contextual_dismissed:{} },
    state.observerProfile || {}
  );
  const prof = state.observerProfile;
  const total = OBSERVER_QUESTIONS.length;
  const answered = OBSERVER_QUESTIONS.filter(q => prof.answers[q.id]).length;
  const now = Date.now();

  const next = _getNextObserverQuestion();

  if (!next){
    // Compute next refresh date across all core answers
    let nextRefreshMs = Infinity;
    OBSERVER_QUESTIONS.forEach(q => {
      const at = prof.answered_at[q.id] || 0;
      if (at) nextRefreshMs = Math.min(nextRefreshMs, at + (q.expires_after_days||365)*86400000);
    });
    const daysToRefresh = nextRefreshMs < Infinity ? Math.max(0, Math.round((nextRefreshMs - now)/86400000)) : null;
    el.innerHTML = `<div class="v8-profile-complete">
      <span>✅ Profile current — ${answered}/${total} answered${daysToRefresh !== null ? ` · refreshes in ~${daysToRefresh} days` : ""}</span>
      <button class="small ghost" data-v8-profile-reset style="font-size:11px">✏️ Edit</button>
    </div>`;
    el.style.display = "";
    return;
  }

  const qText = next.text.replace(/\{name\}/g, escapeHtml(cName));
  const contextBadge = next._context_label
    ? `<div style="font-size:11px; color:#92400E; font-weight:700; margin-bottom:6px">${escapeHtml(next._context_label)}</div>`
    : `<div class="v8-profile-progress">💬 Help me understand ${escapeHtml(cName)} · ${answered}/${total} answered</div>`;
  const prevAnswer = next._prev_answer
    ? `<div style="font-size:11px; color:var(--muted); margin-bottom:5px; font-style:italic">Last answer: "${escapeHtml(next._prev_answer)}"</div>`
    : "";
  const notRelevantBtn = next._trigger && next._trigger !== "refresh"
    ? `<button class="small ghost" style="font-size:10px" data-v8-profile-cdismiss="${next.id}">Not relevant</button>`
    : "";

  el.innerHTML = `<div class="v8-profile-card">
    ${contextBadge}
    <div class="v8-profile-q">${qText}</div>
    <div class="v8-profile-example">${escapeHtml(next.example||"")}</div>
    ${prevAnswer}
    <textarea class="v8-profile-input" id="v8-profile-input-${next.id}"
      placeholder="Your answer…" rows="2">${escapeHtml(prof.answers[next.id]||"")}</textarea>
    <div class="v8-profile-actions">
      <button class="small primary" data-v8-profile-save="${next.id}">💾 Save</button>
      <button class="small ghost"   data-v8-profile-skip="${next.id}">Skip for now</button>
      ${notRelevantBtn}
    </div>
  </div>`;
  el.style.display = "";
}
```

---

### C+6: Update click handlers in the existing delegation block (extends B6)

#### C+6a: Update the existing skip handler to also save `skipped_at`

FIND (inside the `document.addEventListener("click", ...)` block):
```javascript
  const skipQBtn = e.target.closest("[data-v8-profile-skip]");
  if (skipQBtn){
    const qId = skipQBtn.dataset.v8ProfileSkip;
    state.observerProfile = state.observerProfile || { answers:{}, answered_at:{}, skipped:[] };
    if (!state.observerProfile.skipped.includes(qId)) state.observerProfile.skipped.push(qId);
    if (typeof saveState === "function") saveState(state);
    try { renderTutorTab(); } catch(err){}
    return;
  }
```
REPLACE with:
```javascript
  const skipQBtn = e.target.closest("[data-v8-profile-skip]");
  if (skipQBtn){
    const qId = skipQBtn.dataset.v8ProfileSkip;
    state.observerProfile = state.observerProfile || { answers:{}, answered_at:{}, skipped:[], skipped_at:{}, contextual_dismissed:{} };
    if (!state.observerProfile.skipped.includes(qId)) state.observerProfile.skipped.push(qId);
    state.observerProfile.skipped_at = state.observerProfile.skipped_at || {};
    state.observerProfile.skipped_at[qId] = Date.now();
    if (typeof saveState === "function") saveState(state);
    try { renderTutorTab(); } catch(err){}
    return;
  }
```

#### C+6b: Add "Not relevant" (contextual dismiss) handler

INSERT immediately AFTER the updated skip handler above (before `// Observer Q&A: Reset / edit profile`):

```javascript
  // Observer Q&A: Contextual question dismiss ("Not relevant")
  const cdismissBtn = e.target.closest("[data-v8-profile-cdismiss]");
  if (cdismissBtn){
    const qId = cdismissBtn.dataset.v8ProfileCdismiss;
    state.observerProfile = state.observerProfile || { answers:{}, answered_at:{}, skipped:[], skipped_at:{}, contextual_dismissed:{} };
    state.observerProfile.contextual_dismissed = state.observerProfile.contextual_dismissed || {};
    state.observerProfile.contextual_dismissed[qId] = Date.now();
    if (typeof saveState==="function") saveState(state);
    try { renderTutorTab(); } catch(err){}
    return;
  }
```

---

### C+7: Update `defaultForKey` for `observerProfile` (supersedes B4 entry for observerProfile)

FIND (inside `function defaultForKey(k)`):
```javascript
  if (k === "observerProfile") return { answers:{}, answered_at:{}, skipped:[] };
```
REPLACE with:
```javascript
  if (k === "observerProfile") return { answers:{}, answered_at:{}, skipped:[], skipped_at:{}, contextual_dismissed:{} };
```

---

## WORKSTREAM F — Page UX: labels, XP, skill popups, info icons, observer Q&A placement, close z-index

Apply F AFTER completing all prior workstreams (A–E, C+).

---

### F1: Hero card — rename header to "How is [name] doing?" + push/pull chips

#### F1a: Update title in `renderTutorTab()`

FIND in `renderTutorTab()` the lines that set the element `v7TutorTitle`.
(Grep first: `grep -n "v7TutorTitle" Maxine_Dashboard.html | head -10`)

REPLACE the line that assigns text/content to `v7TutorTitle` with:

```javascript
  if (title){
    const _heroChildName = ((typeof currentChild==="function") ? currentChild() : null)?.name || "Maxine";
    title.textContent = `How is ${_heroChildName} doing?`;
  }
```

#### F1b: Add push/pull chips element inside the hero card HTML

FIND (in `<section id="tutorView">`) the element with `id="v7TutorNarrative"`.
INSERT immediately AFTER its closing `</div>` (or `</p>`):

```html
          <div id="v8TutorPushPull" style="display:none; margin-top:10px; display:flex; gap:8px; flex-wrap:wrap"></div>
```

#### F1c: Populate push/pull chips in `renderTutorTab()`

FIND in `renderTutorTab()` the line that sets `v7TutorNarrative`'s content to
`computeTutorNarrative()`. INSERT IMMEDIATELY AFTER it:

```javascript
  // v8/F — push/pull chips
  const _ppEl = document.getElementById("v8TutorPushPull");
  if (_ppEl){
    const _ks  = (typeof getKeystoneGaps==="function") ? getKeystoneGaps().slice(0,2) : [];
    const _pot = (typeof getGreatestPotential==="function") ? getGreatestPotential() : null;
    const _pullTxt = _pot ? `🔥 Pulling: ${_pot.domain_emoji||""} ${_pot.domain_label||""}` : "";
    const _pushTxt = _ks.length ? `🎯 Push: ${_ks.map(k => escapeHtml(k.t||k.id)).join(", ")}` : "";
    const _chips = [_pullTxt, _pushTxt].filter(Boolean)
      .map(t => `<span class="v8-pushpull-chip">${t}</span>`).join("");
    _ppEl.innerHTML = _chips;
    _ppEl.style.display = _chips ? "" : "none";
  }
```

#### F1d: Add CSS for push/pull chips

Inside the `/* v7 — Tutor tab` CSS block, INSERT (before `@media (max-width:640px)`):

```css
/* v8/F — push/pull chips */
.v8-pushpull-chip{
  display:inline-flex; align-items:center; font-size:12px; font-weight:600;
  padding:3px 10px; border-radius:20px;
  background:#EFF6FF; color:#1E40AF; border:1px solid #BFDBFE;
}
.v8-pushpull-chip:first-child{ background:#FFF7ED; color:#9A3412; border-color:#FED7AA; }
```

---

### F2: XP points in Snapshot card

#### F2a: Add `_calcXP()` helper

INSERT IMMEDIATELY BEFORE `function renderTutorTab()`:

```javascript
/* _calcXP — cumulative XP = 100 per mastered skill, 200 for keystones.
   Gives parents a simple milestone number that grows over time.             */
function _calcXP(){
  const pool = [...SKILLS, ...(SKILLS_CUSTOM_SEED||[]),
                ...(Array.isArray(state.skillsCustom) ? state.skillsCustom : [])];
  return pool.reduce((acc, s) => {
    if (!s || !isSkillMastered(s.id)) return acc;
    return acc + (s.keystone ? 200 : 100);
  }, 0);
}
```

#### F2b: Append XP block to Snapshot card

FIND in `renderTutorTab()` the line that sets `v7TutorSnapshot`'s innerHTML.
(Grep: `grep -n "v7TutorSnapshot" Maxine_Dashboard.html | head -10`)

IMMEDIATELY AFTER the line that sets `snap.innerHTML = ...` (or wherever the
snap element's content is finalized), INSERT:

```javascript
  if (snap && typeof _calcXP === "function"){
    const _xpVal = _calcXP();
    const _xpStr = _xpVal.toLocaleString("fr-CH");   // thin-space thousands: 3 200
    const _mastCount = Math.round(_xpVal / 100);
    snap.innerHTML += `<div style="margin-top:10px; padding:8px 12px;
      background:#FFFBEB; border:1px solid #FDE68A; border-radius:8px;
      display:flex; align-items:center; gap:10px">
      <span style="font-size:22px">⭐</span>
      <div>
        <div style="font-size:18px; font-weight:800; color:#92400E; line-height:1">${_xpStr} XP</div>
        <div style="font-size:11px; color:var(--muted); margin-top:2px">${_mastCount} skill${_mastCount===1?"":"s"} mastered</div>
      </div>
    </div>`;
  }
```

---

### F3: Skill detail popup modal

#### F3a: Add modal HTML

FIND the LAST `</div>` before `</body>` (i.e., the closing tag of the outermost
app wrapper, just before `</body></html>`). INSERT BEFORE `</body>`:

```html
<!-- v8/F — Skill detail bottom-sheet modal -->
<div id="v8SkillModal" class="v8-skill-modal-overlay" role="dialog" aria-modal="true">
  <div class="v8-skill-modal-sheet">
    <button class="v8-skill-modal-close" id="v8SkillModalClose" aria-label="Close">✕</button>
    <div id="v8SkillModalBody"></div>
  </div>
</div>
<!-- v8/F — Info term floating tooltip -->
<div id="v8InfoPopup" class="v8-info-popup" role="tooltip"></div>
```

#### F3b: Add CSS for modal and info icons

Inside the `/* v7 — Tutor tab` CSS block (AFTER the `.v8-pushpull-chip` block, BEFORE `@media`):

```css
/* v8/F — Skill detail modal */
.v8-skill-modal-overlay{
  display:none; position:fixed; inset:0; z-index:2000;
  background:rgba(0,0,0,0.45); align-items:flex-end; justify-content:center;
}
.v8-skill-modal-overlay.v8-open{ display:flex; }
.v8-skill-modal-sheet{
  background:#fff; border-radius:16px 16px 0 0; max-width:500px; width:100%;
  padding:20px 20px 36px; max-height:82vh; overflow-y:auto; position:relative;
}
.v8-skill-modal-close{
  position:absolute; top:12px; right:14px; background:none; border:none;
  font-size:22px; cursor:pointer; color:var(--ink); z-index:2002; line-height:1; padding:4px;
}
.v8-skill-modal-title{ font-size:17px; font-weight:800; margin:0 36px 4px 0; color:var(--ink); }
.v8-skill-modal-meta{ font-size:12px; color:var(--muted); margin-bottom:12px; }
.v8-skill-modal-label{
  font-size:10px; font-weight:700; text-transform:uppercase; letter-spacing:.06em;
  color:var(--muted); margin-bottom:3px; margin-top:10px;
}
.v8-skill-modal-text{ font-size:13px; color:var(--ink); line-height:1.5; }
/* Clickable skill name in What's next */
.v8-skill-btn{
  background:none; border:none; cursor:pointer; text-align:left; padding:0;
  color:var(--ink); font:inherit; font-size:inherit;
  text-decoration:underline dotted; text-underline-offset:3px;
}
.v8-skill-btn:hover{ color:var(--primary,#3B82F6); }
/* ⓘ info icon button */
.v8-info-btn{
  display:inline-flex; align-items:center; justify-content:center;
  width:15px; height:15px; border-radius:50%; border:1.5px solid var(--muted);
  background:none; cursor:pointer; font-size:9px; font-weight:800;
  color:var(--muted); margin-left:5px; padding:0; vertical-align:middle; flex-shrink:0;
}
.v8-info-btn:hover{ border-color:var(--primary,#3B82F6); color:var(--primary,#3B82F6); }
/* Floating tooltip */
.v8-info-popup{
  position:fixed; z-index:2500; background:#1E293B; color:#F8FAFC;
  border-radius:10px; padding:10px 14px; font-size:12px; line-height:1.55;
  max-width:260px; box-shadow:0 8px 24px rgba(0,0,0,.25);
  opacity:0; pointer-events:none; transition:opacity .15s; display:none;
}
.v8-info-popup.v8-visible{ opacity:1; pointer-events:auto; display:block; }
```

#### F3c: Add `_openSkillPopup()`, `INFO_TERMS`, and `_infoIcon()` helpers

INSERT IMMEDIATELY BEFORE `function renderTutorTab()`:

```javascript
/* _openSkillPopup(skillId) — populates and opens the v8SkillModal.           */
function _openSkillPopup(skillId){
  const allPool = [...SKILLS, ...(SKILLS_CUSTOM_SEED||[]),
                   ...(Array.isArray(state.skillsCustom) ? state.skillsCustom : [])];
  const sk = allPool.find(s => s && s.id === skillId);
  if (!sk){ return; }
  const dom = DOMAINS.find(d => d.key === sk.dom) || { emoji:"✨", label: sk.dom||"" };
  const downstream = allPool.filter(x => Array.isArray(x.prereqs) && x.prereqs.includes(sk.id)).length;
  const prereqNames = (sk.prereqs||[]).map(pid => {
    const p = allPool.find(x => x.id === pid);
    return p ? escapeHtml(p.t||pid) : escapeHtml(pid);
  }).join(", ");
  const frontier = (typeof classifySkillFrontier==="function") ? classifySkillFrontier(sk) : "";
  const frontierBadge = { verify:"🔁 verify", ready:"✅ ready", stretch:"🌱 stretch", locked:"🔒 locked", below:"✓ mastered" }[frontier] || "";

  const body = document.getElementById("v8SkillModalBody");
  if (body) body.innerHTML = `
    <div class="v8-skill-modal-title">
      ${escapeHtml(sk.t||sk.id)}
      ${sk.keystone ? `<span style="font-size:11px;background:#FCD34D;border-radius:4px;padding:1px 6px;color:#7C2D12;margin-left:6px">keystone</span>` : ""}
      ${frontierBadge ? `<span style="font-size:11px;background:#F1F5F9;border-radius:4px;padding:1px 6px;color:var(--muted);margin-left:6px">${frontierBadge}</span>` : ""}
    </div>
    <div class="v8-skill-modal-meta">${dom.emoji} ${escapeHtml(dom.label)}${sk.age_min ? ` · ~${sk.age_min}m+` : ""}${sk.difficulty ? ` · difficulty ${sk.difficulty}/10` : ""}</div>
    ${sk.how  ? `<div class="v8-skill-modal-label">How to practise</div><div class="v8-skill-modal-text">${escapeHtml(sk.how)}</div>` : ""}
    ${sk.what ? `<div class="v8-skill-modal-label">What it looks like</div><div class="v8-skill-modal-text">${escapeHtml(sk.what)}</div>` : ""}
    ${sk.why  ? `<div class="v8-skill-modal-label">Why it matters</div><div class="v8-skill-modal-text">${escapeHtml(sk.why)}</div>` : ""}
    ${downstream > 0 ? `<div class="v8-skill-modal-label">Unlocks</div><div class="v8-skill-modal-text">${downstream} skill${downstream===1?"":"s"} once mastered</div>` : ""}
    ${prereqNames ? `<div class="v8-skill-modal-label">Needs first</div><div class="v8-skill-modal-text">${prereqNames}</div>` : ""}
  `;
  const modal = document.getElementById("v8SkillModal");
  if (modal) modal.classList.add("v8-open");
}

/* INFO_TERMS — explanations shown when the parent taps a ⓘ icon.             */
const INFO_TERMS = {
  keystone:   "Keystones are high-value skills that unlock the most future learning. Each keystone is a bottleneck — mastering one typically unblocks 3–10 other skills across multiple domains. They should be the top priority.",
  bridge:     "Bridge skills connect different development domains. Mastering a bridge skill accelerates progress across multiple areas simultaneously — for example, imitation bridges social, language, and motor learning.",
  zpd:        "Zone of Proximal Development — the sweet spot where a skill is just beyond current mastery but reachable with gentle adult support. Learning inside the ZPD is the most effective and motivating.",
  revalidate: "Skills in the revalidate list were logged as mastered earlier, but are worth a fresh check — either the child's standard has risen, or the skill has not been observed recently in a more demanding context."
};

/* _infoIcon(key) — returns HTML for an inline ⓘ button linked to INFO_TERMS. */
function _infoIcon(key){
  return `<button class="v8-info-btn" data-v8-info-term="${escapeHtml(key)}" aria-label="What does this mean?">i</button>`;
}
```

#### F3d: Wire skill popup, info icon, and modal-close handlers

FIND in the `document.addEventListener("click", ...)` delegation block:
```javascript
  // Weekly missions: Refresh
```
INSERT BEFORE it:

```javascript
  // Skill detail popup — triggered by data-v8-skill-popup buttons
  const skillPopupBtn = e.target.closest("[data-v8-skill-popup]");
  if (skillPopupBtn){
    e.preventDefault();
    if (typeof _openSkillPopup === "function") _openSkillPopup(skillPopupBtn.dataset.v8SkillPopup);
    return;
  }
  // Skill modal close — ✕ button or backdrop
  const skillModalClose = e.target.id === "v8SkillModalClose" || e.target.id === "v8SkillModal";
  if (skillModalClose){
    const modal = document.getElementById("v8SkillModal");
    if (modal) modal.classList.remove("v8-open");
    return;
  }
  // ⓘ Info icon — show floating tooltip
  const infoBtn = e.target.closest("[data-v8-info-term]");
  if (infoBtn){
    e.preventDefault();
    const key = infoBtn.dataset.v8InfoTerm;
    const txt = (typeof INFO_TERMS !== "undefined" && INFO_TERMS[key]) || "";
    const tip = document.getElementById("v8InfoPopup");
    if (!tip || !txt) return;
    // Hide if already showing the same key
    if (tip.dataset.activeKey === key && tip.classList.contains("v8-visible")){
      tip.classList.remove("v8-visible"); tip.dataset.activeKey = "";
      return;
    }
    tip.textContent = txt;
    tip.dataset.activeKey = key;
    const rect = infoBtn.getBoundingClientRect();
    tip.style.top  = `${Math.min(rect.bottom + 8, window.innerHeight - 200)}px`;
    tip.style.left = `${Math.max(8, Math.min(rect.left - 8, window.innerWidth - 280))}px`;
    tip.classList.add("v8-visible");
    return;
  }
```

Also FIND (still in the click delegation block, outside the infoBtn block above):
```javascript
});
```
(the FINAL closing `});` of the `document.addEventListener("click", ...)` block — not an inner one)

IMMEDIATELY BEFORE that final `});` INSERT a catch-all tooltip dismisser:

```javascript
  // Dismiss info tooltip on any other click
  const tipEl = document.getElementById("v8InfoPopup");
  if (tipEl && tipEl.classList.contains("v8-visible") && !e.target.closest("[data-v8-info-term]")){
    tipEl.classList.remove("v8-visible"); tipEl.dataset.activeKey = "";
  }
```

---

### F4: ⓘ Info icons + clickable skills in "What's next" section headers

**Step 1 — discover exact header strings:**

Run:
```bash
grep -n "keystone\|bridge\|ZPD\|zpd\|sweet.spot\|revalidat" Maxine_Dashboard.html | grep -i "tutor\|section\|h3\|prio\|innerHTML" | head -20
```

Identify the lines inside `renderTutorTab()` where the Priorities section innerHTML is built.
These will contain strings like `"Keystone gaps"`, `"Bridge skills"`, `"ZPD"`, `"Revalidate"`.

**Step 2 — add `_infoIcon()` calls and `data-v8-skill-popup` to each:**

For each section label line in the Priorities/What's Next innerHTML builder, append `${_infoIcon("keystone")}` (or the appropriate key) immediately after the label text. Examples:

- FIND: `` `...Keystone gap... `` → REPLACE: `` `...Keystone gap${_infoIcon("keystone")}... ``
- FIND: `` `...Bridge skill... `` → REPLACE: `` `...Bridge skill${_infoIcon("bridge")}... ``
- FIND: `` `...ZPD... `` or `` `...sweet.spot... `` → REPLACE with `${_infoIcon("zpd")}`
- FIND: `` `...Revalidat... `` → REPLACE with `${_infoIcon("revalidate")}`

**Step 3 — make skill names clickable:**

Find all places in the Priorities section innerHTML builder where skill names are rendered as plain text (typically `escapeHtml(sk.t||sk.id)` or `escapeHtml(ks.t||ks.id)` or `escapeHtml(s.label)`). Wrap each in a button:

```javascript
// Before:
escapeHtml(sk.t||sk.id)
// After:
`<button class="v8-skill-btn" data-v8-skill-popup="${escapeHtml(sk.id)}">${escapeHtml(sk.t||sk.id)}</button>`
```

Do the same for any skill references in the Watch, Potential, and Pending sections.

---

### F5: Move v8TutorProfile (Observer Q&A) to "Outstanding questions" slot

This moves the Observer Q&A card from between the baseline sweep and the snapshot
(where C2 placed it) to below the Priorities card — making it part of the "What's next" flow.

#### F5a: Remove from current position

FIND (in `<section id="tutorView">` HTML — inserted by C2):
```html
    <!-- v8 — Observer Q&A -->
    <div id="v8TutorProfile" style="display:none; margin-bottom:14px"></div>
```
DELETE this block entirely.

#### F5b: Re-insert after Priorities card

FIND (in `<section id="tutorView">` HTML) the card div that contains `v7TutorPriorities`:
```html
    <div class="card v7-tutor-section">
```
(locate by the presence of `v7TutorPriorities` inside it — use grep:
`grep -n "v7TutorPriorities" Maxine_Dashboard.html`)

After the `</div>` that closes that card, INSERT:

```html
    <!-- v8 — Outstanding questions (observer Q&A, part of What's next) -->
    <div id="v8TutorProfile" style="display:none; margin-bottom:14px"></div>
```

---

### F6: Close button z-index — never covered by floating chatbot button

**Step 1 — find chatbot/FAB z-index:**
```bash
grep -n "chatbot\|chat-btn\|fab\|floating\|message.*btn\|msg-btn\|z-index.*[0-9]" Maxine_Dashboard.html | grep -i "z-index\|zIndex" | head -15
```

Note the highest z-index value used by any persistent floating button (`_fabZ`).

**Step 2 — add override rule:**

Inside the `/* v7 — Tutor tab` CSS block (or in the global style block, after all other rules), INSERT:

```css
/* v8/F — Close buttons always above floating action buttons */
.v8-skill-modal-overlay{ z-index:2000; }
.v8-skill-modal-sheet  { z-index:2001; }
.v8-skill-modal-close  { z-index:2002; }
#v8InfoPopup           { z-index:2500; }
```

If the app has a specific class or id for a chatbot/message floating button (e.g. `#chatBtn`, `.chat-fab`), and its z-index is ≥ 2000, increase the modal overlay z-index values proportionally so that `overlay > chatbot`. If unsure, set `.v8-skill-modal-overlay` to `z-index:9100`, `.v8-skill-modal-sheet` to `z-index:9101`, `.v8-skill-modal-close` to `z-index:9102`, `#v8InfoPopup` to `z-index:9500`.

Also add a general rule targeting any existing overlay close buttons in the app (search: `grep -n "close.*overlay\|overlay.*close\|closeOverlay\|close-modal" Maxine_Dashboard.html | head -10`). For any existing close button styles found, ensure they have `z-index` ≥ the chatbot FAB z-index.

---

## WORKSTREAM G — Tutor-quality upgrades: slippage radar, observer coaching, practicing status, stall Q&A, post-mastery probe, tutor attention banner, calibrated honesty

Apply G AFTER completing all prior workstreams (A–E, C+, F).

---

### G1 — Slippage radar (Skill 1: "runs but can she still walk?")

A skill mastered months ago without any recent confirming observation is at risk of having quietly regressed. The child may have moved on but the milestone was auto-estimated or observed only once.

#### G1a: Add `_getSlipRiskSkills()` helper

INSERT IMMEDIATELY BEFORE `function renderTutorTab()`:

```javascript
/* _getSlipRiskSkills — skills mastered >SLIP_DAYS ago with no confirming observation
   since, AND at least one downstream skill is now mastered (meaning the child has moved
   well past this tier — worth a sanity check, e.g. "she walks, but is she still doing
   fine motor grip?").
   Returns at most 4 skills, sorted by age of last observation (oldest first).        */
const SLIP_DAYS = 90;                          // days without observation → slip risk
const SLIP_DOWNSTREAM_MIN = 1;                 // need at least 1 downstream mastered

function _getSlipRiskSkills(){
  const now = Date.now();
  const slipMs = SLIP_DAYS * 86400000;
  const pool   = [...SKILLS, ...(SKILLS_CUSTOM_SEED||[]),
                  ...(Array.isArray(state.skillsCustom) ? state.skillsCustom : [])];
  const obs    = state.observations || [];

  return pool.filter(sk => {
    if (!sk || !isSkillMastered(sk.id)) return false;
    // Last observation for this skill
    const lastObs = obs.filter(o => o && o.skillId === sk.id)
                       .sort((a,b) => ((b.estimated_ts||b.ts||0) - (a.estimated_ts||a.ts||0)))[0];
    const lastTs = lastObs ? (lastObs.estimated_ts || lastObs.ts || 0) : 0;
    if (now - lastTs < slipMs) return false;              // observed recently — fine
    // At least SLIP_DOWNSTREAM_MIN downstream skills mastered
    const downstreamMastered = pool.filter(x =>
      Array.isArray(x.prereqs) && x.prereqs.includes(sk.id) && isSkillMastered(x.id)
    ).length;
    return downstreamMastered >= SLIP_DOWNSTREAM_MIN;
  })
  .sort((a,b) => {
    const lastA = (obs.filter(o=>o&&o.skillId===a.id).sort((p,q)=>(q.ts||0)-(p.ts||0))[0]||{}).ts||0;
    const lastB = (obs.filter(o=>o&&o.skillId===b.id).sort((p,q)=>(q.ts||0)-(p.ts||0))[0]||{}).ts||0;
    return lastA - lastB;   // oldest first
  })
  .slice(0, 4);
}
```

#### G1b: Add `v8TutorSlipRadar` HTML element

FIND (in `<section id="tutorView">`) the line:
```html
    <!-- v8 — Baseline sweep (below-frontier bulk mastery) -->
    <div id="v8TutorBaseline" style="display:none; margin-bottom:14px"></div>
```
INSERT IMMEDIATELY AFTER that line:
```html
    <!-- v8/G — Slippage radar (worth a recheck) -->
    <div id="v8TutorSlipRadar" style="display:none; margin-bottom:14px"></div>
```

#### G1c: Add `renderTutorSlipRadar()` function

INSERT IMMEDIATELY BEFORE `function renderTutorTab()`:

```javascript
/* renderTutorSlipRadar — shows skills at slip risk with a "Still doing it?" button. */
function renderTutorSlipRadar(){
  const el = document.getElementById("v8TutorSlipRadar");
  if (!el) return;
  const risks = _getSlipRiskSkills();
  if (!risks.length){ el.style.display = "none"; return; }

  const childName = ((typeof currentChild==="function"?currentChild():null)||{}).name || "the child";
  const items = risks.map(sk => {
    const dom = DOMAINS.find(d=>d.key===sk.dom)||{emoji:"·",label:sk.dom||""};
    return `<div style="display:flex; align-items:center; justify-content:space-between; gap:8px;
      padding:8px 0; border-bottom:1px solid var(--line); flex-wrap:wrap">
      <span style="font-size:13px">${dom.emoji} <strong>${escapeHtml(sk.t||sk.id)}</strong>
        <span style="font-size:11px; color:var(--muted)"> — not checked in ${SLIP_DAYS}+ days</span>
      </span>
      <div style="display:flex; gap:6px; flex-shrink:0">
        <button class="small primary" data-v8-slip-confirm="${escapeHtml(sk.id)}">✓ Still solid</button>
        <button class="small ghost"   data-v8-slip-recheck="${escapeHtml(sk.id)}">↩ Needs work</button>
      </div>
    </div>`;
  }).join("");

  el.innerHTML = `<div class="card v7-tutor-section">
    <h3 class="v7-tutor-h">🔁 Worth a double-check</h3>
    <p style="font-size:12px; color:var(--muted); margin:0 0 8px">
      ${escapeHtml(childName)} has moved well past these — but it's been a while since we confirmed them. Quick sanity check.
    </p>
    ${items}
  </div>`;
  el.style.display = "";
}
```

#### G1d: Wire slip-radar click handlers

FIND in the `document.addEventListener("click", ...)` delegation block:
```javascript
  // Skill detail popup — triggered by data-v8-skill-popup buttons
```
INSERT BEFORE it:
```javascript
  // Slip radar: "Still solid" → re-log as mastered to reset slip clock
  const slipConfirm = e.target.closest("[data-v8-slip-confirm]");
  if (slipConfirm){
    const id = slipConfirm.dataset.v8SlipConfirm;
    if (typeof addObservation==="function"){
      addObservation({ skillId:id, status:"mastered", source:"slip_reconfirm" });
    }
    if (typeof showToast==="function") showToast("✓ Confirmed — clock reset");
    try { renderTutorTab(); } catch(e){}
    return;
  }
  // Slip radar: "Needs work" → log working_on_it so it re-enters frontier
  const slipRecheck = e.target.closest("[data-v8-slip-recheck]");
  if (slipRecheck){
    const id = slipRecheck.dataset.v8SlipRecheck;
    if (typeof addObservation==="function"){
      addObservation({ skillId:id, status:"working_on_it", source:"slip_regression" });
    }
    if (typeof showToast==="function") showToast("↩ Returned to active frontier");
    try { renderTutorTab(); } catch(e){}
    return;
  }
```

#### G1e: Call `renderTutorSlipRadar()` inside `renderTutorTab()`

FIND (inside `renderTutorTab()`):
```javascript
  // v8 — Baseline sweep card
  renderTutorBaseline();
```
INSERT IMMEDIATELY AFTER it:
```javascript
  // v8/G — Slippage radar
  renderTutorSlipRadar();
```

#### G1f: Add slip-risk observer Q&A trigger to `_getContextualQuestions()`

FIND inside `_getContextualQuestions()` the comment:
```javascript
  return result;
}
```
INSERT BEFORE `return result`:

```javascript
  // 4. Slip-risk questions — for skills at slippage risk, ask for a quick confirmation
  const slipSkills = (typeof _getSlipRiskSkills==="function") ? _getSlipRiskSkills().slice(0,1) : [];
  slipSkills.forEach(sk => {
    const qid = `slip_${sk.id}`;
    if (dismissed[qid] || prof.answers[qid]) return;
    result.push({
      id: qid,
      text: `We haven't checked "${sk.t||sk.id}" in a while — can {name} still do this reliably?`,
      category: "goals",
      example: "e.g. \"yes, every day\" / \"actually she seems to have regressed a little\" / \"haven't specifically tested it\"",
      _context_label: "🔁 Slip-check — confirm still solid",
      _trigger: "slip"
    });
  });
```

---

### G2 — Observer coaching tips (Skill 2: the observer IS the coach)

The tutor knows the child's profile but the observer enacts the sessions. The tutor must coach the observer on HOW to engage — not just what to do but how to behave.

#### G2a: Add `q_intervention_style` to OBSERVER_QUESTIONS

FIND the last entry in `OBSERVER_QUESTIONS` (the one with `id:"q_context"`). INSERT a new entry BEFORE it:

```javascript
  { id:"q_intervention_style", expires_after_days:180, text:"When {name} struggles with something, what's your instinct — do you step in quickly, or wait and let her work through it?", category:"context", example:"e.g. \"I tend to jump in\" / \"I try to wait but it's hard\" / \"I wait it out, she gets frustrated otherwise\"" },
```

(This becomes the 10th core question; `q_context` becomes 11th. Update `const total = OBSERVER_QUESTIONS.length;` will self-correct since it uses `.length`.)

#### G2b: Add `coach_tip` field to missions via Haiku prompt

FIND in `generateMissionsViaHaiku` the line:
```
- best_moment: when in the day ...
```
ADD to the JSON schema description:
```
- coach_tip: one sentence on HOW the observer should engage during this activity (when to step back, how to prompt without rescuing, whether to model first or wait)
```

FIND the missions mapping code inside `generateMissionsViaHaiku`:
```javascript
      return {
        num: NUMS[i]||`${i+1}.`,
        skillId: m.skill_id,
```
ADD `coach_tip: m.coach_tip||"",` to the returned object.

FIND in `_missionsAlgorithmicFallback` the returned object (same structure). ADD:
```javascript
      coach_tip: "",
```

#### G2c: Render `coach_tip` in mission cards

FIND in the D4 missions renderer (inside `renderTutorTab()`) the mission card template:
```javascript
            ${m.why  ? `<div class="v8-mission-why">${escapeHtml(m.why)}</div>` : ""}
            <button class="small" data-v8-mission-skill=
```
INSERT between `m.why` and the button:
```javascript
            ${m.coach_tip ? `<div style="font-size:11px; color:#1E40AF; background:#EFF6FF; border-radius:6px; padding:4px 8px; margin-bottom:6px">👁 ${escapeHtml(m.coach_tip)}</div>` : ""}
```

---

### G3 — "Practicing" observation status (Skill 3: track deliberate practice time)

An observer should be able to log that they are *actively practicing* a skill in a session. This signals deliberate effort and lets the tutor detect "we're trying but it's not landing" vs. "we haven't tried at all."

#### G3a: Change mission "Did this today!" to log `"practicing"`

FIND (in the D3 mission click handler, inside the `document.addEventListener("click", ...)` block):
```javascript
      addObservation({ skillId:sid, status:"working_on_it", source:"weekly_mission" });
```
REPLACE with:
```javascript
      addObservation({ skillId:sid, status:"practicing", source:"weekly_mission" });
```

#### G3b: Extend stall detection in `_getContextualQuestions()` to count `"practicing"` intensity

FIND inside `_getContextualQuestions()` the keystone-stall block:
```javascript
    const recentObs = (state.observations||[]).filter(o => o && o.skillId===sk.id && (o.ts||0) > now - 28*86400000);
    if (!recentObs.length){
```
REPLACE with:
```javascript
    const recentObs = (state.observations||[]).filter(o =>
      o && o.skillId===sk.id && (o.ts||0) > now - 28*86400000
    );
    const practicingCount = recentObs.filter(o => o.status==="practicing").length;
    // If ≥3 practicing logs but still no mastery → actively stuck, worth asking why
    if (!recentObs.length || practicingCount >= 3){
```
Update the question text inside this block to distinguish the two cases:
```javascript
      const stallText = practicingCount >= 3
        ? `"${sk.t||sk.id}" has been practiced ${practicingCount} times recently but hasn't clicked yet. What seems to be getting in the way?`
        : `"${sk.t||sk.id}" has been on the horizon for a while. Any barriers?`;
      result.push({
        id: qid,
        text: stallText,
        category: "goals",
        example: "e.g. \"she tries but can't quite do it\" / \"haven't had opportunity\" / \"seems very close\"",
        _context_label: practicingCount >= 3 ? "🔄 Actively stuck — help me understand" : "⏳ Stalled keystone — help me understand",
        _trigger: "keystone"
      });
```
(Remove the previous `result.push({...})` call that was there before and replace with the above.)

#### G3c: Show "practicing" badge in priorities section

In the skill popup (already covered by F3 — the `frontierBadge` map), ensure `"practicing"` observations are reflected. Extend the skill popup's body with a practice log summary:

FIND in `_openSkillPopup`:
```javascript
    ${prereqNames ? `<div class="v8-skill-modal-label">Needs first</div><div class="v8-skill-modal-text">${prereqNames}</div>` : ""}
```
INSERT AFTER it:
```javascript
    ${(function(){
      const practiceObs = (state.observations||[]).filter(o => o && o.skillId===skillId && o.status==="practicing");
      if (!practiceObs.length) return "";
      const recent = practiceObs.filter(o => (o.ts||0) > Date.now() - 30*86400000).length;
      return `<div class="v8-skill-modal-label">Practice log</div><div class="v8-skill-modal-text">${practiceObs.length} session${practiceObs.length===1?"":"s"} total${recent ? `, ${recent} in the last 30 days` : ""}</div>`;
    })()}
```

---

### G4 — Broader stall Q&A (Skill 6: why hasn't this landed yet?)

Extend stall detection beyond keystones to all ready/stretch class skills stalled >42 days. The question framing should signal that the skill *should* be achievable, not just that it's pending.

#### G4a: Add non-keystone stall questions to `_getContextualQuestions()`

FIND inside `_getContextualQuestions()` the comment:
```javascript
  // 3. Keystone-stall questions — keystone in ready/stretch class with no observation in last 28 days
```
After the entire keystone-stall block (the `ks.slice(0, 2).forEach(...)` block), INSERT:

```javascript
  // 5. Non-keystone stall questions — any ready/stretch skill stalled >42 days, up to 1 per domain
  const GENERAL_STALL_DAYS = 42;
  const usedDomains = new Set(result.map(q => q._stall_dom).filter(Boolean));
  const allPool_g4 = [...SKILLS, ...(SKILLS_CUSTOM_SEED||[]),
                      ...(Array.isArray(state.skillsCustom)?state.skillsCustom:[])];
  const stalledNonKs = allPool_g4.filter(s => {
    if (!s || s.keystone) return false;
    const cls = (typeof classifySkillFrontier==="function") ? classifySkillFrontier(s) : "";
    if (cls !== "ready" && cls !== "stretch") return false;
    if (usedDomains.has(s.dom)) return false;
    const recentAny = (state.observations||[]).some(o =>
      o && o.skillId===s.id && (o.ts||0) > now - GENERAL_STALL_DAYS*86400000
    );
    return !recentAny;
  }).slice(0, 1);    // max 1 non-keystone stall question

  stalledNonKs.forEach(sk => {
    const qid = `stall_nks_${sk.id}`;
    if (dismissed[qid] || prof.answers[qid]) return;
    const dom = (typeof DOMAINS!=="undefined") ? DOMAINS.find(d=>d.key===sk.dom)||{emoji:"✨",label:sk.dom} : {emoji:"✨",label:sk.dom};
    result.push({
      id: qid,
      text: `"${sk.t||sk.id}" (${dom.emoji} ${dom.label}) should be within {name}'s reach by now — has she had a chance to try it? Anything getting in the way?`,
      category: "goals",
      example: "e.g. \"we haven't tried it recently\" / \"she attempts it but not reliably\" / \"this one seems harder than expected\"",
      _context_label: "📋 In reach but not yet landed",
      _trigger: "stall_general",
      _stall_dom: sk.dom
    });
  });
```

---

### G5 — Post-mastery keystone probe (Skill 7: check mastery quality)

For important skills recently mastered, the tutor should confirm the mastery is solid and generalised — not just a one-time lab performance.

#### G5a: Add `_getMasteryProbeQuestions()` helper

INSERT IMMEDIATELY AFTER `_getContextualQuestions()` (before `_getNextObserverQuestion`):

```javascript
/* _getMasteryProbeQuestions — for keystones mastered 14–75 days ago,
   returns quality-check questions to confirm the mastery is generalised
   and integrated into daily life (not just a single lucky observation).     */
function _getMasteryProbeQuestions(){
  const result = [];
  const prof = state.observerProfile || {};
  const dismissed = prof.contextual_dismissed || {};
  const now = Date.now();
  const PROBE_MIN_DAYS = 14;    // mastered at least 14 days ago
  const PROBE_MAX_DAYS = 75;    // but not older than 75 days (too stale)

  const pool = [...SKILLS, ...(SKILLS_CUSTOM_SEED||[]),
                ...(Array.isArray(state.skillsCustom)?state.skillsCustom:[])];
  const obs  = state.observations || [];

  const candidates = pool.filter(sk => {
    if (!sk || !sk.keystone || !isSkillMastered(sk.id)) return false;
    const masteryObs = obs
      .filter(o => o && o.skillId===sk.id &&
        (o.status==="mastered" || o.status==="already_mastered"))
      .sort((a,b) => ((b.estimated_ts||b.ts||0) - (a.estimated_ts||a.ts||0)));
    if (!masteryObs.length) return false;
    const masteredTs = masteryObs[0].estimated_ts || masteryObs[0].ts || 0;
    const age = (now - masteredTs) / 86400000;
    return age >= PROBE_MIN_DAYS && age <= PROBE_MAX_DAYS;
  }).slice(0, 2);

  candidates.forEach(sk => {
    const qid = `probe_${sk.id}`;
    if (dismissed[qid] || prof.answers[qid]) return;
    result.push({
      id: qid,
      text: `Since {name} mastered "${sk.t||sk.id}" — how is she using it in daily life? Is it fully integrated, or still occasional?`,
      category: "goals",
      example: "e.g. \"uses it every day, it's natural now\" / \"does it but still needs reminding\" / \"showed it once, haven't seen it since\"",
      _context_label: "🎖 Quality check — recently mastered keystone",
      _trigger: "mastery_probe"
    });
  });

  return result;
}
```

#### G5b: Insert `_getMasteryProbeQuestions()` into `_getNextObserverQuestion()` priority queue

FIND inside `_getNextObserverQuestion()`:
```javascript
  // 2. Contextual questions (era → domain → keystone)
  const contextual = _getContextualQuestions();
  if (contextual.length) return contextual[0];
```
INSERT BETWEEN the expired-core block and the contextual block:
```javascript
  // 1b. Post-mastery keystone probes (quality check — higher signal than general contextual)
  const probes = (typeof _getMasteryProbeQuestions==="function") ? _getMasteryProbeQuestions() : [];
  if (probes.length) return probes[0];
```

(So the final priority order is: expired core → mastery probes → contextual → unanswered core → recycled skipped.)

---

### G6 — Tutor attention banner (Skill 10: tutor-initiated pop-up questions)

When the tutor has a pending question for the observer (stall, slip-check, mastery probe, expired answer), a subtle attention indicator appears at the top of the Tutor tab. Tapping it scrolls the observer to the Q&A card.

#### G6a: Add `v8TutorAttentionBanner` HTML element inside the hero card

FIND (in `<section id="tutorView">`) the element with `id="v8TutorPushPull"` (added in F1b). INSERT IMMEDIATELY BEFORE it:
```html
          <!-- v8/G — Tutor attention banner: shown when tutor has a pending question -->
          <div id="v8TutorAttentionBanner" style="display:none; margin-top:8px;
            background:#FEF9C3; border:1px solid #FDE047; border-radius:8px;
            padding:8px 12px; font-size:12px; cursor:pointer; color:#713F12;
            display:flex; align-items:center; gap:6px">
            💬 <span id="v8TutorAttentionText">The tutor has a question for you</span>
            <span style="margin-left:auto; font-size:10px; opacity:.7">↓ scroll to see</span>
          </div>
```

#### G6b: Populate banner in `renderTutorTab()`

FIND in `renderTutorTab()` (after the push/pull chips block added in F1c):
```javascript
  // v8 — Observer Q&A
  renderObserverProfile();
```
INSERT IMMEDIATELY BEFORE it:
```javascript
  // v8/G — Tutor attention banner
  const _banner = document.getElementById("v8TutorAttentionBanner");
  if (_banner){
    const _nextQ = (typeof _getNextObserverQuestion==="function") ? _getNextObserverQuestion() : null;
    if (_nextQ){
      const _bannerText = document.getElementById("v8TutorAttentionText");
      if (_bannerText){
        const _labelMap = {
          refresh:"🔄 The tutor has an updated question for you",
          era:"🌱 New milestone — the tutor wants to understand better",
          domain:"✨ A new domain just opened — the tutor has a question",
          keystone:"⏳ A skill seems stuck — the tutor wants to know why",
          slip:"🔁 Worth a quick check — the tutor has a question",
          mastery_probe:"🎖 The tutor wants to confirm a mastered skill",
          stall_general:"📋 A skill is in reach — the tutor wants to understand"
        };
        _bannerText.textContent = _labelMap[_nextQ._trigger] || "💬 The tutor has a question for you";
      }
      _banner.style.display = "flex";
      // Click: scroll to v8TutorProfile
      _banner.onclick = () => {
        const _pEl = document.getElementById("v8TutorProfile");
        if (_pEl){ _pEl.scrollIntoView({ behavior:"smooth", block:"start" }); }
      };
    } else {
      _banner.style.display = "none";
    }
  }
```

---

### G7 — Calibrated honesty (Skill 12: surface frontier limits)

When the child is at the advanced edge of a domain (≥70% mastered), the tutor should honestly note that structured practice has diminishing returns — environment and immersion drive the rest.

#### G7a: Add `_getFrontierLimitNote()` helper

INSERT IMMEDIATELY BEFORE `function renderTutorTab()`:

```javascript
/* _getFrontierLimitNote — returns a string (or null) if the child has mastered
   ≥70% of a domain's skills. Signals that gains in that domain are now driven
   by environment, immersion, and opportunity rather than structured practice. */
const FRONTIER_SATURATION = 0.70;   // fraction of domain mastered → calibrated honesty kicks in

function _getFrontierLimitNote(){
  const pool = [...SKILLS, ...(SKILLS_CUSTOM_SEED||[]),
                ...(Array.isArray(state.skillsCustom)?state.skillsCustom:[])];
  const childName = ((typeof currentChild==="function")?currentChild():null)?.name || "Maxine";

  const notes = [];
  (typeof DOMAINS!=="undefined" ? DOMAINS : []).forEach(dom => {
    const domSkills  = pool.filter(s => s && s.dom === dom.key);
    if (domSkills.length < 5) return;    // too few skills to judge
    const mastCount  = domSkills.filter(s => isSkillMastered(s.id)).length;
    const fraction   = mastCount / domSkills.length;
    if (fraction < FRONTIER_SATURATION) return;

    const pct = Math.round(fraction * 100);
    // Domain-specific immersion suggestions
    const suggestions = {
      gross:     "outdoor free play and varied physical environments matter more than structured sessions",
      fine:      "access to varied tools (scissors, clay, beads) and creative freedom drive the rest",
      cognitive: "open-ended puzzles, stories, and real-world exploration take over from direct teaching",
      vocab:     "rich conversation, books, and narrative play are the dominant levers now",
      social:    "peer interaction quality and regularity matter far more than adult-led coaching",
      sensory:   "natural environmental variety and self-directed sensory play are the primary inputs"
    };
    const tip = suggestions[dom.key] || "environment and daily life exposure drive further gains";
    notes.push(`${dom.emoji} ${dom.label}: ${pct}% mastered — at this level, ${tip}.`);
  });

  if (!notes.length) return null;
  return `Frontier note for ${childName}: ${notes.join(" ")} Structured practice has diminishing returns here — lean into environment.`;
}
```

#### G7b: Add frontier limit note to `computeTutorNarrative()`

FIND inside `computeTutorNarrative()` the last line:
```javascript
  return [p1, p2 + velBit, p3 + pProfile].join(" ");
```
REPLACE with:
```javascript
  const frontierNote = (typeof _getFrontierLimitNote==="function") ? _getFrontierLimitNote() : null;
  const parts = [p1, p2 + velBit, p3 + pProfile];
  if (frontierNote) parts.push(frontierNote);
  return parts.join(" ");
```

---

### G: State keys and defaults

#### G-state: Add new keys to `PER_CHILD_KEYS` and `defaultForKey`

`_getSlipRiskSkills` and `_getMasteryProbeQuestions` use only existing state
(`state.observations`). No new per-child keys are needed.

Verify: `SLIP_DAYS`, `SLIP_DOWNSTREAM_MIN`, `FRONTIER_SATURATION`,
`GENERAL_STALL_DAYS`, `PROBE_MIN_DAYS`, `PROBE_MAX_DAYS` are all module-level
constants — they don't go in state.

---

## VERIFICATION CHECKLIST

After applying all workstreams (A–E, C+, F), verify:

1. `node --check Maxine_Dashboard.html` — expected: pre-existing `<\/script>` error
   at ~line 9173 only; no new syntax errors in new code.
2. `grep -c "v8TutorBaseline\|v8TutorProfile\|v8-mission" Maxine_Dashboard.html` — should be ≥ 8.
3. `grep -c "bulkBaselineSweep\|renderTutorBaseline\|renderObserverProfile\|generateMissionsViaHaiku\|_missionsAlgorithmicFallback\|_estimateEarlyTs" Maxine_Dashboard.html` — should be ≥ 12 (definitions + call sites).
4. `grep "observerProfile\|baselineSweepDismissed\|weeklyMissions" Maxine_Dashboard.html | grep "PER_CHILD_KEYS"` — should return 1 line (the updated PER_CHILD_KEYS line).
5. `grep -c "data-v8-sweep-domain\|data-v8-profile-save\|data-v8-mission-skill" Maxine_Dashboard.html` — should be ≥ 3.
6. `grep -c "_installMissionsHook\|MISSIONS_MASTERY_TRIGGER\|_missionsMasteryCount" Maxine_Dashboard.html` — should be ≥ 3.
7. `grep -c "generateMissionsViaHaiku" Maxine_Dashboard.html` — should be ≥ 3 (definition + mastery hook + refresh handler).
8. Confirm `_installMissionsHook` IIFE appears AFTER `_installMmHook` IIFE in the file.
9. `grep -c "_getNextObserverQuestion\|_getContextualQuestions\|ERA_TRANSITION_QUESTIONS\|DOMAIN_UNLOCK_QUESTIONS" Maxine_Dashboard.html` — should be ≥ 6 (definitions + call sites).
10. `grep -c "expires_after_days" Maxine_Dashboard.html` — should be ≥ 10 (one per OBSERVER_QUESTIONS entry).
11. `grep -c "data-v8-profile-cdismiss\|contextual_dismissed\|skipped_at" Maxine_Dashboard.html` — should be ≥ 4.
12. Confirm file ends with `</script></body></html>` (not truncated).
13. Confirm `ERA_TRANSITION_QUESTIONS` keys match actual ERAS array keys in the file
    (`grep -o '"key":"[^"]*"' Maxine_Dashboard.html | grep -i era | head -20` to list them).
    If keys don't match, update ERA_TRANSITION_QUESTIONS accordingly.
14. `grep -c "_calcXP\|_openSkillPopup\|_infoIcon\|INFO_TERMS" Maxine_Dashboard.html` — should be ≥ 8 (definitions + call sites).
15. `grep -c "v8SkillModal\|v8-skill-modal\|v8-skill-btn\|v8-info-btn" Maxine_Dashboard.html` — should be ≥ 8.
16. `grep -c "v8TutorPushPull\|v8-pushpull-chip" Maxine_Dashboard.html` — should be ≥ 3.
17. `grep -c "data-v8-skill-popup\|data-v8-info-term" Maxine_Dashboard.html` — should be ≥ 6 (modal, sections, click handlers).
18. Confirm `v8TutorProfile` div appears AFTER the `v7TutorPriorities` card in the HTML
    (line number of v8TutorProfile > line number of v7TutorPriorities).
19. Confirm `v8SkillModal` and `v8InfoPopup` appear just before `</body>`.
20. Confirm modal `.v8-skill-modal-close` has a z-index > any floating chatbot/FAB button in the file.
21. `grep -c "_getSlipRiskSkills\|renderTutorSlipRadar\|v8TutorSlipRadar\|data-v8-slip" Maxine_Dashboard.html` — should be ≥ 6.
22. `grep -c "_getMasteryProbeQuestions\|mastery_probe\|probe_" Maxine_Dashboard.html` — should be ≥ 4.
23. `grep -c "_getFrontierLimitNote\|FRONTIER_SATURATION\|frontierNote" Maxine_Dashboard.html` — should be ≥ 4.
24. `grep -c "v8TutorAttentionBanner\|v8TutorAttentionText" Maxine_Dashboard.html` — should be ≥ 3.
25. `grep -c "q_intervention_style\|coach_tip" Maxine_Dashboard.html` — should be ≥ 4.
26. `grep -c "status.*practicing\|\"practicing\"" Maxine_Dashboard.html` — should be ≥ 3.
27. `grep -c "stall_nks_\|stall_general\|GENERAL_STALL_DAYS" Maxine_Dashboard.html` — should be ≥ 3.
28. `grep -c "slip_reconfirm\|slip_regression\|SLIP_DAYS" Maxine_Dashboard.html` — should be ≥ 3.
29. Confirm `_getMasteryProbeQuestions()` is called between the expired-core block and
    the contextual block inside `_getNextObserverQuestion()` (priority order preserved).
30. Confirm `renderTutorSlipRadar()` is called inside `renderTutorTab()` after
    `renderTutorBaseline()`.

Report final byte count and any deviations from the spec.

---

## ⚠️ WORKSTREAM H RECONCILIATION NOTES (from H implementation run)

**R13 — Skill domain key is `.dom`, NOT `.domain`.**
The raw skill objects store domain in `.dom` (e.g., `{id:"gm-walk", dom:"gross", …}`).
The spec used `s.domain` which evaluates to `undefined` for every skill, making all
domain bars and radar axes render at 0%. Always use `s.dom` (with `s.domain` as
fallback only for custom skills that may differ): `s.dom || s.domain`.

**R14 — `classifySkillFrontier` takes a skill OBJECT, not a skill ID string.**
`classifySkillFrontier(s.id)` misclassifies everything — the function reads `.prereqs`,
`.dom`, `.difficulty` off its argument. Always call `classifySkillFrontier(s)` where
`s` is the full skill object from `SKILLS` or `state.skillsCustom`.
Applies to any column-building code (ZPD Ready, Stretch) in the kanban and elsewhere.

**R15 — Mission object field names differ from H5 spec.**
Actual mission objects returned by `generateMissionsViaHaiku()` / `state.weeklyMissions.missions`:
- Skill ref: `m.skillId` (primary) — NOT `m.target_skill_ids[0]`
- Title: `m.title` (primary) — NOT `m.activity_title`
- Duration: `m.duration` — NOT `m.expected_duration_min`
- Domain: derived from the resolved skill's `.dom` — NOT `m.domain`
Keep spec-style names as secondary fallbacks: `m.skillId || (m.target_skill_ids||[])[0]`, etc.

**R16 — `addObservation` parameter key is `skillId`, NOT `skill_id`.**
The function signature expects `{skillId, status, source}`.
`skill_id` is silently ignored, causing the observation to log with no skill link.
Always use `addObservation({ skillId: …, status: …, source: … })`.

**R17 — Hero card rebuild removes push-chip and attention banner.**
`_buildHeroCard()` replaces `.v7-tutor-hero`'s entire innerHTML. The push-chip (F1c)
and tutor attention banner (G6b) that previously lived inside this card are no longer
rendered. Their populate code is null-guarded so no JS errors occur — they simply
don't appear. If you need to reinstate them, add their element shells to the hero's
bottom section HTML inside `_buildHeroCard()` (after the XP bar, before `v7TutorNarrative`).

---

## WORKSTREAM H — Visual redesign

Choices: Hero B · Domains C · Skills A · Heatmap A · Missions C.

Apply sequentially H0 → H1 → H2 → H3 → H4 → H5.
After each sub-workstream: `wc -c Maxine_Dashboard.html` + `node --check` (JS-extraction method per prior note).

---

### H0 — CSS additions

GREP for this line (to find insertion point):
```
.v7-tutor-why{ color:var(--muted); font-size:12px; }
```
INSERT AFTER that line:
```css
/* ── WORKSTREAM H: visual redesign ── */
/* H1 game hero card */
.v8-hero-top{background:#1F2A44;border-radius:14px 14px 0 0;padding:16px;color:#fff;text-align:center}
.v8-hero-av{font-size:48px;line-height:1;margin-bottom:6px}
.v8-hero-name{font-size:20px;font-weight:800;letter-spacing:-.02em}
.v8-hero-badge{display:inline-block;background:#F59E0B;color:#fff;font-size:10px;font-weight:800;padding:3px 12px;border-radius:999px;letter-spacing:.05em;margin-top:6px}
.v8-hero-bot{padding:14px;background:var(--card);border-radius:0 0 14px 14px}
.v8-hero-bars{display:grid;gap:7px;margin-bottom:12px}
.v8-hero-row{display:flex;align-items:center;gap:8px}
.v8-hero-lbl{width:80px;font-size:10px;font-weight:700;color:var(--muted);flex-shrink:0}
.v8-hero-bar{flex:1;height:7px;border-radius:999px;background:#F1F4FA;overflow:hidden}
.v8-hero-fill{height:100%;border-radius:999px;transition:width .8s cubic-bezier(.4,0,.2,1)}
.v8-hero-pct{width:32px;text-align:right;font-size:10px;font-weight:700;color:var(--ink)}
.v8-xp-row{display:flex;justify-content:space-between;font-size:11px;margin-bottom:3px}
.v8-xp-lv{font-weight:800;color:var(--accent)}
.v8-xp-num{color:var(--muted);font-weight:600}
.v8-xp-bar{height:6px;border-radius:999px;background:#E0E7FF;overflow:hidden}
.v8-xp-fill{height:100%;background:linear-gradient(90deg,#2E5BFF,#818CF8);border-radius:999px;transition:width .8s cubic-bezier(.4,0,.2,1)}
/* H2 domain radar */
.v8-radar-wrap{display:flex;flex-direction:column;align-items:center}
/* H3 kanban */
.v8-kanban{display:grid;grid-template-columns:repeat(3,1fr);gap:8px}
.v8-kan-head{font-size:9px;font-weight:800;letter-spacing:.06em;text-transform:uppercase;padding:5px 8px;border-radius:7px 7px 0 0;text-align:center}
.v8-kan-body{display:flex;flex-direction:column;gap:4px;padding:5px;border-radius:0 0 8px 8px;min-height:60px}
.v8-kan-item{border-radius:7px;padding:6px 8px;font-size:11px;font-weight:700;display:flex;align-items:center;gap:5px;cursor:pointer;border:1px solid transparent;transition:opacity .1s}
.v8-kan-item:hover{opacity:.75}
@media(max-width:480px){.v8-kanban{grid-template-columns:1fr}}
/* H4 heatmap */
.v8-heat-wrap{display:flex;gap:2px;overflow-x:auto;padding-bottom:4px}
.v8-heat-col{display:flex;flex-direction:column;gap:2px;flex-shrink:0}
.v8-heat-cell{width:12px;height:12px;border-radius:2px;cursor:pointer;transition:transform .1s}
.v8-heat-cell:hover{transform:scale(1.5)}
.v8-heat-legend{display:flex;align-items:center;gap:4px;margin-top:8px;font-size:10px;color:var(--muted)}
/* H5 mission checklist */
.v8-mc-item{display:flex;align-items:center;gap:10px;padding:10px 0;border-bottom:1px solid var(--line)}
.v8-mc-item:last-child{border-bottom:none}
.v8-mc-dot{width:22px;height:22px;border-radius:7px;flex-shrink:0;display:flex;align-items:center;justify-content:center;font-size:12px}
.v8-mc-txt{flex:1;min-width:0}
.v8-mc-name{font-size:12px;font-weight:700;color:var(--ink)}
.v8-mc-sub{font-size:10px;color:var(--muted);margin-top:1px}
.v8-mc-check{width:24px;height:24px;border-radius:7px;border:2px solid var(--line);flex-shrink:0;cursor:pointer;display:flex;align-items:center;justify-content:center;font-size:13px;font-weight:700;transition:all .12s;color:transparent}
.v8-mc-check:hover{border-color:var(--good);background:#DCFCE7}
.v8-mc-check.v8-chk-done{background:#DCFCE7;border-color:#16A34A;color:#16A34A}
```

---

### H1 — Game character hero card

**Goal**: Replace the flat `.v7-tutor-hero` card with dark-navy top (emoji · name · level badge) / white bottom (per-domain bars · XP bar · narrative).

#### H1a — Strip padding from the card shell

FIND in HTML:
```html
<div class="card v7-tutor-hero" style="margin-bottom:14px">
```
REPLACE WITH:
```html
<div class="card v7-tutor-hero" style="margin-bottom:14px;padding:0;overflow:hidden">
```

#### H1b — Add constants and helpers

GREP for `function renderTutorTab` to locate the tutor render function.
Insert the following IMMEDIATELY BEFORE `function renderTutorTab`:

```javascript
const _V8_DOMAIN_META = [
  {key:"gross",    label:"Gross Motor", color:"#3B82F6"},
  {key:"fine",     label:"Fine Motor",  color:"#F59E0B"},
  {key:"sensory",  label:"Sensory",     color:"#F97316"},
  {key:"cognitive",label:"Cognitive",   color:"#6366F1"},
  {key:"vocab",    label:"Language",    color:"#EC4899"},
  {key:"social",   label:"Social",      color:"#6B7280"},
];
const _V8_LEVEL_NAMES = ["","Newborn","Explorer","Adventurer","Pioneer","Champion","Master"];
const _V8_XP_PER_LEVEL = 500;
const _V8_HEAT_WEEKS = 16;
const _V8_HEAT_COLORS = ["#EEF2FF","#BFDBFE","#60A5FA","#2563EB","#1E3A8A"];

function _domainMasteryPct(domainKey) {
  const pool = [
    ...SKILLS,
    ...(Array.isArray(state.skillsCustom) ? state.skillsCustom : [])
  ].filter(s => s && s.domain === domainKey);
  if (!pool.length) return 0;
  return Math.round(pool.filter(s => isSkillMastered(s.id)).length / pool.length * 100);
}

function _buildHeroCard() {
  const el = document.querySelector(".v7-tutor-hero");
  if (!el) return;
  const childId = typeof getActiveChildId === "function" ? getActiveChildId() : null;
  const child   = typeof currentChild === "function" ? currentChild() : null;
  const name    = child?.name  || "Maxine";
  const emoji   = child?.emoji || "👧";
  const xp      = typeof _calcXP === "function" ? _calcXP() : 0;
  const level   = Math.max(1, Math.floor(xp / _V8_XP_PER_LEVEL) + 1);
  const lvName  = (_V8_LEVEL_NAMES[Math.min(level, _V8_LEVEL_NAMES.length - 1)] || "Champion").toUpperCase();
  const xpInLv  = xp % _V8_XP_PER_LEVEL;
  const xpPct   = Math.round(xpInLv / _V8_XP_PER_LEVEL * 100);

  const bars = _V8_DOMAIN_META.map(d => {
    const pct = _domainMasteryPct(d.key);
    return `<div class="v8-hero-row">
      <span class="v8-hero-lbl">${escapeHtml(d.label)}</span>
      <div class="v8-hero-bar"><div class="v8-hero-fill" style="width:0%;background:${d.color}" data-w="${pct}"></div></div>
      <span class="v8-hero-pct">${pct}%</span>
    </div>`;
  }).join("");

  // Preserve the narrative element content before replacing innerHTML
  const narrativeEl = document.getElementById("v7TutorNarrative");
  const narrativeOuter = narrativeEl ? narrativeEl.outerHTML : `<div id="v7TutorNarrative" class="v7-tutor-narr"></div>`;

  el.innerHTML = `
    <div class="v8-hero-top">
      <div class="v8-hero-av">${escapeHtml(emoji)}</div>
      <div class="v8-hero-name">${escapeHtml(name)}</div>
      <div class="v8-hero-badge">⭐ LEVEL ${level} — ${escapeHtml(lvName)}</div>
    </div>
    <div class="v8-hero-bot">
      <div class="v8-hero-bars">${bars}</div>
      <div>
        <div class="v8-xp-row">
          <span class="v8-xp-lv">Lv ${level}</span>
          <span class="v8-xp-num">${xp.toLocaleString()} XP · ${xpPct}% to next</span>
        </div>
        <div class="v8-xp-bar"><div class="v8-xp-fill" id="v8HeroXpFill" style="width:0%"></div></div>
      </div>
      ${narrativeOuter}
    </div>`;

  // Animate bar fills after paint
  requestAnimationFrame(() => requestAnimationFrame(() => {
    el.querySelectorAll(".v8-hero-fill[data-w]").forEach(f => { f.style.width = f.dataset.w + "%"; });
    const xpEl = document.getElementById("v8HeroXpFill");
    if (xpEl) xpEl.style.width = xpPct + "%";
  }));
}
```

#### H1c — Call `_buildHeroCard()` at the top of `renderTutorTab`

FIND the FIRST line inside `function renderTutorTab` that does real work (e.g., sets
`v7TutorTitle.textContent` or clears a container). INSERT BEFORE it:
```javascript
_buildHeroCard();
```

After `_buildHeroCard()` runs, `v7TutorTitle` and `v7TutorMeta` no longer exist in the DOM.
Guard any subsequent code that references them:
```javascript
const _tutorTitleEl = document.getElementById("v7TutorTitle");
if (_tutorTitleEl) _tutorTitleEl.textContent = …;
```
(Or simply remove those lines — the hero card already renders the child name and meta.)

---

### H2 — Domain radar (Snapshot card)

**Goal**: Replace `v7TutorSnapshot` contents with an SVG hexagonal spider chart.

Insert the following function IMMEDIATELY AFTER `_buildHeroCard` (still before `renderTutorTab`):

```javascript
function _buildDomainRadar() {
  const el = document.getElementById("v7TutorSnapshot");
  if (!el) return;
  const vals  = _V8_DOMAIN_META.map(d => _domainMasteryPct(d.key) / 100);
  const CX = 110, CY = 105, R = 80;
  // Axes: top = Gross (−90°), clockwise every 60°
  const DEGS  = [-90, -30, 30, 90, 150, 210];
  const RADS  = DEGS.map(d => d * Math.PI / 180);
  const toXY  = (angle, r) => [CX + Math.cos(angle) * r, CY + Math.sin(angle) * r];
  const hexPts = scale => RADS.map(a => toXY(a, R * scale).join(",")).join(" ");
  const dataPts = vals.map((v, i) => toXY(RADS[i], R * v).join(",")).join(" ");

  const gridLines = [0.25, 0.5, 0.75, 1.0].map(s =>
    `<polygon points="${hexPts(s)}" fill="none" stroke="#CBD5E1" stroke-width="${s===1?1:0.6}" opacity="${s===1?1:0.45}"/>`
  ).join("");
  const axisLines = RADS.map(a => {
    const [ex,ey] = toXY(a, R);
    return `<line x1="${CX}" y1="${CY}" x2="${ex.toFixed(1)}" y2="${ey.toFixed(1)}" stroke="#E2E8F0" stroke-width="1"/>`;
  }).join("");
  const dots = vals.map((v, i) => {
    const [px,py] = toXY(RADS[i], R * v);
    return `<circle cx="${px.toFixed(1)}" cy="${py.toFixed(1)}" r="4" fill="${_V8_DOMAIN_META[i].color}"/>`;
  }).join("");
  const LABEL_R = R + 20;
  const labels = _V8_DOMAIN_META.map((d, i) => {
    const [lx, ly] = toXY(RADS[i], LABEL_R);
    const anchor = lx < CX - 6 ? "end" : lx > CX + 6 ? "start" : "middle";
    const pct = Math.round(vals[i] * 100);
    return `<text x="${lx.toFixed(1)}" y="${(ly+4).toFixed(1)}" text-anchor="${anchor}"
      font-size="9" font-weight="700" fill="#5C6680"
      font-family="-apple-system,BlinkMacSystemFont,sans-serif">${escapeHtml(d.label)}
      <tspan fill="${d.color}" font-size="8"> ${pct}%</tspan></text>`;
  }).join("");

  el.innerHTML = `<div class="v8-radar-wrap">
    <svg width="220" height="210" viewBox="0 0 220 210" style="overflow:visible;display:block;margin:0 auto">
      ${gridLines}${axisLines}
      <polygon points="${dataPts}" fill="#2E5BFF" fill-opacity="0.12"
        stroke="#2E5BFF" stroke-width="2" stroke-linejoin="round"/>
      ${dots}${labels}
    </svg>
  </div>`;
}
```

FIND the code block inside `renderTutorTab` that sets `v7TutorSnapshot.innerHTML`
(grep: `v7TutorSnapshot`). Replace or wrap it so that `_buildDomainRadar()` is called
INSTEAD. If the existing code also appends a domain list below the SVG, keep that block
below the `_buildDomainRadar()` call — do not remove it.

---

### H3 — Skills kanban (Priorities card)

**Goal**: Replace `v7TutorPriorities` with a 3-column kanban: Mastered (6 most recent) · ZPD Ready · Stretch.

Insert the following function IMMEDIATELY AFTER `_buildDomainRadar`:

```javascript
function _buildKanban() {
  const el = document.getElementById("v7TutorPriorities");
  if (!el) return;

  const pool = [
    ...SKILLS,
    ...(Array.isArray(state.skillsCustom) ? state.skillsCustom : [])
  ].filter(Boolean);

  // Column 1: 6 most recently mastered
  const masteredAt = state.masteredAt || {};
  const recentMastered = pool
    .filter(s => isSkillMastered(s.id))
    .sort((a, b) => (masteredAt[b.id] || 0) - (masteredAt[a.id] || 0))
    .slice(0, 6);

  // Column 2: ZPD ready (ready + verify)
  const zdpReady = pool.filter(s =>
    !isSkillMastered(s.id) &&
    typeof classifySkillFrontier === "function" &&
    ["ready","verify"].includes(classifySkillFrontier(s.id))
  );

  // Column 3: Stretch (first 4)
  const stretch = pool.filter(s =>
    !isSkillMastered(s.id) &&
    typeof classifySkillFrontier === "function" &&
    classifySkillFrontier(s.id) === "stretch"
  ).slice(0, 4);

  function kanItem(s, bg, fg, border) {
    const nameStr = escapeHtml(s.t || s.id);
    const emojiStr = s.emoji ? `<span>${escapeHtml(s.emoji)}</span>` : "";
    const star = s.keystone ? `<span style="font-size:8px;margin-left:auto">⭐</span>` : "";
    const onclick = `typeof _openSkillPopup==="function"&&_openSkillPopup("${escapeHtml(s.id)}")`;
    return `<div class="v8-kan-item" style="background:${bg};color:${fg};border-color:${border}" onclick="${onclick}">
      ${emojiStr}
      <span style="flex:1;min-width:0;overflow:hidden;text-overflow:ellipsis;white-space:nowrap">${nameStr}</span>
      ${star}
    </div>`;
  }

  const empty = `<div style="font-size:11px;color:var(--muted);padding:4px;font-style:italic">None yet</div>`;

  el.innerHTML = `<div class="v8-kanban">
    <div>
      <div class="v8-kan-head" style="background:#DCFCE7;color:#14532D">✓ Mastered</div>
      <div class="v8-kan-body" style="background:#F0FDF4">
        ${recentMastered.map(s=>kanItem(s,"#DCFCE7","#14532D","#86EFAC")).join("")||empty}
      </div>
    </div>
    <div>
      <div class="v8-kan-head" style="background:#EEF2FF;color:#2E5BFF">🔓 ZPD Ready</div>
      <div class="v8-kan-body" style="background:#F5F7FF">
        ${zdpReady.map(s=>kanItem(s,"#EEF2FF","#1E3A8A","#A5B4FC")).join("")||empty}
      </div>
    </div>
    <div>
      <div class="v8-kan-head" style="background:#FEF9C3;color:#92400E">⏳ Stretch</div>
      <div class="v8-kan-body" style="background:#FEFCE8">
        ${stretch.map(s=>kanItem(s,"#FEF3C7","#92400E","#FDE68A")).join("")||empty}
      </div>
    </div>
  </div>`;
}
```

FIND the code inside `renderTutorTab` that sets `v7TutorPriorities.innerHTML`.
Replace that assignment with a call to `_buildKanban()`.

---

### H4 — Activity heatmap (new card)

**Goal**: Insert a new GitHub-style 16-week activity heatmap card, driven by `state.skillStatus` and `state.observations` timestamps.

#### H4a — HTML: new card

FIND in the HTML `tutorView` section:
```html
<div id="v8TutorBaseline" style="display:none; margin-bottom:14px"></div>
```
INSERT AFTER:
```html
<div class="card" id="v8TutorHeatmap" style="margin-bottom:14px;display:none"></div>
```

#### H4b — JS function

Insert IMMEDIATELY AFTER `_buildKanban`:

```javascript
function _buildHeatmap() {
  const el = document.getElementById("v8TutorHeatmap");
  if (!el) return;

  // Aggregate all activity timestamps
  const tsList = [];
  Object.values(state.skillStatus || {}).forEach(v => { if (v?.ts) tsList.push(v.ts); });
  (state.observations || []).forEach(o => { if (o?.ts) tsList.push(o.ts); });

  // Build date-key → count map
  const dayMap = {};
  tsList.forEach(ts => {
    const key = new Date(ts).toISOString().slice(0, 10);
    dayMap[key] = (dayMap[key] || 0) + 1;
  });

  const maxCount = Math.max(1, ...Object.values(dayMap));
  const now = new Date(); now.setHours(0, 0, 0, 0);

  function colorFor(count) {
    if (!count) return _V8_HEAT_COLORS[0];
    const idx = Math.ceil(count / maxCount * (_V8_HEAT_COLORS.length - 1));
    return _V8_HEAT_COLORS[Math.min(idx, _V8_HEAT_COLORS.length - 1)];
  }

  let cols = "";
  for (let w = 0; w < _V8_HEAT_WEEKS; w++) {
    let cells = "";
    for (let d = 0; d < 7; d++) {
      const daysAgo = (_V8_HEAT_WEEKS - 1 - w) * 7 + (6 - d);
      const date = new Date(now.getTime() - daysAgo * 86400000);
      const key   = date.toISOString().slice(0, 10);
      const count = dayMap[key] || 0;
      cells += `<div class="v8-heat-cell" style="background:${colorFor(count)}" title="${key}: ${count}"></div>`;
    }
    cols += `<div class="v8-heat-col">${cells}</div>`;
  }

  const legendDots = _V8_HEAT_COLORS.map(c =>
    `<span style="width:12px;height:12px;border-radius:2px;background:${c};display:inline-block"></span>`
  ).join("");

  el.style.display = "";
  el.innerHTML = `
    <h2 style="font-size:13px;margin:0 0 4px;color:var(--muted);letter-spacing:.08em;text-transform:uppercase">Activity</h2>
    <div style="font-size:11px;color:var(--muted);margin-bottom:8px">Last ${_V8_HEAT_WEEKS} weeks · each square = 1 day</div>
    <div class="v8-heat-wrap">${cols}</div>
    <div class="v8-heat-legend">Less ${legendDots} More</div>`;
}
```

#### H4c — Call site

Inside `renderTutorTab`, AFTER the `_buildHeroCard()` call, add:
```javascript
_buildHeatmap();
```

---

### H5 — Mission checklist

**Goal**: Replace the mission card list in `v7TutorHorizons` with a compact tap-to-check list.

Insert the following two functions IMMEDIATELY AFTER `_buildHeatmap`:

```javascript
function _buildMissionChecklist() {
  const el = document.getElementById("v7TutorHorizons");
  if (!el) return;
  const missions = state.weeklyMissions?.missions;
  if (!missions?.length) {
    el.innerHTML = `<div style="font-size:13px;color:var(--muted);font-style:italic;padding:4px 0">No missions yet — tap ↺ Refresh to generate.</div>`;
    return;
  }

  const _domClr = {
    gross:"#3B82F6",fine:"#F59E0B",sensory:"#F97316",
    cognitive:"#6366F1",vocab:"#EC4899",social:"#6B7280"
  };
  const _domBg = {
    gross:"#DBEAFE",fine:"#FEF3C7",sensory:"#FFE4D6",
    cognitive:"#E0E7FF",vocab:"#FCE7F3",social:"#E5E7EB"
  };
  if (!window._v8McChecked) window._v8McChecked = new Set();

  const allSkills = [...SKILLS, ...(Array.isArray(state.skillsCustom)?state.skillsCustom:[])].filter(Boolean);

  const items = missions.map((m, i) => {
    const skillId  = (m.target_skill_ids || [])[0] || "";
    const skill    = allSkills.find(s => s && s.id === skillId);
    const domain   = skill?.domain || m.domain || "cognitive";
    const dotColor = _domClr[domain] || "#6B7280";
    const dotBg    = _domBg[domain]  || "#E5E7EB";
    const title    = escapeHtml(m.activity_title || m.title || skillId);
    const subParts = [
      domain.charAt(0).toUpperCase() + domain.slice(1),
      m.expected_duration_min ? `${m.expected_duration_min} min` : ""
    ].filter(Boolean);
    const sub      = subParts.map(escapeHtml).join(" · ");
    const checked  = window._v8McChecked.has(i);
    return `<div class="v8-mc-item">
      <div class="v8-mc-dot" style="background:${dotBg};color:${dotColor}">${skill?.emoji ? escapeHtml(skill.emoji) : "🎯"}</div>
      <div class="v8-mc-txt">
        <div class="v8-mc-name">${title}</div>
        ${sub ? `<div class="v8-mc-sub">${sub}</div>` : ""}
      </div>
      <div class="v8-mc-check${checked?" v8-chk-done":""}" id="v8mc_${i}"
        onclick="_v8McTap(${i},'${escapeHtml(skillId)}')">${checked?"✓":""}</div>
    </div>`;
  }).join("");

  const doneCount = window._v8McChecked.size;
  el.innerHTML = `<div>${items}</div>
    <div style="font-size:11px;color:var(--muted);text-align:center;margin-top:8px;padding-top:8px;border-top:1px solid var(--line)">${doneCount} / ${missions.length} done today</div>`;
}

function _v8McTap(idx, skillId) {
  if (!window._v8McChecked) window._v8McChecked = new Set();
  if (window._v8McChecked.has(idx)) {
    window._v8McChecked.delete(idx);
  } else {
    window._v8McChecked.add(idx);
    if (skillId && typeof addObservation === "function") {
      addObservation({ skill_id: skillId, status: "practicing", source: "mission_checklist" });
    }
  }
  _buildMissionChecklist();
}
```

FIND the code inside `renderTutorTab` (or a dedicated missions render function) that sets
`v7TutorHorizons.innerHTML` with the mission card HTML. Replace that block with a call to
`_buildMissionChecklist()`.

NOTE: The ↺ Refresh button (`data-v8-missions-refresh`) should remain wired to `generateMissionsViaHaiku()`
as-is — only the render function changes. After missions regenerate, the refresh handler should
call `_buildMissionChecklist()` to re-render the new list.

---

### Workstream H verification checklist (items 31–40)

31. `.v7-tutor-hero` has `padding:0;overflow:hidden` in HTML.
32. `_buildHeroCard()` exists; tutor view shows dark navy top with emoji, name, level badge.
33. Domain bars animate from 0% to actual percentages after first paint (check in browser).
34. XP fill animates; level badge shows correct name (Explorer / Adventurer / etc.).
35. `_buildDomainRadar()` exists; snapshot card shows SVG spider chart; all 6 axis labels visible.
36. Domain % values are non-zero when skills are mastered; data polygon is not a flat dot.
37. `_buildKanban()` exists; priorities card shows 3 columns with correct skill items.
38. Kanban items call `_openSkillPopup` on click (no JS error if popup doesn't exist yet).
39. `v8TutorHeatmap` card renders and is visible; squares coloured by density; no JS errors.
40. Mission checklist tap toggles ✓ / uncheck; done-count updates; `addObservation` called with `"practicing"`.

Report final byte count and any deviations.
