# User Privileges Profile — Step 1 Solution Assessment

**Problem statement**
- Signed-in users cannot easily confirm the active account or privileges, creating confusion and avoidable support requests.

**Option A – Dedicated profile page reached via header username link (preferred)**
- Pros: Reuses existing page paradigm; supports richer privilege descriptions; satisfies requirement to use username as navigation affordance; minimal intrusion on current layouts.
- Cons: Requires routing/auth updates and page template work; still demands separate settings surface if not already present.

**Option B – Inline account summary dropdown/modal anchored to header username**
- Pros: Fast to access without leaving context; lightweight implementation if privilege data is simple; keeps user in current workflow.
- Cons: Crowds header space; hard to present detailed privilege explanations; modal logic adds UI complexity across viewports.

**Option C – Global banner or sidebar module showing account + privileges**
- Pros: Always visible once signed in; minimal navigation changes; easy to feature additional calls-to-action.
- Cons: Consumes persistent UI real estate; risks habituation/ignoring; less aligned with privacy expectations if displayed in shared contexts.

**Recommendation**
- Build Option A: a dedicated profile page linked directly from the username in the header. It balances clarity, extensibility for privilege messaging, and respects the user's request to avoid a separate "Profile" link while keeping navigation intuitive.
