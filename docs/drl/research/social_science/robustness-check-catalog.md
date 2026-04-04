# Robustness Check Catalog
*Decision Guide for Social Science Research*

## Overview

A robustness check tests whether your main finding holds under reasonable alternative analytical choices. The goal is not to generate more stars on your coefficient, but to demonstrate that your result is not an artifact of one particular specification, sample definition, or measurement choice. Robustness checks address the problem of researcher degrees of freedom -- the many decisions a researcher makes (which controls to include, how to measure variables, which sample to use) that could each change the results.

This catalog provides a structured inventory of standard robustness checks organized by category. Use it as a menu: not every check applies to every study, but every study should include checks from multiple categories.

## Why Robustness Matters

### Researcher Degrees of Freedom

Simmons, Nelson, and Simonsohn (2011) demonstrated that flexible data analysis can produce statistically significant results from pure noise. Even without intentional p-hacking, the cumulative effect of many small analytical choices can produce false positives. Robustness checks are the discipline against this.

### Pre-Registration and Specification Curves

The gold standard is pre-registration: specify your analysis plan before seeing the data. When pre-registration is not possible (secondary data, archival studies), the next best approach is a specification curve analysis (Simonsohn, Simmons, and Nelson, 2020) that reports results across all reasonable specifications.

### What Reviewers Expect

Top journals in economics, political science, and sociology routinely require:
- At least 3-5 robustness checks for the main result
- Checks that address the most obvious threats to your specific identification strategy
- Results presented in a robustness table (usually in an appendix)
- Discussion of which checks pass and which raise concerns

## Category 1: Alternative Specifications

These checks test whether your result depends on the particular functional form or set of controls.

### Progressive Control Addition

Start with a parsimonious model (just the key variable) and progressively add control variables. Report all specifications. The coefficient of interest should be relatively stable.

- Column 1: Bivariate relationship
- Column 2: Add demographic controls
- Column 3: Add economic/institutional controls
- Column 4: Add fixed effects
- Column 5: Full specification

If the coefficient changes dramatically when adding a specific control, investigate why. It could indicate omitted variable bias in the parsimonious model or a "bad control" problem with the added variable.

### Functional Form

- Linear vs. log-transformed dependent variable
- Quadratic terms for key variables
- Spline/piecewise linear specifications
- Ordered categories vs. continuous treatment of ordinal variables

### Alternative Fixed Effects

- No fixed effects vs. unit FE vs. time FE vs. two-way FE
- Alternative levels of fixed effects (e.g., state vs. county vs. MSA)
- Mundlak/Chamberlain correlated random effects as an alternative to FE

### Interaction and Nonlinearity

- Test for nonlinear effects by splitting the sample at the median of the key variable
- Add interaction terms between key variables and moderators suggested by theory
- Test whether effects differ across subgroups (heterogeneous treatment effects)

## Category 2: Alternative Samples

These checks test whether your result is driven by a particular subset of observations.

### Dropping Outliers

- Winsorize at 1st/99th percentiles (replace extreme values with percentile values)
- Trim at 1st/99th percentiles (drop extreme values entirely)
- Drop observations with Cook's distance > 4/n
- Report results for both original and trimmed/winsorized samples

### Subsample Analysis

- Restrict to specific time periods (early vs. late, pre-crisis vs. post-crisis)
- Restrict to specific geographies or institutional contexts
- Male vs. female, large vs. small firms, developed vs. developing countries
- Split by key moderating variables that theory suggests should matter

### Leave-One-Out

- Drop each country/state/industry one at a time and re-estimate. If results change dramatically when one unit is dropped, investigate that unit.
- For DiD: drop each treatment cohort one at a time.
- For cross-country studies: drop regions one at a time (e.g., drop all African countries, drop all OECD countries).

### Sample Period Sensitivity

- Vary the start and end dates of the sample period
- For DiD: vary the pre-treatment and post-treatment window lengths
- Test whether results hold in a balanced panel (only units observed in all periods)

## Category 3: Alternative Measurements

These checks test whether your result depends on how you measured your key variables.

### Alternative Dependent Variables

- Different measures of the same concept (e.g., GDP per capita vs. GDP growth vs. log GDP)
- Different data sources for the same variable
- Standardized vs. raw measures
- Indices constructed from multiple indicators (PCA, factor analysis, simple average)

### Alternative Independent Variables

- Different operationalizations of the treatment variable
- Continuous vs. binary treatment (above/below median)
- Alternative lag structures (contemporaneous, 1-year lag, 2-year lag)
- Different data sources for the key regressor

### Measurement Error

- If measurement error is suspected, use IV where an alternative measure instruments for the noisy one
- Report results for all available measures of the same concept
- Discuss the direction of expected bias from measurement error (usually attenuation toward zero for classical measurement error in X)

## Category 4: Alternative Estimators

These checks test whether your result depends on the specific statistical method.

### Standard Error Adjustments

- OLS with homoscedastic SEs vs. robust SEs vs. clustered SEs
- Different levels of clustering (e.g., firm vs. industry vs. state)
- Wild cluster bootstrap (when number of clusters is small, < 50)
- Conley (1999) spatial SEs if observations are geographically proximate

### Alternative Estimation Methods

- OLS vs. WLS (weighted least squares)
- Linear probability model vs. logit/probit (for binary outcomes)
- Poisson vs. negative binomial (for count outcomes)
- Quantile regression (to check if effects vary across the outcome distribution)
- Bayesian estimation (to check sensitivity to priors and obtain credible intervals)

### For Panel Data

- Fixed effects vs. first differences
- Static FE vs. dynamic panel (Arellano-Bond GMM)
- Correlated random effects (Mundlak approach)

### For IV

- 2SLS vs. LIML (less biased with weak instruments)
- Alternative instrument sets
- Reduced-form estimates (regress Y directly on Z -- interpretable even if first stage is weak)

## Category 5: Sensitivity and Falsification

These are the strongest robustness checks because they directly test the identifying assumption.

### Coefficient Stability (Oster Bounds)

Oster (2019) extends the Altonji, Elder, and Taber (2005) approach. The idea: if adding observed controls barely changes the coefficient, unobserved confounders (which are likely correlated with observables) would also not change it much.

Compute the Oster delta: the ratio of selection on unobservables to selection on observables that would be required to explain away the result. Convention: delta > 1 provides reasonable confidence that the result is not driven by omitted variables.

### Rosenbaum Bounds

For matching studies. Ask: how large would an unobserved confounder need to be to overturn the result? Report the Gamma value at which the result becomes insignificant.

### E-Values

VanderWeele and Ding (2017). Report the minimum strength of association (on the risk-ratio scale) that an unmeasured confounder would need to have with both treatment and outcome to fully explain away the observed effect. Useful for any observational study.

### Placebo Tests

Replace the actual treatment with a fake treatment that should have no effect:
- **Placebo timing**: For DiD, assign treatment at a time before the actual treatment occurred.
- **Placebo outcome**: Test the treatment on an outcome it should not affect.
- **Placebo treatment group**: Test the treatment on a group that was not actually treated.
- **Placebo cutoff**: For RDD, test at a cutoff where no treatment discontinuity exists.

Significant placebo effects undermine your identification.

### Falsification Tests

Identify observable implications of your causal story that you can test:
- If X causes Y through mechanism M, does X also affect M?
- If the effect is causal, it should not appear in populations where the mechanism cannot operate.
- If the policy affected group A but not group B, does the effect appear only for group A?

## Template Robustness Plan

For each study, construct a robustness plan before running the analysis:

```
## Robustness Plan for [Paper Title]

### Main specification
- Estimator: [OLS/IV/DiD/RDD/matching]
- Key assumption: [state in one sentence]

### Primary robustness checks (report in main paper)
1. [Most important alternative specification]
2. [Test of identifying assumption]
3. [Placebo or falsification test]

### Secondary robustness checks (report in appendix)
4. [Alternative measurement of key variable]
5. [Alternative sample definition]
6. [Alternative standard errors]
7. [Sensitivity analysis -- Oster/Rosenbaum/E-value]

### If any check fails
- Investigate the reason
- Discuss in the paper honestly
- Consider whether it undermines the main finding or reveals heterogeneity
```

## How to Report Robustness Results

### In the Main Paper

- Describe the robustness checks you performed in 1-2 paragraphs
- Summarize results: "Our main finding is robust to [list of checks]. Results are reported in Appendix Table X."
- If a check fails, discuss it honestly and explain what it means for interpretation

### Robustness Tables

- Mirror the structure of your main results table
- Each column = one robustness check (clearly labeled)
- Report the coefficient of interest and its standard error
- Include N and any relevant diagnostics
- Title should describe what varies across columns

### Specification Curves

For maximum transparency, present a specification curve:
1. Top panel: coefficient estimates sorted from smallest to largest across all reasonable specifications
2. Bottom panel: dot matrix showing which specification choices correspond to each estimate
3. Report the share of specifications yielding significant results

## Decision Checklist

- [ ] You have planned robustness checks before running the main analysis
- [ ] Checks span multiple categories (specifications, samples, measurements, estimators)
- [ ] At least one check directly tests the identifying assumption
- [ ] At least one placebo or falsification test is included
- [ ] Sensitivity analysis (Oster/Rosenbaum/E-value) is reported
- [ ] Results are presented clearly in appendix tables
- [ ] Failed checks are discussed honestly, not hidden
- [ ] All robustness decisions are logged in `docs/decisions/`
