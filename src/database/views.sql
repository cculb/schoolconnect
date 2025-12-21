-- PowerSchool Database Views
-- Useful query views for the MCP tools

-- View: Missing Assignments
-- Lists all missing assignments with course and teacher info
CREATE VIEW IF NOT EXISTS v_missing_assignments AS
SELECT
    a.id,
    s.first_name || ' ' || COALESCE(s.last_name, '') AS student_name,
    s.id AS student_id,
    a.course_name,
    a.teacher_name,
    a.assignment_name,
    a.category,
    a.due_date,
    a.term,
    julianday('now') - julianday(a.due_date) AS days_overdue,
    a.recorded_at
FROM assignments a
JOIN students s ON a.student_id = s.id
WHERE a.status = 'Missing'
ORDER BY a.due_date DESC;

-- View: Current Grades
-- Latest grades by student and course
CREATE VIEW IF NOT EXISTS v_current_grades AS
SELECT
    s.id AS student_id,
    s.first_name || ' ' || COALESCE(s.last_name, '') AS student_name,
    c.course_name,
    c.teacher_name,
    c.room,
    g.term,
    g.letter_grade,
    g.percent,
    g.absences,
    g.tardies,
    g.recorded_at
FROM students s
JOIN courses c ON c.student_id = s.id
JOIN grades g ON g.course_id = c.id
WHERE g.recorded_at = (
    SELECT MAX(g2.recorded_at)
    FROM grades g2
    WHERE g2.course_id = c.id AND g2.term = g.term
)
ORDER BY s.first_name, c.course_name, g.term;

-- View: Grade Trends
-- Shows grade progression Q1 -> Q2 -> Q3 -> Q4
CREATE VIEW IF NOT EXISTS v_grade_trends AS
SELECT
    s.id AS student_id,
    s.first_name || ' ' || COALESCE(s.last_name, '') AS student_name,
    c.course_name,
    MAX(CASE WHEN g.term = 'Q1' THEN g.letter_grade END) AS q1,
    MAX(CASE WHEN g.term = 'Q2' THEN g.letter_grade END) AS q2,
    MAX(CASE WHEN g.term = 'S1' THEN g.letter_grade END) AS s1,
    MAX(CASE WHEN g.term = 'Q3' THEN g.letter_grade END) AS q3,
    MAX(CASE WHEN g.term = 'Q4' THEN g.letter_grade END) AS q4,
    MAX(CASE WHEN g.term = 'S2' THEN g.letter_grade END) AS s2
FROM students s
JOIN courses c ON c.student_id = s.id
LEFT JOIN grades g ON g.course_id = c.id
GROUP BY s.id, c.id, s.first_name, s.last_name, c.course_name
ORDER BY s.first_name, c.course_name;

-- View: Attendance Alerts
-- Students with attendance below 90%
CREATE VIEW IF NOT EXISTS v_attendance_alerts AS
SELECT
    s.id AS student_id,
    s.first_name || ' ' || COALESCE(s.last_name, '') AS student_name,
    a.term,
    a.attendance_rate,
    a.days_present,
    a.days_absent,
    a.tardies,
    a.total_days,
    CASE
        WHEN a.attendance_rate < 80 THEN 'critical'
        WHEN a.attendance_rate < 90 THEN 'warning'
        ELSE 'ok'
    END AS alert_level,
    a.recorded_at
FROM students s
JOIN attendance_summary a ON a.student_id = s.id
WHERE a.attendance_rate < 95  -- Show all below 95% for monitoring
ORDER BY a.attendance_rate ASC;

-- View: Upcoming Assignments
-- Assignments due in the next 14 days
CREATE VIEW IF NOT EXISTS v_upcoming_assignments AS
SELECT
    a.id,
    s.first_name || ' ' || COALESCE(s.last_name, '') AS student_name,
    s.id AS student_id,
    a.course_name,
    a.teacher_name,
    a.assignment_name,
    a.category,
    a.due_date,
    julianday(a.due_date) - julianday('now') AS days_until_due,
    a.status,
    a.term
FROM assignments a
JOIN students s ON a.student_id = s.id
WHERE a.due_date >= date('now')
  AND a.due_date <= date('now', '+14 days')
  AND a.status != 'Collected'
ORDER BY a.due_date ASC;

-- View: Assignment Completion Rate
-- Completion rate by student and course
CREATE VIEW IF NOT EXISTS v_assignment_completion_rate AS
SELECT
    s.id AS student_id,
    s.first_name || ' ' || COALESCE(s.last_name, '') AS student_name,
    a.course_name,
    COUNT(*) AS total_assignments,
    SUM(CASE WHEN a.status = 'Collected' THEN 1 ELSE 0 END) AS completed,
    SUM(CASE WHEN a.status = 'Missing' THEN 1 ELSE 0 END) AS missing,
    SUM(CASE WHEN a.status = 'Late' THEN 1 ELSE 0 END) AS late,
    ROUND(100.0 * SUM(CASE WHEN a.status = 'Collected' THEN 1 ELSE 0 END) / COUNT(*), 1) AS completion_rate
FROM assignments a
JOIN students s ON a.student_id = s.id
GROUP BY s.id, a.course_name
ORDER BY completion_rate ASC;

-- View: Student Summary
-- High-level summary for each student
CREATE VIEW IF NOT EXISTS v_student_summary AS
SELECT
    s.id AS student_id,
    s.first_name || ' ' || COALESCE(s.last_name, '') AS student_name,
    s.grade_level,
    s.school_name,
    (SELECT COUNT(DISTINCT course_name) FROM courses WHERE student_id = s.id) AS course_count,
    (SELECT COUNT(*) FROM assignments WHERE student_id = s.id AND status = 'Missing') AS missing_assignments,
    (SELECT attendance_rate FROM attendance_summary WHERE student_id = s.id ORDER BY recorded_at DESC LIMIT 1) AS attendance_rate,
    (SELECT MAX(completed_at) FROM scrape_history WHERE student_id = s.id AND status = 'completed') AS last_sync
FROM students s;

-- View: Action Items
-- Prioritized action items for parents
CREATE VIEW IF NOT EXISTS v_action_items AS
SELECT
    'missing_assignment' AS type,
    'high' AS priority,
    s.id AS student_id,
    s.first_name || ' ' || COALESCE(s.last_name, '') AS student_name,
    'Missing: ' || a.assignment_name || ' (' || a.course_name || ')' AS message,
    'Contact ' || COALESCE(a.teacher_name, 'teacher') || ' about missing ' || a.assignment_name AS suggested_action,
    a.due_date AS relevant_date
FROM assignments a
JOIN students s ON a.student_id = s.id
WHERE a.status = 'Missing'

UNION ALL

SELECT
    'attendance_warning' AS type,
    CASE WHEN att.attendance_rate < 80 THEN 'critical' ELSE 'high' END AS priority,
    s.id AS student_id,
    s.first_name || ' ' || COALESCE(s.last_name, '') AS student_name,
    'Attendance at ' || ROUND(att.attendance_rate, 1) || '% (' || att.days_absent || ' absences)' AS message,
    'Review attendance records and address any patterns' AS suggested_action,
    att.recorded_at AS relevant_date
FROM attendance_summary att
JOIN students s ON att.student_id = s.id
WHERE att.attendance_rate < 90

ORDER BY priority DESC, relevant_date DESC;

-- View: Daily Attendance
-- Lists all daily attendance records with student info
CREATE VIEW IF NOT EXISTS v_daily_attendance AS
SELECT
    s.id AS student_id,
    s.first_name,
    s.last_name,
    s.first_name || ' ' || COALESCE(s.last_name, '') AS student_name,
    ar.date,
    ar.status,
    ar.code,
    ar.period,
    ar.recorded_at
FROM attendance_records ar
JOIN students s ON ar.student_id = s.id
ORDER BY ar.date DESC;

-- View: Attendance Patterns
-- Aggregates attendance by day of week to detect patterns
CREATE VIEW IF NOT EXISTS v_attendance_patterns AS
SELECT
    s.id AS student_id,
    s.first_name,
    s.last_name,
    s.first_name || ' ' || COALESCE(s.last_name, '') AS student_name,
    CASE cast(strftime('%w', ar.date) AS INTEGER)
        WHEN 0 THEN 'Sunday'
        WHEN 1 THEN 'Monday'
        WHEN 2 THEN 'Tuesday'
        WHEN 3 THEN 'Wednesday'
        WHEN 4 THEN 'Thursday'
        WHEN 5 THEN 'Friday'
        WHEN 6 THEN 'Saturday'
    END AS day_name,
    strftime('%w', ar.date) AS day_number,
    SUM(CASE WHEN ar.status IN ('Absent', 'A') THEN 1 ELSE 0 END) AS absence_count,
    SUM(CASE WHEN ar.status IN ('Tardy', 'T') THEN 1 ELSE 0 END) AS tardy_count,
    SUM(CASE WHEN ar.status IN ('Present', 'P', '.') THEN 1 ELSE 0 END) AS present_count,
    SUM(CASE WHEN ar.status IN ('Excused', 'E') THEN 1 ELSE 0 END) AS excused_count,
    COUNT(*) AS total_records,
    ROUND(100.0 * SUM(CASE WHEN ar.status IN ('Present', 'P', '.') THEN 1 ELSE 0 END) / COUNT(*), 1) AS attendance_rate
FROM attendance_records ar
JOIN students s ON ar.student_id = s.id
GROUP BY s.id, strftime('%w', ar.date)
ORDER BY s.first_name, day_number;

-- View: Weekly Attendance Summary
-- Summarizes attendance by week
CREATE VIEW IF NOT EXISTS v_weekly_attendance AS
SELECT
    s.id AS student_id,
    s.first_name || ' ' || COALESCE(s.last_name, '') AS student_name,
    strftime('%Y-%W', ar.date) AS week_key,
    date(ar.date, 'weekday 0', '-6 days') AS week_start,
    SUM(CASE WHEN ar.status IN ('Present', 'P', '.') THEN 1 ELSE 0 END) AS days_present,
    SUM(CASE WHEN ar.status IN ('Absent', 'A') THEN 1 ELSE 0 END) AS days_absent,
    SUM(CASE WHEN ar.status IN ('Tardy', 'T') THEN 1 ELSE 0 END) AS tardies,
    SUM(CASE WHEN ar.status IN ('Excused', 'E') THEN 1 ELSE 0 END) AS excused,
    COUNT(*) AS total_days
FROM attendance_records ar
JOIN students s ON ar.student_id = s.id
GROUP BY s.id, strftime('%Y-%W', ar.date)
ORDER BY week_start DESC;

-- View: Teacher Comments
-- Lists all teacher comments with student and course info
CREATE VIEW IF NOT EXISTS v_teacher_comments AS
SELECT
    tc.id,
    s.id AS student_id,
    s.first_name || ' ' || COALESCE(s.last_name, '') AS student_name,
    tc.course_name,
    tc.course_number,
    tc.expression,
    tc.teacher_name,
    tc.teacher_email,
    tc.term,
    tc.comment,
    tc.recorded_at
FROM teacher_comments tc
JOIN students s ON tc.student_id = s.id
ORDER BY tc.term DESC, tc.course_name;

-- View: Teacher Comments by Term
-- Groups comments by term with counts
CREATE VIEW IF NOT EXISTS v_teacher_comments_by_term AS
SELECT
    s.id AS student_id,
    s.first_name || ' ' || COALESCE(s.last_name, '') AS student_name,
    tc.term,
    COUNT(*) AS comment_count,
    GROUP_CONCAT(tc.course_name, ', ') AS courses_with_comments
FROM teacher_comments tc
JOIN students s ON tc.student_id = s.id
GROUP BY s.id, tc.term
ORDER BY tc.term DESC;
