"""Seed database with ground truth test data for SchoolPulse POC."""

import sqlite3
from pathlib import Path

GROUND_TRUTH = {
    "student": "Delilah Rae Culbreth",
    "first_name": "Delilah",
    "last_name": "Rae Culbreth",
    "grade_level": 6,
    "missing_assignments": 2,
    "missing_assignment_names": [
        "Atomic Structure Knowledge Check",
        "FORMATIVE - Edpuzzle on Autocracies"
    ],
    "attendance_rate": 88.6,
    "days_absent": 9,
    "tardies": 2,
    "courses_count": 12,
}


def get_db_path() -> Path:
    """Get the database path (check parent directory first, then current)."""
    parent_db = Path(__file__).parent.parent / "powerschool.db"
    local_db = Path(__file__).parent / "powerschool.db"

    if parent_db.exists():
        return parent_db
    return local_db


def update_attendance_to_ground_truth(db_path: Path) -> None:
    """Update attendance summary to match ground truth values."""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Get student ID for Delilah
    cursor.execute("SELECT id FROM students WHERE first_name = 'Delilah'")
    result = cursor.fetchone()

    if result:
        student_id = result[0]
        # Update attendance to match ground truth
        cursor.execute("""
            UPDATE attendance_summary
            SET attendance_rate = ?,
                days_absent = ?,
                tardies = ?,
                total_days = ?
            WHERE student_id = ?
        """, (
            GROUND_TRUTH["attendance_rate"],
            GROUND_TRUTH["days_absent"],
            GROUND_TRUTH["tardies"],
            70,  # Total school days so far
            student_id
        ))
        conn.commit()
        print(f"Updated attendance for student_id={student_id}")
    else:
        print("No Delilah found in database")

    conn.close()


def create_test_database(db_path: Path) -> None:
    """Create a new database with ground truth test data."""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Create tables
    cursor.executescript("""
        CREATE TABLE IF NOT EXISTS students (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            powerschool_id TEXT UNIQUE NOT NULL,
            first_name TEXT NOT NULL,
            last_name TEXT,
            grade_level TEXT,
            school_name TEXT DEFAULT 'Eagle Schools',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS courses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id INTEGER NOT NULL,
            course_name TEXT NOT NULL,
            expression TEXT,
            room TEXT,
            teacher_name TEXT,
            teacher_email TEXT,
            course_section TEXT,
            term TEXT,
            powerschool_frn TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (student_id) REFERENCES students(id)
        );

        CREATE TABLE IF NOT EXISTS grades (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            course_id INTEGER NOT NULL,
            student_id INTEGER NOT NULL,
            term TEXT NOT NULL,
            letter_grade TEXT,
            percent REAL,
            gpa_points REAL,
            absences INTEGER DEFAULT 0,
            tardies INTEGER DEFAULT 0,
            recorded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (course_id) REFERENCES courses(id),
            FOREIGN KEY (student_id) REFERENCES students(id)
        );

        CREATE TABLE IF NOT EXISTS assignments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            course_id INTEGER,
            student_id INTEGER NOT NULL,
            course_name TEXT NOT NULL,
            teacher_name TEXT,
            assignment_name TEXT NOT NULL,
            category TEXT,
            due_date DATE,
            score TEXT,
            max_score REAL,
            percent REAL,
            letter_grade TEXT,
            status TEXT DEFAULT 'Unknown',
            codes TEXT,
            term TEXT,
            recorded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (course_id) REFERENCES courses(id),
            FOREIGN KEY (student_id) REFERENCES students(id)
        );

        CREATE TABLE IF NOT EXISTS attendance_summary (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id INTEGER NOT NULL,
            term TEXT,
            attendance_rate REAL,
            days_present INTEGER DEFAULT 0,
            days_absent INTEGER DEFAULT 0,
            days_excused INTEGER DEFAULT 0,
            days_unexcused INTEGER DEFAULT 0,
            tardies INTEGER DEFAULT 0,
            total_days INTEGER DEFAULT 0,
            recorded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (student_id) REFERENCES students(id)
        );
    """)

    # Insert student
    cursor.execute("""
        INSERT OR IGNORE INTO students (powerschool_id, first_name, last_name, grade_level)
        VALUES (?, ?, ?, ?)
    """, ("55260", GROUND_TRUTH["first_name"], GROUND_TRUTH["last_name"], str(GROUND_TRUTH["grade_level"])))

    student_id = cursor.lastrowid or 1

    # Insert courses (12 total)
    courses = [
        ("Math 6", "Smith, John", "jsmith@school.edu", "101"),
        ("Science (grade 6)", "Johnson, Mary", "mjohnson@school.edu", "202"),
        ("Social Studies (grade 6)", "Williams, Robert", "rwilliams@school.edu", "303"),
        ("Language Arts 6", "Brown, Lisa", "lbrown@school.edu", "104"),
        ("PE 6", "Davis, Mike", "mdavis@school.edu", "GYM"),
        ("Art 6", "Wilson, Sarah", "swilson@school.edu", "ART"),
        ("Music 6", "Taylor, James", "jtaylor@school.edu", "MUS"),
        ("Spanish 6", "Garcia, Maria", "mgarcia@school.edu", "205"),
        ("Technology 6", "Anderson, Tom", "tanderson@school.edu", "LAB"),
        ("Advisory", "Miller, Stephen", "smiller@school.edu", "106"),
        ("Reading 6", "Thomas, Karen", "kthomas@school.edu", "107"),
        ("Health 6", "Jackson, Chris", "cjackson@school.edu", "108"),
    ]

    for course_name, teacher, email, room in courses:
        cursor.execute("""
            INSERT INTO courses (student_id, course_name, teacher_name, teacher_email, room, term)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (student_id, course_name, teacher, email, room, "Q2"))

    # Insert missing assignments
    cursor.execute("""
        INSERT INTO assignments (student_id, course_name, teacher_name, assignment_name, category, due_date, status, term)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (student_id, "Science (grade 6)", "Johnson, Mary", "Atomic Structure Knowledge Check", "Formative", "2024-12-10", "Missing", "Q2"))

    cursor.execute("""
        INSERT INTO assignments (student_id, course_name, teacher_name, assignment_name, category, due_date, status, term)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (student_id, "Social Studies (grade 6)", "Williams, Robert", "FORMATIVE - Edpuzzle on Autocracies", "Formative", "2024-12-12", "Missing", "Q2"))

    # Insert some completed assignments
    cursor.execute("""
        INSERT INTO assignments (student_id, course_name, teacher_name, assignment_name, category, due_date, score, max_score, status, term)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (student_id, "Math 6", "Smith, John", "Chapter 5 Test", "Summative", "2024-12-08", "85", 100, "Collected", "Q2"))

    # Insert attendance summary
    cursor.execute("""
        INSERT INTO attendance_summary (student_id, term, attendance_rate, days_present, days_absent, tardies, total_days)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (student_id, "YTD", GROUND_TRUTH["attendance_rate"], 61, GROUND_TRUTH["days_absent"], GROUND_TRUTH["tardies"], 70))

    # Insert grades
    course_grades = [
        ("Math 6", "B+", 87.5),
        ("Science (grade 6)", "B", 83.2),
        ("Social Studies (grade 6)", "B-", 81.0),
        ("Language Arts 6", "A-", 91.5),
        ("PE 6", "A", 95.0),
        ("Art 6", "A", 94.0),
        ("Music 6", "A-", 92.0),
        ("Spanish 6", "B+", 88.0),
    ]

    for idx, (course_name, grade, percent) in enumerate(course_grades, 1):
        cursor.execute("""
            INSERT INTO grades (course_id, student_id, term, letter_grade, percent)
            VALUES (?, ?, ?, ?, ?)
        """, (idx, student_id, "Q2", grade, percent))

    conn.commit()
    conn.close()
    print(f"Created test database at {db_path}")


def verify_ground_truth(db_path: Path) -> dict:
    """Verify database matches ground truth."""
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    results = {}

    # Check student
    cursor.execute("SELECT * FROM students WHERE first_name = 'Delilah'")
    student = cursor.fetchone()
    results["student_found"] = student is not None

    if student:
        student_id = student["id"]

        # Check missing assignments
        cursor.execute("""
            SELECT COUNT(*) as count FROM assignments
            WHERE student_id = ? AND status = 'Missing'
        """, (student_id,))
        results["missing_count"] = cursor.fetchone()["count"]

        # Check attendance
        cursor.execute("""
            SELECT attendance_rate, days_absent, tardies
            FROM attendance_summary WHERE student_id = ?
        """, (student_id,))
        att = cursor.fetchone()
        if att:
            results["attendance_rate"] = att["attendance_rate"]
            results["days_absent"] = att["days_absent"]
            results["tardies"] = att["tardies"]

        # Check courses
        cursor.execute("""
            SELECT COUNT(DISTINCT course_name) as count FROM courses WHERE student_id = ?
        """, (student_id,))
        results["courses_count"] = cursor.fetchone()["count"]

    conn.close()
    return results


def main():
    db_path = get_db_path()

    if db_path.exists():
        print(f"Database exists at {db_path}")
        # Update attendance to match ground truth
        update_attendance_to_ground_truth(db_path)
    else:
        print(f"Creating new database at {db_path}")
        create_test_database(db_path)

    # Verify
    results = verify_ground_truth(db_path)
    print("\nGround Truth Verification:")
    print(f"  Student found: {results.get('student_found', False)}")
    print(f"  Missing assignments: {results.get('missing_count', 0)} (expected: 2)")
    print(f"  Attendance rate: {results.get('attendance_rate', 0)}% (expected: 88.6%)")
    print(f"  Days absent: {results.get('days_absent', 0)} (expected: 9)")
    print(f"  Tardies: {results.get('tardies', 0)} (expected: 2)")
    print(f"  Courses: {results.get('courses_count', 0)} (expected: 12)")


if __name__ == "__main__":
    main()
