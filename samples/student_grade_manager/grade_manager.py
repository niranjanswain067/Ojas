"""Reference implementation for the Student Grade Manager sample project."""

from dataclasses import dataclass
from typing import Any, Dict, List, Tuple


@dataclass
class Student:
    student_id: str
    name: str


@dataclass
class Course:
    course_id: str
    title: str
    credits: float


class GradeManager:
    """Manages students, courses, numeric/letter grades, and GPA calculations."""

    def __init__(self) -> None:
        self.students: Dict[str, Student] = {}
        self.courses: Dict[str, Course] = {}
        # (student_id, course_id) -> score
        self.grades: Dict[Tuple[str, str], float] = {}

    def add_student(self, student_id: str, name: str) -> Student:
        if student_id in self.students:
            raise ValueError(f"Student '{student_id}' already exists")
        s = Student(student_id=student_id, name=name)
        self.students[student_id] = s
        return s

    def add_course(self, course_id: str, title: str, credits: float = 3.0) -> Course:
        if course_id in self.courses:
            raise ValueError(f"Course '{course_id}' already exists")
        if credits <= 0:
            raise ValueError("Credits must be positive")
        c = Course(course_id=course_id, title=title, credits=credits)
        self.courses[course_id] = c
        return c

    def record_grade(self, student_id: str, course_id: str, score: float) -> None:
        if student_id not in self.students:
            raise KeyError(f"Student '{student_id}' not found")
        if course_id not in self.courses:
            raise KeyError(f"Course '{course_id}' not found")
        if not (0.0 <= score <= 100.0):
            raise ValueError("Score must be between 0 and 100")
        self.grades[(student_id, course_id)] = float(score)

    @staticmethod
    def score_to_letter(score: float) -> str:
        if score >= 90:
            return "A"
        if score >= 80:
            return "B"
        if score >= 70:
            return "C"
        if score >= 60:
            return "D"
        return "F"

    @staticmethod
    def letter_to_points(letter: str) -> float:
        return {"A": 4.0, "B": 3.0, "C": 2.0, "D": 1.0, "F": 0.0}.get(letter, 0.0)

    def calculate_gpa(self, student_id: str) -> float:
        if student_id not in self.students:
            raise KeyError(f"Student '{student_id}' not found")
        total_points = 0.0
        total_credits = 0.0
        for (sid, cid), score in self.grades.items():
            if sid == student_id:
                credits = self.courses[cid].credits
                points = self.letter_to_points(self.score_to_letter(score))
                total_points += points * credits
                total_credits += credits
        if total_credits == 0:
            return 0.0
        return round(total_points / total_credits, 2)

    def get_report_card(self, student_id: str) -> Dict[str, Any]:
        if student_id not in self.students:
            raise KeyError(f"Student '{student_id}' not found")
        courses_list = []
        for (sid, cid), score in self.grades.items():
            if sid == student_id:
                letter = self.score_to_letter(score)
                courses_list.append({
                    "course_id": cid,
                    "title": self.courses[cid].title,
                    "score": score,
                    "letter": letter,
                })
        return {
            "student_id": student_id,
            "name": self.students[student_id].name,
            "courses": courses_list,
            "gpa": self.calculate_gpa(student_id),
        }

    def course_average(self, course_id: str) -> float:
        if course_id not in self.courses:
            raise KeyError(f"Course '{course_id}' not found")
        scores = [score for (sid, cid), score in self.grades.items() if cid == course_id]
        if not scores:
            return 0.0
        return round(sum(scores) / len(scores), 2)

    def top_performers(self) -> List[Dict[str, Any]]:
        ranked = [
            {
                "student_id": sid,
                "name": s.name,
                "gpa": self.calculate_gpa(sid),
            }
            for sid, s in self.students.items()
        ]
        ranked.sort(key=lambda x: x["gpa"], reverse=True)
        return ranked
