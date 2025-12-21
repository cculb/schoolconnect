---
name: check-attendance
description: Check attendance records for a student including attendance rate, days present, absences, and tardies.
whenToUse: User asks about attendance, absences, tardiness, or school attendance patterns. Triggered by phrases like "attendance record", "how many days has [student] missed", "attendance rate", "absences", or "tardies".
tags: [student-data, schoolconnect]
---

# Check Attendance

## Purpose

Retrieves attendance information for a student, providing:
- Attendance rate percentage
- Total days present
- Number of absences
- Number of tardies
- Total school days tracked
- Alerts for concerning attendance patterns

This skill helps parents monitor attendance compliance and identify patterns that may affect academic success.

## How to Use

1. Identify the student name from the user's query
2. Call the `get_attendance_summary` MCP tool with the student's first name
3. Present attendance data with context about what is considered good/concerning
4. Flag critical attendance issues (below 80%) or warnings (below 90%)
5. Offer to show detailed daily attendance or pattern analysis if needed

Attendance benchmarks:
- 95%+ : Excellent attendance
- 90-95%: Good, minor concern
- 80-90%: Warning, needs attention
- Below 80%: Critical, may affect academics

## Example

**User Query:**
"How is Tyler's attendance this year?"

**Assistant Response:**
```
Let me check Tyler's attendance record...

[Calls get_attendance_summary with student_name: "Tyler"]

Attendance Summary for Tyler:

- Attendance Rate: 92.3%
- Days Present: 142
- Days Absent: 11
- Tardies: 3
- Total School Days: 154

Status: GOOD - Attendance is above 90%, but there's room for improvement.

Note: Attendance below 95% may start affecting academic performance. Tyler has missed 11 days so far this year.

Would you like me to:
- Show daily attendance records to identify patterns
- Analyze which days of the week have the most absences
- Compare to recommended attendance thresholds
```

**Example with Warning:**

**User Query:**
"Check Emma's attendance"

**Assistant Response:**
```
[Calls get_attendance_summary with student_name: "Emma"]

Attendance Summary for Emma:

- Attendance Rate: 87.5%
- Days Present: 135
- Days Absent: 18
- Tardies: 7
- Total School Days: 154

WARNING: Attendance is below 90%. This may affect academic progress.

Recommendations:
1. Review attendance patterns to identify chronic absence days
2. Discuss any underlying issues (illness, transportation, etc.)
3. Consider meeting with school counselor about support options

Would you like me to show which days of the week Emma is most often absent?
```

## MCP Tools Used

- `get_attendance_summary`: Retrieves attendance summary including rate percentage, days present, absences, tardies, and total school days. Provides alerts for attendance below 95%.

## Related Skills

- Use daily attendance tool to see specific dates and patterns
- Use attendance patterns tool to identify concerning trends (e.g., "always absent Mondays")
- Use action items tool for attendance-related recommendations
