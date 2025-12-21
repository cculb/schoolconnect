---
name: teacher-meeting-prep
description: Prepare talking points and questions for parent-teacher meetings or conferences
whenToUse: User has an upcoming parent-teacher meeting or conference and needs preparation. Triggered by phrases like "prepare for meeting", "parent-teacher conference", "meeting with [teacher]", or "get ready for conference".
tags: [student-data, schoolconnect, communication]
---

# Teacher Meeting Preparation

Prepare for a productive parent-teacher meeting by gathering relevant data about your student's performance in a specific course.

## What This Does

This skill helps you:
- Gather current grade information for the course
- Review missing assignments and completion rates
- Identify specific discussion topics
- Prepare thoughtful questions to ask the teacher

## How to Use

### Basic Usage

Ask Claude to prepare for a meeting with a specific teacher:

```
Prepare me for a meeting with Mrs. Smith about Math
```

```
Help me get ready for a conference about Emma's English class
```

### What You'll Get

The skill uses the `prepare_teacher_meeting` MCP tool to generate:

1. **Teacher Information**
   - Teacher name and contact details
   - Classroom location
   - Email address (if available)

2. **Current Standing**
   - Latest grade and term
   - Total assignments
   - Number of missing assignments

3. **Missing Work to Discuss**
   - List of incomplete assignments
   - Due dates for each item

4. **Suggested Questions**
   - Tailored questions based on your student's situation
   - Questions about skills needed for success
   - Opportunities for makeup work or extra help
   - Resources available for support at home

## Example Questions

The tool automatically suggests relevant questions like:

- What are the most important skills for success in this class?
- Is there an opportunity to make up the missing work?
- How can we better support learning at home?
- What resources are available for extra help?
- Are there any upcoming major projects or tests to prepare for?

## Tips for Success

- **Review before the meeting**: Go through the preparation materials at least a day before
- **Bring specific examples**: The tool provides assignment names and dates you can reference
- **Ask follow-up questions**: Use the suggested questions as a starting point
- **Take notes**: Document action items and commitments during the meeting
- **Follow up**: Use the `draft_teacher_email` tool to send a thank-you note after

## Related Skills

- Use `/draft-teacher-email` to send a follow-up or thank-you email after the meeting
- Use `/communication-suggestions` to identify which teachers you should meet with first
