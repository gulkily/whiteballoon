# Init DB Integrity — Step 1 Solution Assessment

**Problem statement**
- `./wb init-db` only creates missing tables and lacks a thorough schema verification step, so drifted or corrupted schemas might go unnoticed.

**Option A – SQLModel metadata inspection + repair (preferred)**
- Pros: Use SQLAlchemy inspector to compare actual tables/columns vs. SQLModel definitions; rebuild or migrate missing columns on the fly; keeps logic within existing tooling.
- Cons: Limited for complex migrations (e.g., type changes) unless paired with Alembic or custom scripts.

**Option B – Alembic-based migration check**
- Pros: Robust migration framework designed for schema diffs; can apply upgrade scripts automatically; well-established practice.
- Cons: Requires maintaining Alembic scripts; higher initial setup cost; we might not want migrations yet.

**Option C – External validation script**
- Pros: Separate audit tool can run deep checks (indexes, foreign keys) without modifying init workflow.
- Cons: Adds extra command; admins must remember to run it; fixing drift still requires additional code.

**Recommendation**
- Implement Option A: enhance `init-db` to inspect tables/columns, warn or repair when drift is detected (e.g., add missing columns, re-create tables), and optionally provide a report. Evaluate adding migration framework later if needs grow.
