"""Test suite for Student Grade Manager sample project."""

import pytest
from grade_manager import GradeManager


def test_students_and_courses():
    gm = GradeManager()
    gm.add_student("S1", "Alice")
    gm.add_course("C1", "Math", credits=4.0)
    with pytest.raises(ValueError):
        gm.add_student("S1", "Duplicate")
    with pytest.raises(ValueError):
        gm.add_course("C2", "Zero Credits", credits=0)


def test_record_grade_and_validation():
    gm = GradeManager()
    gm.add_student("S1", "Alice")
    gm.add_course("C1", "Math", credits=3.0)
    gm.record_grade("S1", "C1", 95)
    with pytest.raises(ValueError):
        gm.record_grade("S1", "C1", 105)
    with pytest.raises(KeyError):
        gm.record_grade("S99", "C1", 80)


def test_gpa_and_report_card():
    gm = GradeManager()
    gm.add_student("S1", "Alice")
    gm.add_course("C1", "Math", credits=4.0)
    gm.add_course("C2", "History", credits=2.0)

    gm.record_grade("S1", "C1", 92)  # A = 4.0 * 4 = 16
    gm.record_grade("S1", "C2", 85)  # B = 3.0 * 2 = 6
    # Weighted GPA = 22 / 6 = 3.67
    assert gm.calculate_gpa("S1") == 3.67

    card = gm.get_report_card("S1")
    assert card["name"] == "Alice"
    assert card["gpa"] == 3.67
    assert len(card["courses"]) == 2


def test_course_average_and_top_performers():
    gm = GradeManager()
    gm.add_student("S1", "Alice")
    gm.add_student("S2", "Bob")
    gm.add_course("C1", "CS101", credits=3.0)

    gm.record_grade("S1", "C1", 90)
    gm.record_grade("S2", "C1", 70)
    assert gm.course_average("C1") == 80.0

    top = gm.top_performers()
    assert top[0]["student_id"] == "S1"
    assert top[1]["student_id"] == "S2"
