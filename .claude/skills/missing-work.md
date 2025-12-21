---
name: missing-work
description: Find all missing assignments for a student, showing which assignments were not turned in and how many days overdue.
whenToUse: User asks about missing assignments, incomplete work, or what needs to be turned in. Triggered by phrases like "missing assignments", "what work is missing", "incomplete homework", "what does [student] need to turn in", or "overdue work".
tags: [student-data, schoolconnect]
---

# Missing Work

## Purpose

Retrieves all missing assignments for a student, providing critical information for catching up:
- Assignment names
- Course and teacher information
- Due dates
- Days overdue calculation
- Prioritization based on how overdue

This is one of the most important skills for identifying immediate action items and preventing grades from dropping.

## How to Use

1. Identify the student name from the user's query
2. Call the `get_missing_assignments` MCP tool with the student's first name
3. Present missing work organized by priority (most overdue first)
4. Suggest immediate actions for each assignment
5. Offer to help contact teachers about make-up opportunities

Special handling:
- Can use "all" to see missing work across all students
- Highlight assignments that are significantly overdue (>7 days)
- Group by teacher if multiple assignments from same course

## Example

**User Query:**
"What assignments is Marcus missing?"

**Assistant Response:**
```
Let me check Marcus's missing assignments...

[Calls get_missing_assignments with student_name: "Marcus"]

Missing Assignments for Marcus:

High Priority (>7 days overdue):
- **Chapter 5 Quiz** (14 days overdue)
  - Course: Algebra II
  - Teacher: Mr. Chen
  - Due: 2024-01-15

Recent:
- **Book Report Draft** (3 days overdue)
  - Course: English 10
  - Teacher: Ms. Johnson
  - Due: 2024-01-26

- **Lab Write-up: Chemical Reactions**
  - Course: Chemistry
  - Teacher: Dr. Martinez
  - Due: 2024-01-28

Recommendations:
1. Contact Mr. Chen about Chapter 5 Quiz - significantly overdue
2. Prioritize finishing the Book Report Draft this weekend
3. Complete Lab Write-up before it becomes overdue

Would you like me to draft an email to Mr. Chen about making up the quiz?
```

## MCP Tools Used

- `get_missing_assignments`: Retrieves all missing (not turned in) assignments for a student. Returns assignment names, courses, teachers, due dates, and calculates days overdue. Accepts student name or "all" for all students.

## Related Skills

- Use `check-grades` to see how missing work impacts grades
- Use teacher communication tools to request make-up opportunities
- Use action items tool for prioritized recommendations
