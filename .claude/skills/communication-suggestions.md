---
name: communication-suggestions
description: Get AI-driven suggestions on when and why to contact teachers based on student data including missing work, grade trends, and attendance patterns
whenToUse: User asks who to contact, which teachers to email, or needs communication priorities. Triggered by phrases like "who should I contact", "communication suggestions", "which teachers", or "should I email anyone".
tags: [communication, schoolconnect, analytics]
---

# Communication Suggestions

Get intelligent, data-driven recommendations on which teachers to contact and why, prioritized by urgency.

## What This Does

This skill analyzes your student's academic data to identify:
- Teachers who should be contacted about specific concerns
- Priority level for each communication (HIGH, MEDIUM, LOW)
- Specific reasons for reaching out (missing work, low grades, attendance)
- Suggested communication topics

## How to Use

### Basic Usage

Ask Claude for communication recommendations:

```
Should I contact any of Emma's teachers?
```

```
Who do I need to reach out to about John's schoolwork?
```

```
Give me communication suggestions for all my students
```

### What You'll Get

The `get_communication_suggestions` MCP tool provides:

1. **Prioritized Recommendations**
   - HIGH priority: Urgent issues requiring immediate attention
   - MEDIUM priority: Concerns worth addressing soon
   - LOW priority: Optional check-ins or positive communications

2. **Specific Reasons**
   - Number of missing assignments per teacher
   - Current grade concerns (D or F grades)
   - Attendance rate issues
   - Course-specific patterns

3. **Suggested Topics**
   - `missing_work` - For teachers with multiple missing assignments
   - `grade_concern` - For courses with low grades
   - `general` - For check-ins or thank-you messages

4. **Action Details**
   - Assignment names for missing work discussions
   - Specific grade information for academic concerns

## Priority Levels Explained

### HIGH Priority (🔴)

Immediate action recommended:
- **3+ missing assignments** with one teacher
- **Grade of F** in any course
- **Multiple concerning patterns** (missing work + low grade)

Contact these teachers within 1-2 days.

### MEDIUM Priority (🟡)

Action recommended within a week:
- **1-2 missing assignments** with one teacher
- **Grade of D** in any course
- **Attendance rate below 90%** (contact counselor/admin)
- **Declining grade trend** (was B, now C)

Contact these teachers within 3-5 days.

### LOW Priority

Optional communications:
- **All assignments complete, good grades** - Consider thank-you notes
- **Improved performance** - Acknowledge teacher's support
- **Upcoming curriculum questions** - Proactive engagement

Contact when convenient or during regular check-ins.

## Data Sources Analyzed

The tool examines:

1. **Missing Assignments** (via `get_missing_assignments`)
   - Groups by teacher
   - Counts missing items per class
   - Identifies overdue work

2. **Current Grades** (via `get_current_grades`)
   - Flags grades of D, F, or 1-2 (standards-based)
   - Identifies courses needing attention

3. **Attendance Summary** (via `get_attendance_summary`)
   - Checks attendance rate
   - Suggests counselor contact if below 90%

4. **Grade Trends** (via `get_grade_trends`)
   - Identifies declining performance
   - Highlights improvement opportunities

## Example Output

### When There Are Concerns

```
## Communication Suggestions for Emma

### Recommended Outreach

🔴 **HIGH**: Contact **Mrs. Smith**
   - Topic: Missing Work
   - Reason: 4 missing assignment(s)
   - Details: Homework 1, Quiz 2, Project Draft, Reading Log

🟡 **MEDIUM**: Contact **Mr. Johnson**
   - Topic: Grade Concern
   - Reason: Grade of D in Mathematics
```

### When Everything Looks Good

```
## Communication Suggestions for Emma

✅ **No urgent communications needed!**

Everything looks good. Consider reaching out for:
- Regular check-ins with teachers
- Thank-you notes for positive experiences
- Questions about upcoming projects or curriculum
```

## Using Suggestions Effectively

### For HIGH Priority Items

1. **Act quickly**: Contact within 1-2 days
2. **Use draft-teacher-email**: Generate professional email about the topic
3. **Be specific**: Reference the exact assignments or grades mentioned
4. **Seek solutions**: Ask about makeup opportunities or support strategies

### For MEDIUM Priority Items

1. **Schedule communication**: Plan to reach out within the week
2. **Gather context**: Review course details with `get_course_score_details`
3. **Prepare questions**: Think about what you want to learn
4. **Consider timing**: Avoid Friday afternoons or busy periods

### For Positive Communications

1. **Express appreciation**: Teachers value recognition
2. **Be specific**: Mention what your student enjoys about the class
3. **Keep it brief**: A short, genuine thank-you is meaningful
4. **Timing**: Send after a positive event (good grade, successful project)

## Automation and Proactive Monitoring

### Regular Check-ins

Run this skill weekly to stay ahead of issues:

```
Every Monday: "Give me communication suggestions for Emma"
```

This helps you:
- Catch problems early before they escalate
- Build positive relationships with teachers
- Stay informed about academic progress

### Combining with Other Skills

**Workflow Example:**

1. **Get suggestions**: `/communication-suggestions` to identify who to contact
2. **Gather details**: `/teacher-meeting-prep` for specific course data
3. **Draft email**: `/draft-teacher-email` to compose message
4. **Send and track**: Copy draft to email, send, note in calendar

## Understanding "No Suggestions"

If the tool reports no urgent communications:

- **This is good news!** Your student is on track
- Consider proactive positive communications
- Schedule optional check-ins with teachers
- Ask about upcoming projects or curriculum

Don't wait for problems - positive parent-teacher relationships help prevent issues.

## Related Skills

- Use `/draft-teacher-email` to compose messages for suggested contacts
- Use `/teacher-meeting-prep` to prepare for in-person conferences
- Use `get_teacher_profile` to look up contact information

## Customization

You can ask for filtered suggestions:

```
Are there any high-priority teachers I should contact?
```

```
Which teachers should I thank for Emma's progress?
```

```
Show me only missing work communication suggestions
```
