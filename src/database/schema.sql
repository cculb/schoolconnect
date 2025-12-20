-- PowerSchool Parent Portal Database Schema
-- SQLite3 compatible

-- Students table
CREATE TABLE IF NOT EXISTS students (
    student_id TEXT PRIMARY KEY,
    first_name TEXT NOT NULL,
    last_name TEXT NOT NULL,
    grade_level INTEGER NOT NULL,
    school_name TEXT NOT NULL,
    district_code TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Courses table
CREATE TABLE IF NOT EXISTS courses (
    course_id TEXT PRIMARY KEY,
    course_section TEXT,
    course_name TEXT NOT NULL,
    expression TEXT,  -- Period/block e.g., "1/6(A-B)"
    room TEXT,
    term TEXT,        -- "S1", "S2", "Q1", etc.
    teacher_name TEXT,
    teacher_email TEXT,
    enroll_date DATE,
    leave_date DATE,
    student_id TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (student_id) REFERENCES students(student_id)
);

-- Grades table (historical tracking)
CREATE TABLE IF NOT EXISTS grades (
    grade_id TEXT PRIMARY KEY,
    course_id TEXT NOT NULL,
    student_id TEXT NOT NULL,
    term TEXT NOT NULL,        -- "Q1", "Q2", "Q3", "Q4", "S1", "S2"
    letter_grade TEXT,
    percent REAL,
    gpa_points REAL,
    recorded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (course_id) REFERENCES courses(course_id),
    FOREIGN KEY (student_id) REFERENCES students(student_id)
);

-- Assignments table
CREATE TABLE IF NOT EXISTS assignments (
    assignment_id TEXT PRIMARY KEY,
    course_id TEXT NOT NULL,
    student_id TEXT NOT NULL,
    assignment_name TEXT NOT NULL,
    category TEXT,             -- "Evidence", "Formative", etc.
    due_date DATE,
    score REAL,
    max_score REAL,
    percent REAL,
    letter_grade TEXT,
    status TEXT,               -- "Collected", "Missing", "Late", "Exempt"
    has_comment INTEGER DEFAULT 0,
    has_description INTEGER DEFAULT 0,
    recorded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (course_id) REFERENCES courses(course_id),
    FOREIGN KEY (student_id) REFERENCES students(student_id)
);

-- Attendance records (individual day/period)
CREATE TABLE IF NOT EXISTS attendance_records (
    attendance_id TEXT PRIMARY KEY,
    student_id TEXT NOT NULL,
    course_id TEXT,            -- Nullable for daily attendance
    date DATE NOT NULL,
    period TEXT,               -- Nullable for daily attendance
    status TEXT NOT NULL,      -- "Present", "Absent", "Tardy", "Excused", etc.
    code TEXT,                 -- Raw code: "A", "T", "E", "U", etc.
    recorded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (student_id) REFERENCES students(student_id),
    FOREIGN KEY (course_id) REFERENCES courses(course_id)
);

-- Attendance summary (aggregated stats)
CREATE TABLE IF NOT EXISTS attendance_summary (
    summary_id TEXT PRIMARY KEY,
    student_id TEXT NOT NULL,
    term TEXT NOT NULL,        -- "YTD", "S1", "Q1", etc.
    days_enrolled INTEGER,
    days_present INTEGER,
    days_absent INTEGER,
    days_absent_excused INTEGER,
    days_absent_unexcused INTEGER,
    tardies INTEGER,
    tardies_excused INTEGER,
    tardies_unexcused INTEGER,
    attendance_rate REAL,      -- Percentage e.g., 88.60
    recorded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (student_id) REFERENCES students(student_id)
);

-- Teacher comments
CREATE TABLE IF NOT EXISTS teacher_comments (
    comment_id TEXT PRIMARY KEY,
    student_id TEXT NOT NULL,
    course_id TEXT NOT NULL,
    teacher_name TEXT,
    term TEXT,
    comment_text TEXT NOT NULL,
    recorded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (student_id) REFERENCES students(student_id),
    FOREIGN KEY (course_id) REFERENCES courses(course_id)
);

-- Scrape history for tracking sync operations
CREATE TABLE IF NOT EXISTS scrape_history (
    scrape_id TEXT PRIMARY KEY,
    student_id TEXT NOT NULL,
    started_at TIMESTAMP NOT NULL,
    completed_at TIMESTAMP,
    status TEXT NOT NULL,      -- "success", "partial", "failed"
    pages_scraped INTEGER DEFAULT 0,
    errors TEXT,               -- JSON array of error messages
    FOREIGN KEY (student_id) REFERENCES students(student_id)
);

-- Indexes for common queries
CREATE INDEX IF NOT EXISTS idx_courses_student ON courses(student_id);
CREATE INDEX IF NOT EXISTS idx_grades_student ON grades(student_id);
CREATE INDEX IF NOT EXISTS idx_grades_course ON grades(course_id);
CREATE INDEX IF NOT EXISTS idx_grades_term ON grades(term);
CREATE INDEX IF NOT EXISTS idx_assignments_student ON assignments(student_id);
CREATE INDEX IF NOT EXISTS idx_assignments_course ON assignments(course_id);
CREATE INDEX IF NOT EXISTS idx_assignments_due_date ON assignments(due_date);
CREATE INDEX IF NOT EXISTS idx_assignments_status ON assignments(status);
CREATE INDEX IF NOT EXISTS idx_attendance_records_student ON attendance_records(student_id);
CREATE INDEX IF NOT EXISTS idx_attendance_records_date ON attendance_records(date);
CREATE INDEX IF NOT EXISTS idx_attendance_summary_student ON attendance_summary(student_id);
CREATE INDEX IF NOT EXISTS idx_scrape_history_student ON scrape_history(student_id);
