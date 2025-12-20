-- PowerSchool Parent Portal Database Views
-- Useful pre-built queries for common operations

-- Missing assignments (no date filter - show all missing)
CREATE VIEW IF NOT EXISTS v_missing_assignments AS
SELECT 
    s.student_id,
    s.first_name || ' ' || s.last_name as student_name,
    c.course_id,
    c.course_name,
    c.teacher_name,
    c.teacher_email,
    a.assignment_id,
    a.assignment_name,
    a.category,
    a.due_date,
    CAST(julianday('now') - julianday(a.due_date) AS INTEGER) as days_overdue
FROM assignments a
JOIN students s ON a.student_id = s.student_id
JOIN courses c ON a.course_id = c.course_id
WHERE a.status = 'Missing'
ORDER BY a.due_date DESC;

-- Current grades by student (latest recorded term)
CREATE VIEW IF NOT EXISTS v_current_grades AS
SELECT 
    s.student_id,
    s.first_name || ' ' || s.last_name as student_name,
    c.course_id,
    c.course_name,
    c.teacher_name,
    c.room,
    g.term,
    g.letter_grade,
    g.percent,
    g.gpa_points,
    g.recorded_at
FROM grades g
JOIN students s ON g.student_id = s.student_id
JOIN courses c ON g.course_id = c.course_id
WHERE g.recorded_at = (
    SELECT MAX(g2.recorded_at) 
    FROM grades g2 
    WHERE g2.student_id = g.student_id 
    AND g2.course_id = g.course_id
    AND g2.term = g.term
)
ORDER BY s.last_name, c.course_name;

-- Grade trends (compare across terms)
CREATE VIEW IF NOT EXISTS v_grade_trends AS
SELECT 
    s.student_id,
    s.first_name || ' ' || s.last_name as student_name,
    c.course_id,
    c.course_name,
    MAX(CASE WHEN g.term = 'Q1' THEN g.letter_grade END) as Q1,
    MAX(CASE WHEN g.term = 'Q2' THEN g.letter_grade END) as Q2,
    MAX(CASE WHEN g.term = 'Q3' THEN g.letter_grade END) as Q3,
    MAX(CASE WHEN g.term = 'Q4' THEN g.letter_grade END) as Q4,
    MAX(CASE WHEN g.term = 'S1' THEN g.letter_grade END) as S1,
    MAX(CASE WHEN g.term = 'S2' THEN g.letter_grade END) as S2
FROM grades g
JOIN students s ON g.student_id = s.student_id
JOIN courses c ON g.course_id = c.course_id
GROUP BY s.student_id, c.course_id;

-- Attendance alerts (students with attendance issues)
CREATE VIEW IF NOT EXISTS v_attendance_alerts AS
SELECT 
    s.student_id,
    s.first_name || ' ' || s.last_name as student_name,
    s.grade_level,
    a.term,
    a.attendance_rate,
    a.days_absent,
    a.days_absent_excused,
    a.days_absent_unexcused,
    a.tardies,
    CASE 
        WHEN a.attendance_rate < 90 THEN 'Critical'
        WHEN a.attendance_rate < 95 THEN 'Warning'
        ELSE 'Good'
    END as alert_level
FROM attendance_summary a
JOIN students s ON a.student_id = s.student_id
WHERE a.term = 'YTD'
ORDER BY a.attendance_rate ASC;

-- Assignment completion rate by course
CREATE VIEW IF NOT EXISTS v_assignment_completion AS
SELECT 
    s.student_id,
    s.first_name || ' ' || s.last_name as student_name,
    c.course_id,
    c.course_name,
    c.teacher_name,
    COUNT(*) as total_assignments,
    SUM(CASE WHEN a.status = 'Collected' THEN 1 ELSE 0 END) as completed,
    SUM(CASE WHEN a.status = 'Missing' THEN 1 ELSE 0 END) as missing,
    SUM(CASE WHEN a.status = 'Late' THEN 1 ELSE 0 END) as late,
    SUM(CASE WHEN a.status = 'Exempt' THEN 1 ELSE 0 END) as exempt,
    ROUND(100.0 * SUM(CASE WHEN a.status = 'Collected' THEN 1 ELSE 0 END) / COUNT(*), 1) as completion_rate
FROM assignments a
JOIN students s ON a.student_id = s.student_id
JOIN courses c ON a.course_id = c.course_id
GROUP BY s.student_id, c.course_id
ORDER BY completion_rate ASC;

-- Upcoming assignments (next 14 days)
CREATE VIEW IF NOT EXISTS v_upcoming_assignments AS
SELECT 
    s.student_id,
    s.first_name || ' ' || s.last_name as student_name,
    c.course_id,
    c.course_name,
    c.teacher_name,
    a.assignment_id,
    a.assignment_name,
    a.category,
    a.due_date,
    CAST(julianday(a.due_date) - julianday('now') AS INTEGER) as days_until_due
FROM assignments a
JOIN students s ON a.student_id = s.student_id
JOIN courses c ON a.course_id = c.course_id
WHERE a.due_date >= date('now')
AND a.due_date <= date('now', '+14 days')
AND a.status NOT IN ('Collected', 'Exempt')
ORDER BY a.due_date;

-- Recent scores (assignments graded in last 7 days)
CREATE VIEW IF NOT EXISTS v_recent_scores AS
SELECT 
    s.student_id,
    s.first_name || ' ' || s.last_name as student_name,
    c.course_id,
    c.course_name,
    a.assignment_id,
    a.assignment_name,
    a.category,
    a.score,
    a.max_score,
    a.percent,
    a.letter_grade,
    a.recorded_at
FROM assignments a
JOIN students s ON a.student_id = s.student_id
JOIN courses c ON a.course_id = c.course_id
WHERE a.recorded_at >= datetime('now', '-7 days')
AND a.score IS NOT NULL
ORDER BY a.recorded_at DESC;

-- Student summary view (aggregated stats per student)
CREATE VIEW IF NOT EXISTS v_student_summary AS
SELECT 
    s.student_id,
    s.first_name,
    s.last_name,
    s.first_name || ' ' || s.last_name as student_name,
    s.grade_level,
    s.school_name,
    (SELECT COUNT(*) FROM courses c WHERE c.student_id = s.student_id) as course_count,
    (SELECT COUNT(*) FROM assignments a WHERE a.student_id = s.student_id AND a.status = 'Missing') as missing_assignments,
    (SELECT attendance_rate FROM attendance_summary WHERE student_id = s.student_id AND term = 'YTD') as attendance_rate,
    (SELECT AVG(gpa_points) FROM grades g WHERE g.student_id = s.student_id AND gpa_points IS NOT NULL) as avg_gpa
FROM students s;

-- Course summary with latest grade
CREATE VIEW IF NOT EXISTS v_course_summary AS
SELECT 
    c.course_id,
    c.course_name,
    c.expression,
    c.room,
    c.term,
    c.teacher_name,
    c.teacher_email,
    c.student_id,
    s.first_name || ' ' || s.last_name as student_name,
    (
        SELECT g.letter_grade 
        FROM grades g 
        WHERE g.course_id = c.course_id 
        ORDER BY g.recorded_at DESC 
        LIMIT 1
    ) as current_grade,
    (
        SELECT COUNT(*) 
        FROM assignments a 
        WHERE a.course_id = c.course_id AND a.status = 'Missing'
    ) as missing_count
FROM courses c
JOIN students s ON c.student_id = s.student_id
ORDER BY c.course_name;
