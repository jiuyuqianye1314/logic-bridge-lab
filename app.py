from __future__ import annotations

import ast
from contextlib import contextmanager
from datetime import datetime, timezone
import json
from pathlib import Path
import re
import signal
import threading
from typing import Any, Dict, List, Tuple

import pandas as pd
import streamlit as st
from streamlit_ace import st_ace


# =========================================================
# PAGE CONFIG & COMPLIANCE SETTINGS
# =========================================================
st.set_page_config(
    page_title="Logic Bridge Lab",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Passcode to protect Teacher Dashboard from unauthorized student access
TEACHER_PASSCODE = "MIT1120"

# =========================================================
# STYLE (With explicit light text colors for Dark/Light mode safety)
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
        padding: 0.18rem 0.55rem;
        border-radius: 999px;
        background: #E8EDFF;
        color: #1E2A78;
        font-size: 0.78rem;
        font-weight: 600;
        margin-right: 0.35rem;
        margin-bottom: 0.25rem;
    }
    .panel-box {
        padding: 0.85rem 1rem;
        border-radius: 12px;
        background: #161B2E;
        color: #F0F2F6;
        border: 1px solid #2C3559;
        margin-bottom: 0.85rem;
    }
    .guide-card {
        padding: 0.9rem 1rem;
        border-radius: 12px;
        background: #161D35;
        color: #F0F2F6;
        border: 1px solid #3B4B80;
        border-top: 4px solid #5C7CFA;
        margin-bottom: 0.75rem;
        height: 100%;
    }
    .guide-step-badge {
        display: inline-block;
        padding: 0.15rem 0.55rem;
        border-radius: 6px;
        background: #5C7CFA;
        color: #FFFFFF;
        font-size: 0.78rem;
        font-weight: 700;
        margin-bottom: 0.45rem;
    }
    .step-box {
        padding: 0.65rem 0.85rem;
        border-radius: 10px;
        background: #151A2D;
        color: #F0F2F6;
        border: 1px solid #2C3559;
        margin-bottom: 0.5rem;
        font-size: 0.92rem;
    }
    .status-good {
        padding: 0.8rem 1rem;
        border-radius: 10px;
        background: #102A1B;
        color: #E8F5E9;
        border: 1px solid #2B7A4B;
        margin-bottom: 0.6rem;
        border-left: 5px solid #4CAF50;
    }
    .status-warn {
        padding: 0.8rem 1rem;
        border-radius: 10px;
        background: #2D240E;
        color: #FFF8E1;
        border: 1px solid #A47C1B;
        margin-bottom: 0.6rem;
        border-left: 5px solid #FF9800;
    }
    .status-bad {
        padding: 0.8rem 1rem;
        border-radius: 10px;
        background: #2B1414;
        color: #FFEBEE;
        border: 1px solid #B04B4B;
        margin-bottom: 0.6rem;
        border-left: 5px solid #F44336;
    }
    .muted {
        color: #B9C0D0;
        font-size: 0.9rem;
    }
    .explorer-item {
        padding: 0.55rem 0.75rem;
        border-radius: 10px;
        border: 1px solid #2C3559;
        background: #111629;
        color: #F0F2F6;
        margin-bottom: 0.45rem;
        font-size: 0.9rem;
    }
    .assistant-card {
        padding: 0.8rem;
        border-radius: 12px;
        border: 1px solid #39436F;
        background: #141C33;
        color: #F0F2F6;
        margin-bottom: 0.55rem;
    }
    .assistant-card-green {
        padding: 0.8rem;
        border-radius: 12px;
        border: 1px solid #2D7D46;
        background: #13291C;
        color: #E8F5E9;
        margin-bottom: 0.55rem;
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
    "open", "exec", "eval", "compile", "input", "__import__",
    "globals", "locals", "vars", "dir", "getattr", "setattr",
    "delattr", "help", "quit", "exit", "os", "sys",
    "subprocess", "pathlib", "shutil", "memoryview", "breakpoint",
}

KNOWLEDGE_LIBRARY = {
    "modulo": {
        "title": "Modulo (%)",
        "body": "Use `a % b` to get the remainder. In the Euclidean Algorithm, replacing `(a, b)` with `(b, a % b)` reduces the problem step by step.",
        "example": "12 % 8  # returns 4\na, b = b, a % b",
        "pro_tip": "Math insight: gcd(a, b) == gcd(b, a % b) always holds until b reaches 0.",
    },
    "while_loop": {
        "title": "while loop",
        "body": "A `while` loop repeats until a condition becomes False. Ideal when the exact number of steps is unknown.",
        "example": "while b != 0:\n    a, b = b, a % b\nreturn a",
        "pro_tip": "Always make sure loop variables change inside the loop to avoid infinite loops.",
    },
    "function_reuse": {
        "title": "Function Reuse",
        "body": "Call an existing helper function like `gcd(a, b)` inside a new function instead of rewriting the loop.",
        "example": "def simplify_fraction(a, b):\n    g = gcd(a, b)  # reuse helper!",
        "pro_tip": "Modular code (DRY: Don't Repeat Yourself) makes debugging and testing much easier.",
    },
    "edge_cases": {
        "title": "Edge Cases (Guard Clause)",
        "body": "Check special or invalid inputs (such as `b == 0`) at the very top of your function before performing division.",
        "example": "if b == 0:\n    return 'Undefined'",
        "pro_tip": "Placing guard clauses first prevents ZeroDivisionError before helper functions run.",
    },
    "tuple_return": {
        "title": "Tuple Return & Integer Division",
        "body": "Return two integers as a tuple using parentheses `(num, den)` and integer division `//`.",
        "example": "return (a // g, b // g)  # use // instead of / to keep integers",
        "pro_tip": "In Python, `8 / 4` gives `2.0` (float), whereas `8 // 4` gives `2` (int).",
    },
    "testing": {
        "title": "Testing Mindset",
        "body": "Passing visible tests is not enough. Good programmers test normal cases, coprime pairs, and boundary values like 0.",
        "example": "# Normal: (8, 12) -> (2, 3)\n# Edge: (9, 0) -> 9",
        "pro_tip": "Hidden tests often check inputs where `a < b`, `a == b`, or `b == 0`.",
    },
    "debugging": {
        "title": "Debugging Strategy",
        "body": "Compare Expected vs. Your Result: check return type (`tuple` vs `list`), `None` returns, or `//` vs `/`.",
        "example": "# Check: did you write `return` instead of `print`?",
        "pro_tip": "Tracing variables by hand with small inputs like `(8, 12)` reveals 90% of logic bugs.",
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
            "Use a `while` loop that continues until `b == 0`.",
            "Inside the loop, update both variables simultaneously: `a, b = b, a % b`.",
            "When the loop ends (`b == 0`), `a` holds the greatest common divisor—remember to `return a`.",
        ],
        "common_mistakes": [
            "Forgetting to update both `a` and `b` simultaneously inside the loop.",
            "Using division `/` instead of remainder `%`.",
            "Returning `b` (which is 0) instead of `a` at the end.",
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
            "First compute `g = gcd(a, b)` using the helper function above.",
            "Divide both `a` and `b` by `g` using integer division `//`.",
            "Return the result as a tuple: `return (a // g, b // g)`.",
        ],
        "common_mistakes": [
            "Returning a list `[num, den]` instead of a tuple `(num, den)`.",
            "Using single slash `/` (which produces floats like `2.0`) instead of `//`.",
            "Forgetting to divide both numerator and denominator by `gcd(a, b)`.",
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
            "Check the denominator `b` at the very beginning of the function.",
            "If `b == 0`, immediately return `'Undefined'`.",
            "Otherwise, compute `g = gcd(a, b)` and return `(a // g, b // g)`.",
        ],
        "common_mistakes": [
            "Checking `b == 0` too late (after dividing by `g`, causing ZeroDivisionError).",
            "Returning `None` or printing `'Undefined'` instead of returning the string `'Undefined'`.",
            "Handling `b == 0` properly but forgetting to return a tuple for normal cases.",
        ],
    },
]

PAGES = [
    "1. Home",
    "2. Learning Workspace",
    "3. Teacher Dashboard",
]


# =========================================================
# PRIVACY & COMPLIANCE HELPERS
# =========================================================
def is_valid_anonymous_id(raw_id: str) -> Tuple[bool, str]:
    """Blocks Student IDs (7-8 digits) and email addresses to enforce anonymity."""
    cleaned = raw_id.strip()
    if not cleaned:
        return True, ""
    if "@" in cleaned:
        return False, "Privacy Guard: Do not enter an email address. Use a random code (e.g., MIT_01)."
    if re.search(r"(^|[^0-9])\d{7,8}([^0-9]|$)", cleaned):
        return False, "Privacy Guard: Do not enter a Student ID. Use a random code (e.g., MIT_01)."
    if len(cleaned) > 25:
        return False, "Keep your anonymous code under 25 characters (e.g., MIT_01)."
    return True, ""


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


def clear_all_submissions() -> None:
    ensure_storage()
    SUBMISSION_FILE.write_text("", encoding="utf-8")


def get_mission_by_id(mission_id: str) -> Dict[str, Any]:
    for mission in MISSIONS:
        if mission["id"] == mission_id:
            return mission
    return MISSIONS[0]


def get_unlock_source_label(concept_key: str) -> str:
    """Returns which mission(s) unlock a given knowledge concept."""
    sources = []
    for idx, m in enumerate(MISSIONS, start=1):
        if concept_key in m["unlocks"]:
            sources.append(f"Mission {idx}")
    return " or ".join(sources) if sources else "Code Missions"


def check_result_match(result: Any, expected: Any) -> Tuple[bool, str]:
    if result is None:
        return False, "returned_none"
    if isinstance(expected, tuple) and isinstance(result, list):
        return False, "returned_list_instead_of_tuple"
    if isinstance(expected, tuple) and isinstance(result, tuple) and len(result) == 2:
        if any(isinstance(x, float) for x in result):
            return False, "float_division_used"
    return (result == expected), ""


# =========================================================
# EXECUTION TIME LIMIT (Inherits from BaseException so user code cannot catch it)
# =========================================================
class TimeoutException(BaseException):
    pass


@contextmanager
def time_limit(seconds: int = 2):
    def signal_handler(signum, frame):
        raise TimeoutException("Code execution timed out (possible infinite loop).")

    can_alarm = (
        hasattr(signal, "SIGALRM")
        and threading.current_thread() is threading.main_thread()
    )
    if can_alarm:
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
        "student_count": 1,
        "consent_agreed": False,
        "teacher_authenticated": False,
        "confirm_purge": False,
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
        "run_counts": {m["id"]: 0 for m in MISSIONS},
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


def reset_all_draft_and_lab() -> None:
    st.session_state.group_id = ""
    st.session_state.class_id = ""
    st.session_state.consent_agreed = False
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
    st.session_state.selected_mission = MISSIONS[0]["id"]
    st.session_state.completed_missions = []
    st.session_state.unlocked_knowledge = []
    st.session_state.mission_feedback = {}
    st.session_state.hint_levels = {m["id"]: 0 for m in MISSIONS}
    st.session_state.run_counts = {m["id"]: 0 for m in MISSIONS}
    st.session_state.code_buffers = {m["id"]: m["starter_code"] for m in MISSIONS}
    st.session_state.last_submission_message = ""
    st.session_state.last_checked_mission = None


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
        "compliance": {
            "voluntary_consent_confirmed": st.session_state.consent_agreed,
            "data_purpose": "Anonymous Product Usability & Instructional Design Feedback Only",
        },
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
            "hints_used": dict(st.session_state.hint_levels),
            "run_counts": dict(st.session_state.run_counts),
            "latest_feedback": st.session_state.mission_feedback,
        },
    }


def build_submission_record() -> Dict[str, Any]:
    flags = current_stage_flags()
    return {
        "timestamp": now_utc_str(),
        "consent_confirmed": st.session_state.consent_agreed,
        "group_id": st.session_state.group_id or "Anonymous",
        "class_id": st.session_state.class_id or "General",
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
        "total_hints_used": sum(st.session_state.hint_levels.values()),
        "total_code_runs": sum(st.session_state.run_counts.values()),
        "evidence_archive": build_evidence_archive(),
    }


def summary_dataframe(records: List[Dict[str, Any]]) -> pd.DataFrame:
    if not records:
        return pd.DataFrame(
            columns=[
                "Time",
                "Consent",
                "Group ID",
                "Class",
                "Students",
                "Think",
                "Pair",
                "GenAI",
                "Audit",
                "Reflect",
                "Progress",
                "Missions",
                "Hints",
                "Runs",
                "Unlocked",
            ]
        )

    rows = []
    for r in records:
        rows.append(
            {
                "Time": r.get("timestamp", ""),
                "Consent": "✅" if r.get("consent_confirmed") else "⚠️",
                "Group ID": r.get("group_id", ""),
                "Class": r.get("class_id", ""),
                "Students": r.get("student_count", ""),
                "Think": "✅" if r.get("think_done") else "",
                "Pair": "✅" if r.get("pair_done") else "",
                "GenAI": "✅" if r.get("genai_done") else "",
                "Audit": "✅" if r.get("audit_done") else "",
                "Reflect": "✅" if r.get("reflect_done") else "",
                "Progress": r.get("completeness_score", ""),
                "Missions": len(r.get("missions_completed", [])),
                "Hints": r.get("total_hints_used", 0),
                "Runs": r.get("total_code_runs", 0),
                "Unlocked": len(r.get("unlocked_knowledge", [])),
            }
        )
    return pd.DataFrame(rows)


# =========================================================
# HARDENED CODE SANDBOX CHECKER
# =========================================================
def validate_ast(tree: ast.AST) -> List[str]:
    errors = []
    for node in ast.walk(tree):
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            errors.append("Import statements are not allowed in this code lab.")
        if isinstance(node, ast.Attribute):
            errors.append("Attribute access is not allowed in this code lab.")
        if isinstance(
            node,
            (
                ast.Global,
                ast.Nonlocal,
                ast.ClassDef,
                ast.Lambda,
                ast.Try,
                ast.AsyncFunctionDef,
                ast.AsyncFor,
                ast.AsyncWith,
                ast.Await,
                ast.Yield,
                ast.YieldFrom,
            ),
        ):
            errors.append(f"{type(node).__name__} is not allowed here.")
        if isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name) and node.func.id in BLOCKED_NAMES:
                errors.append(f"The function `{node.func.id}` is not allowed.")
        if isinstance(node, ast.Name):
            if node.id in BLOCKED_NAMES or (node.id.startswith("__") and node.id.endswith("__")):
                errors.append(f"The identifier `{node.id}` is not allowed.")
    return list(set(errors))


def grade_code(code: str, mission: Dict[str, Any]) -> Dict[str, Any]:
    total_tests = len(mission["public_tests"]) + len(mission["hidden_tests"])

    if len(code) > 2500:
        return {
            "ok": False,
            "type": "safety",
            "diag_tag": "safety",
            "level": "error",
            "message": "Code length exceeds the 2,500-character sandbox limit.",
            "passed": 0,
            "total": total_tests,
            "details": [],
        }

    try:
        tree = ast.parse(code)
    except SyntaxError as e:
        return {
            "ok": False,
            "type": "syntax",
            "diag_tag": "syntax",
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
            "diag_tag": "safety",
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
            "diag_tag": "timeout",
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
            "diag_tag": "runtime",
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
            "diag_tag": "missing_function",
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
    first_diag_tag = ""

    for test in all_tests:
        args = test["input"]
        expected = test["expected"]
        diag_tag = ""
        try:
            with time_limit(2):
                result = fn(*args)
            ok, diag_tag = check_result_match(result, expected)
        except TimeoutException:
            result = "Timed out"
            ok = False
            diag_tag = "timeout"
        except ZeroDivisionError:
            result = "Error: ZeroDivisionError"
            ok = False
            diag_tag = "zero_division"
        except Exception as e:
            result = f"Error: {e}"
            ok = False
            diag_tag = "runtime_in_call"

        if ok:
            passed += 1
        elif not first_diag_tag and diag_tag:
            first_diag_tag = diag_tag

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
        msg = "Excellent! Your code passed all public and hidden tests — new Knowledge Map badges unlocked!"
        level = "correct"
    else:
        public_failed = [d for d in details if d["public"] and not d["ok"]]
        if public_failed:
            f = public_failed[0]
            msg = (
                f"Not quite yet. Public test failed for input {f['input']}. "
                f"Expected {f['expected']} ({type(f['expected']).__name__}), "
                f"but got {f['result']} ({type(f['result']).__name__})."
            )
            level = "partial"
        else:
            msg = "Your code passed the visible tests, but some hidden tests failed. Check edge cases and robustness."
            level = "partial"

    return {
        "ok": success,
        "type": "graded",
        "diag_tag": first_diag_tag,
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


def ace_editor(label: str, value: str, key: str, height: int = 310) -> str:
    code = st_ace(
        value=value,
        language="python",
        theme="tomorrow_night_eighties",
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
    shown = st.session_state.hint_levels.get(mission["id"], 0)
    if shown > 0:
        st.markdown("**💡 Guided Hints**")
        for i in range(min(shown, len(mission["hints"]))):
            st.info(f"**Hint {i + 1}:** {mission['hints'][i]}")

    if not feedback:
        if shown == 0:
            st.info("Run your code to see test results and diagnostic feedback.")
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


def render_sidebar() -> None:
    with st.sidebar:
        st.markdown(f"## {PROJECT_TITLE}")
        st.caption("Pedagogy-led AI support for the logic-to-code transition")

        page = st.radio("Navigation", PAGES, index=PAGES.index(st.session_state.page))
        st.session_state.page = page

        st.markdown("---")
        with st.expander("1️⃣ Step 1: Anonymous Setup", expanded=True):
            raw_group_id = st.text_input(
                "Anonymous Tester / Group ID",
                value=st.session_state.group_id,
                placeholder="e.g., MIT_01 (Press Enter)",
            )
            id_valid, id_err = is_valid_anonymous_id(raw_group_id)
            if not id_valid:
                st.error(id_err)
            else:
                st.session_state.group_id = raw_group_id.strip()

            st.session_state.class_id = st.text_input(
                "Session / Class Tag",
                value=st.session_state.class_id,
                placeholder="e.g., Tryout_1120",
            )
            st.session_state.student_count = st.number_input(
                "Number of Students",
                min_value=1,
                max_value=10,
                value=int(st.session_state.student_count),
                step=1,
            )

        st.markdown("---")
        st.markdown("### 📊 Progress & Unlocks")
        flags = current_stage_flags()
        done = sum(flags.values())
        st.progress(done / 5)
        st.write(f"{done}/5 stages · {len(st.session_state.completed_missions)}/{len(MISSIONS)} missions")

        st.write(f"{'✅' if st.session_state.think_done else '⬜'} Think (Unlocks Blueprint)")
        st.write(f"{'✅' if st.session_state.pair_done else '⬜'} Pair (Unlocks Pseudocode)")
        st.write(f"{'✅' if st.session_state.genai_done else '⬜'} GenAI Support")
        st.write(f"{'✅' if st.session_state.audit_done else '⬜'} Audit")
        st.write(f"{'✅' if st.session_state.reflect_done else '⬜'} Reflect")
        st.caption("Click 'Save ... Stage' inside each tab to check off items above.")

        st.markdown("---")
        st.markdown("### 💾 Final Save & Submit")
        st.session_state.consent_agreed = st.checkbox(
            "I voluntarily share this anonymous session for tool usability improvement (unrelated to course grades).",
            value=st.session_state.consent_agreed,
            key="sidebar_consent_chk",
        )

        can_submit = st.session_state.consent_agreed and id_valid
        if st.button(
            "💾 Submit Progress",
            type="primary",
            use_container_width=True,
            disabled=not can_submit,
        ):
            record = build_submission_record()
            append_submission(record)
            st.session_state.last_submission_message = f"Saved at {record['timestamp']}."
            st.toast(f"✅ {st.session_state.last_submission_message}")

        if not st.session_state.consent_agreed:
            st.caption("Tick the voluntary consent box above to unlock the Submit button.")

        if st.button("🔄 Reset Current Session", use_container_width=True):
            reset_all_draft_and_lab()
            st.toast("🔄 Session and code workspace reset for next tester!")
            st.rerun()


# =========================================================
# PAGES
# =========================================================
def render_home() -> None:
    render_header()
    st.markdown("---")

    st.subheader("📖 How to Use This App (Student Quick-Start Guide)")
    st.markdown(
        """
        <div class='status-good'>
            <b>🔒 Privacy & Voluntary Participation Notice:</b><br>
            1. Participation is <b>100% voluntary</b> and has <b>zero impact</b> on your course grades or attendance.<br>
            2. All data is <b>strictly anonymous</b> and used solely to improve software usability and instructional design (not for formal research publication).<br>
            3. Please enter a random code (e.g., <code>MIT_01</code>) in the left sidebar—do <b>not</b> enter your real name, Student ID, or email.
        </div>
        """,
        unsafe_allow_html=True,
    )

    g1, g2, g3, g4 = st.columns(4)
    with g1:
        st.markdown(
            """
            <div class='guide-card'>
                <div class='guide-step-badge'>STEP 1 · SETUP</div><br>
                <b>Set Anonymous ID</b><br>
                <span class='muted'>In the left sidebar under <b>Anonymous Setup</b>, enter a random code like <code>MIT_01</code> and press Enter.</span>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with g2:
        st.markdown(
            """
            <div class='guide-card'>
                <div class='guide-step-badge'>STEP 2 · SAVE & SYNC</div><br>
                <b>Save Think & Pair</b><br>
                <span class='muted'>Write your math plan in <b>1. Think</b> & <b>2. Pair</b> and click <b>Save Stage</b>. This unlocks your synced <i>Logic Blueprint</i> inside the IDE!</span>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with g3:
        st.markdown(
            """
            <div class='guide-card'>
                <div class='guide-step-badge'>STEP 3 · PASS & UNLOCK</div><br>
                <b>Solve Missions (🔒 → 🏆)</b><br>
                <span class='muted'>Write Python in <b>💻 Code Lab IDE</b> and click <b>▶ Run Code</b>. Passing all tests unlocks locked tutorials in the Knowledge Map!</span>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with g4:
        st.markdown(
            """
            <div class='guide-card'>
                <div class='guide-step-badge'>STEP 4 · FINAL SUBMIT</div><br>
                <b>Consent & Archive</b><br>
                <span class='muted'>Save <b>3. GenAI</b> to <b>5. Reflect</b>, tick the voluntary consent box on the left sidebar, and click <b>💾 Submit Progress</b>.</span>
            </div>
            """,
            unsafe_allow_html=True,
        )

    # Detailed Explanation of How Saving & Unlocking Works
    st.subheader("🔓 How Saving Answers & Unlocking Tutorials Works")
    u1, u2 = st.columns(2)
    with u1:
        st.markdown(
            """
            <div class='panel-box'>
                <b>1. How Saving Text Answers Unlocks Your Logic Blueprint</b><br><br>
                <ul>
                    <li>Inside <b>📝 1. Think</b> and <b>🤝 2. Pair</b>, typing alone does not sync—you must click the blue <b>Save Think Stage</b> / <b>Save Pair Stage</b> button at the bottom of each form.</li>
                    <li>Once saved, the left sidebar updates from <code>⬜</code> to <code>✅</code>, and your notes automatically unlock inside <b>💻 Code Lab IDE → 🪜 Guide & Notes</b> as your personal <i>Logic Blueprint</i>.</li>
                    <li>Similarly, in <b>3. GenAI</b>, <b>4. Audit</b>, and <b>5. Reflect</b>, click each tab's <b>Save Stage</b> button before final submission.</li>
                </ul>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with u2:
        st.markdown(
            """
            <div class='panel-box'>
                <b>2. How Passing Missions Unlocks Tutorials (🔒 → 🏆)</b><br><br>
                <ul>
                    <li>Locked items in <b>🌐 Full Knowledge Map</b> are unlocked by writing Python code and passing all public & hidden tests via <b>▶ Run Code</b>:</li>
                    <li><b>Mission 1 (<code>gcd</code>):</b> Unlocks <i>Modulo (%)</i>, <i>while loop</i>, and <i>Testing Mindset</i>.</li>
                    <li><b>Mission 2 (<code>simplify_fraction</code>):</b> Unlocks <i>Function Reuse</i>, <i>Tuple Return & Integer Division</i>, and <i>Debugging Strategy</i>.</li>
                    <li><b>Mission 3 (<code>safe_simplify_fraction</code>):</b> Unlocks <i>Edge Cases (Guard Clause)</i>.</li>
                </ul>
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.markdown("---")
    left, right = st.columns([2, 1])

    with left:
        st.subheader("Core Learning Rule")
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
            <div class='status-warn'><b>Classroom Principle:</b> AI is used as a thinking scaffold—attempt the logic yourself before asking AI for help.</div>
            """,
            unsafe_allow_html=True,
        )

    with right:
        summary = current_draft_summary()
        st.subheader("Current Session Status")
        st.markdown(f"**Anonymous ID:** {summary['group_id']}")
        st.markdown(f"**Session Tag:** {summary['class_id']}")
        st.markdown(f"**Completed Stages:** {summary['completed_stages']}/5")
        st.markdown(f"**Concepts Unlocked:** {summary['knowledge_unlocked']}/{len(KNOWLEDGE_LIBRARY)}")
        st.markdown(f"**Missions Completed:** {summary['missions_completed']}/{len(MISSIONS)}")

        st.markdown("---")
        if st.button("🚀 Start in Learning Workspace", type="primary", use_container_width=True):
            st.session_state.page = "2. Learning Workspace"
            st.rerun()


def render_workspace() -> None:
    render_header()

    # Interactive 4-Tab Detailed Student Manual inside Workspace
    with st.expander("📖 Student Guide: How to Save Answers, Unlock Tutorials & Submit (Click to expand)", expanded=False):
        gtab1, gtab2, gtab3, gtab4 = st.tabs([
            "1️⃣ Setup & Think/Pair Sync",
            "2️⃣ Code Lab & Unlocks (🔒→🏆)",
            "3️⃣ GenAI, Audit & Reflect",
            "4️⃣ Final Submit & Shared Laptop Reset",
        ])

        with gtab1:
            st.markdown(
                """
                * **Step A — Set Anonymous ID (Left Sidebar):** Enter a random code like `MIT_01` under *Anonymous Setup* and press Enter (do **not** use your real name or Student ID).
                * **Step B — Save `📝 1. Think` & `🤝 2. Pair`:** Write your math explanation and pseudocode, then **click the blue `Save Think Stage` / `Save Pair Stage` button** at the bottom of each form.
                * **Step C — Check Your Unlocked Blueprint:** Once saved, the sidebar turns `✅`, and your notes automatically appear inside **💻 Code Lab IDE → Left Panel → `🪜 Guide & Notes`** as your *Logic Blueprint*.
                """
            )
        with gtab2:
            st.markdown(
                """
                * **Select & Code:** Choose **Mission 1**, **2**, or **3** in the left `📁 Explorer`, write your Python function in the middle editor, and click **`▶ Run Code`**.
                * **Need a Clue?** Click **`💡 Hint`** to reveal up to 3 step-by-step clues without spoiling the full solution.
                * **Unlock Knowledge Badges (`🔒 → 🏆`):** Passing all public and hidden tests for a mission automatically unlocks its concepts in the right-hand **🌐 Full Knowledge Map**:
                  * **Pass Mission 1 (`gcd`):** Unlocks *Modulo (%)*, *while loop*, and *Testing Mindset*.
                  * **Pass Mission 2 (`simplify_fraction`):** Unlocks *Function Reuse*, *Tuple Return & Integer Division*, and *Debugging Strategy*.
                  * **Pass Mission 3 (`safe_simplify_fraction`):** Unlocks *Edge Cases (Guard Clause)*.
                """
            )
        with gtab3:
            st.markdown(
                """
                * **🤖 3. GenAI:** If you used an AI tool for hints or debugging, record why you asked, your prompt, and whether you accepted its suggestion → click **`Save GenAI Stage`**.
                * **🔎 4. Audit:** Tick the checklist to verify code accuracy, edge cases, and independent thinking → click **`Save Audit Stage`**.
                * **🤔 5. Reflect:** Summarize what AI helped with and what required human judgement → click **`Save Reflect Stage`**.
                * *(Reminder: Every tab has its own `Save Stage` button at the bottom—click it to mark that stage `✅` in the sidebar.)*
                """
            )
        with gtab4:
            st.markdown(
                """
                * **Permanent Submission (Important):** Stage `Save` buttons only hold your progress in the current browser session. To archive your completed session:
                  1. Tick the **voluntary consent checkbox** under *Final Save & Submit* in the left sidebar.
                  2. Click **`💾 Submit Progress`** (or **`Submit Current Draft`** at the bottom of `5. Reflect`).
                  3. Wait for the green **`✅ Saved at ...`** confirmation toast.
                * **Sharing a Laptop?** After the first student clicks `💾 Submit Progress`, click **`🔄 Reset Current Session`** in the left sidebar to wipe all answers, code buffers, and unlocked badges for the next student.
                """
            )

    st.markdown("---")

    tab_ide, tab_think, tab_pair, tab_genai, tab_audit, tab_reflect = st.tabs([
        "💻 Code Lab IDE", "📝 1. Think", "🤝 2. Pair", "🤖 3. GenAI", "🔎 4. Audit", "🤔 5. Reflect"
    ])

    with tab_ide:
        render_code_lab_ide()

    with tab_think:
        st.subheader("Think Stage")
        if st.session_state.think_done:
            st.success("✅ Status: Saved & synced to 'Code Lab IDE → Guide & Notes'. You can edit and re-save anytime.")
        else:
            st.info("⬜ Status: Not saved yet — fill in your logic below and click **Save Think Stage** to unlock your Logic Blueprint.")

        with st.form("think_form"):
            think_math = st.text_area(
                "1) Explain the mathematical logic for simplifying a fraction",
                value=st.session_state.think_math,
                height=130,
                placeholder="Example: To simplify a/b, find the greatest common divisor (gcd) of a and b...",
            )
            think_python = st.text_area(
                "2) Bridge the idea to Python",
                value=st.session_state.think_python,
                height=120,
                placeholder="Example: Use a while loop with modulo (%) to compute gcd(a, b)...",
            )
            submitted = st.form_submit_button("Save Think Stage", type="primary")

        if submitted:
            st.session_state.think_math = think_math
            st.session_state.think_python = think_python
            st.session_state.think_done = bool(think_math.strip() or think_python.strip())
            st.toast("✅ Think stage saved & synced to IDE!")
            st.rerun()

    with tab_pair:
        st.subheader("Pair Stage")
        if st.session_state.pair_done:
            st.success("✅ Status: Saved & synced to 'Code Lab IDE → Guide & Notes'.")
        else:
            st.info("⬜ Status: Not saved yet — fill in your pseudocode below and click **Save Pair Stage** to sync it to the IDE.")

        with st.form("pair_form"):
            pseudocode = st.text_area(
                "Group pseudocode / algorithm sketch",
                value=st.session_state.pair_pseudocode,
                height=150,
                placeholder="1. Check if b == 0 -> return 'Undefined'\n2. Find g = gcd(a, b)\n3. Return (a // g, b // g)",
            )
            roles = st.text_area(
                "Group roles / collaboration notes (e.g., Driver & Navigator — no real names)",
                value=st.session_state.pair_roles,
                height=95,
            )
            tests = st.text_area(
                "Planned test cases",
                value=st.session_state.pair_tests,
                height=95,
            )
            submitted = st.form_submit_button("Save Pair Stage", type="primary")

        if submitted:
            st.session_state.pair_pseudocode = pseudocode
            st.session_state.pair_roles = roles
            st.session_state.pair_tests = tests
            st.session_state.pair_done = bool(pseudocode.strip() or roles.strip() or tests.strip())
            st.toast("✅ Pair stage saved & synced to IDE!")
            st.rerun()

    with tab_genai:
        st.subheader("GenAI Support")
        if st.session_state.genai_done:
            st.success("✅ Status: GenAI stage saved.")
        else:
            st.info("⬜ Status: Not saved yet — record any AI support below and click **Save GenAI Stage**.")

        with st.form("genai_form"):
            reason = st.text_area("Why are you using AI at this point?", value=st.session_state.genai_reason, height=80)
            prompt = st.text_area("What prompt would you ask?", value=st.session_state.genai_prompt, height=120)
            output = st.text_area("What did the AI suggest? (summary only)", value=st.session_state.genai_output, height=110)
            use_decision = st.text_area("Did you use the suggestion? Why or why not?", value=st.session_state.genai_use, height=110)
            submitted = st.form_submit_button("Save GenAI Stage", type="primary")

        if submitted:
            st.session_state.genai_reason = reason
            st.session_state.genai_prompt = prompt
            st.session_state.genai_output = output
            st.session_state.genai_use = use_decision
            st.session_state.genai_done = bool(reason.strip() or prompt.strip() or output.strip() or use_decision.strip())
            st.toast("✅ GenAI stage saved!")
            st.rerun()

    with tab_audit:
        st.subheader("Audit Stage")
        if st.session_state.audit_done:
            st.success("✅ Status: Audit stage saved.")
        else:
            st.info("⬜ Status: Not saved yet — complete the audit checklist below and click **Save Audit Stage**.")

        with st.form("audit_form"):
            c1, c2 = st.columns(2)
            with c1:
                accuracy = st.checkbox("We checked mathematical / code correctness", value=st.session_state.audit_accuracy)
                clarity = st.checkbox("We checked whether the explanation is clear", value=st.session_state.audit_clarity)
            with c2:
                edge_cases = st.checkbox("We checked hidden or edge cases", value=st.session_state.audit_edge_cases)
                overreliance = st.checkbox("We discussed whether AI is doing too much thinking for us", value=st.session_state.audit_overreliance)

            judgement = st.text_area("Final judgement about the AI support", value=st.session_state.audit_judgement, height=120)
            submitted = st.form_submit_button("Save Audit Stage", type="primary")

        if submitted:
            st.session_state.audit_accuracy = accuracy
            st.session_state.audit_clarity = clarity
            st.session_state.audit_edge_cases = edge_cases
            st.session_state.audit_overreliance = overreliance
            st.session_state.audit_judgement = judgement
            st.session_state.audit_done = bool(accuracy or clarity or edge_cases or overreliance or judgement.strip())
            st.toast("✅ Audit stage saved!")
            st.rerun()

    with tab_reflect:
        st.subheader("Reflect Stage")
        if st.session_state.reflect_done:
            st.success("✅ Status: Reflect stage saved.")
        else:
            st.info("⬜ Status: Not saved yet — write your reflection below and click **Save Reflect Stage**.")

        with st.form("reflect_form"):
            helpful = st.text_area("What did AI help with?", value=st.session_state.reflect_helpful, height=105)
            human = st.text_area("What still required human judgement?", value=st.session_state.reflect_human, height=105)
            next_time = st.text_area("What would you improve next time?", value=st.session_state.reflect_next, height=105)
            submitted = st.form_submit_button("Save Reflect Stage", type="primary")

        if submitted:
            st.session_state.reflect_helpful = helpful
            st.session_state.reflect_human = human
            st.session_state.reflect_next = next_time
            st.session_state.reflect_done = bool(helpful.strip() or human.strip() or next_time.strip())
            st.toast("✅ Reflect stage saved!")
            st.rerun()

        st.markdown("---")
        st.subheader("Finalize & Submit")
        id_valid, _ = is_valid_anonymous_id(st.session_state.group_id)
        if not st.session_state.consent_agreed:
            st.warning("Please tick the voluntary consent checkbox in the left sidebar before submitting.")

        if st.button(
            "Submit Current Draft",
            type="primary",
            disabled=not (st.session_state.consent_agreed and id_valid),
        ):
            record = build_submission_record()
            append_submission(record)
            st.session_state.last_submission_message = f"Submission saved at {record['timestamp']}."
            st.toast(f"✅ {st.session_state.last_submission_message}")


def render_code_lab_ide() -> None:
    mission = get_mission_by_id(st.session_state.selected_mission)
    feedback = st.session_state.mission_feedback.get(mission["id"])
    current_code = st.session_state.code_buffers[mission["id"]]

    left, middle, right = st.columns([1.2, 1.8, 1.0], gap="medium")

    with left:
        with st.container(height=580):
            l_tab1, l_tab2 = st.tabs(["📁 Explorer", "🪜 Guide & Notes"])

            with l_tab1:
                for m in MISSIONS:
                    done = "✅" if m["id"] in st.session_state.completed_missions else "⬜"
                    is_current = m["id"] == mission["id"]
                    if st.button(
                        f"{done} {m['title']}",
                        use_container_width=True,
                        key=f"explorer_{m['id']}",
                        type="primary" if is_current else "secondary",
                    ):
                        st.session_state.selected_mission = m["id"]
                        st.rerun()

                st.markdown(
                    f"""
                    <div class='panel-box' style='margin-top: 15px;'>
                        <b>🎯 Current Goal</b><br>
                        <span class='muted'>{mission["goal"]}</span>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

                st.markdown("### 👀 Public Test Cases")
                for t in mission["public_tests"]:
                    st.markdown(
                        f"""
                        <div class='explorer-item'>
                            <b>In:</b> <code>{t["input"]}</code> &nbsp;→&nbsp;
                            <b>Expected:</b> <code>{t["expected"]}</code>
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )

            with l_tab2:
                st.caption("💡 Fill in '1. Think' & '2. Pair' and click their 'Save' buttons to unlock your Logic Blueprint below.")
                if (
                    st.session_state.think_math.strip()
                    or st.session_state.think_python.strip()
                    or st.session_state.pair_pseudocode.strip()
                ):
                    st.markdown("**🧭 Your Unlocked Logic Blueprint**")
                    if st.session_state.think_math.strip():
                        st.caption("**Math Logic:**")
                        st.write(st.session_state.think_math)
                    if st.session_state.think_python.strip():
                        st.caption("**Python Bridge:**")
                        st.write(st.session_state.think_python)
                    if st.session_state.pair_pseudocode.strip():
                        st.caption("**Group Pseudocode:**")
                        st.code(st.session_state.pair_pseudocode, language="text")
                else:
                    st.info("🔒 Locked: Save your notes in the 'Think' or 'Pair' tab to unlock your Logic Blueprint here.")

                code_edited = current_code.strip() != mission["starter_code"].strip()
                mission_passed = mission["id"] in st.session_state.completed_missions

                st.markdown("### 🪜 Checklist")
                steps = [
                    ("Save math idea (1. Think)", st.session_state.think_done),
                    ("Save pseudocode (2. Pair)", st.session_state.pair_done),
                    ("Write & run function code", code_edited or mission_passed),
                    ("Pass all tests (Unlocks badges)", mission_passed),
                    ("Save Audit & Reflect + Submit", st.session_state.audit_done or st.session_state.reflect_done),
                ]
                for label, done in steps:
                    st.markdown(
                        f"<div class='step-box'>{'✅' if done else '⬜'} {label}</div>",
                        unsafe_allow_html=True,
                    )

    with middle:
        code = ace_editor(
            "Python Workspace",
            current_code,
            key=f"editor_{mission['id']}",
            height=310,
        )
        st.session_state.code_buffers[mission["id"]] = code

        b1, b2, b3, b4 = st.columns(4)
        with b1:
            if st.button("▶ Run Code", type="primary", use_container_width=True, key=f"run_{mission['id']}"):
                st.session_state.run_counts[mission["id"]] = st.session_state.run_counts.get(mission["id"], 0) + 1
                result = grade_code(code, mission)
                st.session_state.mission_feedback[mission["id"]] = result
                st.session_state.last_checked_mission = mission["id"]
                if result["ok"]:
                    unlock_for_mission(mission)
                    st.toast("🏆 Mission passed! New Knowledge Map tutorials unlocked!")
                st.rerun()

        with b2:
            if st.button("💡 Hint", use_container_width=True, key=f"hint_{mission['id']}"):
                current = st.session_state.hint_levels.get(mission["id"], 0)
                max_hints = len(mission["hints"])
                if current < max_hints:
                    st.session_state.hint_levels[mission["id"]] = current + 1
                    st.toast(f"💡 Unlocked Hint {current + 1}/{max_hints} below!")
                else:
                    st.toast(f"💡 All {max_hints} hints are already shown below.")
                st.rerun()

        with b3:
            if st.button("📋 Test Results", use_container_width=True, key=f"tests_{mission['id']}"):
                st.session_state.last_checked_mission = mission["id"]
                st.session_state.mission_feedback.setdefault(
                    mission["id"],
                    {
                        "ok": False,
                        "type": "info",
                        "diag_tag": "",
                        "level": "partial",
                        "message": "Visible tests shown below. Write or refine your code, then click Run.",
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
                st.session_state.mission_feedback.pop(mission["id"], None)
                st.rerun()

        st.markdown("#### ✅ Output Console")
        render_feedback_panel(feedback, mission)

    with right:
        with st.container(height=580):
            st.markdown("### 🤖 Assistant")

            if not feedback:
                st.info("Write your code and click **Run** for instant diagnostic feedback.")
            else:
                ftype = feedback.get("type")
                diag_tag = feedback.get("diag_tag", "")

                if ftype == "syntax":
                    st.error("**Syntax Issue:** Check colons `:`, indentation, or parentheses.")
                elif ftype == "missing_function":
                    st.error(f"**Function Mismatch:** Use exact name `{mission['function_name']}`.")
                elif ftype == "timeout":
                    st.error("**Infinite Loop:** Condition never became False.")
                elif ftype == "runtime":
                    st.error(f"**Runtime Error:** {feedback.get('message')}")
                elif feedback.get("ok"):
                    st.success("**All Tests Passed!**")
                else:
                    if diag_tag == "returned_none":
                        st.warning("**Diagnosis:** Returned `None`. Forgot `return`?")
                    elif diag_tag == "returned_list_instead_of_tuple":
                        st.warning("**Diagnosis:** Returned `list` instead of `tuple`.")
                    elif diag_tag == "float_division_used":
                        st.warning("**Diagnosis:** Contains floats. Use `//` instead of `/`.")
                    elif diag_tag == "zero_division":
                        st.warning("**Diagnosis:** Division by zero! Check `b == 0` first.")
                    else:
                        st.warning(f"**Logic Mismatch:** {feedback.get('message')}")

            with st.expander("📚 Concept Scaffolds (Unlocks)", expanded=True):
                for key in mission["unlocks"]:
                    unlocked = key in st.session_state.unlocked_knowledge
                    item = KNOWLEDGE_LIBRARY[key]
                    cls = "assistant-card-green" if unlocked else "assistant-card"
                    badge = "🏆 Mastered" if unlocked else "📖 Scaffold"
                    pro_tip_html = f"<br><br><b>💡 Pro Tip:</b> {item['pro_tip']}" if unlocked else ""
                    st.markdown(
                        f"""
                        <div class='{cls}'>
                            <b>{item["title"]}</b> <span class='mini-tag'>{badge}</span><br>
                            <span class='muted'>{item["body"]}{pro_tip_html}</span>
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )
                    st.code(item["example"], language="python")

            with st.expander("🧩 Common Mistakes", expanded=False):
                for m in mission["common_mistakes"]:
                    st.write(f"- {m}")

            with st.expander("🌐 Full Knowledge Map (Pass Missions to Unlock)", expanded=False):
                st.caption("Complete coding missions via '▶ Run Code' to unlock tutorials and Pro Tips:")
                unlocked_set = set(st.session_state.unlocked_knowledge)
                for key, item in KNOWLEDGE_LIBRARY.items():
                    is_mastered = key in unlocked_set
                    if is_mastered:
                        st.markdown(f"**{item['title']}** 🏆 *(Unlocked)*")
                        st.caption(f"💡 {item['pro_tip']}")
                    else:
                        req_mission = get_unlock_source_label(key)
                        st.markdown(f"**{item['title']}** 🔒 *(Pass {req_mission} to unlock)*")


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


def render_teacher_dashboard() -> None:
    render_header()
    st.markdown("---")

    # Privacy Access Gate for Teacher Dashboard
    if not st.session_state.teacher_authenticated:
        st.subheader("🔒 Restricted Area: Instructor & Evaluator Access")
        st.info("To protect participant privacy, please enter the instructor passcode to view aggregated submissions.")
        with st.form("teacher_login_form"):
            pwd = st.text_input("Instructor Passcode", type="password", placeholder="Enter passcode")
            login_btn = st.form_submit_button("Unlock Dashboard", type="primary")
        if login_btn:
            if pwd == TEACHER_PASSCODE:
                st.session_state.teacher_authenticated = True
                st.rerun()
            else:
                st.error("Incorrect passcode.")
        return

    top_col1, top_col2 = st.columns([4, 1])
    with top_col2:
        if st.button("🔒 Lock Dashboard", use_container_width=True):
            st.session_state.teacher_authenticated = False
            st.rerun()

    records = load_submissions()
    summary_df = summary_dataframe(records)

    tab1, tab2, tab3 = st.tabs(["📊 Submissions & Charts", "💻 Live Checker", "⬇️ Evidence Export & Data Cleanup"])

    with tab1:
        st.subheader("Submissions Dashboard")
        c1, c2 = st.columns([2, 1])
        with c1:
            st.dataframe(summary_df, use_container_width=True, hide_index=True)
        with c2:
            if not summary_df.empty:
                st.markdown("**Progress Score Distribution**")
                chart_data = summary_df["Progress"].value_counts().sort_index()
                st.bar_chart(chart_data)
            else:
                st.info("No submissions yet.")

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
        st.subheader("Data Retention & Compliance Controls")
        st.write("- All records use coded anonymous IDs rather than personal identifiers.")
        st.write("- Data is collected strictly for anonymous usability and instructional design evaluation.")

        st.session_state.confirm_purge = st.checkbox(
            "I have backed up the data and want to permanently delete all stored records.",
            value=st.session_state.confirm_purge,
        )
        if st.button(
            "🗑️ Delete All Stored Records",
            disabled=not st.session_state.confirm_purge,
        ):
            clear_all_submissions()
            st.session_state.confirm_purge = False
            st.success("All stored submission records have been permanently deleted.")
            st.rerun()


# =========================================================
# MAIN
# =========================================================
def main() -> None:
    init_session()
    render_sidebar()

    page = st.session_state.page

    if page == "1. Home":
        render_home()
    elif page == "2. Learning Workspace":
        render_workspace()
    elif page == "3. Teacher Dashboard":
        render_teacher_dashboard()
    else:
        render_home()


if __name__ == "__main__":
    main()
