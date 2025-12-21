-- PowerSchool Parent Portal Database Schema
-- Based on real data extracted from PowerSchool parent portal

-- Drop tables if exist (for fresh start)
DROP TABLE IF EXISTS communication_templates;
DROP TABLE IF EXISTS communications;
DROP TABLE IF EXISTS teachers;
DROP TABLE IF EXISTS teacher_comments;
DROP TABLE IF EXISTS scrape_history;
DROP TABLE IF EXISTS attendance_records;
DROP TABLE IF EXISTS attendance_summary;
DROP TABLE IF EXISTS assignment_details;
DROP TABLE IF EXISTS course_categories;
DROP TABLE IF EXISTS assignments;
DROP TABLE IF EXISTS grades;
DROP TABLE IF EXISTS courses;
DROP TABLE IF EXISTS students;

-- Students table
CREATE TABLE students (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    powerschool_id TEXT UNIQUE NOT NULL,  -- PowerSchool student ID (e.g., "12345")
    first_name TEXT NOT NULL,
    last_name TEXT,
    grade_level TEXT,
    school_name TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Courses table
CREATE TABLE courses (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    student_id INTEGER NOT NULL,
    course_name TEXT NOT NULL,
    expression TEXT,                       -- Period/block (e.g., "1/6(A-B)")
    room TEXT,
    teacher_name TEXT,
    teacher_email TEXT,
    course_section TEXT,                   -- Course section code
    term TEXT,                             -- Term (e.g., "S1", "YR")
    powerschool_frn TEXT,                  -- PowerSchool FRN for linking to assignments
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (student_id) REFERENCES students(id),
    UNIQUE(student_id, course_name, expression, term)
);

-- Grades table (historical grades by term)
CREATE TABLE grades (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    course_id INTEGER NOT NULL,
    student_id INTEGER NOT NULL,
    term TEXT NOT NULL,                    -- Q1, Q2, Q3, Q4, S1, S2
    letter_grade TEXT,                     -- Letter grade (A, B, C, etc.) or numeric (1, 2, 3, 4)
    percent REAL,                          -- Percentage if available
    gpa_points REAL,                       -- GPA points if available
    absences INTEGER DEFAULT 0,
    tardies INTEGER DEFAULT 0,
    recorded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (course_id) REFERENCES courses(id),
    FOREIGN KEY (student_id) REFERENCES students(id),
    UNIQUE(course_id, term, recorded_at)
);

-- Assignments table
CREATE TABLE assignments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    course_id INTEGER,
    student_id INTEGER NOT NULL,
    course_name TEXT NOT NULL,             -- Course name (for lookup)
    teacher_name TEXT,
    assignment_name TEXT NOT NULL,
    category TEXT,                         -- Category (e.g., "Formative", "Summative")
    due_date DATE,
    score TEXT,                            -- Score (can be numeric or text like "Missing")
    max_score REAL,
    percent REAL,
    letter_grade TEXT,
    status TEXT DEFAULT 'Unknown',         -- Missing, Late, Collected, Submitted
    codes TEXT,                            -- Original codes from PowerSchool
    term TEXT,                             -- Term (e.g., "Q1", "Q2")
    recorded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (course_id) REFERENCES courses(id),
    FOREIGN KEY (student_id) REFERENCES students(id)
);

-- Course categories (for weighted grading)
CREATE TABLE IF NOT EXISTS course_categories (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    course_id INTEGER NOT NULL,
    category_name TEXT NOT NULL,
    weight REAL,                            -- percentage weight (0-100)
    points_earned REAL,                     -- total points earned in category
    points_possible REAL,                   -- total points possible in category
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (course_id) REFERENCES courses(id),
    UNIQUE(course_id, category_name)
);
CREATE INDEX IF NOT EXISTS idx_course_categories_course ON course_categories(course_id);

-- Assignment details (extended info from score detail pages)
CREATE TABLE IF NOT EXISTS assignment_details (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    assignment_id INTEGER NOT NULL,
    description TEXT,                       -- assignment description
    standards TEXT,                         -- JSON array of standards (e.g., ["6.NS.1", "6.NS.2"])
    comments TEXT,                          -- teacher comments
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (assignment_id) REFERENCES assignments(id),
    UNIQUE(assignment_id)
);
CREATE INDEX IF NOT EXISTS idx_assignment_details_assignment ON assignment_details(assignment_id);

-- Attendance records (daily)
CREATE TABLE attendance_records (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    student_id INTEGER NOT NULL,
    date DATE NOT NULL,
    status TEXT,                           -- Present, Absent, Tardy
    code TEXT,                             -- Attendance code
    period TEXT,                           -- Period if applicable
    recorded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (student_id) REFERENCES students(id),
    UNIQUE(student_id, date, period)
);

-- Attendance summary (aggregated)
CREATE TABLE attendance_summary (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    student_id INTEGER NOT NULL,
    term TEXT,                             -- Term or "YTD" for year-to-date
    attendance_rate REAL,                  -- Percentage (e.g., 88.6)
    days_present INTEGER DEFAULT 0,
    days_absent INTEGER DEFAULT 0,
    days_excused INTEGER DEFAULT 0,
    days_unexcused INTEGER DEFAULT 0,
    tardies INTEGER DEFAULT 0,
    total_days INTEGER DEFAULT 0,
    recorded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (student_id) REFERENCES students(id)
);

-- Teacher comments table (from /guardian/teachercomments.html)
-- Stores teacher comments by course and term
CREATE TABLE IF NOT EXISTS teacher_comments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    student_id INTEGER NOT NULL,
    course_id INTEGER,                       -- Optional link to courses table
    course_name TEXT NOT NULL,               -- Course name from comments page
    course_number TEXT,                      -- Course number (e.g., "54436")
    expression TEXT,                         -- Period/block (e.g., "1/6(A-B)")
    teacher_name TEXT,
    teacher_email TEXT,
    term TEXT NOT NULL,                      -- Q1, Q2, Q3, Q4, S1, S2
    comment TEXT NOT NULL,                   -- The actual teacher comment
    recorded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (student_id) REFERENCES students(id),
    FOREIGN KEY (course_id) REFERENCES courses(id),
    UNIQUE(student_id, course_name, term, comment)
);
CREATE INDEX IF NOT EXISTS idx_teacher_comments_student ON teacher_comments(student_id);
CREATE INDEX IF NOT EXISTS idx_teacher_comments_term ON teacher_comments(term);
CREATE INDEX IF NOT EXISTS idx_teacher_comments_course ON teacher_comments(course_name);

-- Teachers table (for profiles and communication tracking)
CREATE TABLE teachers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,                     -- Full name (e.g., "Miller, Stephen J")
    email TEXT UNIQUE,                      -- Email address
    department TEXT,                        -- Department or subject area
    room TEXT,                              -- Room number
    courses_taught TEXT,                    -- JSON array of courses
    notes TEXT,                             -- Parent notes about this teacher
    last_contacted DATE,                    -- Date of last communication
    communication_count INTEGER DEFAULT 0,  -- Total communications
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Communications table (draft and sent messages)
CREATE TABLE communications (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    teacher_id INTEGER,
    student_id INTEGER,
    type TEXT NOT NULL,                     -- 'email', 'note', 'meeting_request'
    subject TEXT,
    body TEXT NOT NULL,
    status TEXT DEFAULT 'draft',            -- 'draft', 'sent', 'archived'
    context TEXT,                           -- JSON with context (assignment, course, etc.)
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    sent_at TIMESTAMP,
    FOREIGN KEY (teacher_id) REFERENCES teachers(id),
    FOREIGN KEY (student_id) REFERENCES students(id)
);

-- Communication templates
CREATE TABLE communication_templates (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,                     -- Template name
    type TEXT NOT NULL,                     -- 'missing_work', 'grade_concern', 'general', 'meeting_request'
    subject_template TEXT,
    body_template TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Scrape history
CREATE TABLE scrape_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    student_id INTEGER,
    started_at TIMESTAMP NOT NULL,
    completed_at TIMESTAMP,
    status TEXT DEFAULT 'running',         -- running, completed, failed
    pages_scraped TEXT,                    -- JSON array of pages scraped
    assignments_found INTEGER DEFAULT 0,
    error_message TEXT,
    FOREIGN KEY (student_id) REFERENCES students(id)
);

-- Create indexes for common queries
CREATE INDEX idx_assignments_student ON assignments(student_id);
CREATE INDEX idx_assignments_status ON assignments(status);
CREATE INDEX idx_assignments_due_date ON assignments(due_date);
CREATE INDEX idx_assignments_course ON assignments(course_name);
CREATE INDEX idx_grades_student ON grades(student_id);
CREATE INDEX idx_grades_term ON grades(term);
CREATE INDEX idx_attendance_student ON attendance_records(student_id);
CREATE INDEX idx_attendance_date ON attendance_records(date);
CREATE INDEX idx_teachers_email ON teachers(email);
CREATE INDEX idx_communications_teacher ON communications(teacher_id);
CREATE INDEX idx_communications_student ON communications(student_id);
CREATE INDEX idx_communications_status ON communications(status);
