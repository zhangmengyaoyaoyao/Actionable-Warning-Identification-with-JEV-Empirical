"""Choice questions for JEV / TypeSafe System One.

Maps the original AWI label space onto Choice options:
actionable / unactionable / unknown.
"""

from typesafe_sdk import Choice

QUESTION_ID = "actionability"

# Shared Choice question used for every warning.
# Option names are the labels; descriptions help the model separate them.
ACTIONABILITY_CHOICE = Choice(
    instructions=(
        "Decide whether this static-analysis warning is actionable. "
        "Actionable means a real issue that developers should fix; "
        "unactionable means a false positive or noise that does not need a fix; "
        "unknown means there is not enough evidence to decide."
    ),
    criteria={
        "actionable": (
            "A genuine defect or risk that warrants developer attention and a code change."
        ),
        "unactionable": (
            "A false positive, intentional pattern, or warning that does not require a fix."
        ),
        "unknown": (
            "Insufficient context or conflicting signals; cannot confidently classify."
        ),
    },
)


def build_questions():
    """Return the questions map expected by system_one()."""
    return {QUESTION_ID: ACTIONABILITY_CHOICE}
