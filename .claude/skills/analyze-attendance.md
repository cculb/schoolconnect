---
name: analyze-attendance
description: Analyze attendance patterns including day-of-week trends, streaks, and identify concerning patterns requiring intervention
whenToUse: User asks for attendance analysis, pattern identification, or chronic absence concerns. Triggered by phrases like "attendance patterns", "when is [student] usually absent", "analyze attendance", or "attendance trends".
tags: [student-data, schoolconnect, analytics]
---

# Analyze Attendance Patterns

Perform deep analysis of student attendance patterns to identify trends, problem days, and concerning behaviors that may impact academic performance.

## What This Skill Does

This skill provides comprehensive attendance analysis by combining multiple MCP tools:

- **get_attendance_patterns** - Day-of-week analysis and attendance streaks
- **get_attendance_summary** - Overall attendance rate and totals
- **get_daily_attendance** - Detailed daily records for context

The analysis identifies patterns that may not be obvious from raw numbers alone, such as "frequently absent on Mondays" or extended absence streaks.

## Analysis Components

### 1. Overall Attendance Metrics
- Attendance rate percentage
- Total days present vs absent
- Tardy count
- Total school days recorded

### 2. Current Status & Streaks
- Current streak type (present or absent)
- Current streak length in days
- Longest present streak (shows best performance period)
- Longest absent streak (identifies concerning patterns)

### 3. Day-of-Week Breakdown
- Attendance statistics for each weekday (Monday-Friday)
- Present, absent, and tardy counts per day
- Attendance rate calculated per day
- Identifies problem days with high absence rates

### 4. Pattern Recognition
- Days with concerning absence patterns (20%+ absence rate)
- Frequency analysis (e.g., "3 out of 8 Mondays absent")
- Ranked list of problematic days

## Interpretation Guidance

### Attendance Rate Thresholds
- **95-100%** - Excellent attendance, no concerns
- **90-95%** - Warning level, monitor for patterns
- **85-90%** - Concerning, intervention suggested
- **Below 85%** - Critical, immediate intervention required
- **Below 80%** - Severe concern, may impact academic eligibility

### Streak Analysis
- **Present streak 10+ days** - Positive momentum, encourage continuation
- **Present streak 20+ days** - Excellent consistency, celebrate achievement
- **Absent streak 2+ days** - Needs attention, check for illness or issues
- **Absent streak 3+ days** - High priority concern, contact school
- **Absent streak 5+ days** - Critical, may require medical documentation

### Day-of-Week Patterns
- **20%+ absences on specific day** - Clear pattern, investigate cause
- **30%+ absences on specific day** - Strong pattern requiring intervention
- **Multiple problem days** - Systemic issue, needs comprehensive plan
- **Monday/Friday patterns** - May indicate weekend-related issues
- **Mid-week patterns** - May indicate specific class or social concerns

### Tardy Patterns
- **1-3 tardies per month** - Minor concern, remind about punctuality
- **4-6 tardies per month** - Moderate concern, identify morning routine issues
- **7+ tardies per month** - Significant concern, develop improvement plan
- **Tardies on same day of week** - Pattern suggests specific obstacle

## Example Usage

**Scenario**: Parent notices their student has been absent frequently and wants to understand the pattern

**Invocation**:
```
Use the analyze-attendance skill to analyze Emma's attendance patterns
```

**Example Output**:
```
## Attendance Patterns for Emma

### Current Status
Currently on a **3-day absence streak**

- Longest present streak: 15 days
- Longest absence streak: 5 days

### By Day of Week

| Day | Present | Absent | Tardy | Rate |
|-----|---------|--------|-------|------|
| Monday | 6 | 4 | 1 | 60% |
| Tuesday | 9 | 1 | 0 | 90% |
| Wednesday | 10 | 0 | 0 | 100% |
| Thursday | 8 | 2 | 1 | 80% |
| Friday | 7 | 3 | 0 | 70% |

### Concerning Patterns

- Frequently absent on **Monday**: 4/10 (40%)
- Frequently absent on **Friday**: 3/10 (30%)

**Overall Attendance Rate**: 87.2%
```

**Interpretation**:
- **Critical finding**: Strong Monday pattern (40% absence rate) suggests weekend transition difficulty or Sunday night illness pattern
- **Secondary pattern**: Friday absences (30%) may indicate end-of-week fatigue or early weekend departures
- **Current concern**: 3-day absence streak requires immediate follow-up with student/family
- **Historical concern**: Previous 5-day absence streak suggests this is recurring behavior
- **Overall rate**: 87.2% is concerning (below 90% threshold) and requires intervention
- **Action items**:
  1. Contact family about current 3-day absence
  2. Discuss Monday absence pattern - is there a recurring Sunday night issue?
  3. Create plan to improve attendance to at least 95%
  4. Consider if specific classes or activities on Monday/Friday are factors

## Pattern-Based Recommendations

### Monday/Friday Pattern
**Likely causes**:
- Weekend activities interfering with sleep schedule
- Chronic illness that worsens over weekends
- Family commitments or travel
- Anxiety about start/end of week

**Recommended actions**:
- Establish consistent weekend sleep schedule
- Limit Sunday night activities
- Discuss weekend plans with student
- Consider if Monday morning classes are particularly challenging

### Mid-Week Pattern (Tuesday-Thursday)
**Likely causes**:
- Specific class difficulty or avoidance
- Social issues (bullying, peer conflict)
- Extracurricular scheduling conflicts
- Medical appointments

**Recommended actions**:
- Review class schedule for those days
- Check for social concerns
- Consolidate medical appointments to one day if possible
- Talk with student about specific day concerns

### Scattered Pattern (No Clear Day-of-Week)
**Likely causes**:
- Chronic illness (asthma, allergies, migraines)
- Mental health challenges
- Transportation inconsistencies
- Family instability

**Recommended actions**:
- Medical evaluation if health-related
- Counseling support if mental health-related
- Work with school on transportation solutions
- Connect family with support services

### High Tardy Rate
**Likely causes**:
- Morning routine challenges
- Transportation timing issues
- Sleep difficulties
- First period anxiety

**Recommended actions**:
- Earlier bedtime and wake-up time
- Prepare materials night before
- Adjust transportation schedule
- Consider breakfast at school program

## When to Use This Skill

- **Monthly attendance reviews** - Proactively monitor patterns
- **After receiving attendance warnings** - Understand root causes
- **Before school meetings** - Have data-driven conversation
- **When student complaints increase** - Correlate with attendance
- **Term/semester planning** - Identify improvement opportunities
- **After illness recovery** - Ensure return to normal patterns

## Related Skills

- Use **weekly-report** for attendance in context of overall performance
- Use **action-items** to get specific steps for attendance improvement
- Combine with **grade-trends** to see if absences correlate with grade drops
