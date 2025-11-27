## Problem Statement
Running hubs in "strict" mode requires pre-populating every peer (name, token, public key). Operators want an optional loose mode where peers can self-register during push/pull to simplify onboarding.

## Options
- **A. Single loose mode flag covering both push & pull**
  - Pros: Simple toggle, minimal config overhead.
  - Cons: No granularity—some operators might allow auto-add for uploads but still want to restrict downloads (or vice versa).
- **B. Separate auto-registration flags: `allow_auto_register_push`, `allow_auto_register_pull`**
  - Pros: Fine-grained control (e.g., allow peers to upload bundles without being able to pull until approved). Clear auditing per pathway.
  - Cons: Slightly more configuration; need to handle partial states carefully.
- **C. External “registration” endpoint** (peers request approval, human approves, hub updates config)
  - Pros: Strong gatekeeping; keeps auto-creation out of the hot path.
  - Cons: Reintroduces manual steps, negating the loose-mode goal.

## Recommendation
Adopt **Option B**. Two explicit flags let operators decide if uploads, downloads, or both should auto-register. This stays close to the current behavior (strict by default) while giving fine-grained flexibility, and avoids building a separate approval workflow.
