---
name: draft-teacher-email
description: Draft professional, courteous emails to teachers about various topics including missing work, grade concerns, meeting requests, or general check-ins
whenToUse: User asks to draft an email, write to a teacher, or compose a message. Triggered by phrases like "draft email", "write to teacher", "email Mr./Mrs. [Name]", or "compose message".
tags: [communication, schoolconnect]
---

# Draft Teacher Email

Generate professional, well-structured email drafts for communicating with your student's teachers.

## What This Does

This skill helps you compose appropriate, respectful emails to teachers about:
- Missing assignments and makeup work opportunities
- Grade concerns and academic support
- Requesting parent-teacher conferences
- General check-ins and thank-you messages

All drafts follow professional parent-teacher communication standards.

## How to Use

### Basic Usage

Ask Claude to draft an email about a specific topic:

```
Draft an email to Mr. Johnson about Emma's missing assignments
```

```
Write an email to Mrs. Chen requesting a meeting about Math
```

```
Help me write a thank-you email to the science teacher
```

### Email Topics

The skill supports four main topics:

1. **missing_work** - About incomplete assignments
2. **grade_concern** - Discussing low grades or academic progress
3. **meeting_request** - Requesting a parent-teacher conference
4. **general** - Check-ins, thank-you notes, or other communications

### What You'll Get

The `draft_teacher_email` MCP tool generates:

1. **Email Header**
   - Teacher's email address (if available)
   - Professional subject line

2. **Email Body**
   - Formal greeting (e.g., "Dear Mrs. Smith")
   - Context-appropriate opening
   - Specific details about your concern (grades, missing work, etc.)
   - Clear questions or requests
   - Professional closing (e.g., "Best regards")

3. **Customization Note**
   - Reminder that this is a draft for editing
   - Placeholder for parent name

## Professional Tone Guidelines

All generated emails follow these principles:

### Do's
- Use formal greetings: "Dear Mr./Mrs./Ms. [Name]"
- Express appreciation for the teacher's time and dedication
- Be specific about concerns or questions
- Offer to collaborate and support learning at home
- Close professionally: "Best regards," "Thank you," "Sincerely"
- Keep tone respectful and courteous

### Don'ts
- Avoid accusatory language
- Don't make demands
- Never use casual greetings like "Hey" or "Hi there"
- Don't write in anger or frustration
- Avoid overly lengthy explanations

## Example Email Structure

### Missing Work Email

```
Subject: Regarding Emma's Missing Assignment(s)

Dear Mrs. Smith,

I hope this email finds you well. I am writing regarding my child Emma's
missing assignment(s) in your class.

I understand the following assignment(s) are currently marked as missing:
- Assignment 1 (due: 2024-01-15)
- Assignment 2 (due: 2024-01-18)

I wanted to reach out to discuss how we can help Emma get caught up. Is
there an opportunity for the work to be submitted late, or would you
recommend an alternative approach?

Please let me know if there's anything we can do at home to better support
Emma's progress in your class.

Thank you for your time and dedication to your students.

Best regards,
[Parent Name]
```

### Grade Concern Email

```
Subject: Checking in on Emma's Progress

Dear Mr. Johnson,

I hope this message finds you well. I wanted to reach out to discuss Emma's
current progress in your class.

I noticed that Emma's current grade is C, and I wanted to better understand
what areas might need improvement and how we can support their learning at
home.

Could you share any insights on:
- Specific areas where Emma could improve
- Study strategies that might be helpful
- Any upcoming assignments or tests to focus on

I appreciate your guidance and partnership in Emma's education.

Thank you,
[Parent Name]
```

## Tips for Using Drafts

1. **Review and edit**: Always read through and personalize the draft
2. **Add your name**: Replace `[Parent Name]` with your actual name
3. **Check timing options**: For meeting requests, add specific available times
4. **Add custom context**: Include any additional details the tool didn't capture
5. **Proofread**: Check for spelling and grammar before sending
6. **Save a copy**: Keep a record of sent emails for follow-up

## Adding Custom Context

You can provide additional context when requesting a draft:

```
Draft an email to Mrs. Chen about missing work. Mention that Emma was sick
last week and we want to understand the makeup policy.
```

The tool will incorporate your custom message into the appropriate section of the email.

## Related Skills

- Use `/teacher-meeting-prep` before requesting a meeting to gather talking points
- Use `/communication-suggestions` to identify which teachers need communication
- Check `get_teacher_profile` to verify teacher contact information

## Email Topic Reference

### missing_work
When to use: Student has incomplete assignments
Includes: List of missing items, due dates, request for makeup opportunities

### grade_concern
When to use: Grade is lower than expected, want to understand how to improve
Includes: Current grade, request for improvement strategies, partnership offer

### meeting_request
When to use: Need to schedule a face-to-face or virtual conference
Includes: Request for meeting, suggested times (you fill in), flexible scheduling

### general
When to use: Check-ins, thank-you notes, positive updates, or general questions
Includes: Friendly opening, your custom message, offer to support learning
