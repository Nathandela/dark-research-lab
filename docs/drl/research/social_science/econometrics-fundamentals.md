# Econometrics Fundamentals
*Decision Guide for Social Science Research*

## Overview

Econometrics is the application of statistical methods to economic and social science data. This guide covers the core toolkit a researcher needs to estimate relationships, test hypotheses, and report results in a publishable format. The focus is practical: which method to use, when, and how to diagnose problems before they undermine your conclusions.

This document assumes familiarity with basic statistics (hypothesis testing, distributions, confidence intervals). It targets researchers choosing between estimation strategies for observational data analysis.

## OLS Regression

### When to Use

Ordinary Least Squares is the default estimator when you have a continuous outcome variable and want to estimate conditional means. Use OLS as a starting point unless you have specific reasons to choose otherwise (binary outcome, count data, censored data, endogeneity).

### The Five Classical Assumptions

1. **Linearity**: The relationship between X and Y is linear in parameters (not necessarily in variables -- you can include polynomials and interactions).
2. **Exogeneity**: E[epsilon | X] = 0. The error term is uncorrelated with regressors. This is the assumption most often violated in social science, and its violation produces biased estimates.
3. **No perfect multicollinearity**: No regressor is a perfect linear combination of others. Near-multicollinearity inflates standard errors but does not bias coefficients.
4. **Homoscedasticity**: Var(epsilon | X) = sigma^2 (constant variance). Violation does not bias coefficients but makes standard errors unreliable.
5. **No autocorrelation**: Cov(epsilon_i, epsilon_j) = 0 for i != j. Violated in time-series and panel data.

### Diagnostics Checklist

- **Linearity**: Plot residuals vs. fitted values. Look for systematic curvature. Consider adding polynomial terms or using log transformations.
- **Multicollinearity**: Compute Variance Inflation Factors (VIF). Values above 10 warrant investigation; above 5 is worth noting. Centering interaction terms can reduce VIF.
- **Heteroscedasticity**: Breusch-Pagan test or White test. If present, use heteroscedasticity-robust standard errors (HC1 or HC3) as default practice.
- **Normality of residuals**: Q-Q plot, Shapiro-Wilk test. Matters mainly for small samples (n < 30). With large samples, CLT makes coefficient distributions approximately normal regardless.
- **Outliers and influence**: Cook's distance, DFBETAS. Report results with and without influential observations as a robustness check.

### Interpreting Coefficients

- **Level-level**: A one-unit increase in X is associated with a beta-unit change in Y.
- **Log-level**: A one-unit increase in X is associated with a (beta * 100)% change in Y.
- **Level-log**: A 1% increase in X is associated with a (beta / 100)-unit change in Y.
- **Log-log**: A 1% increase in X is associated with a beta% change in Y (elasticity).

Always report the unit of measurement. Always distinguish between statistical significance and practical significance by reporting effect sizes alongside p-values.

## Panel Data Methods

### When You Have Panel Data

Panel data (repeated observations of the same units over time) opens up powerful methods for controlling unobserved heterogeneity. The central question: are there unit-specific unobserved factors correlated with your regressors?

### Pooled OLS

Treats all observations as independent. Only valid if there is no unobserved unit-level heterogeneity. Almost never appropriate in social science -- if you have panel data, you should exploit its structure.

### Fixed Effects (FE)

**What it does**: Includes a dummy variable for each unit (or equivalently, demeans within units). This absorbs all time-invariant unobserved characteristics of each unit.

**When to use**: When unobserved unit-specific factors (culture, geography, institutional history) are likely correlated with your regressors. This is the default choice for most social science applications.

**Limitations**:
- Cannot estimate the effect of time-invariant regressors (gender, country of birth) because they are absorbed by the unit dummies.
- Requires within-unit variation in X. If your key variable barely changes within units over time, FE estimates will be imprecise.
- Amplifies measurement error bias relative to OLS because within-unit variation is smaller than total variation.

**Time fixed effects**: Include year dummies to absorb common shocks affecting all units in a given period. Almost always include these alongside unit fixed effects (two-way FE).

### Random Effects (RE)

**What it does**: Models unit-specific effects as random draws from a distribution, uncorrelated with regressors.

**When to use**: When the unobserved unit effects are uncorrelated with your independent variables. This is a strong assumption rarely met in observational social science.

**Advantage over FE**: More efficient (smaller standard errors) and can estimate effects of time-invariant variables.

### The Hausman Test

Tests whether the RE assumption (uncorrelated effects) holds by comparing FE and RE coefficients. If they differ significantly, use FE. In practice:

- If the Hausman test rejects, use Fixed Effects.
- If it does not reject, you can use Random Effects for efficiency, but many reviewers and journals default to FE regardless because RE's assumption is hard to defend.
- Report both models if the choice is ambiguous.

### Clustered Standard Errors

With panel data, standard errors should almost always be clustered at the unit level. This allows for arbitrary within-unit serial correlation and heteroscedasticity. Rule of thumb: cluster at the level of treatment assignment or the highest level of aggregation of the key regressor.

**Warning**: Clustered SEs require a sufficient number of clusters (generally 30+). With few clusters, use wild cluster bootstrap or bias-corrected cluster-robust SEs (Cameron, Gelbach, and Miller, 2008).

## Time-Series Considerations

### Stationarity

A time series is stationary if its statistical properties (mean, variance, autocorrelation) do not change over time. Non-stationary series can produce spurious regressions -- high R-squared and significant t-statistics for variables that have no real relationship.

**Testing**: Augmented Dickey-Fuller (ADF) test, Phillips-Perron test, KPSS test. Use multiple tests because each has different null hypotheses (ADF/PP: null is unit root; KPSS: null is stationarity).

**Remedies**: First-differencing, detrending, or cointegration analysis if variables share a common stochastic trend.

### Autocorrelation

Serial correlation in errors violates OLS assumptions and produces unreliable standard errors.

**Detection**: Durbin-Watson test (first-order AR only), Breusch-Godfrey test (higher-order AR).

**Remedies**: Newey-West (HAC) standard errors, which are robust to both heteroscedasticity and autocorrelation. Specify the lag truncation parameter based on sample size (common rule: 0.75 * T^(1/3)).

### Granger Causality

A variable X Granger-causes Y if past values of X improve predictions of Y beyond past values of Y alone. This is predictive precedence, not causal inference. Never interpret Granger causality as actual causation in a paper.

### Cointegration

When two or more non-stationary series share a common stochastic trend, they are cointegrated -- their linear combination is stationary even though the individual series are not. This is economically meaningful: it implies a long-run equilibrium relationship.

**Testing**: Engle-Granger two-step procedure (test residuals from a levels regression for stationarity) or Johansen trace/maximum eigenvalue test (allows multiple cointegrating vectors).

**Modeling**: If cointegration is present, use an Error Correction Model (ECM) that captures both short-run dynamics (changes) and the long-run equilibrium (levels). Do not first-difference cointegrated series -- differencing discards the long-run relationship.

### Dynamic Panel Models

When a lagged dependent variable is included as a regressor in a panel model, FE is biased (Nickell bias) because the demeaned lagged dependent variable is correlated with the demeaned error. The bias is severe in short panels (small T).

**Remedies**:
- Arellano-Bond (difference GMM): instruments lagged levels for first-differenced equations. Appropriate for short T, large N panels.
- Blundell-Bond (system GMM): adds a levels equation to improve efficiency. Report the number of instruments (too many instruments leads to overfitting and weakened specification tests).
- Anderson-Hsiao: use lagged differences as instruments. Simpler but less efficient than GMM.
- Always report the Hansen/Sargan test for overidentifying restrictions and the AR(2) test for serial correlation.

## Method Selection Decision Tree

Use this to choose your primary estimation strategy:

1. **What is your outcome variable?**
   - Continuous -> OLS family (proceed to step 2)
   - Binary -> Logit/Probit (or Linear Probability Model with robust SEs for marginal effects)
   - Count -> Poisson/Negative Binomial
   - Censored/Truncated -> Tobit/Heckman
   - Duration -> Survival models (Cox, Weibull)

2. **Do you have panel data?**
   - No -> Cross-sectional OLS with robust SEs (proceed to step 3)
   - Yes -> Panel methods (proceed to step 4)

3. **Cross-section: Is endogeneity a concern?**
   - No -> OLS with robust SEs, report diagnostics
   - Yes -> See identification-strategies.md for IV, matching, etc.

4. **Panel: Are unit effects correlated with regressors?**
   - Yes or uncertain -> Fixed Effects with clustered SEs
   - No (rare) -> Random Effects, but report FE as robustness check
   - Time-varying confounders? -> Consider DiD, event study, or dynamic panel (GMM)

5. **Is autocorrelation present?**
   - Yes -> Newey-West SEs, or model temporal dynamics explicitly (lagged dependent variables, ARIMA errors)

## Reporting Results in a Paper

### Coefficient Tables

Standard table format for regression results:

- One column per model specification (start simple, add controls progressively)
- Report coefficients with standard errors in parentheses below
- Mark significance levels: * p<0.10, ** p<0.05, *** p<0.01
- Include N, R-squared (within R-squared for FE), number of clusters/units
- Note the type of standard errors used (robust, clustered, HAC)
- Include F-statistic or joint significance test for key variables

### What to Report in Prose

- Sign, magnitude, and significance of key coefficients
- Economic significance: what does the coefficient mean in practical terms? (e.g., "A one standard deviation increase in X is associated with a 0.3 standard deviation increase in Y")
- Comparison across specifications: are results stable when adding controls?
- Any diagnostics that informed model choice

### Common Reporting Mistakes

- Reporting only p-values without effect sizes
- Not reporting the number of observations that differ across specifications (sample changes)
- Failing to mention the type of standard errors used
- Stepwise adding controls without theoretical justification
- Calling results "insignificant" instead of "not statistically significant at conventional levels"
- Interpreting R-squared as a measure of model quality (it is not -- it measures variance explained, which is often low in social science and that is fine)

## Common Pitfalls

1. **Omitted variable bias**: The most common threat. If a variable is correlated with both your regressor and your outcome, and you do not control for it, your estimate is biased. The direction of bias depends on the sign of the correlations.
2. **Bad controls**: Do not control for variables that are themselves affected by the treatment (post-treatment variables). This introduces collider bias and can bias estimates in either direction.
3. **Overcontrolling**: Adding many irrelevant controls reduces precision without reducing bias. Include controls based on theory, not data availability.
4. **p-hacking**: Running many specifications and reporting only the significant ones. Pre-register your specification or report all specifications you ran.
5. **Misinterpreting interaction terms**: The coefficient on X1*X2 does not mean "the effect of X1 depends on X2" unless you have also included X1 and X2 as main effects. In nonlinear models (logit, probit), the interaction effect differs from the coefficient on the interaction term.

## Decision Checklist

Before submitting your analysis, verify:

- [ ] You can justify every control variable on theoretical grounds
- [ ] You have tested for and addressed heteroscedasticity
- [ ] Standard errors are appropriate for your data structure (robust, clustered, HAC)
- [ ] You report effect sizes alongside statistical significance
- [ ] Coefficient interpretation matches your functional form (log-log, level-log, etc.)
- [ ] For panel data: you justify FE vs. RE choice (Hausman test or theoretical argument)
- [ ] Your sample size is reported and consistent across specifications
- [ ] You have checked for influential outliers
- [ ] Results are robust to reasonable alternative specifications (see robustness-check-catalog.md)
- [ ] You have logged your methodology choices in `docs/decisions/`
