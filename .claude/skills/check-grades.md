---
name: check-grades
description: Check current grades for a student across all courses, showing letter grades, percentages, and teacher names.
whenToUse: User asks about grades, report card, academic performance in specific courses, or wants to see how student is performing. Triggered by phrases like "what are [student]'s grades", "how is [student] doing in math", "show me grades", or "check report card".
tags: [student-data, schoolconnect]
---

# Check Grades

## Purpose

Retrieves current grades for a student across all enrolled courses, providing:
- Letter grades (A, B, C, D, F or 1-4 scale)
- Percentage scores where available
- Term information (Q1, Q2, S1, Q3, Q4, S2)
- Teacher names for each course

This skill helps parents quickly assess academic performance and identify courses that may need attention.

## How to Use

1. Identify the student name from the user's query
2. Call the `get_current_grades` MCP tool with the student's first name
3. Present grades in a clear table format
4. Highlight any concerning grades (D, F, or low percentages)
5. Offer to provide more details on specific courses if needed

Optional follow-ups:
- Suggest checking missing assignments for courses with low grades
- Offer to show grade trends over time
- Recommend preparing for teacher meetings for struggling courses

## Example

**User Query:**
"What are Sarah's current grades?"

**Assistant Response:**
```
Here are Sarah's current grades:

[Calls get_current_grades with student_name: "Sarah"]

Course                          | Grade      | Term | Teacher
--------------------------------|------------|------|------------------
English 10                      | A (92%)    | Q2   | Ms. Johnson
Algebra II                      | B (85%)    | Q2   | Mr. Chen
Chemistry                       | C (76%)    | Q2   | Dr. Martinez
World History                   | A (94%)    | Q2   | Mr. Thompson
Spanish II                      | B (88%)    | Q2   | Sra. Garcia
PE                             | A (95%)    | Q2   | Coach Davis

Overall: 5 As and Bs, 1 C. Would you like me to:
- Check for missing work in Chemistry
- Show grade trends to see if Chemistry is improving
- Help draft an email to Dr. Martinez
```

## MCP Tools Used

- `get_current_grades`: Retrieves current grades for all courses. Returns letter grades, percentages, terms, course names, and teacher information.

## Related Skills

- Use `missing-work` to identify assignments affecting grades
- Use grade trends tool for historical performance
- Use teacher communication tools to reach out about low grades
