---
description: Identify and analyze grade trends across academic terms (Q1, Q2, Q3, Q4, S1, S2) to spot improvement or decline requiring intervention
---

# Grade Trends Analysis

Analyze how student grades change across academic terms to identify improvement trajectories, declining performance, and courses requiring immediate attention.

## What This Skill Does

This skill provides temporal grade analysis by using these MCP tools:

- **get_grade_trends** - Shows grade progression across quarters and semesters (Q1→Q2→Q3→Q4, S1→S2)
- **get_current_grades** - Current standing for comparison with historical trends

The analysis reveals whether a student is improving, maintaining, or declining in each course, enabling proactive intervention before final grades are set.

## Analysis Components

### 1. Grade Progression Table
- Course-by-course view across all terms
- Visual tracking of letter grade changes
- Comparison between quarters and semesters
- Identification of missing term grades (indicates dropped courses or incomplete data)

### 2. Trend Classification
For each course, classify the trend as:
- **Improving** - Grade increasing over time (C→B→A or D→C)
- **Stable** - Grade consistent across terms (B→B→B)
- **Declining** - Grade decreasing over time (A→B→C or B→C)
- **Recovering** - Declined then improved (A→C→B)
- **Volatile** - Inconsistent with swings (B→D→A→C)

### 3. Concern Identification
- Courses with significant drops (2+ letter grades)
- Courses trending toward failing
- Courses that improved but need maintenance
- Semester grades vs quarter grades comparison

## Interpretation Guidance

### Grade Change Severity Levels

**Letter Grade Drops**:
- **1 grade drop** (A→B, B→C) - Monitor, may be normal variation
- **2 grade drops** (A→C, B→D) - Concerning, investigate cause
- **3+ grade drops** (A→D, A→F) - Critical, immediate intervention required
- **To failing** (any→D/F) - Urgent, contact teacher immediately

**Letter Grade Improvements**:
- **1 grade improvement** (C→B, B→A) - Positive, encourage continued effort
- **2 grade improvements** (D→B, C→A) - Excellent progress, celebrate and maintain
- **3+ grade improvements** (F→C, F→B) - Outstanding recovery, recognize achievement

### Term-Specific Patterns

**Q1 Baseline**:
- First quarter sets expectations
- Lower Q1 grade may indicate adjustment period
- Higher Q1 grade shows strong start

**Q2 Mid-Quarter Check**:
- Q2 improvement (Q1→Q2↑) - Student adapting well
- Q2 decline (Q1→Q2↓) - Warning sign, intervene before semester grade
- Q2 stable - Consistent performance established

**S1 Semester Grade**:
- Should reflect Q1-Q2 average with slight weight to Q2
- If S1 significantly differs from quarters, final exam impacted grade
- S1 sets baseline for second semester

**Q3 Second Semester Start**:
- Compare Q3 to Q1 for year-over-year trend
- Q3 lower than Q1 - May indicate burnout or difficulty increase
- Q3 higher than Q1 - Student learned and improved

**Q4 Final Quarter**:
- Critical for final semester grade
- Declining Q3→Q4 - Senioritis or burnout concern
- Improving Q3→Q4 - Strong finish, commendable

**S2 Final Semester**:
- Determines final course grade with S1
- S2 improvement over S1 - Year ended strong
- S2 decline from S1 - Concerning finish

### Threshold Alerts

**Immediate Action Required**:
- **Failing grade** (D or F) in any term
- **Drop of 2+ letter grades** in single quarter transition
- **Consistent decline** across 3+ consecutive terms
- **Below 70%** at any point

**Monitor Closely**:
- **Drop of 1 letter grade** from previous term
- **Grade at C** (especially if previously A/B student)
- **Volatile pattern** (up and down more than 1 grade)
- **Between 70-80%** percentage

**Positive Recognition**:
- **Improvement of 2+ grades** - celebrate achievement
- **Stable A/B** across all terms - recognize consistency
- **Recovery from D/F** to C or higher - acknowledge effort

## Example Usage

**Scenario**: Parent wants to see if their student's Math grade is improving or declining over the year

**Invocation**:
```
Use the grade-trends skill to analyze Marcus's grade trends, focusing on Math
```

**Example Output**:
```
## Grade Trends for Marcus

| Course | Q1 | Q2 | S1 | Q3 | Q4 | S2 |
|--------|----|----|----|----|----|----|
| Math 8 | B | C | C | D | - | - |
| English 8 | A | A | A | B | - | - |
| Science 8 | B | B | B | B | - | - |
| Social Studies | A | B | B | B | - | - |
| PE | A | A | A | A | - | - |
| Art | B | A | A | A | - | - |

### Trend Analysis

**Critical Concern - Math 8**:
- Q1: B (85%)
- Q2: C (75%) - **1 grade drop**
- S1: C (78%)
- Q3: D (68%) - **2 total grades down from Q1**
- ⚠️ **ALERT**: Consistent decline, now at failing threshold (below 70%)
- **Action Required**: Immediate teacher meeting needed

**Minor Concern - English 8**:
- Dropped from A to B in Q3 (1 grade drop)
- Still passing, but break from perfect trend
- Monitor in Q4 to ensure doesn't decline further

**Stable Performance**:
- Science 8: Consistent B across all terms - reliable
- PE: Perfect A maintenance - strength area

**Positive Trends**:
- Art: Improved Q1→Q2 (B→A) and maintained
- Shows student can improve with engagement
```

**Interpretation**:
- **Primary concern**: Math 8 shows alarming 2-grade decline (B→D) over three quarters
  - Pattern suggests cumulative difficulty (material builds on itself)
  - Q3 grade of 68% is dangerously close to failing
  - Without intervention, likely to fail S2 and possibly the course
- **Secondary concern**: English 8 drop from A to B needs monitoring
  - Single grade drop less severe than Math
  - May indicate increased difficulty in Q3 curriculum
- **Positive indicators**: Art improvement shows student capable of growth
  - Proves student can improve when engaged with material
  - Model this success for struggling subjects
- **Stable areas**: Science and PE show consistency - not causing stress

**Recommended Actions**:
1. **URGENT**: Schedule Math teacher meeting within 1 week
2. Request Math tutoring or intervention plan immediately
3. Check Math assignments - likely missing work or low test scores
4. Review Math concepts from Q1-Q2 that may be foundation issues
5. Consider Math study group or peer tutoring
6. Monitor English 8 in Q4 - if drops to C, intervene
7. Celebrate and study Art success - what made this improve?

## Common Patterns and Meanings

### The "Downward Spiral" (A→B→C→D)
- **Meaning**: Cumulative subject where foundational gaps compound
- **Common in**: Math, Science, Foreign Language
- **Action**: Immediate tutoring, possible need to review earlier material
- **Timeline**: Urgent - each term makes recovery harder

### The "Adjustment Drop" (High→Low Q1, Stable Q2+)
- **Meaning**: Student struggled with new teacher/difficulty, then adapted
- **Common in**: First term of new course level
- **Action**: Monitor to ensure stability continues, praise adaptation
- **Timeline**: Watch for regression, but less urgent

### The "Burnout Pattern" (Stable→Stable→Stable→Drop)
- **Meaning**: Student maintained performance, then fatigued
- **Common in**: Q4 (end of year fatigue) or Q3 (post-winter)
- **Action**: Check workload, stress levels, sleep habits
- **Timeline**: Moderate urgency - prevent complete collapse

### The "Strong Finish" (Low→Low→Higher→High)
- **Meaning**: Slow start but improving, growth mindset in action
- **Common in**: Challenging subjects with engaged student
- **Action**: Celebrate progress, encourage continuation
- **Timeline**: Positive - ensure momentum into next year

### The "Rollercoaster" (Up→Down→Up→Down)
- **Meaning**: Inconsistent effort, test anxiety, or variable grading
- **Common in**: Project-heavy courses, students with executive function challenges
- **Action**: Investigate grading patterns, create consistent study routine
- **Timeline**: Moderate - pattern needs breaking

## When to Use This Skill

- **After each quarter** - Track progression before it's too late
- **Before semester exams** - Identify courses needing study focus
- **Parent-teacher conferences** - Data-driven conversation about trajectory
- **Course selection time** - Understand student's strengths for next year
- **When student reports struggling** - Quantify the concern
- **Year-end review** - Identify summer tutoring needs

## Related Skills

- Use **weekly-report** for current snapshot including grade trends
- Use **action-items** for specific steps to address declining grades
- Combine with **analyze-attendance** to see if absences correlate with grade drops
