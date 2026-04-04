# Identification Strategies
*Decision Guide for Social Science Research*

## Overview

Identification is the process of isolating a causal effect from observational data by exploiting specific features of the data-generating process. Without a credible identification strategy, regression estimates capture associations that may be driven by confounding, reverse causality, or selection bias. This guide covers the threats to valid inference, the logic of identification, how to select a strategy based on your data, and how to document your approach in a paper.

This document complements causal-inference-strategies.md, which details the mechanics of specific estimators (IV, DiD, RDD, matching). This document focuses on the upstream question: how to think about identification and how to argue for the credibility of your research design.

## What Is Identification?

A parameter is identified when the data and the model's assumptions are sufficient to uniquely determine its value. In causal inference, identification means your research design allows you to distinguish the causal effect from confounding.

Formally: you want to estimate beta in Y = alpha + beta * D + epsilon, where D is the treatment. The parameter beta is identified as a causal effect only if E[D * epsilon] = 0 -- the treatment is uncorrelated with unobserved determinants of the outcome. Every identification strategy is a mechanism for achieving this condition.

### The Credibility Revolution

Angrist and Pischke (2010) described a "credibility revolution" in empirical economics: a shift from structural models with many assumptions toward reduced-form designs (IV, DiD, RDD) that rely on transparent, testable assumptions. The core insight: a simple design with a clear identification argument is more credible than a complex model with many untestable assumptions.

This shift has spread to political science, sociology, and public health. Modern social science rewards transparent identification over technical sophistication.

## Threats to Internal Validity

Internal validity means the estimated effect is a credible estimate of the true causal effect for the studied population. The main threats:

### Omitted Variable Bias (OVB)

A variable W is omitted and causes bias when:
1. W affects Y (W is a determinant of the outcome)
2. W is correlated with D (W is related to treatment assignment)
3. W is not included in the regression

The direction of bias: sign(bias) = sign(correlation of W with D) * sign(effect of W on Y).

**Example**: Estimating the effect of education on earnings without controlling for ability. Ability affects earnings (condition 1), ability is correlated with education (condition 2), and ability is unobserved (condition 3). The OLS estimate of education's effect is biased upward because ability has a positive correlation with both education and earnings.

**Remedies**: Include controls (if W is observed), use FE (if W is time-invariant), use IV (if you have an instrument), or bound the bias (Oster, 2019).

### Reverse Causality

The observed correlation between D and Y may run from Y to D rather than from D to Y.

**Example**: Do exports cause economic growth, or does economic growth cause exports? Cross-sectional regressions cannot distinguish the two.

**Remedies**: Use lagged treatment (cautiously -- lagged D may still be correlated with current epsilon), use IV, exploit a temporal shock (DiD), or use RDD where treatment assignment is mechanical.

### Measurement Error

When variables are measured with error, estimates are biased:
- **Classical measurement error in Y**: No bias in coefficients, just larger standard errors.
- **Classical measurement error in X**: Attenuation bias -- coefficients are biased toward zero. With multiple regressors, bias is in unpredictable directions.
- **Non-classical measurement error**: Bias in any direction.

**Remedies**: Use better data, use IV (instrument with an alternative measure), or discuss the direction and likely magnitude of bias.

### Selection Bias

Units that receive treatment differ systematically from those that do not, and these differences also affect the outcome.

**Example**: Estimating the effect of job training programs by comparing trainees to non-trainees. Trainees may be more motivated (positive selection) or have worse labor market prospects (negative selection).

**Remedies**: The entire toolkit of causal inference -- randomization, IV, DiD, RDD, matching -- exists to address selection bias.

### Simultaneity

D and Y are jointly determined. This is a special case of reverse causality common in equilibrium settings (supply and demand, prices and quantities).

**Remedies**: IV with an instrument that shifts one curve but not the other.

## Threats to External Validity

External validity means the estimated effect generalizes beyond the studied population, time period, and institutional context.

### Generalizability

- **Population**: Does the sample represent the target population? Convenience samples, opt-in surveys, and administrative data from specific institutions may not generalize.
- **Context**: Effects estimated in one country, one policy regime, or one time period may not transfer.
- **Treatment variation**: The effect of a specific policy change in a specific context is not necessarily the effect of the same policy implemented differently.

### LATE vs. ATE

IV estimates a Local Average Treatment Effect for compliers. Compliers may differ from the full population. RDD estimates the effect at the cutoff, which may not represent the effect further from the cutoff. DiD estimates the effect on the treated, which may differ from the effect on the untreated.

### SUTVA Violations

The Stable Unit Treatment Value Assumption requires that one unit's treatment does not affect another unit's outcome. Violations occur with:
- **Spillovers**: Treating one individual affects untreated individuals in the same network/area.
- **General equilibrium effects**: A job training program that helps participants may reduce employment for non-participants.
- **Interference**: In vaccine studies, vaccinating some individuals protects the unvaccinated (herd immunity).

SUTVA violations bias standard estimates because the "untreated" comparison group is actually affected by treatment.

## Strategy Selection Based on Data Availability

### You Have a Natural Experiment

A natural experiment is an event or institutional feature that generates quasi-random variation in treatment.

**Policy change with clear timing and affected group**: Use DiD. The policy creates a treatment group (affected) and a control group (unaffected), with a before/after comparison.

**Score-based assignment with a threshold**: Use RDD. The cutoff generates quasi-random assignment near the threshold.

**Exogenous shock correlated with treatment**: Use IV. The shock is the instrument.

### You Have Rich Administrative Data

With detailed individual-level data, you may be able to argue selection on observables:
- Use matching (PSM, CEM, entropy balancing) with sensitivity analysis
- Combine matching with DiD for additional credibility
- Report Oster bounds and E-values

### You Have Repeated Cross-Sections

Not as powerful as true panel data, but you can use:
- Synthetic control (Abadie, Diamond, and Hainmueller, 2010) for case studies with aggregate data
- Repeated cross-section DiD (comparing group averages over time)

### You Have Cross-Sectional Data Only

The weakest setting for causal inference. Options:
- IV if a credible instrument exists
- Cross-sectional matching with strong sensitivity analysis
- OLS with careful discussion of omitted variable bias direction
- Honest framing: "We estimate associations. Causal interpretation requires [assumption]."

### You Have No Clean Identification

This is common and not a reason to abandon the project. Options:
- **Bounds analysis**: Report a range of estimates under different assumptions about the degree of confounding (Manski, 2003).
- **Sensitivity analysis**: Oster (2019) bounds, E-values, Rosenbaum bounds.
- **Multiple imperfect strategies**: If OLS, IV, and matching all point in the same direction despite different assumptions, the convergence is informative.
- **Honest reporting**: Frame results as suggestive evidence, discuss specific threats, and avoid causal language.

## Documenting Your Identification Strategy

### In the Methodology Section

Every empirical paper should include a subsection titled "Identification Strategy" or "Empirical Strategy" that contains:

1. **The estimating equation**: Written out in full, with subscripts and error terms.
2. **The key assumption**: Stated in plain language. "Our identification relies on the assumption that [parallel trends hold / the instrument is excludable / assignment at the cutoff is quasi-random]."
3. **Why the assumption is plausible**: Institutional details, prior evidence, logical argument.
4. **What could go wrong**: The specific threat that would violate the assumption.
5. **How you test or address it**: Pre-trends tests, placebo checks, falsification tests, sensitivity analysis.

### Example Identification Paragraph

"We identify the effect of minimum wage increases on employment using a difference-in-differences strategy. We compare employment in counties bordering a state that raised its minimum wage (treatment) to employment in counties on the other side of the state border (control), before and after the policy change. This design relies on the assumption that border-county pairs would have followed parallel employment trends absent the minimum wage change. We provide evidence for this assumption in two ways: (i) Figure 2 shows parallel pre-trends in the five years preceding the policy change, and (ii) Table 4 reports an event-study specification in which pre-treatment leads are individually and jointly insignificant (F = 0.87, p = 0.52). The primary threat to our identification is that minimum wage increases may coincide with other state-level policy changes; we address this by controlling for state-level unemployment insurance generosity and EITC expansions."

## Common Fallacies

### "Controlling For" Is Not Identification

Adding control variables to an OLS regression does not establish causation. Controls can reduce omitted variable bias if the controls are pre-treatment confounders, but they introduce bias if they are:
- **Post-treatment variables**: Variables affected by the treatment (bad controls problem, Angrist and Pischke, 2009)
- **Colliders**: Variables caused by both treatment and outcome (conditioning on a collider opens a spurious path)
- **Mediators** (when you want the total effect): Controlling for the mechanism through which treatment operates removes part of the effect you want to estimate

### Stepwise Regression Is Not Identification

Adding variables one at a time and watching how the coefficient changes is informative about the correlation structure of your data, but it does not identify a causal effect. The coefficient change tells you about the correlation between the added variable and both the treatment and the outcome -- it does not tell you which specification is "correct."

### "Significant After Controls" Is Not Identification

A coefficient remaining significant after adding controls means it is not fully explained by those specific controls. It does not mean it is unexplained by any confounder. There may be unobserved confounders that controls do not capture.

### Fixed Effects Solve Everything

Unit fixed effects absorb time-invariant unobservables, but they do not address:
- Time-varying confounders
- Reverse causality
- Selection into treatment based on anticipated future outcomes (Ashenfelter's dip)

### Lagged Variables Solve Reverse Causality

Using X(t-1) to predict Y(t) helps with strict simultaneity but does not address persistent confounders that affect both past X and current Y. If an omitted variable is correlated with both X(t-1) and Y(t), the lagged specification is still biased.

## Decision Checklist

- [ ] You have named your identification strategy explicitly
- [ ] You have stated the key identifying assumption in plain language
- [ ] You have argued why the assumption is plausible in your setting
- [ ] You have identified the primary threat to your identification
- [ ] You have provided evidence supporting the identifying assumption (where testable)
- [ ] You have performed at least one placebo or falsification test
- [ ] You have reported sensitivity analysis for untestable assumptions
- [ ] Your language (causal vs. associational) matches your identification strength
- [ ] You have discussed external validity and the population for which your estimate applies
- [ ] You have avoided the common fallacies listed above
- [ ] Strategy and assumptions are logged in `docs/decisions/`
