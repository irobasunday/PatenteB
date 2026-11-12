
from pathlib import Path
import ast
import shutil

folder = Path(__file__).resolve().parent
quiz_file = folder / "quiz.py"
backup_file = folder / "quiz_before_recovery.py"

if not quiz_file.exists():
    raise SystemExit("ERROR: quiz.py was not found.")

required_files = [
    "browser_identity.py",
    "quiz_attempt_storage.py",
    "quiz_question_recovery.py",
]

for filename in required_files:
    if not (folder / filename).exists():
        raise SystemExit(f"ERROR: {filename} was not found.")

source = quiz_file.read_text(encoding="utf-8-sig")

# Do not install the recovery code twice.
if "def persist_quiz_progress(" in source:
    raise SystemExit(
        "Recovery functions are already present. "
        "No changes were made."
    )

# Check the original file before modifying it.
ast.parse(source)

def replace_function(code, name, replacement):
    tree = ast.parse(code)

    node = next(
        (
            item for item in tree.body
            if isinstance(item, ast.FunctionDef)
            and item.name == name
        ),
        None,
    )

    if node is None:
        raise ValueError(f"Function not found: {name}")

    lines = code.splitlines(keepends=True)

    lines[node.lineno - 1:node.end_lineno] = [
        replacement.rstrip() + "\n"
    ]

    return "".join(lines)


# Add PostgreSQL recovery imports.
imports = """
from browser_identity import get_browser_id, create_browser_id
from quiz_question_recovery import fetch_questions_by_ids
from quiz_attempt_storage import (
    load_active_attempt,
    start_attempt,
    save_progress,
    finish_attempt,
)
"""

anchor = "from audio_player import show_italian_audio"

if anchor not in source:
    raise SystemExit("ERROR: Audio import was not found.")

source = source.replace(
    anchor,
    anchor + "\n" + imports,
    1,
)


# Functions for saving and starting quiz attempts.
helpers = '''
def persist_quiz_progress():
    """Save answers and question position to PostgreSQL."""

    if st.session_state.get("quiz_retry_mode"):
        return

    saved = save_progress(
        st.session_state.quiz_attempt_id,
        st.session_state.browser_id,
        "quiz",
        st.session_state.quiz_answers,
        st.session_state.quiz_question_index,
    )

    if not saved:
        raise RuntimeError(
            "Unable to save the active quiz attempt."
        )


def start_persisted_quiz(questions):
    """Start a new quiz and save its question IDs."""

    started_at = datetime.now(timezone.utc)

    attempt_id = start_attempt(
        st.session_state.browser_id,
        "quiz",
        [question["id"] for question in questions],
        started_at,
    )

    reset_quiz(questions)

    st.session_state.quiz_attempt_id = attempt_id
    st.session_state.quiz_started_at = started_at
    st.session_state.quiz_retry_mode = False


'''

source = source.replace(
    "def initialize_quiz():",
    helpers + "def initialize_quiz():",
    1,
)


# Restore saved quiz BEFORE generating new questions.
initialize_code = '''
def initialize_quiz():
    """Restore an active quiz or start a new one."""

    if "quiz_questions" not in st.session_state:

        browser_id = st.session_state.get("browser_id")

        if not browser_id:
            raise RuntimeError(
                "Browser identity is not available."
            )

        attempt = load_active_attempt(browser_id, "quiz")

        if attempt is not None:

            questions = fetch_questions_by_ids(
                attempt["question_ids"]
            )

            if len(questions) != TOTAL_QUESTIONS:
                raise ValueError(
                    "Saved quiz must contain 30 questions."
                )

            st.session_state.quiz_questions = questions
            st.session_state.quiz_attempt_id = attempt["id"]

            st.session_state.quiz_question_index = max(
                0,
                min(
                    int(attempt["question_index"]),
                    len(questions) - 1,
                ),
            )

            valid_ids = {
                question["id"] for question in questions
            }

            st.session_state.quiz_answers = {
                int(key): value
                for key, value in attempt["answers"].items()
                if int(key) in valid_ids
                and isinstance(value, bool)
            }

            st.session_state.quiz_started_at = (
                attempt["started_at"]
            )

            st.session_state.quiz_retry_mode = False

            st.session_state.quiz_completion_prompt_shown = (
                len(st.session_state.quiz_answers)
                == len(questions)
            )

        else:

            questions = fetch_quiz_questions()

            if (
                len(questions) != TOTAL_QUESTIONS
                or len({
                    question["id"]
                    for question in questions
                }) != TOTAL_QUESTIONS
                or len({
                    question["chapter_id"]
                    for question in questions
                }) != 25
            ):
                raise ValueError(
                    "Expected 30 unique questions "
                    "covering all 25 chapters."
                )

            start_persisted_quiz(questions)

    defaults = {
        "quiz_question_index": 0,
        "quiz_answers": {},
        "quiz_finished": False,
        "quiz_completion_prompt_shown": False,
        "quiz_show_completion_dialog": False,
        "quiz_submit_pending": False,
        "quiz_finish_reason": None,
        "quiz_translations_visible": {},
        "quiz_translation_cache": {},
        "quiz_results_view": "summary",
        "quiz_retry_mode": False,
        "quiz_finished_at": None,
    }

    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value

    if "quiz_started_at" not in st.session_state:
        st.session_state.quiz_started_at = (
            datetime.now(timezone.utc)
        )
'''

source = replace_function(
    source,
    "initialize_quiz",
    initialize_code,
)


# Save progress after an answer is selected.
tree = ast.parse(source)
node = next(
    item for item in tree.body
    if isinstance(item, ast.FunctionDef)
    and item.name == "select_answer"
)

lines = source.splitlines(keepends=True)
part = "".join(lines[node.lineno - 1:node.end_lineno])

# Insert before the final rerun, not the expiry rerun.
position = part.rfind("    st.rerun()")

if position == -1:
    raise ValueError(
        "Cannot locate select_answer rerun."
    )

part = (
    part[:position]
    + "    persist_quiz_progress()\n"
    + part[position:]
)

lines[node.lineno - 1:node.end_lineno] = [part]
source = "".join(lines)


# Save progress when navigating between questions.
tree = ast.parse(source)
node = next(
    item for item in tree.body
    if isinstance(item, ast.FunctionDef)
    and item.name == "go_to_question"
)

lines = source.splitlines(keepends=True)
part = "".join(lines[node.lineno - 1:node.end_lineno])

navigation = (
    "        st.session_state.quiz_question_index = index\n"
    "        st.rerun()"
)

if navigation not in part:
    raise ValueError(
        "Cannot locate quiz navigation code."
    )

part = part.replace(
    navigation,
    "        st.session_state.quiz_question_index = index\n"
    "        persist_quiz_progress()\n"
    "        st.rerun()",
    1,
)

lines[node.lineno - 1:node.end_lineno] = [part]
source = "".join(lines)


# Finalize the PostgreSQL attempt when quiz finishes.
finish_anchor = (
    "    st.session_state.quiz_finished_at = finished_at"
)

finish_replacement = '''
    if not st.session_state.get("quiz_retry_mode"):

        updated = finish_attempt(
            st.session_state.quiz_attempt_id,
            st.session_state.browser_id,
            "quiz",
            st.session_state.quiz_answers,
            (
                "expired"
                if reason == "time_expired"
                else "submitted"
            ),
        )

        if not updated:
            raise RuntimeError(
                "Unable to finalize the saved quiz."
            )

    st.session_state.quiz_finished_at = finished_at
'''

if finish_anchor not in source:
    raise ValueError("Quiz finish code was not found.")

source = source.replace(
    finish_anchor,
    finish_replacement.rstrip(),
    1,
)


# Start New Quiz must create a new database attempt.
new_quiz_anchor = (
    "            reset_quiz(questions)\n\n"
    "            st.session_state.quiz_retry_mode = False"
)

if new_quiz_anchor not in source:
    raise ValueError(
        "Start New Quiz section was not found."
    )

source = source.replace(
    new_quiz_anchor,
    "            start_persisted_quiz(questions)\n\n"
    "            st.session_state.quiz_retry_mode = False",
    1,
)


# Wait for the browser identifier before loading questions.
show_quiz_anchor = (
    "    try:\n"
    "        initialize_quiz()\n"
)

show_quiz_replacement = '''
    browser_id = get_browser_id()

    if not browser_id:

        st.info(
            "Checking browser identity. "
            "If this is your first visit, "
            "click Initialize Browser."
        )

        if st.button(
            "Initialize Browser",
            key="quiz_initialize_browser",
        ):
            create_browser_id()
            st.info(
                "Browser identifier submitted for saving. "
                "Click Continue after it is saved."
            )

        if st.button(
            "Continue",
            key="quiz_identity_continue",
        ):
            st.rerun()

        return

    try:
        initialize_quiz()
'''

if show_quiz_anchor not in source:
    raise ValueError(
        "Quiz initialization call was not found."
    )

source = source.replace(
    show_quiz_anchor,
    show_quiz_replacement.lstrip("\n"),
    1,
)


# Verify all required recovery functions exist.
required_functions = [
    "persist_quiz_progress",
    "start_persisted_quiz",
    "initialize_quiz",
    "show_quiz",
]

tree = ast.parse(source, filename="quiz.py")

function_names = {
    node.name
    for node in tree.body
    if isinstance(node, ast.FunctionDef)
}

for name in required_functions:
    if name not in function_names:
        raise ValueError(
            f"Missing function after update: {name}"
        )


# Only replace quiz.py after the syntax check passes.
shutil.copy2(quiz_file, backup_file)

quiz_file.write_text(
    source,
    encoding="utf-8",
)

print("SUCCESS: Recovery code installed.")
print("Python syntax check passed.")
print("Backup saved as quiz_before_recovery.py")
print("Original quiz design preserved.")
