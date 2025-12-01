# Auto Registration Session — Step 2 Feature Description

## Problem
Newly registered users must manually log in and verify before receiving a usable session, even when their invite comes from a trusted source. This adds friction and delays access to the product experience.

## User Stories
- As a new user invited by a trusted admin, I want to start using the site immediately after registration so I can post or browse without extra steps.
- As an admin, I want to define which invite tokens auto-approve so I maintain control over who bypasses manual verification.
- As a system maintainer, I want logging/auditing of auto-approved registrations so we can review access decisions later.

## Core Requirements
- Extend invite tokens so that those issued by approved admins default to `auto_approve=true` (retain a flag for future tightening when necessary).
- After registration, when the invite indicates auto-approval (default case), mark the new user as fully verified and create a full session immediately; if auto-approve is explicitly disabled, fall back to the half-auth workflow.
- Record audit information (who auto-approved, which token was used, timestamp).
- Update registration and pending dashboards so that auto-approved users are redirected directly to the fully authenticated experience.
- Provide documentation/guidance explaining how admins can issue auto-approve invites and the security implications.

## User Flow
1. Admin creates an invite (auto-approval enabled by default for admin-issued tokens).
2. New user registers with the invite token.
3. Registration logic detects the default auto-approve flag, fully approves the user, creates a full session, and redirects to the main dashboard.
4. Audit/log entries note the auto-approval event for review.
5. Unflagged invites continue to use the existing verification workflow, ensuring compatibility.

## Success Criteria
- Users who register with auto-approve invites land in the fully authenticated dashboard without manual login/verification.
- Users with non-auto-approve invites continue to see the pending dashboard unchanged.
- Audit logs or database records clearly capture auto-approval events.
- Documentation (README/code tour) describes how to create and manage auto-approve invites and the associated risks.
- Security review confirms no unintended bypasses (e.g., ensures only designated tokens trigger auto-approval).
