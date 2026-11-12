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
# STYLING
# =========================================================
st.markdown(
    """
    <style>
    .main-title {
        font-size: 2.1rem;
        font-weight: 800;
        margin-bottom: 0.2rem;
    }
    .sub-title {
        color: #A9B8FF;
        font-size: 1rem;
        margin-bottom: 1rem;
    }
    .section-card {
        padding: 1rem;
        border-radius: 12px;
        background: rgba(255,255,255,0.04);
        border: 1px solid rgba(255,255,255,0.08);
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
    .ok-box {
        padding: 0.8rem 1rem;
        border-radius: 10px;
        background: #102A1B;
        border: 1px solid #2B7A4B;
        margin-bottom: 0.7rem;
    }
    .warn-box {
        padding: 0.8rem 1rem;
        border-radius: 10px;
        background: #2D240E;
        border: 1px solid #A47C1B;
        margin-bottom: 0.7rem;
    }
    .muted {
        color: #B9C0D0;
        font-size: 0.92rem;
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
        "body": "A helper function such as `gcd(a, b)` can be reused inside `simplify_fraction(a, b)`.",
    },
    "edge_cases": {
        "title": "Edge Cases",
        "body": "Always think about special inputs such as zero, negative numbers, or already simplified fractions.",
    },
    "tuple_return": {
        "title": "Tuple Return",
        "body": "A function can return more than one value using a tuple, e.g. `return (2, 3)`.",
    },
    "testing": {
        "title": "Testing Mindset",
        "body": "A correct-looking answer may still fail hidden cases. Good programmers test normal cases, edge cases, and unexpected inputs.",
    },
    "debugging": {
        "title": "Debugging",
        "body": "When code fails, identify whether the problem is syntax, logic, function naming, or edge-case handling.",
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
    "8. Code Lab",
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
        # Fallback for environments without SIGALRM
        yield


# =========================================================
# SESSION STATE
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
        "code_buffers": {m["id"]: m["starter_code"] for m in MISSIONS},
        "last_submission_message": "",
        "teacher_live_code": "",
        "teacher_checker_mission": MISSIONS[0]["id"],
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
            "message": str(e),
            "passed": 0,
            "total": total_tests,
            "details": [],
        }
    except Exception as e:
        return {
            "ok": False,
            "type": "runtime",
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
    else:
        public_failed = [d for d in details if d["public"] and not d["ok"]]
        if public_failed:
            f = public_failed[0]
            msg = (
                f"Not quite yet. Public test failed for input {f['input']}. "
                f"Expected {f['expected']}, but got {f['result']}."
            )
        else:
            msg = "Your code passed the visible tests, but some hidden tests failed. Check edge cases and robustness."

    return {
        "ok": success,
        "type": "graded",
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
# SIDEBAR
# =========================================================
def render_sidebar() -> str:
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

        stage_names = [
            ("Think", st.session_state.think_done),
            ("Pair", st.session_state.pair_done),
            ("GenAI", st.session_state.genai_done),
            ("Audit", st.session_state.audit_done),
            ("Reflect", st.session_state.reflect_done),
        ]
        for name, ok in stage_names:
            st.write(f"{'✅' if ok else '⬜'} {name}")

        st.markdown("---")
        if st.button("Reset Current Draft", use_container_width=True):
            keys_to_clear = [
                "think_math",
                "think_python",
                "pair_pseudocode",
                "pair_roles",
                "pair_tests",
                "genai_reason",
                "genai_prompt",
                "genai_output",
                "genai_use",
                "audit_accuracy",
                "audit_clarity",
                "audit_edge_cases",
                "audit_overreliance",
                "audit_judgement",
                "reflect_helpful",
                "reflect_human",
                "reflect_next",
                "think_done",
                "pair_done",
                "genai_done",
                "audit_done",
                "reflect_done",
                "last_submission_message",
            ]
            for k in keys_to_clear:
                if isinstance(st.session_state.get(k), bool):
                    st.session_state[k] = False
                else:
                    st.session_state[k] = ""
            st.rerun()

    return page


# =========================================================
# SHARED HEADER
# =========================================================
def render_header() -> None:
    st.markdown(f"<div class='main-title'>🧠 {PROJECT_TITLE}</div>", unsafe_allow_html=True)
    st.markdown(f"<div class='sub-title'>{PROJECT_TAGLINE}</div>", unsafe_allow_html=True)

    tags = [
        "Think",
        "Pair",
        "GenAI Support",
        "Audit",
        "Reflect",
    ]
    st.markdown("".join([f"<span class='mini-tag'>{t}</span>" for t in tags]), unsafe_allow_html=True)


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
            <div class='section-card'>
                <b>Think → Pair → GenAI → Audit → Reflect</b><br><br>
                This prototype operationalises the lesson design by guiding students through a structured sequence:
                <ol>
                    {''.join([f"<li>{x}</li>" for x in LEARNING_RULE])}
                </ol>
            </div>
            """,
            unsafe_allow_html=True,
        )

        st.markdown(
            """
            <div class='ok-box'><b>Pedagogical principle:</b> AI is used as a scaffold, not as an answer engine.</div>
            <div class='warn-box'><b>Classroom rule:</b> Students should attempt the task before using AI.</div>
            """,
            unsafe_allow_html=True,
        )

        st.subheader("This lesson task")
        st.write("Students use the Euclidean Algorithm to write:")
        st.code(
            "gcd(a, b)\n"
            "simplify_fraction(a, b)\n"
            "safe_simplify_fraction(a, b)",
            language="python",
        )

        st.info(
            "New upgrade: students can now write Python directly in the platform, receive immediate correctness feedback, and unlock knowledge cards step by step."
        )

    with right:
        st.subheader("Current Draft Summary")
        summary = current_draft_summary()

        st.markdown(f"**Group ID**  \n{summary['group_id']}")
        st.markdown(f"**Class**  \n{summary['class_id']}")
        st.markdown(f"**Student Count**  \n{summary['student_count']}")
        st.markdown(f"**Completed Stages**  \n{summary['completed_stages']}/5")
        st.markdown(f"**Knowledge Unlocked**  \n{summary['knowledge_unlocked']}")
        st.markdown(f"**Code Missions Completed**  \n{summary['missions_completed']}")

        st.markdown("---")
        st.subheader("Evidence Alignment")
        st.write("This app can support collection of:")
        st.markdown(
            """
            - pseudocode drafts
            - AI-use logs
            - auditor decisions
            - reflection data
            - code-lab progress
            - submission summaries
            """
        )


def render_think() -> None:
    render_header()
    st.markdown("---")
    st.subheader("Think")
    st.caption("Students articulate the logic before collaboration or AI support.")

    with st.form("think_form"):
        think_math = st.text_area(
            "1) Explain the mathematical logic for simplifying a fraction",
            value=st.session_state.think_math,
            height=160,
            placeholder="Example: To simplify 8/12, first find the gcd of 8 and 12, then divide both by that gcd...",
        )
        think_python = st.text_area(
            "2) Bridge the idea to Python",
            value=st.session_state.think_python,
            height=140,
            placeholder="Example: I need a function gcd(a, b), then another function to divide numerator and denominator...",
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
    st.caption("Students compare reasoning, refine pseudocode, and define simple test cases.")

    with st.form("pair_form"):
        pseudocode = st.text_area(
            "Group pseudocode / algorithm sketch",
            value=st.session_state.pair_pseudocode,
            height=180,
            placeholder="Example:\n1. While b != 0, update a and b\n2. gcd = a\n3. Divide numerator and denominator by gcd",
        )
        roles = st.text_area(
            "Group roles / collaboration notes",
            value=st.session_state.pair_roles,
            height=100,
            placeholder="Example: Student A explains math logic; Student B checks test cases; Student C compares outputs...",
        )
        tests = st.text_area(
            "Planned test cases",
            value=st.session_state.pair_tests,
            height=100,
            placeholder="Example:\n(8,12) -> (2,3)\n(7,13) -> (7,13)\n(5,0) -> Undefined",
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
    st.caption("Students document why and how they used AI, instead of treating AI as an invisible shortcut.")

    with st.form("genai_form"):
        reason = st.text_area(
            "Why are you using AI at this point?",
            value=st.session_state.genai_reason,
            height=80,
            placeholder="Example: We want AI to help us check whether our loop logic is correct.",
        )
        prompt = st.text_area(
            "What prompt would you ask?",
            value=st.session_state.genai_prompt,
            height=140,
            placeholder="Example: Explain whether this gcd loop is correct and suggest a cleaner version without solving the full task for us.",
        )
        output = st.text_area(
            "What did the AI suggest? (summary only)",
            value=st.session_state.genai_output,
            height=120,
            placeholder="Example: AI suggested using a, b = b, a % b and reminded us to consider denominator = 0.",
        )
        use_decision = st.text_area(
            "Did you use the suggestion? Why or why not?",
            value=st.session_state.genai_use,
            height=120,
            placeholder="Example: We used the loop update but changed the error-handling ourselves.",
        )
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
    st.caption("Students evaluate AI outputs critically before accepting them.")

    with st.form("audit_form"):
        col1, col2 = st.columns(2)
        with col1:
            accuracy = st.checkbox(
                "We checked mathematical / code correctness",
                value=st.session_state.audit_accuracy,
            )
            clarity = st.checkbox(
                "We checked whether the explanation is clear",
                value=st.session_state.audit_clarity,
            )
        with col2:
            edge_cases = st.checkbox(
                "We checked hidden or edge cases",
                value=st.session_state.audit_edge_cases,
            )
            overreliance = st.checkbox(
                "We discussed whether AI is doing too much thinking for us",
                value=st.session_state.audit_overreliance,
            )

        judgement = st.text_area(
            "Final judgement about the AI support",
            value=st.session_state.audit_judgement,
            height=120,
            placeholder="Example: Helpful for debugging syntax, but we should not copy the full solution without understanding it.",
        )

        submitted = st.form_submit_button("Save Audit Stage")

    if submitted:
        st.session_state.audit_accuracy = accuracy
        st.session_state.audit_clarity = clarity
        st.session_state.audit_edge_cases = edge_cases
        st.session_state.audit_overreliance = overreliance
        st.session_state.audit_judgement = judgement
        st.session_state.audit_done = bool(
            accuracy or clarity or edge_cases or overreliance or judgement.strip()
        )
        st.success("Audit stage saved.")


def render_reflect() -> None:
    render_header()
    st.markdown("---")
    st.subheader("Reflect")
    st.caption("Students identify what AI helped with and what still required human judgement.")

    with st.form("reflect_form"):
        helpful = st.text_area(
            "What did AI help with?",
            value=st.session_state.reflect_helpful,
            height=110,
            placeholder="Example: AI helped us compare loop structures and test cases.",
        )
        human = st.text_area(
            "What still required human judgement?",
            value=st.session_state.reflect_human,
            height=110,
            placeholder="Example: We still had to decide whether the AI suggestion really matched our task.",
        )
        next_time = st.text_area(
            "What would you improve next time?",
            value=st.session_state.reflect_next,
            height=110,
            placeholder="Example: We will test denominator = 0 earlier and explain our logic before asking AI.",
        )
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


def render_feedback_panel(feedback: Dict[str, Any] | None, mission: Dict[str, Any]) -> None:
    if not feedback:
        st.info("Run your code to see live feedback.")
        return

    if feedback["ok"]:
        st.success(feedback["message"])
    else:
        st.warning(feedback["message"])

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

    st.markdown("**Hints**")
    for hint in mission["hints"]:
        st.write(f"- {hint}")


def render_unlocked_knowledge() -> None:
    if not st.session_state.unlocked_knowledge:
        st.info("No knowledge cards unlocked yet. Complete a mission to unlock concepts.")
        return

    for key in st.session_state.unlocked_knowledge:
        item = KNOWLEDGE_LIBRARY[key]
        st.markdown(
            f"""
            <div class='knowledge-unlocked'>
                <b>🔓 {item["title"]}</b><br>
                <span class='muted'>{item["body"]}</span>
            </div>
            """,
            unsafe_allow_html=True,
        )


def render_knowledge_map() -> None:
    unlocked = set(st.session_state.unlocked_knowledge)
    for key, item in KNOWLEDGE_LIBRARY.items():
        if key in unlocked:
            cls = "knowledge-unlocked"
            prefix = "🔓"
            body = item["body"]
        else:
            cls = "knowledge-locked"
            prefix = "🔒"
            body = "Complete missions to unlock this concept."

        st.markdown(
            f"""
            <div class='{cls}'>
                <b>{prefix} {item["title"]}</b><br>
                <span class='muted'>{body}</span>
            </div>
            """,
            unsafe_allow_html=True,
        )


def render_teacher_live_checker() -> None:
    st.subheader("Teacher Live Checker")
    st.caption("Paste code during class and show students whether it is correct, partially correct, or incorrect.")

    mission_id = st.selectbox(
        "Choose a checking target",
        options=[m["id"] for m in MISSIONS],
        format_func=lambda x: get_mission_by_id(x)["title"],
        index=[m["id"] for m in MISSIONS].index(st.session_state.teacher_checker_mission),
    )
    st.session_state.teacher_checker_mission = mission_id
    mission = get_mission_by_id(mission_id)

    code = st.text_area(
        "Paste demonstration code here",
        value=st.session_state.teacher_live_code,
        height=260,
        key="teacher_live_code_area",
    )
    st.session_state.teacher_live_code = code

    if st.button("Check Demo Code", key="teacher_check_btn"):
        result = grade_code(code, mission)
        render_feedback_panel(result, mission)

    with st.expander("Suggested teacher talk"):
        st.write(
            "Use this checker formatively: show students that 'incorrect' does not always mean 'bad', "
            "and 'correct on visible tests' does not always mean 'fully robust'."
        )


def render_code_lab() -> None:
    render_header()
    st.markdown("---")
    st.subheader("💻 Interactive Code Studio")
    st.caption("Write code, test ideas, get feedback, and unlock knowledge.")

    completed = len(st.session_state.completed_missions)
    total = len(MISSIONS)

    c1, c2, c3 = st.columns(3)
    c1.metric("Missions Completed", f"{completed}/{total}")
    c2.metric("Knowledge Unlocked", len(st.session_state.unlocked_knowledge))
    c3.metric("Current Stage Progress", completeness_score())

    st.progress(completed / total if total else 0.0)
    st.markdown("---")

    left, middle, right = st.columns([1.1, 1.8, 1.2])

    with left:
        st.subheader("Mission Navigator")
        for m in MISSIONS:
            done = "✅" if m["id"] in st.session_state.completed_missions else "⬜"
            if st.button(f"{done} {m['title']}", use_container_width=True, key=f"nav_{m['id']}"):
                st.session_state.selected_mission = m["id"]

        mission = get_mission_by_id(st.session_state.selected_mission)

        st.markdown("---")
        st.subheader("Current Goal")
        st.write(mission["goal"])

        st.markdown("**Public Test Examples**")
        for t in mission["public_tests"]:
            st.write(f"- Input: `{t['input']}` → Expected: `{t['expected']}`")

        with st.expander("Why this mission matters"):
            if mission["id"] == "gcd":
                st.write("This mission focuses on loop logic and the Euclidean Algorithm.")
            elif mission["id"] == "simplify_fraction":
                st.write("This mission focuses on function reuse and returning structured outputs.")
            else:
                st.write("This mission focuses on edge-case awareness and safe programming habits.")

    with middle:
        mission = get_mission_by_id(st.session_state.selected_mission)
        buffer_key = mission["id"]

        st.subheader(mission["title"])
        code = st.text_area(
            "Write your Python code here",
            value=st.session_state.code_buffers[buffer_key],
            height=360,
            key=f"editor_{buffer_key}",
        )
        st.session_state.code_buffers[buffer_key] = code

        b1, b2 = st.columns(2)
        with b1:
            if st.button("▶ Check My Code", use_container_width=True, key=f"run_{buffer_key}"):
                feedback = grade_code(code, mission)
                st.session_state.mission_feedback[buffer_key] = feedback
                if feedback["ok"]:
                    unlock_for_mission(mission)

        with b2:
            if st.button("↺ Reset Starter Code", use_container_width=True, key=f"reset_{buffer_key}"):
                st.session_state.code_buffers[buffer_key] = mission["starter_code"]
                st.rerun()

        st.markdown("### Learning Notes")
        st.info(
            "This studio checks correctness through public and hidden tests. "
            "Passing visible tests is a good start, but robust code also needs to handle less obvious cases."
        )

    with right:
        st.subheader("Feedback & Guidance")
        feedback = st.session_state.mission_feedback.get(st.session_state.selected_mission)
        mission = get_mission_by_id(st.session_state.selected_mission)
        render_feedback_panel(feedback, mission)

        st.markdown("---")
        st.subheader("Unlocked Knowledge")
        render_unlocked_knowledge()

    st.markdown("---")
    tab1, tab2 = st.tabs(["📚 Knowledge Map", "👩‍🏫 Teacher Live Checker"])
    with tab1:
        render_knowledge_map()
    with tab2:
        render_teacher_live_checker()


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
        st.subheader("Current App Notes")
        st.write("- Use coded group IDs rather than personal identifiers.")
        st.write("- The local file storage is suitable for prototype/demo use.")
        st.write("- For long-term deployment, connect to a proper database or approved secure storage.")


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
    elif page == "8. Code Lab":
        render_code_lab()
    else:
        render_home()


if __name__ == "__main__":
    main()
