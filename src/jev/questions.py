"""JEV / TypeSafe System One questions for AWI empirical study.

Three primitives (Choice / Score / Noul) share the same actionable /
unactionable definitions so their results can be compared fairly.
There is no ``unknown`` option.
"""

from typesafe_sdk import Choice, Noul, NoulCriteria, Score

EXPERT_PREFIX = "You are an expert in static analysis warning classification."

ACTIONABLE_DESC = (
    "A genuine defect or risk that warrants developer attention and a code change."
)
UNACTIONABLE_DESC = (
    "A false positive, intentional pattern, or warning that does not require a fix."
)

# Question ids used in a single system_one() call.
QUESTION_ID_CHOICE = "actionability_choice"
QUESTION_ID_SCORE = "actionability_score"
QUESTION_ID_NOUL = "actionability_noul"

PRIMITIVE_DIRS = {
    "choice": "jev-choice",
    "score": "jev-score",
    "noul": "jev-noul",
}

QUESTION_IDS = {
    "choice": QUESTION_ID_CHOICE,
    "score": QUESTION_ID_SCORE,
    "noul": QUESTION_ID_NOUL,
}

# Shared task text; each primitive adds a thin type-specific clause.
_TASK = (
    "Decide whether this static-analysis warning is actionable. "
    "Actionable means a real issue that developers should fix; "
    "unactionable means a false positive or noise that does not need a fix."
)

CHOICE_INSTRUCTIONS = f"{EXPERT_PREFIX} {_TASK} Select exactly one option."
SCORE_INSTRUCTIONS = (
    f"{EXPERT_PREFIX} {_TASK} "
    "Rate the warning on the ordered scale from unactionable to actionable."
)
NOUL_INSTRUCTIONS = (
    f"{EXPERT_PREFIX} {_TASK} "
    "Is this warning actionable?"
)

ACTIONABILITY_CHOICE = Choice(
    instructions=CHOICE_INSTRUCTIONS,
    criteria={
        "actionable": ACTIONABLE_DESC,
        "unactionable": UNACTIONABLE_DESC,
    },
)

# Score levels are ordered low → high: 0 = unactionable, 1 = actionable.
ACTIONABILITY_SCORE = Score(
    instructions=SCORE_INSTRUCTIONS,
    criteria=[UNACTIONABLE_DESC, ACTIONABLE_DESC],
)

ACTIONABILITY_NOUL = Noul(
    instructions=NOUL_INSTRUCTIONS,
    criteria=NoulCriteria(
        true=ACTIONABLE_DESC,
        false=UNACTIONABLE_DESC,
    ),
)


def build_questions():
    """Return the three questions sent together in one system_one() call."""
    return {
        QUESTION_ID_CHOICE: ACTIONABILITY_CHOICE,
        QUESTION_ID_SCORE: ACTIONABILITY_SCORE,
        QUESTION_ID_NOUL: ACTIONABILITY_NOUL,
    }


def questions_for_request(questions=None):
    """Plain-JSON summary of the three questions for result reproducibility."""
    questions = questions or build_questions()
    choice_q = questions[QUESTION_ID_CHOICE]
    score_q = questions[QUESTION_ID_SCORE]
    noul_q = questions[QUESTION_ID_NOUL]
    noul_criteria = noul_q.criteria or {}
    if hasattr(noul_criteria, "model_dump"):
        noul_criteria = noul_criteria.model_dump()
    elif not isinstance(noul_criteria, dict):
        noul_criteria = {
            "true": getattr(noul_criteria, "true", None),
            "false": getattr(noul_criteria, "false", None),
        }
    return {
        QUESTION_ID_CHOICE: {
            "type": "choice",
            "instructions": choice_q.instructions,
            "criteria": dict(choice_q.criteria),
        },
        QUESTION_ID_SCORE: {
            "type": "score",
            "instructions": score_q.instructions,
            "criteria": list(score_q.criteria),
        },
        QUESTION_ID_NOUL: {
            "type": "noul",
            "instructions": noul_q.instructions,
            "criteria": {
                "true": noul_criteria.get("true"),
                "false": noul_criteria.get("false"),
            },
        },
    }
