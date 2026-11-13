from __future__ import annotations

import ast
import json
import signal
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List

import pandas as pd
import streamlit as st
from streamlit_ace import st_ace


# =========================================================
# PAGE CONFIG
# =========================================================
st.set_page_config(
    page_title="Logic Bridge Lab",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded",
)

# =========================================================
# STYLE
# =========================================================
st.markdown(
    """
    <style>
    .main-title {
        font-size: 2.2rem;
        font-weight: 800;
        margin-bottom: 0.15rem;
    }
    .sub-title {
        color: #A9B8FF;
        font-size: 1rem;
        margin-bottom: 1rem;
    }
    .mini-tag {
        display: inline-block;
        padding: 0.2rem 0.6rem;
        border-radius: 999px;
        background: #E8EDFF;
        color: #1E2A78;
        font-size: 0.8rem;
        font-weight: 600;
        margin-right: 0.35rem;
        margin-bottom: 0.3rem;
    }
    .panel-box {
        padding: 0.9rem 1rem;
        border-radius: 14px;
        background: rgba(255,255,255,0.04);
        border: 1px solid rgba(255,255,255,0.08);
        margin-bottom: 0.9rem;
    }
    .step-box {
        padding: 0.75rem 0.9rem;
        border-radius: 12px;
        background: #151A2D;
        border: 1px solid #2C3559;
        margin-bottom: 0.6rem;
    }
    .status-good {
        padding: 0.8rem 1rem;
        border-radius: 10px;
        background: #102A1B;
        border: 1px solid #2B7A4B;
        margin-bottom: 0.6rem;
    }
    .status-warn {
        padding: 0.8rem 1rem;
        border-radius: 10px;
        background: #2D240E;
        border: 1px solid #A47C1B;
        margin-bottom: 0.6rem;
    }
    .status-bad {
        padding: 0.8rem 1rem;
        border-radius: 10px;
        background: #2B1414;
        border: 1px solid #B04B4B;
        margin-bottom: 0.6rem;
    }
    .knowledge-locked {
        padding: 0.8rem;
        border-radius: 10px;
        border: 1px solid #505050;
        background: #171717;
        margin-bottom: 0.6rem;
    }
    .knowledge-unlocked {
        padding: 0.8rem;
        border-radius: 10px;
        border: 1px solid #2D7D46;
        background: #13291C;
        margin-bottom: 0.6rem;
    }
    .muted {
        color: #B9C0D0;
        font-size: 0.92rem;
    }
    .explorer-item {
        padding: 0.55rem 0.75rem;
        border-radius: 10px;
        border: 1px solid #2C3559;
        background: #111629;
        margin-bottom: 0.45rem;
    }
    .assistant-card {
        padding: 0.8rem;
        border-radius: 12px;
        border: 1px solid #39436F;
        background: #141C33;
        margin-bottom: 0.65rem;
    }
    .assistant-card-green {
        padding: 0.8rem;
        border-radius: 12px;
        border: 1px solid #2D7D46;
        background: #13291C;
        margin-bottom: 0.65rem;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# =========================================================
# STORAGE
# =========================================================
DATA_DIR = Path("data")
SUBMISSION_FILE = DATA_DIR / "submissions.jsonl"

# =========================================================
# PROJECT CONSTANTS
# =========================================================
PROJECT_TITLE = "Logic Bridge Lab"
PROJECT_TAGLINE = (
    "A structured learning platform for translating mathematical reasoning into executable Python code."
)

LEARNING_RULE = [
    "Think: articulate the mathematical logic first",
    "Pair: compare and refine logic collaboratively",
    "GenAI Support: use AI strategically for checking, debugging, and testing",
    "Audit: critically evaluate AI outputs before accepting them",
    "Reflect: identify what AI helped with and what still required human judgement",
]

SAFE_BUILTINS = {
    "abs": abs,
    "min": min,
    "max": max,
    "range": range,
    "len": len,
    "int": int,
    "float": float,
    "str": str,
    "tuple": tuple,
    "list": list,
    "bool": bool,
    "print": print,
    "enumerate": enumerate,
}

BLOCKED_NAMES = {
    "open",
    "exec",
    "eval",
    "compile",
    "input",
    "__import__",
    "globals",
    "locals",
    "vars",
    "dir",
    "getattr",
    "setattr",
    "delattr",
    "help",
    "quit",
    "exit",
    "os",
    "sys",
    "subprocess",
    "pathlib",
    "shutil",
}

KNOWLEDGE_LIBRARY = {
    "modulo": {
        "title": "Modulo (%)",
        "body": "Use `a % b` to get the remainder. In the Euclidean Algorithm, repeatedly replacing `(a, b)` with `(b, a % b)` helps find the gcd.",
    },
    "while_loop": {
        "title": "while loop",
        "body": "A `while` loop repeats until a condition becomes false. It is useful for step-by-step reduction algorithms such as gcd.",
    },
    "function_reuse": {
        "title": "Function Reuse",
        "body": "A helper function such as `gcd(a, b)` can be reused inside another function like `simplify_fraction(a, b)`.",
    },
    "edge_cases": {
        "title": "Edge Cases",
        "body": "Always think about special inputs such as denominator = 0, already simplified fractions, or unexpected values.",
    },
    "tuple_return": {
        "title": "Tuple Return",
        "body": "A function can return more than one value using a tuple, e.g. `return (2, 3)`.",
    },
    "testing": {
        "title": "Testing Mindset",
        "body": "Passing visible tests is not enough. Good programmers test normal cases, edge cases, and hidden cases.",
    },
    "debugging": {
        "title": "Debugging",
        "body": "When code fails, ask: is it syntax, logic, wrong function name, or edge-case handling?",
    },
}

MISSIONS = [
    {
        "id": "gcd",
        "title": "Mission 1: Build gcd(a, b)",
        "goal": "Write a function `gcd(a, b)` that returns the greatest common divisor of two integers.",
        "starter_code": """def gcd(a, b):
    # TODO: use the Euclidean Algorithm
    pass
""",
        "function_name": "gcd",
        "public_tests": [
            {"input": (8, 12), "expected": 4},
            {"input": (7, 13), "expected": 1},
        ],
        "hidden_tests": [
            {"input": (24, 18), "expected": 6},
            {"input": (9, 0), "expected": 9},
        ],
        "unlocks": ["modulo", "while_loop", "testing"],
        "hints": [
            "Use a loop until `b == 0`.",
            "A common update pattern is `a, b = b, a % b`.",
            "When the loop ends, `a` is usually the gcd.",
        ],
        "common_mistakes": [
            "Forgetting to update both `a` and `b` inside the loop.",
            "Using division `/` instead of modulo `%`.",
            "Returning `b` instead of `a` at the end.",
        ],
    },
    {
        "id": "simplify_fraction",
        "title": "Mission 2: Build simplify_fraction(a, b)",
        "goal": "Write a function `simplify_fraction(a, b)` that returns a simplified fraction as a tuple `(numerator, denominator)`.",
        "starter_code": """def gcd(a, b):
    while b != 0:
        a, b = b, a % b
    return a

def simplify_fraction(a, b):
    # TODO: return a simplified fraction as (num, den)
    pass
""",
        "function_name": "simplify_fraction",
        "public_tests": [
            {"input": (8, 12), "expected": (2, 3)},
            {"input": (7, 13), "expected": (7, 13)},
        ],
        "hidden_tests": [
            {"input": (12, 18), "expected": (2, 3)},
            {"input": (10, 5), "expected": (2, 1)},
        ],
        "unlocks": ["function_reuse", "tuple_return", "debugging"],
        "hints": [
            "First compute the gcd of numerator and denominator.",
            "Then divide both numbers by the gcd.",
            "Return the result as a tuple, e.g. `(2, 3)`.",
        ],
        "common_mistakes": [
            "Returning a list instead of a tuple.",
            "Forgetting to divide both numbers by the gcd.",
            "Calling the wrong helper function name.",
        ],
    },
    {
        "id": "safe_simplify_fraction",
        "title": "Mission 3: Handle edge cases",
        "goal": "Write a function `safe_simplify_fraction(a, b)` that returns `'Undefined'` if the denominator is 0; otherwise return a simplified tuple.",
        "starter_code": """def gcd(a, b):
    while b != 0:
        a, b = b, a % b
    return a

def safe_simplify_fraction(a, b):
    # TODO: if denominator is 0, return "Undefined"
    # otherwise return a simplified tuple
    pass
""",
        "function_name": "safe_simplify_fraction",
        "public_tests": [
            {"input": (5, 0), "expected": "Undefined"},
            {"input": (8, 12), "expected": (2, 3)},
        ],
        "hidden_tests": [
            {"input": (7, 13), "expected": (7, 13)},
            {"input": (10, 5), "expected": (2, 1)},
        ],
        "unlocks": ["edge_cases", "testing"],
        "hints": [
            "Check the denominator first.",
            "If `b == 0`, return the string `'Undefined'`.",
            "Otherwise, simplify the fraction as before.",
        ],
        "common_mistakes": [
            "Checking denominator too late.",
            "Returning None for denominator = 0.",
            "Handling normal cases but forgetting edge cases.",
        ],
    },
]

PAGES = [
    "1. Home",
    "2. Think",
    "3. Pair",
    "4. GenAI Support",
    "5. Audit",
    "6. Reflect",
    "7. Teacher Dashboard",
    "8. Code Lab IDE",
]

# =========================================================
# UTILITY
# =========================================================
def now_utc_str() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")


def ensure_storage() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    if not SUBMISSION_FILE.exists():
        SUBMISSION_FILE.touch()


def load_submissions() -> List[Dict[str, Any]]:
    ensure_storage()
    rows: List[Dict[str, Any]] = []
    with SUBMISSION_FILE.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                try:
                    rows.append(json.loads(line))
                except Exception:
                    pass
    return rows


def append_submission(record: Dict[str, Any]) -> None:
    ensure_storage()
    with SUBMISSION_FILE.open("a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False, default=str) + "\n")


def get_mission_by_id(mission_id: str) -> Dict[str, Any]:
    for mission in MISSIONS:
        if mission["id"] == mission_id:
            return mission
    return MISSIONS[0]


def normalize_result(x: Any) -> Any:
    if isinstance(x, list) and len(x) == 2:
        return tuple(x)
    return x


# =========================================================
# EXECUTION TIME LIMIT
# =========================================================
class TimeoutException(Exception):
    pass


@contextmanager
def time_limit(seconds: int = 2):
    def signal_handler(signum, frame):
        raise TimeoutException("Code execution timed out.")

    if hasattr(signal, "SIGALRM"):
        old_handler = signal.signal(signal.SIGALRM, signal_handler)
        signal.alarm(seconds)
        try:
            yield
        finally:
            signal.alarm(0)
            signal.signal(signal.SIGALRM, old_handler)
    else:
        yield


# =========================================================
# SESSION
# =========================================================
def init_session() -> None:
    defaults = {
        "page": PAGES[0],
        "group_id": "",
        "class_id": "",
        "student_count": 3,
        "think_math": "",
        "think_python": "",
        "pair_pseudocode": "",
        "pair_roles": "",
        "pair_tests": "",
        "genai_reason": "",
        "genai_prompt": "",
        "genai_output": "",
        "genai_use": "",
        "audit_accuracy": False,
        "audit_clarity": False,
        "audit_edge_cases": False,
        "audit_overreliance": False,
        "audit_judgement": "",
        "reflect_helpful": "",
        "reflect_human": "",
        "reflect_next": "",
        "think_done": False,
        "pair_done": False,
        "genai_done": False,
        "audit_done": False,
        "reflect_done": False,
        "selected_mission": MISSIONS[0]["id"],
        "completed_missions": [],
        "unlocked_knowledge": [],
        "mission_feedback": {},
        "hint_levels": {m["id"]: 0 for m in MISSIONS},
        "code_buffers": {m["id"]: m["starter_code"] for m in MISSIONS},
        "last_submission_message": "",
        "teacher_live_code": "",
        "teacher_checker_mission": MISSIONS[0]["id"],
        "teacher_live_feedback": None,
        "last_checked_mission": None,
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v


def current_stage_flags() -> Dict[str, bool]:
    return {
        "think_done": st.session_state.think_done,
        "pair_done": st.session_state.pair_done,
        "genai_done": st.session_state.genai_done,
        "audit_done": st.session_state.audit_done,
        "reflect_done": st.session_state.reflect_done,
    }


def completeness_score() -> str:
    flags = current_stage_flags()
    return f"{sum(flags.values())}/5"


def current_draft_summary() -> Dict[str, Any]:
    flags = current_stage_flags()
    return {
        "group_id": st.session_state.group_id or "Not set",
        "class_id": st.session_state.class_id or "Not set",
        "student_count": st.session_state.student_count,
        "completed_stages": sum(flags.values()),
        "completeness_score": completeness_score(),
        "missions_completed": len(st.session_state.completed_missions),
        "knowledge_unlocked": len(st.session_state.unlocked_knowledge),
    }


def build_evidence_archive() -> Dict[str, Any]:
    return {
        "draft": {
            "group_id": st.session_state.group_id,
            "class_id": st.session_state.class_id,
            "student_count": st.session_state.student_count,
            "think": {
                "math_reasoning": st.session_state.think_math,
                "python_bridge": st.session_state.think_python,
                "done": st.session_state.think_done,
            },
            "pair": {
                "pseudocode": st.session_state.pair_pseudocode,
                "group_roles": st.session_state.pair_roles,
                "test_cases": st.session_state.pair_tests,
                "done": st.session_state.pair_done,
            },
            "genai_support": {
                "reason_for_ai": st.session_state.genai_reason,
                "prompt": st.session_state.genai_prompt,
                "ai_suggestion_summary": st.session_state.genai_output,
                "use_decision": st.session_state.genai_use,
                "done": st.session_state.genai_done,
            },
            "audit": {
                "accuracy_checked": st.session_state.audit_accuracy,
                "clarity_checked": st.session_state.audit_clarity,
                "edge_cases_checked": st.session_state.audit_edge_cases,
                "overreliance_checked": st.session_state.audit_overreliance,
                "final_judgement": st.session_state.audit_judgement,
                "done": st.session_state.audit_done,
            },
            "reflect": {
                "what_ai_helped_with": st.session_state.reflect_helpful,
                "what_required_human_judgement": st.session_state.reflect_human,
                "what_to_improve_next_time": st.session_state.reflect_next,
                "done": st.session_state.reflect_done,
            },
        },
        "code_lab": {
            "completed_missions": st.session_state.completed_missions,
            "unlocked_knowledge": st.session_state.unlocked_knowledge,
            "latest_feedback": st.session_state.mission_feedback,
        },
    }


def build_submission_record() -> Dict[str, Any]:
    flags = current_stage_flags()
    return {
        "timestamp": now_utc_str(),
        "group_id": st.session_state.group_id or "",
        "class_id": st.session_state.class_id or "",
        "student_count": st.session_state.student_count,
        "think_done": flags["think_done"],
        "pair_done": flags["pair_done"],
        "genai_done": flags["genai_done"],
        "audit_done": flags["audit_done"],
        "reflect_done": flags["reflect_done"],
        "completeness_score": completeness_score(),
        "final_judgement": st.session_state.audit_judgement or "Not set",
        "missions_completed": list(st.session_state.completed_missions),
        "unlocked_knowledge": list(st.session_state.unlocked_knowledge),
        "evidence_archive": build_evidence_archive(),
    }


def summary_dataframe(records: List[Dict[str, Any]]) -> pd.DataFrame:
    if not records:
        return pd.DataFrame(
            columns=[
                "timestamp",
                "group_id",
                "class_id",
                "student_count",
                "think_done",
                "pair_done",
                "genai_done",
                "audit_done",
                "reflect_done",
                "completeness_score",
                "final_judgement",
                "missions_completed",
                "knowledge_unlocked",
            ]
        )

    rows = []
    for r in records:
        rows.append(
            {
                "timestamp": r.get("timestamp", ""),
                "group_id": r.get("group_id", ""),
                "class_id": r.get("class_id", ""),
                "student_count": r.get("student_count", ""),
                "think_done": "✅" if r.get("think_done") else "",
                "pair_done": "✅" if r.get("pair_done") else "",
                "genai_done": "✅" if r.get("genai_done") else "",
                "audit_done": "✅" if r.get("audit_done") else "",
                "reflect_done": "✅" if r.get("reflect_done") else "",
                "completeness_score": r.get("completeness_score", ""),
                "final_judgement": r.get("final_judgement", ""),
                "missions_completed": len(r.get("missions_completed", [])),
                "knowledge_unlocked": len(r.get("unlocked_knowledge", [])),
            }
        )
    return pd.DataFrame(rows)


# =========================================================
# CODE CHECKER
# =========================================================
def validate_ast(tree: ast.AST) -> List[str]:
    errors = []
    for node in ast.walk(tree):
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            errors.append("Import statements are not allowed in this code lab.")
        if isinstance(node, ast.Attribute):
            errors.append("Attribute access is not allowed in this code lab.")
        if isinstance(node, (ast.Global, ast.Nonlocal, ast.ClassDef, ast.Lambda)):
            errors.append(f"{type(node).__name__} is not allowed here.")
        if isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name) and node.func.id in BLOCKED_NAMES:
                errors.append(f"The function `{node.func.id}` is not allowed.")
        if isinstance(node, ast.Name) and node.id in BLOCKED_NAMES:
            errors.append(f"The name `{node.id}` is not allowed.")
    return list(set(errors))


def grade_code(code: str, mission: Dict[str, Any]) -> Dict[str, Any]:
    total_tests = len(mission["public_tests"]) + len(mission["hidden_tests"])

    try:
        tree = ast.parse(code)
    except SyntaxError as e:
        return {
            "ok": False,
            "type": "syntax",
            "level": "error",
            "message": f"Syntax error at line {e.lineno}: {e.msg}",
            "passed": 0,
            "total": total_tests,
            "details": [],
        }

    ast_errors = validate_ast(tree)
    if ast_errors:
        return {
            "ok": False,
            "type": "safety",
            "level": "error",
            "message": " | ".join(ast_errors),
            "passed": 0,
            "total": total_tests,
            "details": [],
        }

    env = {"__builtins__": SAFE_BUILTINS}

    try:
        with time_limit(2):
            exec(compile(tree, filename="<student_code>", mode="exec"), env, env)
    except TimeoutException as e:
        return {
            "ok": False,
            "type": "timeout",
            "level": "error",
            "message": str(e),
            "passed": 0,
            "total": total_tests,
            "details": [],
        }
    except Exception as e:
        return {
            "ok": False,
            "type": "runtime",
            "level": "error",
            "message": f"Runtime error while defining your function: {e}",
            "passed": 0,
            "total": total_tests,
            "details": [],
        }

    fn = env.get(mission["function_name"])
    if not callable(fn):
        return {
            "ok": False,
            "type": "missing_function",
            "level": "error",
            "message": f"Please define a function named `{mission['function_name']}`.",
            "passed": 0,
            "total": total_tests,
            "details": [],
        }

    all_tests = []
    for t in mission["public_tests"]:
        all_tests.append({**t, "public": True})
    for t in mission["hidden_tests"]:
        all_tests.append({**t, "public": False})

    passed = 0
    details = []

    for test in all_tests:
        args = test["input"]
        expected = test["expected"]
        try:
            with time_limit(2):
                result = fn(*args)
            result = normalize_result(result)
            ok = result == expected
        except TimeoutException:
            result = "Timed out"
            ok = False
        except Exception as e:
            result = f"Error: {e}"
            ok = False

        if ok:
            passed += 1

        details.append(
            {
                "input": args,
                "expected": expected,
                "result": result,
                "ok": ok,
                "public": test["public"],
            }
        )

    success = passed == total_tests

    if success:
        msg = "Excellent! Your code passed all public and hidden tests."
        level = "correct"
    else:
        public_failed = [d for d in details if d["public"] and not d["ok"]]
        if public_failed:
            f = public_failed[0]
            msg = (
                f"Not quite yet. Public test failed for input {f['input']}. "
                f"Expected {f['expected']}, but got {f['result']}."
            )
            level = "partial"
        else:
            msg = "Your code passed the visible tests, but some hidden tests failed. Check edge cases and robustness."
            level = "partial"

    return {
        "ok": success,
        "type": "graded",
        "level": level,
        "message": msg,
        "passed": passed,
        "total": total_tests,
        "details": details,
    }


def unlock_for_mission(mission: Dict[str, Any]) -> None:
    if mission["id"] not in st.session_state.completed_missions:
        st.session_state.completed_missions.append(mission["id"])

    for item in mission["unlocks"]:
        if item not in st.session_state.unlocked_knowledge:
            st.session_state.unlocked_knowledge.append(item)


# =========================================================
# RENDER HELPERS
# =========================================================
def render_header() -> None:
    st.markdown(f"<div class='main-title'>🧠 {PROJECT_TITLE}</div>", unsafe_allow_html=True)
    st.markdown(f"<div class='sub-title'>{PROJECT_TAGLINE}</div>", unsafe_allow_html=True)

    tags = ["Think", "Pair", "GenAI", "Audit", "Reflect", "Code IDE"]
    st.markdown("".join([f"<span class='mini-tag'>{t}</span>" for t in tags]), unsafe_allow_html=True)


def ace_editor(label: str, value: str, key: str, height: int = 360) -> str:
    st.markdown(f"**{label}**")
    code = st_ace(
        value=value,
        language="python",
        theme="monokai",
        key=key,
        height=height,
        font_size=14,
        tab_size=4,
        show_gutter=True,
        show_print_margin=False,
        wrap=True,
        auto_update=True,
    )
    return code if code is not None else value


def render_feedback_panel(feedback: Dict[str, Any] | None, mission: Dict[str, Any]) -> None:
    if not feedback:
        st.info("Run your code to see feedback.")
        return

    level = feedback.get("level", "partial")
    if level == "correct":
        st.markdown(
            f"<div class='status-good'><b>Status:</b> Correct ✅<br>{feedback['message']}</div>",
            unsafe_allow_html=True,
        )
    elif level == "error":
        st.markdown(
            f"<div class='status-bad'><b>Status:</b> Error ❌<br>{feedback['message']}</div>",
            unsafe_allow_html=True,
        )
    else:
        st.markdown(
            f"<div class='status-warn'><b>Status:</b> Almost there ⚠️<br>{feedback['message']}</div>",
            unsafe_allow_html=True,
        )

    st.markdown(f"**Score:** {feedback['passed']} / {feedback['total']} tests")

    public_rows = []
    for d in feedback.get("details", []):
        if d["public"]:
            public_rows.append(
                {
                    "Input": str(d["input"]),
                    "Expected": str(d["expected"]),
                    "Your Result": str(d["result"]),
                    "Pass": "✅" if d["ok"] else "❌",
                }
            )

    if public_rows:
        st.dataframe(pd.DataFrame(public_rows), use_container_width=True, hide_index=True)

    st.markdown("**Mission hints**")
    shown = st.session_state.hint_levels.get(mission["id"], 0)
    if shown == 0:
        st.write("- Click **Show Next Hint** to reveal guided hints one by one.")
    else:
        for i in range(min(shown, len(mission["hints"]))):
            st.write(f"- {mission['hints'][i]}")


def render_sidebar() -> None:
    with st.sidebar:
        st.markdown(f"## {PROJECT_TITLE}")
        st.caption("Pedagogy-led AI support for the logic-to-code transition")

        page = st.radio("Navigation", PAGES, index=PAGES.index(st.session_state.page))
        st.session_state.page = page

        st.markdown("---")
        with st.expander("Current Group Setup", expanded=True):
            st.session_state.group_id = st.text_input("Group ID", value=st.session_state.group_id)
            st.session_state.class_id = st.text_input("Class / Tutorial Group", value=st.session_state.class_id)
            st.session_state.student_count = st.number_input(
                "Number of Students in Group",
                min_value=1,
                max_value=10,
                value=int(st.session_state.student_count),
                step=1,
            )

        st.markdown("---")
        st.markdown("### Progress")
        flags = current_stage_flags()
        done = sum(flags.values())
        st.progress(done / 5)
        st.write(f"{done}/5 stages completed")

        st.write(f"{'✅' if st.session_state.think_done else '⬜'} Think")
        st.write(f"{'✅' if st.session_state.pair_done else '⬜'} Pair")
        st.write(f"{'✅' if st.session_state.genai_done else '⬜'} GenAI")
        st.write(f"{'✅' if st.session_state.audit_done else '⬜'} Audit")
        st.write(f"{'✅' if st.session_state.reflect_done else '⬜'} Reflect")

        st.markdown("---")
        if st.button("Reset Current Draft", use_container_width=True):
            st.session_state.think_math = ""
            st.session_state.think_python = ""
            st.session_state.pair_pseudocode = ""
            st.session_state.pair_roles = ""
            st.session_state.pair_tests = ""
            st.session_state.genai_reason = ""
            st.session_state.genai_prompt = ""
            st.session_state.genai_output = ""
            st.session_state.genai_use = ""
            st.session_state.audit_accuracy = False
            st.session_state.audit_clarity = False
            st.session_state.audit_edge_cases = False
            st.session_state.audit_overreliance = False
            st.session_state.audit_judgement = ""
            st.session_state.reflect_helpful = ""
            st.session_state.reflect_human = ""
            st.session_state.reflect_next = ""
            st.session_state.think_done = False
            st.session_state.pair_done = False
            st.session_state.genai_done = False
            st.session_state.audit_done = False
            st.session_state.reflect_done = False
            st.session_state.last_submission_message = ""
            st.rerun()


# =========================================================
# PAGES
# =========================================================
def render_home() -> None:
    render_header()
    st.markdown("---")

    left, right = st.columns([2, 1])

    with left:
        st.subheader("Learning Rule")
        st.markdown(
            f"""
            <div class='panel-box'>
                <b>Think → Pair → GenAI → Audit → Reflect</b><br><br>
                <ol>
                    {''.join([f"<li>{x}</li>" for x in LEARNING_RULE])}
                </ol>
            </div>
            """,
            unsafe_allow_html=True,
        )

        st.markdown(
            """
            <div class='status-good'><b>Pedagogical principle:</b> AI is used as a scaffold, not as an answer engine.</div>
            <div class='status-warn'><b>Classroom rule:</b> Students should attempt the task before using AI.</div>
            """,
            unsafe_allow_html=True,
        )

        st.subheader("New IDE-style upgrade")
        st.markdown(
            """
            - Left panel: task explorer + step-by-step learning path  
            - Middle panel: syntax-highlighted Python editor  
            - Right panel: teaching assistant + knowledge cards + debugging prompts  
            - Teacher can paste code for live checking  
            - Students unlock knowledge as they complete missions
            """
        )

    with right:
        summary = current_draft_summary()
        st.subheader("Current Draft Summary")
        st.markdown(f"**Group ID**  \n{summary['group_id']}")
        st.markdown(f"**Class**  \n{summary['class_id']}")
        st.markdown(f"**Student Count**  \n{summary['student_count']}")
        st.markdown(f"**Completed Stages**  \n{summary['completed_stages']}/5")
        st.markdown(f"**Knowledge Unlocked**  \n{summary['knowledge_unlocked']}")
        st.markdown(f"**Code Missions Completed**  \n{summary['missions_completed']}")


def render_think() -> None:
    render_header()
    st.markdown("---")
    st.subheader("Think")

    with st.form("think_form"):
        think_math = st.text_area(
            "1) Explain the mathematical logic for simplifying a fraction",
            value=st.session_state.think_math,
            height=160,
        )
        think_python = st.text_area(
            "2) Bridge the idea to Python",
            value=st.session_state.think_python,
            height=140,
        )
        submitted = st.form_submit_button("Save Think Stage")

    if submitted:
        st.session_state.think_math = think_math
        st.session_state.think_python = think_python
        st.session_state.think_done = bool(think_math.strip() or think_python.strip())
        st.success("Think stage saved.")


def render_pair() -> None:
    render_header()
    st.markdown("---")
    st.subheader("Pair")

    with st.form("pair_form"):
        pseudocode = st.text_area(
            "Group pseudocode / algorithm sketch",
            value=st.session_state.pair_pseudocode,
            height=180,
        )
        roles = st.text_area(
            "Group roles / collaboration notes",
            value=st.session_state.pair_roles,
            height=100,
        )
        tests = st.text_area(
            "Planned test cases",
            value=st.session_state.pair_tests,
            height=100,
        )
        submitted = st.form_submit_button("Save Pair Stage")

    if submitted:
        st.session_state.pair_pseudocode = pseudocode
        st.session_state.pair_roles = roles
        st.session_state.pair_tests = tests
        st.session_state.pair_done = bool(pseudocode.strip() or roles.strip() or tests.strip())
        st.success("Pair stage saved.")


def render_genai() -> None:
    render_header()
    st.markdown("---")
    st.subheader("GenAI Support")

    with st.form("genai_form"):
        reason = st.text_area("Why are you using AI at this point?", value=st.session_state.genai_reason, height=80)
        prompt = st.text_area("What prompt would you ask?", value=st.session_state.genai_prompt, height=140)
        output = st.text_area("What did the AI suggest? (summary only)", value=st.session_state.genai_output, height=120)
        use_decision = st.text_area("Did you use the suggestion? Why or why not?", value=st.session_state.genai_use, height=120)
        submitted = st.form_submit_button("Save GenAI Stage")

    if submitted:
        st.session_state.genai_reason = reason
        st.session_state.genai_prompt = prompt
        st.session_state.genai_output = output
        st.session_state.genai_use = use_decision
        st.session_state.genai_done = bool(reason.strip() or prompt.strip() or output.strip() or use_decision.strip())
        st.success("GenAI stage saved.")


def render_audit() -> None:
    render_header()
    st.markdown("---")
    st.subheader("Audit")

    with st.form("audit_form"):
        c1, c2 = st.columns(2)
        with c1:
            accuracy = st.checkbox("We checked mathematical / code correctness", value=st.session_state.audit_accuracy)
            clarity = st.checkbox("We checked whether the explanation is clear", value=st.session_state.audit_clarity)
        with c2:
            edge_cases = st.checkbox("We checked hidden or edge cases", value=st.session_state.audit_edge_cases)
            overreliance = st.checkbox("We discussed whether AI is doing too much thinking for us", value=st.session_state.audit_overreliance)

        judgement = st.text_area("Final judgement about the AI support", value=st.session_state.audit_judgement, height=120)
        submitted = st.form_submit_button("Save Audit Stage")

    if submitted:
        st.session_state.audit_accuracy = accuracy
        st.session_state.audit_clarity = clarity
        st.session_state.audit_edge_cases = edge_cases
        st.session_state.audit_overreliance = overreliance
        st.session_state.audit_judgement = judgement
        st.session_state.audit_done = bool(accuracy or clarity or edge_cases or overreliance or judgement.strip())
        st.success("Audit stage saved.")


def render_reflect() -> None:
    render_header()
    st.markdown("---")
    st.subheader("Reflect")

    with st.form("reflect_form"):
        helpful = st.text_area("What did AI help with?", value=st.session_state.reflect_helpful, height=110)
        human = st.text_area("What still required human judgement?", value=st.session_state.reflect_human, height=110)
        next_time = st.text_area("What would you improve next time?", value=st.session_state.reflect_next, height=110)
        submitted = st.form_submit_button("Save Reflect Stage")

    if submitted:
        st.session_state.reflect_helpful = helpful
        st.session_state.reflect_human = human
        st.session_state.reflect_next = next_time
        st.session_state.reflect_done = bool(helpful.strip() or human.strip() or next_time.strip())
        st.success("Reflect stage saved.")

    st.markdown("---")
    st.subheader("Finalize & Submit")

    if st.button("Submit Current Draft", type="primary"):
        record = build_submission_record()
        append_submission(record)
        st.session_state.last_submission_message = f"Submission saved at {record['timestamp']}."
        st.success(st.session_state.last_submission_message)

    if st.session_state.last_submission_message:
        st.info(st.session_state.last_submission_message)


def render_left_explorer(mission: Dict[str, Any]) -> None:
    st.markdown("### 📁 Learning Explorer")

    for m in MISSIONS:
        done = "✅" if m["id"] in st.session_state.completed_missions else "⬜"
        if st.button(f"{done} {m['title']}", use_container_width=True, key=f"explorer_{m['id']}"):
            st.session_state.selected_mission = m["id"]

    st.markdown("---")
    st.markdown(
        f"""
        <div class='panel-box'>
            <b>Current Mission</b><br><br>
            <span class='muted'>{mission["goal"]}</span>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown("### 🪜 Step Guide")
    steps = [
        ("1. Understand the math idea", st.session_state.think_done),
        ("2. Draft pseudocode / plan", st.session_state.pair_done),
        ("3. Code the function", True),
        ("4. Check visible tests", st.session_state.last_checked_mission == mission["id"]),
        ("5. Reflect on edge cases", st.session_state.audit_done or st.session_state.reflect_done),
    ]
    for label, done in steps:
        st.markdown(
            f"""
            <div class='step-box'>
                {'✅' if done else '⬜'} {label}
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.markdown("### 👀 Public Test Cases")
    for t in mission["public_tests"]:
        st.markdown(
            f"""
            <div class='explorer-item'>
                <b>Input:</b> {t["input"]}<br>
                <b>Expected:</b> {t["expected"]}
            </div>
            """,
            unsafe_allow_html=True,
        )


def render_right_learning_assistant(mission: Dict[str, Any], feedback: Dict[str, Any] | None) -> None:
    st.markdown("### 🤖 Teaching Assistant")

    st.markdown(
        """
        <div class='assistant-card'>
            <b>How to use this panel</b><br>
            <span class='muted'>Read the concept first, then run your code, then compare your result with the hints and test feedback.</span>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown("#### 🎯 Concept Focus")
    for key in mission["unlocks"]:
        unlocked = key in st.session_state.unlocked_knowledge
        item = KNOWLEDGE_LIBRARY[key]
        cls = "assistant-card-green" if unlocked else "assistant-card"
        icon = "🔓" if unlocked else "🔒"
        st.markdown(
            f"""
            <div class='{cls}'>
                <b>{icon} {item["title"]}</b><br>
                <span class='muted'>{item["body"] if unlocked else "Complete the mission to unlock this knowledge card."}</span>
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.markdown("#### 🧩 Common Mistakes")
    for m in mission["common_mistakes"]:
        st.write(f"- {m}")

    st.markdown("#### 🛡 Responsible AI Reminder")
    st.markdown(
        """
        <div class='assistant-card'>
            <b>Before asking AI:</b><br>
            <span class='muted'>
            1. Try your own logic first<br>
            2. Ask AI to explain, not just solve<br>
            3. Check whether the AI answer really matches your task<br>
            4. Keep human judgement in the final decision
            </span>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown("#### 🧠 Feedback Interpretation")
    if not feedback:
        st.info("No feedback yet. Run your code first.")
    else:
        ftype = feedback.get("type")
        if ftype == "syntax":
            st.warning("This is a syntax issue. Check colons, brackets, indentation, or unfinished lines.")
        elif ftype == "missing_function":
            st.warning(f"Your function name must be exactly `{mission['function_name']}`.")
        elif ftype == "runtime":
            st.warning("Your code runs into an error during execution. Check variable names and operations.")
        elif ftype == "timeout":
            st.warning("Your code may be stuck in an infinite loop. Re-check your loop condition.")
        elif feedback.get("ok"):
            st.success("Great. Your solution is correct for both visible and hidden tests.")
        else:
            st.info("You are close. Re-check logic, return value format, and edge cases.")


def render_code_lab_ide() -> None:
    render_header()
    st.markdown("---")
    st.subheader("💻 Code Lab IDE")
    st.caption("Left: guided learning path · Middle: coding workspace · Right: teaching assistant")

    completed = len(st.session_state.completed_missions)
    total = len(MISSIONS)
    c1, c2, c3 = st.columns(3)
    c1.metric("Missions Completed", f"{completed}/{total}")
    c2.metric("Knowledge Unlocked", len(st.session_state.unlocked_knowledge))
    c3.metric("Current Stage Progress", completeness_score())

    st.progress(completed / total if total else 0.0)
    st.markdown("---")

    mission = get_mission_by_id(st.session_state.selected_mission)
    feedback = st.session_state.mission_feedback.get(mission["id"])

    left, middle, right = st.columns([1.05, 1.8, 1.15], gap="large")

    with left:
        render_left_explorer(mission)

    with middle:
        st.markdown(f"### 📝 {mission['title']}")
        code = ace_editor(
            "Write your Python code here",
            st.session_state.code_buffers[mission["id"]],
            key=f"editor_{mission['id']}",
            height=420,
        )
        st.session_state.code_buffers[mission["id"]] = code

        b1, b2, b3, b4 = st.columns(4)
        with b1:
            if st.button("▶ Run / Check", use_container_width=True, key=f"run_{mission['id']}"):
                result = grade_code(code, mission)
                st.session_state.mission_feedback[mission["id"]] = result
                st.session_state.last_checked_mission = mission["id"]
                if result["ok"]:
                    unlock_for_mission(mission)
                st.rerun()

        with b2:
            if st.button("💡 Show Next Hint", use_container_width=True, key=f"hint_{mission['id']}"):
                current = st.session_state.hint_levels.get(mission["id"], 0)
                st.session_state.hint_levels[mission["id"]] = min(current + 1, len(mission["hints"]))
                st.rerun()

        with b3:
            if st.button("📋 Show Tests", use_container_width=True, key=f"tests_{mission['id']}"):
                st.session_state.last_checked_mission = mission["id"]
                st.session_state.mission_feedback.setdefault(
                    mission["id"],
                    {
                        "ok": False,
                        "type": "info",
                        "level": "partial",
                        "message": "Visible tests shown below. Write or refine your code, then run the checker.",
                        "passed": 0,
                        "total": len(mission["public_tests"]) + len(mission["hidden_tests"]),
                        "details": [
                            {
                                "input": t["input"],
                                "expected": t["expected"],
                                "result": "Not run yet",
                                "ok": False,
                                "public": True,
                            }
                            for t in mission["public_tests"]
                        ],
                    },
                )
                st.rerun()

        with b4:
            if st.button("↺ Reset", use_container_width=True, key=f"reset_{mission['id']}"):
                st.session_state.code_buffers[mission["id"]] = mission["starter_code"]
                st.session_state.hint_levels[mission["id"]] = 0
                if mission["id"] in st.session_state.mission_feedback:
                    del st.session_state.mission_feedback[mission["id"]]
                st.rerun()

        st.markdown("---")
        st.markdown("### ✅ Output Console")
        render_feedback_panel(feedback, mission)

        with st.expander("Why this mission matters", expanded=False):
            st.write(mission["goal"])
            st.write("This mission is designed to help students connect mathematical logic with executable Python code.")

    with right:
        render_right_learning_assistant(mission, feedback)

    st.markdown("---")
    tab1, tab2 = st.tabs(["📚 Full Knowledge Map", "👩‍🏫 Teacher Live Checker"])

    with tab1:
        st.subheader("Knowledge Unlock Map")
        unlocked = set(st.session_state.unlocked_knowledge)
        for key, item in KNOWLEDGE_LIBRARY.items():
            if key in unlocked:
                cls = "knowledge-unlocked"
                icon = "🔓"
                body = item["body"]
            else:
                cls = "knowledge-locked"
                icon = "🔒"
                body = "Complete missions to unlock this concept."
            st.markdown(
                f"""
                <div class='{cls}'>
                    <b>{icon} {item["title"]}</b><br>
                    <span class='muted'>{body}</span>
                </div>
                """,
                unsafe_allow_html=True,
            )

    with tab2:
        render_teacher_live_checker()


def render_teacher_live_checker() -> None:
    st.subheader("Teacher Live Checker")
    st.caption("Paste code during class and demonstrate why a solution is correct, partially correct, or incorrect.")

    mission_id = st.selectbox(
        "Choose a checking target",
        options=[m["id"] for m in MISSIONS],
        format_func=lambda x: get_mission_by_id(x)["title"],
        index=[m["id"] for m in MISSIONS].index(st.session_state.teacher_checker_mission),
        key="teacher_checker_select",
    )
    st.session_state.teacher_checker_mission = mission_id
    mission = get_mission_by_id(mission_id)

    default_demo = st.session_state.teacher_live_code or mission["starter_code"]
    teacher_code = ace_editor(
        "Paste demonstration code here",
        default_demo,
        key="teacher_live_editor",
        height=300,
    )
    st.session_state.teacher_live_code = teacher_code

    c1, c2 = st.columns(2)
    with c1:
        if st.button("Check Demo Code", use_container_width=True, key="teacher_check_btn"):
            st.session_state.teacher_live_feedback = grade_code(teacher_code, mission)
    with c2:
        if st.button("Load Starter Code", use_container_width=True, key="teacher_load_starter"):
            st.session_state.teacher_live_code = mission["starter_code"]
            st.rerun()

    if st.session_state.teacher_live_feedback:
        render_feedback_panel(st.session_state.teacher_live_feedback, mission)

    with st.expander("Suggested teacher talk"):
        st.write(
            "Use this checker formatively: show students that 'incorrect' does not always mean 'bad', "
            "and 'correct on visible tests' does not always mean 'fully robust'."
        )


def render_teacher_dashboard() -> None:
    render_header()
    st.markdown("---")
    st.subheader("Teacher Dashboard")

    records = load_submissions()
    summary_df = summary_dataframe(records)

    tab1, tab2, tab3 = st.tabs(["Submission Table", "Live Code Checker", "Evidence Export"])

    with tab1:
        st.caption("This table shows saved submission summaries from the current app storage.")
        st.dataframe(summary_df, use_container_width=True, hide_index=True)

    with tab2:
        render_teacher_live_checker()

    with tab3:
        st.subheader("Download Exports")
        csv_data = summary_df.to_csv(index=False).encode("utf-8")
        json_data = json.dumps(records, ensure_ascii=False, indent=2, default=str).encode("utf-8")

        st.download_button(
            "Download Submission Summary (CSV)",
            data=csv_data,
            file_name="submission_summary.csv",
            mime="text/csv",
        )
        st.download_button(
            "Download Full Evidence Archive (JSON)",
            data=json_data,
            file_name="evidence_archive.json",
            mime="application/json",
        )

        st.markdown("---")
        st.write("- Use coded group IDs rather than personal identifiers.")
        st.write("- Local file storage is suitable for prototype/demo use.")
        st.write("- For long-term use, connect to approved secure storage.")


# =========================================================
# MAIN
# =========================================================
def main() -> None:
    init_session()
    render_sidebar()

    page = st.session_state.page

    if page == "1. Home":
        render_home()
    elif page == "2. Think":
        render_think()
    elif page == "3. Pair":
        render_pair()
    elif page == "4. GenAI Support":
        render_genai()
    elif page == "5. Audit":
        render_audit()
    elif page == "6. Reflect":
        render_reflect()
    elif page == "7. Teacher Dashboard":
        render_teacher_dashboard()
    elif page == "8. Code Lab IDE":
        render_code_lab_ide()
    else:
        render_home()


if __name__ == "__main__":
    main()
