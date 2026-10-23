from __future__ import annotations

import random
import sqlite3

from app.config import DB_PATH

DEPARTMENTS = [
    "Computer Science",
    "Information Technology",
    "Electronics",
    "Mechanical Engineering",
    "Civil Engineering",
    "Mathematics",
    "Physics",
    "Biotechnology",
]

COURSE_NAMES = [
    "Data Structures",
    "Database Systems",
    "Algorithms",
    "Operating Systems",
    "Computer Networks",
    "Software Engineering",
    "Digital Logic",
    "Signals and Systems",
    "Thermodynamics",
    "Fluid Mechanics",
    "Structural Analysis",
    "Engineering Mathematics",
    "Electromagnetics",
    "Quantum Physics",
    "Molecular Biology",
    "Bioinformatics",
    "Applied Statistics",
    "Discrete Mathematics",
    "Circuit Theory",
    "Machine Learning",
]

FIRST_NAMES = [
    "Aarav", "Aisha", "Ananya", "Arjun", "Bhavya", "Chaitanya", "Deepak", "Divya", "Esha", "Farah",
    "Gaurav", "Hina", "Ishaan", "Jiya", "Karan", "Kavya", "Manav", "Meera", "Nisha", "Om", "Pooja",
    "Rahul", "Riya", "Sahil", "Sara", "Tanya", "Uday", "Vaishnavi", "Vikram", "Yash", "Zoya",
    "Aditya", "Anik", "Bharat", "Charu", "Disha", "Eklavya", "Faisal", "Geeta", "Harsh", "Ira",
    "Jatin", "Kashvi", "Laksh", "Mansi", "Nitin", "Pallavi", "Qasim", "Ritika", "Sakshi", "Trisha",
    "Ujjwal", "Veda", "Wajid", "Xena", "Yamini", "Zaid", "Aditi", "Aman", "Brittany", "Chetan",
    "Dhruv", "Evelyn", "Falguni", "Girish", "Heena", "Ishan", "Jasmine", "Kunal", "Lavanya", "Mihir",
    "Neha", "Ojas", "Priya", "Rohit", "Shreya", "Tejas", "Urvi", "Vansh", "Wendy", "Yatri",
]

LAST_NAMES = [
    "Agarwal", "Bhatia", "Chopra", "Desai", "Ghosh", "Iyer", "Joshi", "Kapoor", "Lal", "Mehta",
    "Nair", "Patel", "Qureshi", "Rao", "Sharma", "Sinha", "Tripathi", "Verma", "Yadav", "Zacharia",
    "Arora", "Bose", "Dutta", "Fernandes", "Gupta", "Hegde", "Jain", "Kulkarni", "Malhotra", "Nanda",
    "Pillai", "Reddy", "Sen", "Tiwari", "Upadhyay", "Walia", "Xavier", "Yogi", "Zaman",
]

SEMESTERS = [
    "Semester 1",
    "Semester 2",
    "Semester 3",
    "Semester 4",
    "Semester 5",
    "Semester 6",
    "Semester 7",
    "Semester 8",
]


def grade_for_score(score: int) -> str:
    if score >= 90:
        return "A+"
    if score >= 85:
        return "A"
    if score >= 75:
        return "B+"
    if score >= 65:
        return "B"
    if score >= 55:
        return "C"
    if score >= 45:
        return "D"
    if score >= 35:
        return "E"
    return "F"


def seed_database(conn: sqlite3.Connection) -> None:
    conn.execute("DELETE FROM marks")
    conn.execute("DELETE FROM enrollments")
    conn.execute("DELETE FROM courses")
    conn.execute("DELETE FROM students")
    conn.execute("DELETE FROM departments")

    rng = random.Random(42)

    department_rows = [(idx + 1, name) for idx, name in enumerate(DEPARTMENTS)]
    conn.executemany(
        "INSERT INTO departments (department_id, department_name) VALUES (?, ?)",
        department_rows,
    )

    course_rows = []
    for dept_index, dept_name in enumerate(DEPARTMENTS, start=1):
        department_course_names = COURSE_NAMES[(dept_index - 1) * 2 : (dept_index - 1) * 2 + 3]
        for course_index, course_name in enumerate(department_course_names, start=1):
            course_rows.append(
                (dept_index * 100 + course_index, course_name, 3 if course_index % 2 == 0 else 4, dept_index)
            )
    conn.executemany(
        "INSERT INTO courses (course_id, course_name, credits, department_id) VALUES (?, ?, ?, ?)",
        course_rows,
    )

    student_rows = []
    current_id = 1
    for dept_id in range(1, len(DEPARTMENTS) + 1):
        for year in (1, 2, 3, 4):
            for _ in range(15):
                first = rng.choice(FIRST_NAMES)
                last = rng.choice(LAST_NAMES)
                name = f"{first} {last}"
                age = 18 + year + rng.randint(0, 3)
                gender = rng.choice(["Male", "Female", "Other"])
                email = f"{first.lower()}.{last.lower()}{current_id}@example.edu"
                student_rows.append((current_id, name, age, gender, dept_id, year, email))
                current_id += 1

    if len(student_rows) < 100:
        for idx in range(len(student_rows), 120):
            first = FIRST_NAMES[idx % len(FIRST_NAMES)]
            last = LAST_NAMES[idx % len(LAST_NAMES)]
            dept_id = (idx % len(DEPARTMENTS)) + 1
            year = ((idx % 4) + 1)
            age = 18 + year + rng.randint(0, 3)
            gender = ["Male", "Female", "Other"][idx % 3]
            email = f"{first.lower()}.{last.lower()}{idx+1}@example.edu"
            student_rows.append((idx + 1, f"{first} {last}", age, gender, dept_id, year, email))

    conn.executemany(
        "INSERT INTO students (student_id, name, age, gender, department_id, year, email) VALUES (?, ?, ?, ?, ?, ?, ?)",
        student_rows,
    )

    available_course_ids = [course_id for course_id, _, _, _ in course_rows]

    enrollment_rows = []
    enrollment_id = 1
    for student_id in range(1, len(student_rows) + 1):
        selected_course_ids = rng.sample(available_course_ids, k=rng.randint(3, 5))
        for course_id in selected_course_ids:
            semester = SEMESTERS[rng.randint(0, len(SEMESTERS) - 1)]
            enrollment_rows.append((enrollment_id, student_id, course_id, semester))
            enrollment_id += 1

    conn.executemany(
        "INSERT INTO enrollments (enrollment_id, student_id, course_id, semester) "
        "VALUES (?, ?, ?, ?)",
        enrollment_rows,
    )

    mark_rows = []
    mark_id = 1
    for student_id in range(1, len(student_rows) + 1):
        selected_course_ids = rng.sample(available_course_ids, k=rng.randint(2, 4))
        for course_id in selected_course_ids:
            score = rng.randint(30, 98)
            mark_rows.append((mark_id, student_id, course_id, score, grade_for_score(score)))
            mark_id += 1

    conn.executemany(
        "INSERT INTO marks (mark_id, student_id, course_id, marks, grade) "
        "VALUES (?, ?, ?, ?, ?)",
        mark_rows,
    )


if __name__ == "__main__":
    conn = sqlite3.connect(DB_PATH)
    try:
        conn.execute("PRAGMA foreign_keys = ON")
        seed_database(conn)
        conn.commit()
    finally:
        conn.close()
