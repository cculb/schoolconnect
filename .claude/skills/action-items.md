---
name: action-items
description: Get prioritized, actionable next steps for parents based on missing assignments, attendance concerns, and grade issues
whenToUse: User asks for action items, priorities, next steps, or what to do about academic concerns. Triggered by phrases like "what should I do", "action items", "priorities", "next steps", or "what needs attention".
tags: [student-data, schoolconnect, analytics]
---

# Prioritized Action Items

Get a focused, prioritized list of specific actions parents should take based on current student data. Cuts through the noise to identify what matters most right now.

## What This Skill Does

This skill synthesizes multiple data sources into actionable priorities using these MCP tools:

- **get_action_items** - Core prioritization engine combining multiple concerns
- **get_missing_assignments** - Identifies incomplete work requiring immediate attention
- **get_attendance_summary** - Flags attendance dropping below acceptable thresholds
- **get_grade_trends** - Identifies courses with declining performance

The output is a ranked list of specific actions, not just observations. Each item includes the issue, priority level, and suggested concrete steps.

## How Actions Are Prioritized

### Priority Levels

**🔴 HIGH/CRITICAL Priority**:
- Failing grades (D or F)
- 5+ missing assignments in any course
- Attendance below 85%
- Grade dropped 2+ letter grades in one term
- Assignment more than 2 weeks overdue

**🟡 MEDIUM Priority**:
- Grades at C level
- 3-4 missing assignments
- Attendance 85-90%
- Grade dropped 1 letter grade
- Assignment 1-2 weeks overdue
- Teacher requested meeting

**🟢 LOW Priority**:
- 1-2 missing assignments
- Attendance 90-95%
- Upcoming assignment due soon
- Positive teacher comments to acknowledge
- Grade improvement to celebrate

### Prioritization Logic

Actions are ordered by:
1. **Urgency** - Time-sensitive items first (deadlines, critical thresholds)
2. **Impact** - Issues affecting grade/promotion/eligibility before minor concerns
3. **Actionability** - Things parent can directly address before passive monitoring
4. **Dependencies** - Foundational issues before symptoms (e.g., attendance before grade concerns)

## Action Item Format

Each action item includes:

- **Priority indicator** (🔴/🟡/🟢)
- **Issue description** - What the concern is
- **Context** - Relevant details (course, teacher, deadline)
- **Suggested action** - Specific next step to take
- **Timeline** - When to act (immediately, this week, etc.)

## Interpretation Guidance

### Missing Assignment Thresholds
- **1-2 missing** - Low priority, student can likely catch up independently
- **3-4 missing** - Medium priority, parent check-in recommended
- **5-6 missing** - High priority, teacher contact suggested
- **7+ missing** - Critical priority, immediate teacher meeting required

### Attendance Alert Levels
- **Below 95%** - Appears on action list as monitoring item
- **Below 90%** - Medium priority, create attendance improvement plan
- **Below 85%** - High priority, school meeting required
- **Below 80%** - Critical, may affect academic eligibility or promotion

### Grade Concern Urgency
- **Drop to C** - Medium priority if student usually earns A/B
- **Drop to D** - High priority, failing risk
- **Drop to F** - Critical, immediate intervention
- **2+ grade drop** - Escalate priority by one level regardless of current grade

### Timeline Guidance
- **"Immediately"** - Within 24 hours (failing grade, critical attendance)
- **"This week"** - Within 3-5 days (high priority items)
- **"Soon"** - Within 1-2 weeks (medium priority items)
- **"Monitor"** - Ongoing observation (low priority items)

## Example Usage

**Scenario**: Parent opens the app and wants to know "what do I need to do right now?"

**Invocation**:
```
Use the action-items skill to get prioritized actions for Sarah
```

**Example Output**:
```
## Action Items for Sarah

🔴 **[HIGH]** Sarah has 6 missing assignments in Science 8
   → Contact Ms. Johnson to discuss make-up plan for missing labs
   Timeline: This week

🔴 **[HIGH]** Math grade dropped from B to D in Q3 (2 letter grades)
   → Schedule meeting with Mr. Chen to understand grade drop and intervention options
   Timeline: Immediately

🟡 **[MEDIUM]** Attendance at 89% (below 90% threshold)
   → Review recent absences, ensure future appointments scheduled outside school hours
   Timeline: This week

🟡 **[MEDIUM]** 3 assignments due next week
   → Check with Sarah on progress: Chapter 7 Essay (English), Lab Report (Science), Math Quiz
   Timeline: This weekend

🟢 **[LOW]** English grade improved from C to B
   → Acknowledge improvement with Sarah, ask what study strategies worked
   Timeline: Soon
```

**Interpretation**:
- **Two critical issues** requiring immediate attention (6 missing assignments, major grade drop)
- **Science concern** is quantified (6 assignments) with specific teacher contact
- **Math concern** is severe (2-grade drop to D = failing risk) and marked urgent
- **Attendance** flagged as approaching concerning threshold (89% vs 90% warning level)
- **Upcoming work** proactively identified to prevent future missing assignments
- **Positive recognition** included to balance concerns and motivate student

**Recommended Approach**:
1. **Today**: Email/call Mr. Chen about Math grade drop (most urgent - near failing)
2. **Tomorrow**: Email Ms. Johnson about Science missing work plan
3. **This weekend**: Sit with Sarah to review upcoming assignments and attendance pattern
4. **Next week**: If attendance doesn't improve to 90%+, contact school counselor

## Action Types and Suggested Steps

### Missing Assignment Actions
- **1-2 missing**: "Check with [student] on completion plan"
- **3-4 missing**: "Email [teacher] to confirm assignments and due dates"
- **5+ missing**: "Schedule meeting with [teacher] to discuss make-up plan and identify barriers"
- **Overdue 2+ weeks**: "Request partial credit opportunity or alternative assignment"

### Grade Concern Actions
- **C grade**: "Monitor next 2 weeks, consider study skills support"
- **D grade**: "Contact [teacher] this week for intervention plan"
- **F grade**: "Schedule immediate meeting with [teacher] and counselor"
- **2+ grade drop**: "Request detailed grade breakdown, identify specific weak areas"

### Attendance Actions
- **Below 95%**: "Review absence log, identify patterns"
- **Below 90%**: "Create attendance improvement plan, reduce discretionary absences"
- **Below 85%**: "Meet with school attendance officer, may need documentation"
- **Below 80%**: "Urgent school meeting, may affect promotion/eligibility"

### Upcoming Assignment Actions
- **Due in 3-5 days**: "Verify [student] has started, materials available"
- **Due in 1-2 days**: "Check progress, help identify obstacles"
- **Due tomorrow**: "Review draft/prep if possible, ensure timely submission"

### Teacher Communication Actions
- **Positive report**: "Thank teacher, ask how to maintain success"
- **Concern raised**: "Schedule call/meeting to discuss and create plan"
- **No recent contact**: "Send check-in email for mid-term update"

## When to Use This Skill

- **Daily check** - Busy parents who want quick "to-do" list
- **Weekly planning** - Sunday evening prep for the week ahead
- **After data updates** - When grades or assignments are posted
- **Feeling overwhelmed** - Cut through data to see what matters most
- **Before teacher meetings** - Know what to prioritize in conversation
- **After report cards** - Immediate next steps from grade reports

## Filtering Actions

You can filter to specific students:
- **"all" student name** - Get action items across all children (useful for multi-child families)
- **Specific student** - Focus on one child's priorities

For multiple children, actions are grouped by student and still prioritized by urgency across the family.

## What's NOT Included

This skill focuses on **actionable** items, so it excludes:
- ✗ General observations without action ("Student is doing okay")
- ✗ Information items ("Semester ends Dec 20")
- ✗ Historical data ("Last quarter grade was B")
- ✓ Only items requiring parent decision or action

## Related Skills

- Use **weekly-report** for comprehensive context behind action items
- Use **grade-trends** to understand why a grade concern made the action list
- Use **analyze-attendance** for deeper investigation of attendance action items
