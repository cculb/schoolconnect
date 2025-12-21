---
description: Generate a comprehensive weekly report for a student including grades, attendance, missing work, and actionable recommendations
---

# Weekly Student Report

Generate a comprehensive weekly summary of a student's academic performance, combining multiple data sources to provide a holistic view of their progress.

## What This Skill Does

This skill creates a detailed weekly report by combining data from multiple MCP tools:

- **generate_weekly_report** - Core report generation with formatted output
- **get_student_summary** - Overview of courses and key metrics
- **get_current_grades** - Current letter grades and percentages across all courses
- **get_missing_assignments** - All incomplete assignments that need attention
- **get_attendance_summary** - Attendance rate, absences, and tardies

The report provides a comprehensive snapshot suitable for weekly parent reviews, progress tracking, or preparing for teacher meetings.

## Report Sections

### 1. Overview
- Total number of courses enrolled
- Count of missing assignments
- Overall attendance rate with status indicator
- Report generation timestamp

### 2. Current Grades
- All courses with letter grades and percentages
- Quick visual scan of academic standing
- Teacher names for each course

### 3. Missing Work
- Detailed list of assignments not yet submitted
- Course and teacher for each assignment
- Due dates to prioritize completion

### 4. Recommended Actions
- Prioritized list of next steps
- Based on data patterns (missing work, grade trends, attendance)
- Actionable items parents can address

## Interpretation Guidance

### Attendance Indicators
- **95%+** (✅) - Excellent attendance, no concerns
- **90-95%** (⚠️) - Warning level, monitor absences
- **Below 90%** (🔴) - Critical concern, intervention needed

### Missing Assignment Thresholds
- **0 assignments** - Excellent, no immediate action needed
- **1-2 assignments** - Monitor, follow up with student
- **3-5 assignments** - High priority, contact teachers recommended
- **6+ assignments** - Critical priority, schedule parent-teacher meetings

### Grade Concern Levels
- **A/B grades** - Performing well, maintain current approach
- **C grades** - Monitor closely, consider additional support
- **D/F grades** - Immediate intervention required, contact teacher

## Example Usage

**Scenario**: Parent wants a weekly update on their student John

**Invocation**:
```
Use the weekly-report skill to generate John's weekly report
```

**Example Output**:
```
# Weekly Report: John
*Generated: 2024-12-20 09:30*

## Overview
- **Courses**: 6
- **Missing Assignments**: 2
- **Attendance**: 94.5% ⚠️

## Current Grades
| Course | Grade |
|--------|-------|
| Math 8 | B (85%) |
| English 8 | A (92%) |
| Science 8 | C (74%) |
| Social Studies | B (88%) |
| PE | A (95%) |
| Art | A (90%) |

## Missing Work
- ❌ Science Lab Report (Science 8)
- ❌ Chapter 5 Quiz (Math 8)

## Recommended Actions
1. Complete Science Lab Report this weekend (due next Monday)
2. Review Math Chapter 5 and take quiz
3. Monitor Science 8 grade - currently at C, needs improvement
4. Consider extra help in Science - grade dropped from B last quarter
5. Follow up on attendance - 3 absences this month approaching warning threshold
```

**Interpretation**:
- Overall solid performance with 4 A/B grades
- **Science concern**: C grade requires attention, dropped from previous term
- **Missing work**: 2 assignments is manageable but should be completed soon
- **Attendance**: At 94.5%, approaching the 95% threshold - monitor carefully
- **Action priority**: Focus on Science grade and completing missing work

## When to Use This Skill

- **Weekly reviews** - Every Sunday evening to plan the week ahead
- **Before parent-teacher conferences** - Get comprehensive context
- **After report cards** - Compare with previous performance
- **When student seems overwhelmed** - Identify specific problem areas
- **Monthly progress tracking** - Spot trends over time

## Related Skills

- Use **analyze-attendance** for deeper attendance pattern analysis
- Use **grade-trends** to see how grades have changed over quarters
- Use **action-items** for immediate priorities without full report context
