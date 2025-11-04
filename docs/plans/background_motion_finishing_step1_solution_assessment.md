# Background & Motion Finishing Pass — Step 1 Solution Assessment

**Problem statement**
- Gradients and bubble motion vary across pages, leading to visual fatigue mid-scroll and inconsistent atmosphere between hero, feed, and detail views.

**Option A – Harmonize existing gradients/motion tokens (recommended)**
- Pros: Adjusts color stops, opacity, and animation cadence globally; keeps design system lightweight while achieving cohesion.
- Cons: Requires careful cross-page testing to avoid regressions (banding, contrast issues).

**Option B – Replace background with static artwork**
- Pros: Eliminates motion concerns entirely; predictable visuals.
- Cons: Loses brand personality; increases asset weight; less adaptable to themes.

**Option C – Introduce per-page background themes**
- Pros: Tailors ambiance to context (feed vs detail).
- Cons: High design/implementation overhead; risks fragmenting brand if not tightly managed.

**Recommendation**
- Pursue Option A: iterate on existing gradient/motion variables for a unified, performant background once layout changes are in place.
