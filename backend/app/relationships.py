# backend/app/relationships.py

RELATIONSHIPS = {
    ("students", "enrollments"): {
        "students.id": "enrollments.student_id"
    },
    ("courses", "enrollments"): {
        "courses.id": "enrollments.course_id"
    }
}
RELATIONSHIPS = {
    "enrollments": {
        "students": {
            "local_key": "student_id",
            "foreign_key": "id"
        },
        "courses": {
            "local_key": "course_id",
            "foreign_key": "id"
        }
    }
}
