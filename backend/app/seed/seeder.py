"""Synthetic data seeder (STP 6: 500 students, 50 faculty, 10 admins, 50 courses, ~1,000 sessions).

Every seeded account shares one bcrypt (cost 12) hash of ``DEMO_PASSWORD`` so seeding stays fast; real accounts
created through the app always get their own salted hash. Session times are generated relative to *now*, so a fresh
seed always has sessions that are open, about to freeze, frozen and upcoming.
"""
import random
from datetime import timedelta
from decimal import ROUND_HALF_UP, Decimal

from app.core import grading
from app.core.constants import (
    DISPUTE_OPEN,
    DISPUTE_RESOLVED,
    GRADE_DRAFT,
    GRADE_PUBLISHED,
    GRADE_SUBMITTED,
    GRADE_UNDER_REVIEW,
    ROLE_ADMIN,
    ROLE_FACULTY,
    ROLE_STUDENT,
)
from app.core.rubric import normalize_weights
from app.core.security import hash_password
from app.core.settings import CURRENT_TERM, ENROLLMENT_OPEN, set_setting
from app.core.timeutil import utcnow
from app.extensions import db
from app.models import (
    AttendanceRecord,
    Course,
    Enrollment,
    GradeDispute,
    GradeRecord,
    Profile,
    RubricComponent,
    ScheduleSession,
    User,
)
from app.seed import data

DEMO_PASSWORD = "Password@123"
TEMP_USER_PASSWORD = "Temp@12345"
IST = timedelta(hours=5, minutes=30)  # sessions are authored in IST wall-clock, stored as UTC
DAY_PAIRS = [(0, 2), (1, 3), (2, 4), (0, 3), (1, 4)]
SESSION_WEEKS = range(-6, 4)  # 10 weeks x 2 sessions = 20 sessions per course

N_STUDENTS, N_FACULTY, N_ADMINS, N_COURSES = 500, 50, 10, 50


def _email(prefix, n):
    return f"{prefix}{n:03d}@srs.edu"


def _half_marks(value):
    """Round a raw mark to the nearest 0.5, like real partial marking (no 42.67s)."""
    return (Decimal(str(value)) * 2).quantize(Decimal("1"), rounding=ROUND_HALF_UP) / 2


class Seeder:
    def __init__(self, term, seed=2026):
        self.rng = random.Random(seed)
        self.term = term
        self.now = utcnow()
        self.hash = hash_password(DEMO_PASSWORD, rounds=12)

    # ------------------------------------------------------------------ users
    def users(self):
        rng = self.rng
        used = set()

        def name():
            while True:
                candidate = f"{rng.choice(data.FIRST_NAMES)} {rng.choice(data.LAST_NAMES)}"
                if candidate not in used:
                    used.add(candidate)
                    return candidate

        def make(role, inst_id, email, full_name, temp=False, pw_hash=None):
            user = User(
                institutional_id=inst_id, email=email, full_name=full_name, role=role,
                password_hash=pw_hash or self.hash, is_temporary_password=temp, is_active=True,
                created_at=self.now - timedelta(days=rng.randint(30, 400)),
            )
            user.profile = Profile(
                phone=f"+91 9{rng.randint(100000000, 999999999)}" if rng.random() < 0.6 else None,
                personal_email=f"{full_name.split()[0].lower()}{rng.randint(10, 99)}@gmail.com" if rng.random() < 0.4 else None,
                emergency_contact=f"{rng.choice(data.FIRST_NAMES)} {rng.choice(data.LAST_NAMES)} - +91 9{rng.randint(100000000, 999999999)}"
                if rng.random() < 0.5 else None,
            )
            return user

        self.admins = [make(ROLE_ADMIN, f"ADM{n:03d}", _email("admin", n), name()) for n in range(1, N_ADMINS + 1)]
        self.faculty = [make(ROLE_FACULTY, f"FAC{n:03d}", _email("faculty", n), name()) for n in range(1, N_FACULTY + 1)]
        self.students = [
            make(ROLE_STUDENT, f"PES1UG24CS{n:03d}", _email("student", n), name()) for n in range(1, N_STUDENTS + 1)
        ]
        # A not-yet-activated account to demo the forced password reset (US-02).
        self.temp_user = make(
            ROLE_STUDENT, "PES1UG24CS900", "new.student@srs.edu", "Neha Newcomer",
            temp=True, pw_hash=hash_password(TEMP_USER_PASSWORD, rounds=12),
        )
        db.session.add_all(self.admins + self.faculty + self.students + [self.temp_user])
        db.session.flush()

    # ---------------------------------------------------------------- courses
    def courses(self):
        self.courses_ = []
        for idx, (code, title, credits) in enumerate(data.COURSES[:N_COURSES]):
            # FAC001 teaches the first three sections (demo account); the rest map 1:1 to FAC002..FAC048.
            faculty = self.faculty[0] if idx < 3 else self.faculty[idx - 2]
            capacity = 30 if idx == 49 else (32 if idx == 48 else 60)
            course = Course(
                code=code, title=title, section="A", term=self.term, credits=credits,
                capacity=capacity, assigned_faculty_id=faculty.id,
            )
            template = data.RUBRIC_TEMPLATES[idx % len(data.RUBRIC_TEMPLATES)]
            weights = normalize_weights([w for _, _, w in template])
            for (name, category, raw), weight in zip(template, weights):
                course.rubric.append(
                    RubricComponent(component_name=name, category=category, raw_weight=raw, normalized_weight=weight)
                )
            self.courses_.append(course)
        db.session.add_all(self.courses_)
        db.session.flush()

    # ------------------------------------------------------------ enrollments
    def enrollments(self):
        rng = self.rng
        self.by_course = {c.id: [] for c in self.courses_}
        self.by_student = {s.id: [] for s in self.students}
        seats = {c.id: c.capacity for c in self.courses_}

        def enroll(student, course):
            e = Enrollment(student_id=student.id, course_id=course.id)
            db.session.add(e)
            self.by_course[course.id].append(e)
            self.by_student[student.id].append(e)
            seats[course.id] -= 1

        s1, s2 = self.students[0], self.students[1]
        for idx in (0, 1, 2, 4):  # student001: 4 courses -> can add 2 more, then hits the cap
            enroll(s1, self.courses_[idx])
        for idx in (0, 1, 2, 3, 4, 5):  # student002: already at the 6-course cap
            enroll(s2, self.courses_[idx])
        for student in self.students[2:32]:  # fill the small section so "Section full" can be demoed
            enroll(student, self.courses_[49])
        for student in self.students[32:62]:
            enroll(student, self.courses_[48])  # 2 seats left

        for student in self.students[2:]:
            already = {e.course_id for e in self.by_student[student.id]}
            target = rng.choices([3, 4, 5, 6], weights=[2, 5, 4, 1])[0]
            options = [c for c in self.courses_ if seats[c.id] > 0 and c.id not in already]
            rng.shuffle(options)
            for course in options[: max(target - len(already), 0)]:
                enroll(student, course)
        db.session.flush()

    # --------------------------------------------------------------- sessions
    def sessions(self):
        local_now = self.now + IST
        monday = (local_now - timedelta(days=local_now.weekday())).replace(hour=0, minute=0, second=0, microsecond=0)
        hour_now = self.now.replace(minute=0, second=0, microsecond=0)

        # Anchored demo sessions for FAC001's courses: (offset from now) of two weekly series per course.
        anchors = {
            0: (timedelta(hours=-2), timedelta(days=-3, hours=-1)),    # open now / frozen
            1: (timedelta(hours=-26), timedelta(hours=5)),             # open (yesterday) / later today
            2: (timedelta(hours=-40), timedelta(days=-3, hours=-5)),   # about to freeze / frozen
        }
        self.sessions_ = []
        for idx, course in enumerate(self.courses_):
            if idx in anchors:
                starts = [hour_now + a + timedelta(weeks=w) for a in anchors[idx] for w in SESSION_WEEKS]
                room = f"LH-{idx + 1}"
            else:
                days = DAY_PAIRS[idx % len(DAY_PAIRS)]
                hour = 9 + (idx // len(DAY_PAIRS)) % 8
                starts = [
                    monday + timedelta(weeks=w, days=d, hours=hour) - IST for w in SESSION_WEEKS for d in days
                ]
                room = f"R-{200 + idx}"
            for start in starts:
                self.sessions_.append(
                    ScheduleSession(course_id=course.id, start_time=start, end_time=start + timedelta(hours=1), room_number=room)
                )
        db.session.add_all(self.sessions_)
        db.session.flush()

    # ------------------------------------------------------------- attendance
    def attendance(self):
        rng = self.rng
        presence = {s.id: rng.choices([0.97, 0.9, 0.82, 0.7, 0.55], weights=[3, 5, 3, 2, 1])[0] for s in self.students}
        weak_course = self.courses_[1].id  # student001 is below the 75% alert threshold in this course
        demo_open = {self.courses_[1].id, self.courses_[2].id, self.courses_[0].id}
        faculty_of = {c.id: c.assigned_faculty_id for c in self.courses_}
        rows = []
        for session in self.sessions_:
            if session.start_time > self.now:
                continue
            # Leave FAC001's sessions from the last 48h unmarked so the roll-call flow can be demoed.
            if session.course_id in demo_open and self.now - session.start_time < timedelta(hours=48):
                continue
            for enrollment in self.by_course[session.course_id]:
                p = presence[enrollment.student_id]
                if enrollment.student_id == self.students[0].id:
                    p = 0.6 if session.course_id == weak_course else 0.95
                rows.append(
                    {
                        "session_id": session.id, "student_id": enrollment.student_id,
                        "is_present": rng.random() < p, "marked_at": session.start_time + timedelta(minutes=10),
                        "marked_by": faculty_of[session.course_id],
                    }
                )
        for i in range(0, len(rows), 5000):
            db.session.bulk_insert_mappings(AttendanceRecord, rows[i : i + 5000])
        return len(rows)

    # ----------------------------------------------------------------- grades
    def grades(self):
        rng = self.rng
        ability = {s.id: rng.gauss(74, 11) for s in self.students}
        records = []
        disputes = 0
        dispute_budget = {0: 2, 3: 2, 8: 2, 13: 1}
        for idx, course in enumerate(self.courses_):
            mode = idx % 5  # 0 Published, 1 Submitted, 2 Draft (partial), 3 Published, 4 not started
            if mode == 4:
                continue
            disputed = 0
            for enrollment in self.by_course[course.id]:
                scores = {}
                for comp in course.rubric:
                    raw = ability[enrollment.student_id] + rng.gauss(0, 8)
                    scores[comp.id] = _half_marks(min(max(raw, 0), 100))
                if mode == 2:
                    # Draft: partially entered marks; some students have nothing yet.
                    is_demo_student = enrollment.student_id == self.students[0].id
                    if rng.random() < 0.25 and not is_demo_student:
                        continue
                    keep = len(course.rubric) - 1 if is_demo_student else rng.randint(1, len(course.rubric))
                    scores = dict(list(scores.items())[:keep])
                    state = GRADE_DRAFT
                    total = None
                else:
                    total = grading.compute_weighted_total(scores, course.rubric)
                    state = GRADE_SUBMITTED if mode == 1 else GRADE_PUBLISHED
                if state == GRADE_PUBLISHED and idx in dispute_budget and disputed < dispute_budget[idx] \
                        and enrollment.student_id not in (self.students[0].id, self.students[1].id):
                    state = GRADE_UNDER_REVIEW
                    disputed += 1
                    disputes += 1
                    db.session.add(
                        GradeDispute(
                            enrollment_id=enrollment.id, student_id=enrollment.student_id,
                            reason=rng.choice(data.DISPUTE_REASONS), status=DISPUTE_OPEN, previous_total=total,
                            filed_at=self.now - timedelta(hours=rng.randint(2, 70)),
                        )
                    )
                if idx == 0 and state == GRADE_PUBLISHED and enrollment.student_id == self.students[1].id:
                    # student002 has already used the one regrade this grade allows (cannot dispute again).
                    db.session.add(
                        GradeDispute(
                            enrollment_id=enrollment.id, student_id=enrollment.student_id,
                            reason=rng.choice(data.DISPUTE_REASONS), status=DISPUTE_RESOLVED, previous_total=total,
                            resolution_note="Marks re-checked; the original evaluation stands.",
                            resolved_by=course.assigned_faculty_id,
                            filed_at=self.now - timedelta(days=5), resolved_at=self.now - timedelta(days=4),
                        )
                    )
                enrollment.grade_state = state
                enrollment.weighted_total = total
                for rubric_id, score in scores.items():
                    records.append(
                        {"enrollment_id": enrollment.id, "rubric_id": rubric_id, "numeric_score": score,
                         "state": state, "updated_at": self.now}
                    )
        for i in range(0, len(records), 5000):
            db.session.bulk_insert_mappings(GradeRecord, records[i : i + 5000])
        return len(records), disputes


def seed_database():
    from app.core.settings import current_term

    set_setting(CURRENT_TERM, current_term())
    set_setting(ENROLLMENT_OPEN, "true")
    seeder = Seeder(term=current_term())
    seeder.users()
    seeder.courses()
    seeder.enrollments()
    seeder.sessions()
    attendance_rows = seeder.attendance()
    grade_rows, disputes = seeder.grades()
    db.session.commit()
    return {
        "admins": len(seeder.admins),
        "faculty": len(seeder.faculty),
        "students": len(seeder.students) + 1,
        "courses": len(seeder.courses_),
        "enrollments": sum(len(v) for v in seeder.by_course.values()),
        "sessions": len(seeder.sessions_),
        "attendance_records": attendance_rows,
        "grade_records": grade_rows,
        "open_disputes": disputes,
    }
