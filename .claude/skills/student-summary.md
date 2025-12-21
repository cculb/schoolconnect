---
name: student-summary
description: Fetch a comprehensive summary of a student's academic status including courses, missing assignments, and attendance rate.
whenToUse: User asks for an overview, summary, or general status of a student's academic performance. Triggered by phrases like "how is [student] doing", "student summary", "give me an overview of [student]", or "status update".
tags: [student-data, schoolconnect]
---

# Student Summary

## Purpose

Provides a high-level overview of a student's current academic status by fetching:
- Number of courses enrolled
- Count of missing assignments
- Attendance rate percentage
- Recent action items requiring attention

This is useful as a starting point for understanding a student's overall performance before diving into specific areas like grades, assignments, or attendance details.

## How to Use

1. Identify the student name from the user's query
2. Call the `get_student_summary` MCP tool with the student's first name
3. Present the summary in a clear, parent-friendly format
4. Offer to drill down into specific areas if needed (grades, missing work, attendance)

Special handling:
- Use student's first name (e.g., "John")
- Can use "all" to get summaries for all students
- If no student specified, default to "all"

## Example

**User Query:**
"How is Emily doing in school?"

**Assistant Response:**
```
Let me get Emily's current status...

[Calls get_student_summary with student_name: "Emily"]

Emily's Summary:
- Enrolled in 7 courses
- 3 missing assignments
- Attendance rate: 94.2%

Would you like me to:
- Check her current grades
- Review the missing assignments
- Look at attendance details
```

## MCP Tools Used

- `get_student_summary`: Retrieves comprehensive student summary including course count, missing assignments, and attendance rate. Accepts student name or "all" for all students.

## Related Skills

- Use `check-grades` to see detailed grade information
- Use `missing-work` to review specific missing assignments
- Use `check-attendance` for detailed attendance records
