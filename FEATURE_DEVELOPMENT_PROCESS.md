# Feature Development Process

## Overview
Four-step process for feature development with optional solution assessment.

## The Process

### Step 1: Solution Assessment (Optional)
**When Needed**: Multiple viable approaches, complex trade-offs, or unclear direction

**Format**: Ultra-concise comparison document (≤1 page) in `docs/plans/`
**Filename**: `{feature_name}_solution_assessment.md`
- Problem statement (1 sentence)
- 2-4 solution options with key pros/cons (bullet points only)
- Clear recommendation with brief reasoning

**Avoid**: Long explanations, implementation details, >4 options, verbose prose

---

### Step 2: Feature Description
**Content**: Problem statement, 3-5 user stories, core requirements, user flow, success criteria

**Format**: Concise document (≤1 page) in `docs/plans/`
**Filename**: `{feature_name}_feature_description.md`
- Problem (1-2 sentences)
- User stories (bullet points: "As [role], I want [goal] so that [benefit]")
- Core requirements (3-5 bullet points)
- Simple user flow (numbered steps)
- Success criteria (measurable outcomes)

**Avoid**: Implementation details, code, database schema, UI mockups, verbose descriptions

---

### Step 3: Development Plan
**Content**: Atomic stages (~≤1 hour or ~≤50 lines of change each), dependencies, verification approach (manual is fine), risk assessment

**Format**: Numbered stages in `docs/plans/` (≤1 page)
**Filename**: `{feature_name}_development_plan.md`
- Each stage: goal, dependencies, changes, verification (manual smoke allowed), risks (bullet points)
- Break work into as many small stages as needed; flag any stage that still feels too large so it can be split before implementation.
- Database changes (conceptual, no SQL)
- Function signatures (no implementation)

**Avoid**: Full code, HTML templates, detailed SQL, verbose explanations

---

### Step 4: Implementation
**Process**: Create feature branch, implement stages in order, and favor the simplest viable implementation before iterating on enhancements or automation.

**Critical Requirements**:
- **MUST create feature branch first** (e.g., `feature/request-feed-enhancements`)
- Commit approved planning documents (Steps 1-3) to the feature branch before beginning implementation work.
- Complete stages atomically (<2 hours each)
- Manual smoke verification is sufficient for each stage; do not write automated tests.
- Update the Step 4 implementation summary document after every stage and commit those updates as you go.
- Conclude Step 4 by finalizing the implementation summary document.

**Completion Criteria**:
- All stages implemented and manually verified
- Feature accessible through normal UI (not just direct URLs)
- System dependencies resolved (roles, migrations, etc.)
- Documentation updated

## File Naming Convention
Each step MUST be a separate file in `docs/plans/`:
- **Step 1**: `{feature_name}_step1_solution_assessment.md`
- **Step 2**: `{feature_name}_step2_feature_description.md`
- **Step 3**: `{feature_name}_step3_development_plan.md`
- **Step 4**: `{feature_name}_step4_implementation_summary.md`

**Commit Discipline**: Keep each stage’s document uncommitted until the user reviews it. Commit only after approval and immediately before starting the next stage to keep IDE “dirty file” views meaningful.

## Key Rules

**AI Coding Assistant**:
- Suggest Step 1 for complex or multi-solution features
- Stay in the current step, don't draft or edit deliverables for later steps without approval
- After delivering each step, explicitly request confirmation using the wording “Approved Step N” and pause until the user replies with that exact phrase; do not create the next step’s document or code until that confirmation is received
- ALWAYS create separate files for each step only after the relevant approval
- ALWAYS create a feature branch before Step 4 implementation
- Flag scope creep and return to the appropriate planning step when needed
- If the projected work exceeds roughly a day of effort or would require more than about eight Step 3 stages, recommend breaking the effort into multiple features before proceeding.
- **AVOID database schema changes when possible** – prefer using existing models and fields

**User**:
- Review and approve explicitly at each step
- Flag issues early (easier to change)
- Resist adding features mid-implementation
- Prefer solutions that avoid database migrations; use existing schema where feasible

## Warning Signs
- **Step 1**: >1 page, >4 options, verbose explanations
- **Step 2**: >1 page, code examples, UI/database details
- **Step 3**: >1 page, >2 hour stages, complex dependencies
- **Step 4**: No feature branch, skipping stages, changing requirements mid-flight

## Workflows

**Simple**: Step 2 → Step 3 → Step 4 (feature branch → implement stages → test/commit → complete)

**Complex**: Step 1 (solution assessment) → Step 2 → Step 3 → Step 4
