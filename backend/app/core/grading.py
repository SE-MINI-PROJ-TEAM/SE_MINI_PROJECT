"""Grade lifecycle domain logic shared by the grading features (SYS-F-013..017, PRJ-SO-002).

State machine (SRS 8.3):
    (none) -> Draft -> Submitted -> Published -> Under Review -> Published

A grade may enter ``Under Review`` only once: the guard lives in the dispute service
(features/regrade_disputes), backed by a UNIQUE constraint on ``grade_disputes.enrollment_id``.
"""
from decimal import ROUND_HALF_UP, Decimal

from app.core.constants import (
    GRADE_DRAFT,
    GRADE_PUBLISHED,
    GRADE_SUBMITTED,
    GRADE_UNDER_REVIEW,
)
from app.core.errors import ApiError, bad_request
from app.extensions import db
from app.models import GradeRecord

CENT = Decimal("0.01")

ALLOWED_TRANSITIONS = {
    None: {GRADE_DRAFT},
    GRADE_DRAFT: {GRADE_DRAFT, GRADE_SUBMITTED},
    GRADE_SUBMITTED: {GRADE_PUBLISHED},
    GRADE_PUBLISHED: {GRADE_UNDER_REVIEW},
    GRADE_UNDER_REVIEW: {GRADE_PUBLISHED},
}

# (minimum weighted total, letter, grade points on a 10-point scale). GPA = credit-weighted mean of the points.
GRADE_SCALE = (
    (Decimal("90"), "A", Decimal("10.0")),
    (Decimal("80"), "B", Decimal("8.0")),
    (Decimal("70"), "C", Decimal("6.0")),
    (Decimal("60"), "D", Decimal("4.0")),
    (Decimal("0"), "F", Decimal("0.0")),
)
LETTERS = tuple(row[1] for row in GRADE_SCALE)


def letter_for(total):
    total = Decimal(str(total))
    for minimum, letter, _ in GRADE_SCALE:
        if total >= minimum:
            return letter
    return "F"


def points_for(letter):
    return next(points for _, grade, points in GRADE_SCALE if grade == letter)


def compute_weighted_total(scores, rubric):
    """``scores``: {rubric_id: score}; ``rubric``: iterable of RubricComponent. Raises if any score is missing."""
    total = Decimal("0")
    for component in rubric:
        if component.id not in scores or scores[component.id] is None:
            raise ValueError(component.component_name)
        total += Decimal(str(scores[component.id])) * Decimal(str(component.normalized_weight)) / 100
    return total.quantize(CENT, rounding=ROUND_HALF_UP)


def assert_transition(current, target):
    if target not in ALLOWED_TRANSITIONS.get(current, set()):
        raise ApiError(
            409,
            "INVALID_STATE_TRANSITION",
            f"Grade cannot move from '{current or 'Not graded'}' to '{target}'.",
        )


def set_state(enrollment, target):
    """Validate + apply a lifecycle transition to the enrollment and mirror it on its grade records."""
    assert_transition(enrollment.grade_state, target)
    enrollment.grade_state = target
    GradeRecord.query.filter_by(enrollment_id=enrollment.id).update({"state": target}, synchronize_session=False)


def parse_scores(raw_scores, rubric):
    """Validate a ``[{"rubric_id": .., "score": ..}]`` payload against a course rubric -> {rubric_id: Decimal}."""
    from app.core.validation import to_decimal, to_int

    if not isinstance(raw_scores, list):
        raise bad_request("rubric_scores must be a list.", "INVALID_FIELD")
    valid_ids = {c.id for c in rubric}
    parsed = {}
    for item in raw_scores:
        if not isinstance(item, dict):
            raise bad_request("Each rubric score must be an object.", "INVALID_FIELD")
        rubric_id = to_int(item.get("rubric_id"), "rubric_id")
        if rubric_id not in valid_ids:
            raise bad_request(f"Rubric component {rubric_id} does not belong to this course.", "INVALID_RUBRIC")
        score = to_decimal(item.get("score"), "Score", minimum=0, maximum=100)
        parsed[rubric_id] = score.quantize(CENT, rounding=ROUND_HALF_UP)
    return parsed


def upsert_scores(enrollment, scores, state):
    """Write {rubric_id: score} for an enrollment with the given state (caller commits)."""
    existing = {g.rubric_id: g for g in GradeRecord.query.filter_by(enrollment_id=enrollment.id).all()}
    for rubric_id, score in scores.items():
        record = existing.get(rubric_id)
        if record is None:
            db.session.add(
                GradeRecord(enrollment_id=enrollment.id, rubric_id=rubric_id, numeric_score=score, state=state)
            )
        else:
            record.numeric_score = score
            record.state = state


def scores_for(enrollment_id):
    return {g.rubric_id: g.numeric_score for g in GradeRecord.query.filter_by(enrollment_id=enrollment_id).all()}


def total_or_none(scores, rubric):
    """Weighted total, or None while any rubric component is still unscored."""
    try:
        return compute_weighted_total(scores, rubric)
    except ValueError:
        return None


def submit_enrollment(enrollment, rubric):
    """Draft -> Submitted: needs every component scored; stores the weighted total (SYS-F-014)."""
    scores = scores_for(enrollment.id)
    try:
        total = compute_weighted_total(scores, rubric)
    except ValueError as missing:
        raise ApiError(400, "INCOMPLETE_SCORES", f"Score missing for rubric component '{missing}'.")
    set_state(enrollment, GRADE_SUBMITTED)
    enrollment.weighted_total = total
    return total
