# Corus Neara Demo Roadmap — End-of-Week Product Plan

## Purpose

Prepare a demo-ready Corus proof-of-work for Jack Curtis and Cody Yamikoff at Neara by the end of this week.

The demo should show Corus as a context layer for customer-facing implementation teams. It should not present Corus as a replacement for Neara, RVO, Jira, CRM, GitHub, dashboards, or internal customer-success tooling.

The demo should prove one core product idea:

> One bounded context can generate multiple role-specific surfaces without losing its source boundary, trust state, ownership, or audit trail.

The updated surface model for this demo is:

```text
Owner    → Coordinate
Executor → Implement
Consumer → Value

```

So the demo should focus on three primary surfaces:

```text
Coordinate surface
Implement surface
Value surface

```

The previous intelligence surface should be removed as a primary demo surface. Its function should live underneath the three surfaces as a shared claims/evidence layer.

---

# 1. Product thesis for the demo

## External framing

Corus helps customer-facing implementation teams preserve, govern, and render the context required to turn technical intelligence into coordinated customer value.

## Demo framing

Neara/RVO-style intelligence can identify important technical signals, but customer-facing teams still need to coordinate:

```text
What matters?
How do we accomplish it?
Who owns what?
What can we safely claim?
What evidence supports it?
What remains missing, rejected, or unresolved?

```

Corus does not generate the original grid intelligence. Corus preserves the context around that intelligence so teams can act on it responsibly.

## Product guardrail

The demo must make this clear:

```text
Raw sources are not truth.
LLM outputs are not truth.
Candidate artifacts are not truth.
Admission is the trust boundary.
Derivation is deterministic.
Audit preserves why something counted.

```

---

# 2. Demo audience

## Jack Curtis

Jack should see Corus as a strategic context-infrastructure idea.

The demo should answer:

```text
How does technical intelligence become institutional customer value?
How can leadership see whether context is turning into coordinated outcomes?
How can customer-facing teams preserve context instead of recreating it across accounts?

```

## Cody Yamikoff

Cody should see Corus as a practical tool for a real customer-success / implementation workflow.

The demo should answer:

```text
Does this match how CVAs, FDEs, Directors, and technical teams lose context?
Are these the right role views?
Would this reduce repeated reconstruction work?
Which artifacts are most painful to recreate today?

```

---

# 3. Core demo mechanic: workflow replay

The missing demo mechanic is a simulation.

The demo should not only show static surfaces. It should replay a realistic customer-facing workflow and show Corus responding as context changes.

## Simulation title

```text
Workflow replay: from intelligence output to coordinated customer action

```

## Simulation claim

A realistic Neara account team receives RVO-style risk intelligence and must turn it into customer-specific value, implementation next steps, and coordinated ownership.

Corus responds by:

```text
1. admitting or rejecting source-backed claims
2. updating artifact status
3. deriving what counts inside the boundary
4. rendering updated Coordinate / Implement / Value surfaces
5. preserving an audit trail

```

## Suggested workflow steps


| Step | Workflow event                               | Corus response                                                       | Surface impact                                     |
| ---- | -------------------------------------------- | -------------------------------------------------------------------- | -------------------------------------------------- |
| 1    | Director opens RVO account context           | Creates boundary: Director + account team + RVO subject              | Coordinate shows expected artifacts                |
| 2    | Neara/RVO public source is added             | Source is inventoried and available for interpretation               | Claims appear as candidate                         |
| 3    | CVA role-context source is admitted          | Value artifact is expected                                           | Value shows missing value evidence                 |
| 4    | FDE role-context source is admitted          | Implementation artifact is expected                                  | Implement shows missing implementation context     |
| 5    | Public SCE wildfire-planning source is added | Candidate evidence is proposed                                       | Value and Implement receive source-bounded context |
| 6    | Unsupported cost claim appears               | Claim is rejected or marked missing evidence                         | Value shows “do not claim cost impact yet”         |
| 7    | Implementation detail is admitted            | Artifact status moves from missing to present                        | Implement updates readiness                        |
| 8    | Director reviews account state               | Boundary derives included, missing, rejected, and unresolved context | Coordinate shows readiness/blockers                |


## Simulation UI

Use a split-screen or stepped replay:

```text
Left:
Workflow timeline

Right:
Three live surfaces
- Coordinate
- Implement
- Value

Bottom drawer:
Claims, evidence, source boundary, audit trace

```

The key demo moment:

> Corus is not showing a dashboard. It is replaying how context becomes coordinated action.

---

# 4. Primary surfaces for this demo

## 1. Coordinate surface

Ledger role:

```text
Owner

```

Primary audience:

```text
Director / account lead / implementation leader

```

Core question:

```text
Are we aligned, ready, and accountable?

```

This surface should show:

```text
who owns what
which artifacts are expected
which artifacts are present
which artifacts are missing
which claims are rejected
which handoffs are unresolved
what the next coordination action is

```

Minimum card structure:

```text
Coordinate surface
Owner · Director

Status:
Unresolved / Ready / Blocked

Sees:
The account context has value and implementation artifacts in scope, but one cost claim is rejected and one implementation handoff remains missing.

Supported:
Public source context admitted.

Missing:
Customer-approved ROI assumption and implementation owner confirmation.

Next:
Assign owner for implementation handoff and request approved cost model.

```

---

## 2. Implement surface

Ledger role:

```text
Executor

```

Primary audience:

```text
FDE / technical implementation team

```

Core question:

```text
How do we accomplish it?

```

This surface should show:

```text
what systems may be touched
what implementation detail changed
what customer system context is missing
what validation is required
what is blocked
what next action is defensible

```

Minimum card structure:

```text
Implement surface
Executor · FDE

Status:
Needs validation

Sees:
RVO-style risk intelligence may inform implementation planning, but customer system mappings and operational workflow ownership are not yet admitted.

Supported:
Public Neara/SCE context.

Missing:
Customer integration path, system owner, and implementation acceptance criteria.

Next:
Confirm customer system mapping before generating implementation work items.

```

---

## 3. Value surface

Ledger role:

```text
Consumer

```

Primary audience:

```text
CVA / customer stakeholder / commercial team

```

Core question:

```text
What matters, and why does it matter to the customer?

```

This surface should show:

```text
customer significance
stakeholder relevance
supported value narrative
unsupported or rejected financial assumptions
what can be safely said
what should not be claimed yet

```

Minimum card structure:

```text
Value surface
Consumer · CVA / customer stakeholder

Status:
Value narrative partially supported

Sees:
RVO-style intelligence can support customer conversations about wildfire planning, inspection prioritization, and operational decision-making.

Supported:
Public Neara/SCE context.

Rejected:
Specific dollar impact claim without customer-approved assumptions.

Next:
Use the value narrative, but avoid financial claims until the customer-approved cost model is admitted.

```

---

# 5. Claims and evidence layer

The intelligence surface should not be a primary surface for this demo.

Instead, all three surfaces should include a shared claims/evidence layer.

## Claim object concept

A claim is a specific statement Corus is making, refusing to make, or marking as unresolved.

A claim can be:

```text
supported
candidate
missing_evidence
rejected
synthetic_bounded

```

## Example claims

```text
Supported:
RVO-style intelligence can support inspection prioritization discussions.

Candidate:
This context may influence vegetation management scope.

Missing evidence:
A customer-approved cost model is required before making financial impact claims.

Rejected:
The demo cannot claim a specific dollar impact from public sources alone.

Synthetic bounded:
The old watch-point fixture is retained only to exercise mechanics, not to represent official Neara/SCE output.

```

## Where claims appear

Each surface should show:

```text
Supported claims
Missing claims
Rejected claims
Next defensible action
Source / trace link

```

This keeps the trust layer visible without making the demo too complex.

---

# 6. Page structure

## Section 1 — Hero

Headline:

```text
When intelligence exists, customers still need significance.

```

Subhead:

```text
Corus turns source-backed role-context into coordinated surfaces for customer-facing implementation teams.

```

Support line:

```text
One bounded context. Three role surfaces. Claims and evidence preserved underneath.

```

Primary CTA:

```text
Replay the workflow

```

Secondary CTA:

```text
See how Corus works

```

---

## Section 2 — Context summary strip

Show 4–5 concise proof points:

```text
1 bounded RVO context
3 role surfaces
source-grounded claims
rejected assumptions visible
audit proof available

```

Avoid centering the old 72-watch-point fixture.

---

## Section 3 — Workflow replay

This should be the main demo interaction.

Show:

```text
workflow timeline
surface updates
claim status changes
source/evidence drawer
audit trace link

```

This section should answer:

> What happens when context changes?

---

## Section 4 — One context, three surfaces

Simple mental model:

```text
Sources + admitted artifacts + boundary
→ derived context
→ Coordinate / Implement / Value

```

Copy:

```text
Corus does not create three separate reports. It derives one bounded context and renders it through three role questions: coordinate, implement, and value.

```

---

## Section 5 — Surface cards

Show three primary cards:

```text
Coordinate
Implement
Value

```

Each card should include:

```text
role
core question
what this surface sees
supported claim
missing/rejected claim
next defensible action
source/trace status

```

---

## Section 6 — Implementation detail cards

Use concrete detail cards so the demo does not feel abstract.

Recommended cards:

```text
Asset inspection prioritization
Vegetation management scope
System hardening schedule
Unsupported cost amount

```

Each card should show:

```text
what changed
who needs this
source status
still unknown
next validation step
claim status

```

---

## Section 7 — Source and trust boundary

Show source cards.

Each source card should include:

```text
source title
source type
what it supports
trust status
limit / caveat
open source link

```

Trust states:

```text
public-source grounded
admitted
candidate
missing
rejected
synthetic fixture bounded
audit proof available

```

---

## Section 8 — How Corus works

Do not lead with architecture. Place this after the main product story.

Simple stepper:

```text
Sources enter
→ Interpretation proposes candidates
→ Admission declares trusted objects
→ Boundary selects what counts
→ Context is derived
→ Surfaces render
→ Audit explains

```

Important copy:

```text
Interpretation may propose.
Admission declares.
Derivation computes.
Audit proves.

```

---

## Section 9 — Technical proof

Collapsed by default.

Show:

```text
included objects
excluded objects
claim statuses
rejected assumptions
proof hash
trace details
raw JSON if available

```

The demo should make proof available without making proof the first impression.

---

## Section 10 — Pilot ask

End with a grounded ask:

```text
We are looking for feedback on whether this reflects a real context burden inside Neara’s customer-facing implementation workflow.

```

Questions:

```text
Are Coordinate / Implement / Value the right role surfaces?
Which artifacts are most painful to recreate?
Which handoffs lose the most context?
Which claims require the most evidence before customer use?
What source material would make this useful in a real account?

```

---

# 7. Agent workstreams for the week

## Product / strategy agent

Owns:

```text
demo narrative
surface definitions
pilot framing
Jack/Cody positioning
scope control

```

Deliverables:

```text
one-page demo brief
surface vocabulary
pilot ask
demo script
expected questions and grounded answers

```

## Systems architect agent

Owns:

```text
object model consistency
boundary logic
declared vs derived clarity
source/artifact/contract/moment definitions

```

Deliverables:

```text
architecture note
boundary selection explanation
object glossary
deferred roadmap list

```

## Systems engineer agent

Owns:

```text
kernel correctness
fixture integrity
tests
deterministic derive
audit/explain output

```

Deliverables:

```text
passing tests
golden output
workflow replay fixture
audit proof
demo-safe command sequence

```

## Agentic engineer agent

Owns:

```text
source inventory
typed preprocessing
candidate interpretation
admission workflow
workflow simulation sequence

```

Deliverables:

```text
source packets
candidate object generation
admission report
simulation moments
claim/evidence status model

```

## UI/UX agent

Owns:

```text
Neara-adjacent visual language
page hierarchy
workflow replay interaction
surface cards
source/trust UI
professional demo polish

```

Deliverables:

```text
page structure
copy hierarchy
surface card design
workflow replay design
source/trust drawer
screenshot-ready demo

```

---

# 8. Week schedule

## Day 1 — Freeze scope and vocabulary

Decisions:

```text
Three primary surfaces only:
Coordinate
Implement
Value

Claims/evidence layer underneath all three.

Workflow replay is the primary demo mechanic.

Intelligence is not a primary surface for v0.

```

Deliverables:

```text
final demo narrative
final surface vocabulary
workflow replay script
UI section order
acceptance criteria

```

---

## Day 2 — Data and simulation model

Tasks:

```text
define simulation events
create or update workflow replay fixture
map events to moments
map moments to artifact/claim status changes
define Coordinate / Implement / Value surface payloads
define claim statuses

```

Deliverables:

```text
workflow_simulation fixture
surface payload JSON
claim/evidence model
updated demo data

```

---

## Day 3 — Kernel and agent workflow hardening

Tasks:

```text
ensure source → candidate → admission → derive works for demo
ensure boundary selects contracts by team + subject
ensure missing/rejected artifacts remain useful
ensure audit/explain supports included/excluded logic
ensure tests cover replay steps

```

Deliverables:

```text
passing test suite
golden replay output
audit proof
demo command path

```

---

## Day 4 — UI/UX build and polish

Tasks:

```text
build professional Neara-adjacent page
add workflow replay interaction
add three surface cards
add implementation detail cards
add claims/evidence drawer
add source/trust boundary
collapse raw proof
remove 72-watch-point emphasis

```

Deliverables:

```text
demo page
screenshots
replay interaction
surface cards
source cards
proof drawer

```

---

## Day 5 — Demo package

Tasks:

```text
run full demo
verify source honesty
verify no overclaiming
write Jack walkthrough
write Cody walkthrough
write outreach messages
record fallback video or screenshots

```

Deliverables:

```text
live demo or local recording
demo script
one-page brief
Jack message
Cody message
fallback screenshots
known limitations
pilot ask

```

---

# 9. End-of-week acceptance criteria

## Product acceptance

The demo clearly communicates:

```text
Corus is a context layer, not an RVO replacement.
The wedge is customer-facing implementation teams.
The mental model is one bounded context → multiple role surfaces.
The primary surfaces are Coordinate, Implement, and Value.
Claims/evidence sit underneath the surfaces.
Workflow replay shows context changing over time.

```

## Trust acceptance

The demo clearly distinguishes:

```text
public-source grounded
candidate
admitted
missing
rejected
synthetic fixture bounded
audit proof available

```

## Technical acceptance

The system can show:

```text
source inventory
candidate interpretation
admission boundary
boundary-derived context
surface rendering
claim status changes
audit/explain trace

```

## UI acceptance

The page feels:

```text
professional
Neara-adjacent
executive-readable
technically credible
not overloaded with raw JSON
not overly abstract
not generic dashboard-like

```

## Narrative acceptance

Jack should understand:

```text
This is a strategic context infrastructure idea.

```

Cody should understand:

```text
This reflects a practical CVA/FDE/customer implementation context burden.

```

---

# 10. Explicit non-goals for this week

Do not build:

```text
generic enterprise surface engine
full custom surface DSL
full LLM interpretation product
broad connector platform
permissions UI
on-prem/private runtime
complete claim object architecture
full Data Scientist intelligence surface
cross-department demos
surface marketplace

```

Do not claim:

```text
official Neara validation
official SCE validation
actual cost exposure
replacement for RVO
replacement for Jira/CRM/GitHub
autonomous decision-making
complete enterprise Context OS

```

---

# 11. Post-demo roadmap

## Phase 1 — Validate the pain

Questions:

```text
Do Neara teams recognize this context burden?
Are Coordinate / Implement / Value the right surfaces?
Which role loses the most context?
Which handoff is most painful?
Which artifacts are most important?
Which claims require strongest evidence?

```

## Phase 2 — Productize source-to-candidate workflow

Build:

```text
source inventory
typed preprocessors
source packets
candidate interpretation
evidence traces
admission reports

```

First typed preprocessor:

```text
job descriptions

```

Reason:

```text
Job descriptions reveal repeated role-context burden.

```

## Phase 3 — Productize claims/evidence

Build:

```text
claim object
claim status
source support
rejected claim handling
claim-to-surface rendering
audit proof

```

## Phase 4 — Productize workflow replay

Build:

```text
moment timeline
context replay
surface diffs
before/after context state
audit-linked replay

```

## Phase 5 — Pilot

Pilot scope:

```text
one customer-facing workflow
one account or account archetype
one repeated role-context burden
one source-grounded surface set
one evidence/rejected-assumption trail

```

Pilot output:

```text
a reusable account-context surface that shows what matters, how to accomplish it, who owns it, what can be safely claimed, and what remains unresolved

```

---

# 12. Keeper statements

```text
Corus starts with customer-facing teams because that is where the context burden is visible, expensive, and repeated.

```

```text
A CMS separates content from pages. Corus separates context from surfaces.

```

```text
Coordinate, Implement, and Value are the primary demo surfaces. Claims and evidence are the trust layer beneath them.

```

```text
Corus is not showing a dashboard. It is replaying how context becomes coordinated action.

```

```text
Interpretation may propose. Admission declares. Derivation computes. Audit proves.

```

```text
The demo should prove one thing: customer-facing teams can preserve and replay the context behind why technical intelligence matters.

```

