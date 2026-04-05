# Causal Inference Strategies
*Decision Guide for Social Science Research*

## Overview

The central challenge of empirical social science is estimating causal effects from observational data. Unlike randomized experiments, observational studies cannot randomly assign treatment, so any observed correlation between treatment and outcome may be driven by confounders. Causal inference strategies are research designs that exploit specific features of the data or institutional setting to isolate causal effects despite non-random treatment assignment.

This guide covers the major identification strategies used in economics, political science, sociology, and public health. For each, it describes the core idea, the assumptions required, the tests available to support those assumptions, and the practical implementation steps.

## The Fundamental Problem of Causal Inference

The causal effect of treatment on unit i is: tau_i = Y_i(1) - Y_i(0), where Y_i(1) is the outcome with treatment and Y_i(0) is the outcome without. The fundamental problem: we only observe one of these potential outcomes for each unit. The other is the counterfactual.

The Average Treatment Effect (ATE) is E[Y(1) - Y(0)] over the population. Estimating it requires constructing a credible counterfactual for the treated group. Every identification strategy is, at its core, an argument for why a particular comparison group approximates the counterfactual.

### Selection Bias

The naive comparison E[Y|D=1] - E[Y|D=0] equals the ATE only if treatment is independent of potential outcomes. When it is not -- when units that select into treatment differ systematically from those that do not -- the comparison is contaminated by selection bias. All causal inference strategies are attempts to eliminate or bound this bias.

## Instrumental Variables (IV)

### Core Idea

Find a variable Z (the instrument) that affects the outcome Y only through its effect on the treatment D. The instrument creates exogenous variation in treatment, which can be used to estimate the causal effect.

### Requirements

1. **Relevance**: Z must be correlated with D. Testable: first-stage F-statistic should exceed 10 (Stock and Yogo, 2005); modern guidance recommends effective F > 23 for 5% worst-case bias (Lee et al., 2022).
2. **Exclusion restriction**: Z affects Y only through D. Not directly testable. Must be argued on theoretical/institutional grounds.
3. **Independence**: Z is as good as randomly assigned (uncorrelated with unobservable determinants of Y). Not directly testable.

### What IV Estimates

With heterogeneous treatment effects, 2SLS estimates the Local Average Treatment Effect (LATE) -- the effect for compliers (units whose treatment status changes with the instrument). LATE may differ from ATE, and this should be acknowledged in the paper.

### Implementation Steps

1. Argue instrument validity: describe the institutional setting that generates the instrument and explain why exclusion and independence hold.
2. Estimate first stage: regress D on Z (and controls). Report first-stage F-statistic.
3. Estimate second stage: 2SLS regression of Y on instrumented-D.
4. Report both OLS and IV estimates. If IV is much larger than OLS, discuss why (LATE vs. ATE, measurement error attenuation in OLS, or weak instrument bias).

### Weak Instruments

When the first-stage F-statistic is low, IV estimates are biased toward OLS and confidence intervals are unreliable. Remedies:
- Anderson-Rubin confidence sets (valid regardless of instrument strength)
- LIML estimator (less biased than 2SLS with weak instruments)
- Conditional likelihood ratio test (Moreira, 2003)

### Overidentification

With multiple instruments, use the Sargan/Hansen J-test. A rejection suggests at least one instrument violates the exclusion restriction. Note: failure to reject does not prove validity -- the test has low power.

### Common Instruments in Social Science

- **Draft lottery numbers** for military service (Angrist, 1990)
- **Distance to institution** for access/utilization (Card, 1993)
- **Rainfall** for economic shocks (Miguel, Satyanath, and Sergenti, 2004)
- **Shift-share/Bartik instruments** for local labor demand (Goldsmith-Pinkham et al., 2020)
- **Regulatory changes** that affect treatment but not outcomes directly

## Difference-in-Differences (DiD)

### Core Idea

Compare the change in outcomes over time between a treatment group (exposed to a policy/event) and a control group (not exposed). By differencing over time and across groups, DiD removes both time-invariant group differences and common time trends.

### The Parallel Trends Assumption

The key assumption: absent treatment, the treatment and control groups would have followed parallel outcome trajectories. This is the identifying assumption, and it is fundamentally untestable (it concerns a counterfactual). However, you can provide supporting evidence.

### Supporting Evidence for Parallel Trends

- **Pre-treatment trend plots**: Plot outcome means for treatment and control groups over time. Trends should be visually parallel before treatment.
- **Event study specification**: Estimate leads and lags relative to treatment timing. Pre-treatment coefficients should be individually and jointly insignificant (no anticipation effects and no differential pre-trends).
- **Placebo treatment timing**: Estimate the model using only pre-treatment data with a fake treatment date. Coefficients should be zero.

### Basic 2x2 DiD

Y_it = alpha + beta * Treat_i + gamma * Post_t + delta * (Treat_i * Post_t) + epsilon_it

- delta is the DiD estimate: the causal effect of treatment.
- Cluster standard errors at the group level (the level of treatment assignment).

### Staggered Adoption

When different units receive treatment at different times, the standard two-way fixed effects (TWFE) estimator can be biased if treatment effects are heterogeneous over time. Recent econometric work (Goodman-Bacon, 2021; Callaway and Sant'Anna, 2021; Sun and Abraham, 2021; de Chaisemartin and d'Haultfoeuille, 2020) shows that TWFE uses already-treated units as controls, which contaminates estimates.

**Modern estimators for staggered DiD**:
- **Callaway and Sant'Anna (2021)**: Group-time ATTs, aggregated across cohorts. Recommended default.
- **Sun and Abraham (2021)**: Interaction-weighted estimator.
- **Borusyak, Jaravel, and Spiess (2024)**: Imputation estimator.
- **de Chaisemartin and d'Haultfoeuille (2020)**: Heterogeneity-robust estimator.

Use at least one of these in addition to (or instead of) TWFE. Report both if TWFE is also shown.

### Common Pitfalls

- Insufficient pre-treatment periods to assess parallel trends (need at least 3-4 pre-periods).
- Treatment anticipation effects that violate the "no anticipation" assumption.
- Compositional changes in the sample over time.
- Contamination of the control group (spillover effects).

## Regression Discontinuity Design (RDD)

### Core Idea

When treatment is assigned based on whether a running variable (score) exceeds a threshold, units just above and just below the cutoff are quasi-randomly assigned. Comparing their outcomes estimates the causal effect at the cutoff.

### Sharp vs. Fuzzy RDD

- **Sharp**: Treatment is deterministic at the cutoff. All units above receive treatment; none below do.
- **Fuzzy**: The probability of treatment jumps at the cutoff but does not go from 0 to 1. Estimated via IV, using an indicator for being above the cutoff as an instrument for treatment.

### Implementation Steps

1. **Plot the data**: Show the outcome variable against the running variable with the cutoff marked. This is the most important diagnostic -- if there is no visible jump at the cutoff, the effect is likely small or nonexistent.
2. **Check for manipulation**: Run the McCrary (2008) density test or Cattaneo, Jansson, and Ma (2020) test to verify that units cannot precisely sort around the cutoff. A jump in the density of the running variable at the cutoff suggests manipulation.
3. **Choose bandwidth**: Use data-driven bandwidth selection (Calonico, Cattaneo, and Titiunik, 2014 -- the rdrobust package). Report results for the optimal bandwidth and for alternative bandwidths (half, double).
4. **Estimate**: Local linear regression (preferred over higher-order polynomials) within the bandwidth. Use bias-corrected robust confidence intervals.
5. **Placebo cutoffs**: Estimate the model at fake cutoff values where no treatment discontinuity exists. Significant effects at placebo cutoffs undermine the design.
6. **Covariate balance**: Test whether pre-treatment covariates are smooth through the cutoff. Discontinuities in covariates suggest confounding.

### Bandwidth Selection

Too narrow: imprecise estimates. Too wide: bias from observations far from the cutoff. The MSE-optimal bandwidth from Calonico, Cattaneo, and Titiunik (2014) balances this trade-off. Always show robustness to bandwidth choice.

### Limitations

- Identifies a local effect at the cutoff only. Extrapolation away from the cutoff requires additional assumptions.
- Requires a sufficient density of observations near the cutoff.
- Running variable must not be manipulable by the units being studied.

## Matching Methods

### Core Idea

Construct a comparison group that resembles the treatment group on observed characteristics. If treatment assignment depends only on observables (conditional independence assumption / selection on observables), matching eliminates selection bias.

### The Critical Assumption

**Conditional Independence Assumption (CIA)**: Y(0), Y(1) are independent of D conditional on X. This means there are no unobserved confounders. This is a strong assumption that cannot be tested. It is only credible when you have very rich observable data.

### Propensity Score Matching (PSM)

Estimate the probability of treatment given covariates (the propensity score), then match treated units to control units with similar propensity scores.

**Steps**:
1. Estimate propensity score (logit or probit model).
2. Check common support: trim observations with propensity scores outside the overlap region.
3. Match: nearest-neighbor, caliper, kernel, or radius matching.
4. Assess balance: compare covariate means between matched treatment and control groups. Standardized differences should be below 0.1.
5. Estimate ATT on the matched sample.
6. Report sensitivity analysis (Rosenbaum bounds) to assess how large unobserved confounding would need to be to overturn results.

### Coarsened Exact Matching (CEM)

Coarsen each covariate into bins, then exact-match within bins. Reduces model dependence compared to PSM. Particularly useful when you have a moderate number of discrete covariates.

### Entropy Balancing

Reweight control observations so that covariate moments (mean, variance, skewness) exactly match the treatment group. Achieves exact balance by construction. Less researcher discretion than PSM (no bandwidth/caliper choices). Recommended as a complement or alternative to PSM.

### When Matching Fails

Matching only addresses selection on observables. If you suspect unobserved confounders, matching is insufficient. Combine with:
- Sensitivity analysis (Rosenbaum bounds, E-values)
- Oster (2019) bounds for coefficient stability
- DiD on a matched sample (combines matching with a time dimension)

## Selection on Observables vs. Unobservables

This distinction determines your entire identification strategy:

**Selection on observables**: Treatment depends on variables you can measure and control for. Methods: OLS with controls, matching, entropy balancing. Credible when you have rich administrative data or survey data with detailed covariates.

**Selection on unobservables**: Treatment depends on variables you cannot measure (ability, motivation, preferences). Methods: IV, DiD, RDD, or bounds analysis. Requires a natural experiment, policy change, or institutional feature that generates exogenous variation.

If you are unsure, assume selection on unobservables and look for a natural experiment. Reviewers are more likely to accept a well-executed IV or DiD than a matching study without sensitivity analysis.

## Strategy Selection Decision Tree

1. **Is there a randomized experiment?**
   - Yes -> Simple comparison of means (intent-to-treat), or IV for compliance.
   - No -> Proceed to step 2.

2. **Is there a sharp or fuzzy threshold for treatment assignment?**
   - Yes -> RDD. Check for manipulation at the cutoff.
   - No -> Proceed to step 3.

3. **Is there a clear before/after treatment event with a plausible control group?**
   - Yes -> DiD. Check parallel trends.
   - No -> Proceed to step 4.

4. **Is there a credible instrument?**
   - Yes -> IV. Argue exclusion restriction, report first-stage F.
   - No -> Proceed to step 5.

5. **Do you have very rich observable data?**
   - Yes -> Matching/entropy balancing with sensitivity analysis. Be transparent about CIA.
   - No -> Proceed to step 6.

6. **No clean identification strategy?**
   - Report OLS with controls, be transparent about limitations, use sensitivity analysis (Oster bounds), and frame results as "associations" rather than "causal effects."
   - Consider bounds approaches (partial identification) that report a range of plausible causal effects.

## Reporting Causal Claims

### Language Matters

- With RCT, RDD, or strong IV: "The effect of X on Y is..."
- With DiD with strong parallel trends evidence: "We estimate that X caused..."
- With matching or OLS with controls: "X is associated with..." or "Our estimates suggest..." with discussion of remaining threats.
- Never: "X causes Y" without a credible identification strategy.

### What Every Causal Paper Must Include

1. Explicit statement of the identification strategy and its assumptions
2. Discussion of threats to the identifying assumptions
3. Tests of identifying assumptions (where possible)
4. At least one robustness check addressing the most likely violation
5. Honest discussion of what the design cannot rule out

## Synthetic Control Method

### Core Idea

Construct a weighted combination of untreated units that closely matches the treated unit's pre-treatment trajectory. The synthetic control serves as the counterfactual. Developed by Abadie, Diamond, and Hainmueller (2010).

### When to Use

Case studies with aggregate data: one treated unit (a country, state, or firm) affected by a policy, with multiple untreated donor units. Ideal when DiD is infeasible because only one treated unit exists.

### Implementation Steps

1. Select donor pool: units not affected by treatment and plausibly comparable.
2. Choose matching variables: pre-treatment outcomes and predictors of the outcome.
3. Construct synthetic control: optimize weights on donor units to minimize pre-treatment prediction error.
4. Assess pre-treatment fit: plot treated vs synthetic. Pre-RMSPE should be near zero.
5. Estimate treatment effect: difference between treated and synthetic post-treatment.
6. **Placebo tests** (essential): reassign treatment to each donor unit. Calculate post/pre RMSPE ratio for each. Rank the treated unit's ratio within the placebo distribution. If the treated unit's ratio is extreme (top 5-10%), the effect is statistically significant.
7. Filter out donors with poor pre-treatment fit (convention: pre-RMSPE > 2x treated unit's).
8. **Placebo timing**: apply treatment at earlier period; no effect should appear.
9. Document donor weights; flag if one donor dominates. Test sensitivity to dropping dominant donors.

### Limitations

- Requires good pre-treatment fit (garbage in, garbage out)
- No formal standard errors (inference via placebo distribution)
- External validity limited to the single treated unit

## Bounds Approaches (Partial Identification)

### When No Clean Identification Exists

Manski (2003) showed that when identification assumptions are too strong to be credible, you can still provide informative bounds on the causal effect. Instead of a point estimate with a strong assumption, report a range of estimates under weaker assumptions.

### Key Approaches

**Manski bounds**: With no assumptions beyond random sampling, treatment effects are bounded by the range of the outcome variable. Adding monotonicity or mean independence assumptions tightens the bounds progressively.

**Lee bounds** (2009): For sample selection problems (attrition in RCTs), compute upper and lower bounds on the treatment effect by trimming the group with more observations. Assumes monotonicity: treatment affects selection in only one direction.

**Partial identification with IV**: When exclusion restriction is relaxed (instrument may have a small direct effect on outcome), Conley, Hansen, and Rossi (2012) provide bounds on the treatment effect as a function of the assumed direct-effect magnitude.

### Reporting

- Present the identified set [lower bound, upper bound] alongside the point estimate from the primary specification.
- Discuss which assumptions generate narrower vs wider bounds.
- If bounds include zero, acknowledge that the effect is not sign-identified under weaker assumptions.

## Pre-Analysis Plan Requirements

For prospective studies, a pre-analysis plan locks in analytical decisions before seeing results, reducing researcher degrees of freedom.

### World Bank/McKenzie 10-Item Checklist

1. **Sample description**: how obtained, expected size, randomization method, balance variables
2. **Key data sources**: surveys planned, administrative data types
3. **Hypotheses along causal chain**: key outcomes, measurement steps, subgroup analyses linked to instruments
4. **Variable construction**: functional forms, missing data handling, outlier procedures, coding rules
5. **Treatment effect equation**: regression approach, controls, SE calculation -- write out the exact equation
6. **Multiple outcomes strategy**: index aggregation or domain-family grouping for multiple testing correction
7. **Attrition procedures**: checks for selective attrition, adjustments
8. **Limited variation handling**: criteria for dropping near-constant variables
9. **Theoretical model**: if testing a model, include it pre-commitment
10. **Archival plan**: register on AEA RCT Registry, EGAP, or OSF for time-stamping

### EGAP PAP Structure (8 sections)

1. Study design overview (design type, randomization, unit of analysis, population)
2. Hypotheses (confirmatory vs exploratory, directionality, theoretical link)
3. Measures and index construction (operationalization, survey wording, transformation code)
4. Estimation procedure (estimand, estimator, model specification, test statistic)
5. Inference criteria (SE type, alpha level, multiple comparisons correction)
6. Data issues (extreme values, missing data, attrition handling, imputation approach)
7. Power analysis (effect size assumptions, ICC, design effect, computational code)
8. Timeline and registration (verifiable timestamp, registration before analysis)

## Shift-Share (Bartik) Instruments

### Core Idea

Construct an instrument as the sum of national industry growth rates weighted by local industry shares. Variation comes from differences in local industry composition interacting with national shocks.

### Recent Critique (Goldsmith-Pinkham, Sorkin, and Swift, 2020)

The identifying assumption depends on whether you view the shares or the shocks as exogenous:

- **Shares approach**: Identification comes from the cross-sectional variation in industry shares. Requires shares to be uncorrelated with local outcome determinants (conditional on controls). Can test by checking balance on observables across share variation.
- **Shocks approach** (Borusyak, Hull, and Jaravel, 2022): Identification comes from the exogeneity of national shocks. Requires shocks to be many, mutually uncorrelated, and individually weak. Inference should be at the shock level.

### Which to Use

If you have many industries and believe national shocks are exogenous (e.g., trade shocks from China), the shocks approach is more credible. If you have few industries but believe local shares reflect historical accidents, the shares approach may work.

### Verification

- Report Rotemberg weights: show which industries/shocks drive the estimate
- Test balance of top-contributing shares against observables
- Test robustness to dropping dominant industries
- For the shocks approach: report effective number of shocks and first-stage F

## Decision Checklist

- [ ] You have identified and named your identification strategy
- [ ] You can state the key identifying assumption in one sentence
- [ ] You have provided evidence supporting the assumption (where testable)
- [ ] You have discussed the most likely violation and its implications
- [ ] Your language matches the strength of your identification
- [ ] You have reported robustness checks specific to your strategy
- [ ] For IV: first-stage F > 10, exclusion restriction argued, LATE acknowledged
- [ ] For DiD: pre-trends tested, staggered adoption addressed if applicable
- [ ] For RDD: manipulation test, bandwidth sensitivity, covariate balance
- [ ] For matching: balance assessment, sensitivity analysis, common support
- [ ] For synthetic control: pre-treatment fit assessed, placebo tests conducted, donor weights documented
- [ ] For Bartik: Rotemberg weights reported, dominant industries tested
- [ ] For prospective studies: pre-analysis plan registered and filed
- [ ] Methodology choices are logged in `docs/decisions/`
