# Phase 6: Launch & Growth

**Scope:** Onboarding flows, progressive disclosure, analytics instrumentation, retention mechanics, and feature adoption funnels. This phase answers the question: *once the app is built, how do you get users to their first moment of value, keep them coming back, and systematically learn what to build next?*

---

## Planned Sections (V2)

- `onboarding.md` — The paradox of the active user (Carroll & Rosson): users skip tutorials yet abandon without guidance; first-run experience patterns (checklists, product tours, empty states as onboarding, contextual tooltips); activation metrics and time-to-first-value; segmented onboarding by user role/intent
- `progressive-disclosure.md` — Nielsen's two-tier disclosure principle; Tidwell's pattern language for staged complexity; feature flags as progressive disclosure infrastructure; the "two levels, not three" heuristic; affordances for discoverability of hidden features
- `analytics-instrumentation.md` — Event taxonomy design; North Star metric selection and growth accounting; the instrumentation layer as a product decision (what you measure shapes what you build); avoiding vanity metrics; cohort analysis and retention curves
- `retention-mechanics.md` — Amplitude's benchmark data (98% of users inactive by week two); habit formation through variable reward and investment loops; re-engagement triggers (email, push, in-app); the retention-vs-manipulation boundary; Net Revenue Retention as the SaaS north star
- `feature-adoption.md` — The feature adoption funnel (awareness > trial > adoption > habit); experiment design for feature launches (A/B testing, holdout groups); the peeking problem and statistical validity; when to sunset features; PLG mechanics (freemium, reverse trial, viral loops)

---

## Key Principles

1. **Onboarding is not a tutorial — it is the path to first value.** Carroll and Rosson's paradox of the active user (1987) remains the foundational behavioral constraint: users skip documentation, tutorials, and setup wizards in favor of immediate task engagement, even when reading would save them time. Successful onboarding operates *within* the stream of task behavior, not before it. Empty states that guide action, contextual tooltips at the moment of need, and checklists that create momentum outperform front-loaded product tours.

2. **Progressive disclosure is how complex apps stay simple.** Nielsen's principle: display only the most important options initially; reveal specialized options upon user request. The mechanism resolves the competition between power (comprehensive features) and simplicity (manageable choices). The empirical guidance is clear: two levels of disclosure work; three or more levels create navigational confusion. Feature flags serve as the engineering infrastructure for progressive disclosure at the feature level, enabling staged rollout by cohort, plan tier, or usage milestone.

3. **Measure the job, not the feature.** Analytics instrumentation should trace the user's progress through their job-to-be-done, not merely count clicks on features. A North Star metric should capture the rate at which users complete the core job; supporting metrics should decompose that into the sub-jobs and friction points along the way. The event taxonomy is a product decision that shapes organizational attention — what you instrument is what you optimize.

4. **Retention is the only growth metric that compounds.** Amplitude's 2025 Product Benchmark Report: for half of all products, more than 98% of new users are inactive by week two. Acquisition without retention is a leaking bucket. The retention engineering literature identifies four intervention surfaces — product (habit loops, variable reward), behavioral (nudges, defaults), communication (lifecycle emails, push), and lifecycle (reactivation, resurrection). The ethical boundary between retention mechanics and dark patterns is a genuine design decision, not a compliance afterthought.

5. **Every feature launch is an experiment.** Product-led growth requires treating each feature release as a hypothesis with a measurable outcome. A/B testing provides the causal identification framework, but only if the experiment is properly powered, the peeking problem is addressed (sequential testing, always-valid p-values), and the distinction between short-run novelty effects and durable behavioral change is respected. Holdout groups are essential for measuring long-run feature impact. The best organizations run hundreds to thousands of concurrent experiments.

---

## Cross-References to Research

| Paper | Why it matters for this phase |
|-------|-------------------------------|

---

## Key Questions This Section Will Answer

- How do you design onboarding that accommodates Carroll and Rosson's paradox — users who skip tutorials but abandon without guidance? What is the concrete pattern for embedding guidance within the task stream rather than front-loading it?
- What is the right activation metric for your app? How do you identify the "aha moment" empirically (correlation analysis between early actions and long-term retention) rather than assuming you know what it is?
- How do you design a progressive disclosure architecture that scales from a simple first experience to a power-user interface? What are the concrete UI patterns (expand/collapse, drill-down, settings tiers, feature flags by plan level)?
- What does a well-designed event taxonomy look like? How many events is too few (you cannot see what is happening) vs. too many (noise drowns signal)?
- How do you distinguish genuine retention improvement from dark patterns? Where is the ethical boundary between a habit loop that serves the user's job and one that manufactures engagement for its own sake?

---

# References: Launch and Growth

## Primary Sources

Read these for deep theoretical grounding on this phase's topics.

| Topic | Paper | Path |
|-------|-------|------|

## Supplementary Sources

Consult these for specific questions or adjacent concerns.

| Topic | Paper | Path |
|-------|-------|------|
