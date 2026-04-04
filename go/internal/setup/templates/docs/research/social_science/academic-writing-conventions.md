# Academic Writing Conventions
*Decision Guide for Social Science Research*

## Overview

Academic writing in social science follows conventions that are partly disciplinary tradition, partly functional optimization for peer review. Understanding these conventions is not about style preferences -- it is about efficiently communicating your contribution so that reviewers accept the paper and readers cite it. This guide covers the structure of a standard empirical paper, section-specific conventions, common writing patterns, and the mistakes that signal an inexperienced author.

## Paper Structure

A standard empirical social science paper follows this sequence:

1. **Abstract** (150-250 words)
2. **Introduction** (3-5 pages)
3. **Literature Review / Theoretical Framework** (3-7 pages)
4. **Data and Methodology** (3-5 pages)
5. **Results** (3-7 pages)
6. **Robustness Checks** (2-4 pages, often partly in appendix)
7. **Discussion** (2-4 pages)
8. **Conclusion** (1-2 pages)
9. **References**
10. **Appendix** (tables, additional results, data details)

Journals vary on whether sections 3 and 4 are combined, whether discussion and conclusion are merged, and how the appendix is structured. Always check the target journal's style guide.

## The Abstract

The abstract is the most-read part of any paper. It must contain four elements in approximately this proportion:

- **Context and motivation** (1-2 sentences): What is the problem or question?
- **Method** (1-2 sentences): What did you do to answer it?
- **Key finding** (2-3 sentences): What did you find? Include the main quantitative result.
- **Implication** (1 sentence): Why does this matter?

Do not include citations in the abstract. Do not hedge the main finding excessively. Do not list every variable or control -- focus on the main result.

### Example Structure

"This paper examines whether [X affects Y] using [method/data]. We exploit [identification strategy] to estimate [what]. We find that [main result with magnitude]. This finding suggests that [implication for theory/policy]."

## The Introduction

The introduction is the second most-read section and the one that most determines whether the paper gets accepted. Follow the "gap and contribution" structure:

### Paragraph 1-2: The Hook

Open with the broad question or puzzle that motivates the paper. Ground it in something concrete -- a policy debate, a striking empirical fact, or a theoretical tension. Do not open with "This paper examines..." -- that belongs in paragraph 3 or 4.

### Paragraph 3-4: The Gap

Summarize what we know from existing literature and identify what we do not know. The gap should be specific and important -- not "nobody has studied X using data from country Z" (trivially true and uninteresting) but "existing evidence cannot distinguish between [competing explanation A] and [competing explanation B] because [limitation of prior work]."

### Paragraph 5-6: Your Contribution

State clearly what this paper does. Use language like: "We make three contributions to this literature. First, ... Second, ... Third, ..." Be specific about what is new: new data, new method, new mechanism, new empirical context, or a combination.

### Paragraph 7-8: Preview of Findings

Summarize your main findings in concrete terms. Include magnitudes: "We find that a one standard deviation increase in X is associated with a 15% decline in Y." Do not bury the main result to create suspense -- academic papers are not mystery novels.

### Paragraph 9-10: Roadmap

One paragraph describing the structure of the rest of the paper. This is conventional but should be brief: "Section 2 reviews the literature. Section 3 describes our data and methodology..."

### Common Introduction Mistakes

- Opening with definitions instead of motivation
- Making the gap too broad or too narrow
- Listing what the paper does without saying why it matters
- Overclaiming: "This is the first paper to..." (it rarely is, and reviewers will find the prior work)
- Underspecifying the contribution: "We contribute to the literature on X" (how, specifically?)
- No preview of quantitative results (forces the reader to skip ahead)

## Literature Review

### Purpose

The literature review does three things:
1. Demonstrates you know the field
2. Positions your paper relative to existing work
3. Motivates your specific approach by identifying what prior work cannot answer

It does not need to be comprehensive. It needs to be strategic.

### Organization

**Thematic** (preferred): Group papers by the question they address or the approach they take, not by publication date. Structure around 2-3 themes or debates in the literature that your paper engages with.

**Chronological**: Sometimes appropriate when tracing the development of a methodology or the evolution of a debate. Usually inferior to thematic because it reads as a list rather than an argument.

### Writing Pattern

Each paragraph in the literature review should follow this structure:
1. Topic sentence stating the theme or finding of this strand of literature
2. Key citations with their main findings (2-4 papers per paragraph)
3. Transition identifying the gap or limitation that leads to the next paragraph or to your contribution

Do not write annotated bibliographies: "Smith (2020) studied X and found Y. Jones (2021) studied A and found B." Instead: "Several studies have found Y in the context of X (Smith, 2020; Brown, 2019). However, this finding does not extend to the context of A, where Jones (2021) reports..."

### How Many Citations

A typical empirical paper cites 40-80 sources. The literature review accounts for 60-70% of citations. You should cite:
- All directly relevant papers (same question, same method, same context)
- Foundational methodological papers (the seminal DiD, IV, or RDD reference)
- Key theoretical papers that motivate your hypotheses
- Recent papers that define the current frontier

You should not cite:
- Papers you have not read
- Papers only tangentially related to pad the reference list
- Textbooks (cite the original methodological paper instead)

## Data and Methodology

### Data Section

Describe your data with enough detail that someone could replicate:
- **Source**: Where the data comes from (survey, administrative records, web scraping)
- **Sample construction**: How you went from raw data to analysis sample. Report every filter, every merge, every exclusion criterion with the number of observations lost at each step. A sample flow diagram is ideal.
- **Key variables**: Define treatment, outcome, and control variables. Report summary statistics in a table (mean, SD, min, max, N for each variable).
- **Time period and geography**: Specify exactly.

### Methodology Section

- State the estimating equation explicitly (in LaTeX notation)
- Name the identification strategy and its key assumption
- Justify every methodological choice: why this estimator, why these controls, why this sample
- Reference the methodological paper that introduced the technique you use
- Discuss potential threats to identification and how you address them

### Common Mistakes

- Describing data and methodology together in a way that is hard to follow
- Not reporting the sample flow (how many observations were lost at each cleaning step)
- Not defining variables precisely (what exactly does "income" mean? Pre-tax? Post-transfer? Household or individual?)
- Using a method without citing the original methodological reference

## Results

### Structure

Results sections follow a consistent pattern:

1. **Main result**: Report the core finding first. Present the main regression table with progressive specifications.
2. **Interpretation**: Translate the coefficient into practical terms after presenting it.
3. **Heterogeneity**: Do effects differ across subgroups? Present interaction terms or subsample regressions.
4. **Mechanism**: Can you identify the channel through which the effect operates?
5. **Robustness**: Summarize robustness checks (details in appendix).

### Tables Before Prose

Present the table, then describe it in text. The text should not simply repeat every number in the table. Instead:
- Highlight the main coefficient and its magnitude
- Note the pattern across specifications (stable? changing?)
- Comment on statistical significance and practical significance
- Point out any surprising or important findings in the controls

### Describing Statistical Results

"Column 1 of Table 3 reports OLS estimates of equation (1). The coefficient on trade openness is 0.034 (SE = 0.012), significant at the 1% level, indicating that a one percentage point increase in trade openness is associated with a 3.4% increase in GDP per capita. This estimate is stable across specifications: adding demographic controls (Column 2) and institutional quality measures (Column 3) reduces the coefficient only slightly, to 0.031 and 0.029, respectively."

### Avoid

- "As we can see from Table 3..." (the reader can see the table)
- Repeating every coefficient from every column
- Discussing control variable coefficients at length unless they are theoretically important
- Interpreting insignificant results as "no effect" (absence of evidence is not evidence of absence)

## Discussion

The discussion connects your results to the broader literature and addresses limitations:

1. **Summary of key findings**: One paragraph restating the main result
2. **Relation to prior work**: How do your findings compare to existing studies? Consistent? Contradictory? Why?
3. **Theoretical implications**: What do results mean for the theory or debate you set up in the introduction?
4. **Limitations**: Be honest and specific. "Our identification strategy cannot rule out [specific threat]." Do not list every possible limitation -- focus on the 2-3 most important ones and discuss their likely impact on your estimates.
5. **Policy implications**: If applicable, what do your findings suggest for policy? Be cautious -- policy recommendations require external validity that a single study rarely provides.

## Conclusion

Short (1-2 pages). Do not introduce new results or citations. Structure:

1. Restate the question and the answer (2-3 sentences)
2. Summarize the contribution (1 paragraph)
3. Discuss directions for future research (1 paragraph)

The conclusion should be self-contained: a reader who reads only the abstract and conclusion should understand what the paper does and finds.

## Hedging Language

Social science writing uses hedging to signal appropriate epistemic caution:

**Strong claims** (use with RCT or very strong identification):
- "X causes Y"
- "The effect of X on Y is..."
- "X leads to Y"

**Moderate claims** (use with DiD, RDD, strong IV):
- "We find evidence that X affects Y"
- "Our results suggest that X contributes to Y"
- "The estimates indicate that X is associated with higher Y"

**Weak claims** (use with OLS, matching, correlational analysis):
- "X is positively associated with Y"
- "Our results are consistent with the hypothesis that..."
- "These patterns suggest a relationship between X and Y, though causal interpretation requires caution"

### Hedging Mistakes

- Over-hedging: "It could potentially be argued that there might be a possible association..." (reads as lacking confidence in your own work)
- Under-hedging: Causal language without causal identification
- Inconsistent hedging: Causal language in the results section, hedging in the conclusion (or vice versa)

## Citation Practices

### When to Cite

- Every empirical claim that is not your own finding
- Every methodological technique (cite the original paper)
- Every theoretical argument you draw on
- When summarizing a debate, cite representatives of each side

### When Not to Cite

- Common knowledge within the field ("GDP measures economic output")
- Your own analysis and findings
- Generic statistical concepts ("standard errors measure estimation uncertainty")

### Integration vs. Parenthetical

- **Integrated**: "Acemoglu, Johnson, and Robinson (2001) show that..." -- use when the specific authors matter (seminal work, direct comparison)
- **Parenthetical**: "Colonial institutions have persistent effects on economic development (Acemoglu et al., 2001)" -- use when the finding matters more than who found it

### Multiple Citations

Order by relevance to the specific point, then by date. In economics: "(Smith, 2020; Jones, 2019; Brown, 2018)". In APA style: alphabetical.

## Common Mistakes by Inexperienced Authors

1. **Burying the contribution**: The reader should know what is new by page 2, not page 8.
2. **Weak transitions**: Each paragraph should connect logically to the next. Use transition sentences, not just topic sentences.
3. **Passive voice overuse**: "It was found that..." is weaker than "We find that..." Active voice is standard in modern social science.
4. **Long paragraphs**: Academic papers need white space. Keep paragraphs to 4-8 sentences.
5. **Describing the writing process**: "First, we ran regression A. Then, we decided to add controls." Describe the logic, not the chronology of your research.
6. **Not enough signposting**: Use "Section 3 shows that..." and "As discussed in Section 2..." to help the reader navigate.
7. **Inconsistent terminology**: Choose one term for each concept and use it consistently. Do not alternate between "trade openness," "openness to trade," and "trade liberalization" unless they mean different things.
8. **Appendix hoarding**: Put your best material in the main paper. The appendix is for supporting evidence, not for the results you are least confident about.

## Decision Checklist

- [ ] Abstract contains context, method, finding, and implication
- [ ] Introduction follows hook-gap-contribution-preview structure
- [ ] Contribution is stated clearly and specifically by page 2
- [ ] Literature review is thematic, not a list of summaries
- [ ] Data section includes sample construction and summary statistics
- [ ] Methodology section states the estimating equation and identification strategy
- [ ] Results lead with the main finding, not peripheral results
- [ ] Hedging language matches the strength of identification
- [ ] Limitations are honest and specific, not generic
- [ ] Conclusion is self-contained and introduces no new material
- [ ] All writing conventions documented in `docs/decisions/` where they involve methodological choices
