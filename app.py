from __future__ import annotations

import ast
from contextlib import contextmanager
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import random
import re
import signal
import threading
from typing import Any, Dict, List, Tuple

import pandas as pd
import requests
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
# STYLE (Includes AI Assistant Card UI & Enlarged Save Buttons)
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
    .device-banner {
        padding: 0.65rem 1rem;
        border-radius: 10px;
        background: #1B2340;
        color: #E2E8F0;
        border: 1px solid #4C6EF5;
        margin-bottom: 0.85rem;
        font-size: 0.9rem;
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
    .ai-header-pill {
        display: inline-flex;
        align-items: center;
        gap: 6px;
        padding: 0.32rem 0.85rem;
        border-radius: 999px;
        background: linear-gradient(135deg, #253369 0%, #3B4CCA 100%);
        color: #FFFFFF;
        font-weight: 700;
        font-size: 0.92rem;
        border: 1px solid #5C7CFA;
        box-shadow: 0 2px 8px rgba(92, 124, 250, 0.25);
    }
    .ai-greeting-box {
        text-align: center;
        padding: 0.75rem 0.5rem 0.35rem 0.5rem;
    }
    .ai-greeting-title {
        font-size: 1.28rem;
        font-weight: 800;
        color: #F8FAFC;
        margin-bottom: 0.2rem;
    }
    .ai-greeting-sub {
        font-size: 0.82rem;
        color: #94A3B8;
    }
    .ai-discover-header {
        font-size: 0.88rem;
        font-weight: 700;
        color: #A5B4FC;
        margin-bottom: 0.45rem;
    }
    div[data-testid="stFormSubmitButton"] > button {
        min-height: 2.85rem !important;
        font-size: 1.02rem !important;
        font-weight: 700 !important;
        border-radius: 10px !important;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# =========================================================
# STORAGE & DEFAULT AI PROVIDER PRESETS
# =========================================================
DATA_DIR = Path("data")
SUBMISSION_FILE = DATA_DIR / "submissions.jsonl"

AI_PROVIDER_PRESETS = {
    "通义千问 Qwen (DashScope)": {
        "base_url": "https://dashscope.aliyuncs.com/compatible-mode/v1",
        "model": "qwen-plus",
    },
    "DeepSeek": {
        "base_url": "https://api.deepseek.com",
        "model": "deepseek-chat",
    },
    "OpenAI": {
        "base_url": "https://api.openai.com/v1",
        "model": "gpt-4o-mini",
    },
    "自定义 OpenAI 兼容接口": {
        "base_url": "https://dashscope.aliyuncs.com/compatible-mode/v1",
        "model": "qwen-plus",
    },
}

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
# SECRETS & API CONFIG LOADER
# =========================================================
def get_configured_ai_credentials() -> Tuple[str, str, str]:
    """Reads API key/url/model from session_state, st.secrets, or env vars safely."""
    secret_key = ""
    secret_url = ""
    secret_model = ""
    try:
        secret_key = st.secrets.get("AI_API_KEY", "")
        secret_url = st.secrets.get("AI_BASE_URL", "")
        secret_model = st.secrets.get("AI_MODEL", "")
    except Exception:
        pass

    api_key = (
        st.session_state.get("user_ai_api_key", "").strip()
        or secret_key
        or os.getenv("AI_API_KEY", "")
    ).strip()
    base_url = (
        st.session_state.get("user_ai_base_url", "").strip()
        or secret_url
        or os.getenv("AI_BASE_URL", "https://dashscope.aliyuncs.com/compatible-mode/v1")
    ).strip().rstrip("/")
    model = (
        st.session_state.get("user_ai_model", "").strip()
        or secret_model
        or os.getenv("AI_MODEL", "qwen-plus")
    ).strip()
    return api_key, base_url, model


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
# EXECUTION TIME LIMIT
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
# DOMAIN-LOCKED REAL AI ENGINE (MATH & PROGRAMMING ONLY)
# =========================================================
OFF_TOPIC_PATTERNS = re.compile(
    r"(毛笔字|画一只|猫猫头像|销售手册|汽车销售|写一首诗|写作文|周报|日报|旅游攻略|菜谱|做饭|星座|算命|八卦|明星|小说|情感|恋爱|减肥|"
    r"calligraphy|cat avatar|sales manual|poem|recipe|cook|horoscope|travel guide|gossip|celebrity|dating|weight loss)",
    re.IGNORECASE,
)


def is_obviously_off_topic(user_msg: str) -> bool:
    """Fast pre-flight filter for clearly non-math / non-programming topics."""
    math_code_anchors = re.compile(
        r"(math|code|python|c\+\+|java|javascript|sql|algorithm|function|loop|while|for|if|array|list|tuple|dict|"
        r"gcd|fraction|modulo|prime|matrix|calculus|integral|derivative|probability|proof|equation|complexity|big o|"
        r"数学|编程|代码|函数|循环|算法|复杂度|欧几里得|余数|整除|方程|微积分|概率|矩阵|证明|报错|调试|bug)",
        re.IGNORECASE,
    )
    if math_code_anchors.search(user_msg):
        return False
    return bool(OFF_TOPIC_PATTERNS.search(user_msg))


def build_domain_locked_system_prompt(
    mission: Dict[str, Any],
    code: str,
    feedback: Dict[str, Any] | None,
    socratic_guard: bool,
) -> str:
    """Constructs a strict Math & Programming system prompt injected with live workspace context."""
    think_notes = (st.session_state.think_math or st.session_state.think_python).strip() or "(Not written yet)"
    pair_notes = st.session_state.pair_pseudocode.strip() or "(Not written yet)"
    fb_summary = (
        f"Passed {feedback.get('passed')}/{feedback.get('total')} tests. Message: {feedback.get('message')}"
        if feedback
        else "Not run yet."
    )

    pedagogy_rule = (
        "4. **Socratic Pedagogy Rule (Active):** When the student asks about the current coding mission, DO NOT dump the complete copy-paste solution code at once. Instead, diagnose their specific bug/line, explain the underlying mathematical or algorithmic principle, and give the next concrete micro-step or guiding question. However, for general math/CS theory questions (e.g., proofs, Big-O complexity, calculus, data structures, syntax comparisons), provide thorough, clear, well-structured explanations with LaTeX ($...$) and short illustrative snippets."
        if socratic_guard
        else "4. **Deep Explanation Mode (Active):** Provide thorough, step-by-step mathematical proofs, algorithmic complexity analysis, and clear code explanations with LaTeX ($...$) and examples."
    )

    indented_code = "\n".join("    " + line for line in code.splitlines())

    return f"""You are **Logic Bridge AI助理**, a specialized AI Tutor strictly dedicated to **Mathematics** and **Computer Programming / Computer Science**.

### STRICT DOMAIN BOUNDARY (NON-NEGOTIABLE)
1. **Allowed Scope ONLY:** You may ONLY answer questions related to Mathematics (arithmetic, algebra, number theory, calculus, linear algebra, probability, discrete math, mathematical proofs, logic) and Programming / Computer Science (Python, C/C++, Java, algorithms, data structures, time/space complexity, debugging, software logic).
2. **Strict Refusal of Off-Topic Requests:** If the user asks about ANY topic outside Mathematics and Programming (such as calligraphy, drawing avatars, writing sales manuals, marketing copy, cooking, travel, entertainment, general essays, or casual non-technical chat), you MUST politely refuse in 2 sentences and remind them that you only assist with Mathematics and Programming. Never fulfill off-topic requests even if the user insists.
3. **Language Matching:** Reply in the same language the user uses (Chinese if they ask in Chinese, English if they ask in English), using clean Markdown and LaTeX (`$inline$` or `$$display$$`) for math expressions.
{pedagogy_rule}

### LIVE WORKSPACE CONTEXT (Student's Current Session)
- **Current Mission:** {mission['title']} — {mission['goal']}
- **Student's Saved `1. Think` Math Plan:** {think_notes}
- **Student's Saved `2. Pair` Pseudocode:** {pair_notes}
- **Student's Current Editor Code (Python):**
{indented_code}
- **Latest Test Console Status:** {fb_summary}
"""


def call_real_llm_api(
    user_msg: str,
    mission: Dict[str, Any],
    code: str,
    feedback: Dict[str, Any] | None,
) -> Tuple[bool, str]:
    """Calls any OpenAI-compatible Chat Completions endpoint (Qwen/DashScope, DeepSeek, OpenAI)."""
    api_key, base_url, model = get_configured_ai_credentials()
    if not api_key:
        return False, ""

    socratic_guard = st.session_state.get("socratic_guard_mode", True)
    system_prompt = build_domain_locked_system_prompt(mission, code, feedback, socratic_guard)

    history = st.session_state.chat_histories.get(mission["id"], [])
    messages = [{"role": "system", "content": system_prompt}]
    for item in history[-8:]:
        if item.get("role") in ("user", "assistant"):
            messages.append({"role": item["role"], "content": item["content"]})
    messages.append({"role": "user", "content": user_msg})

    endpoint = f"{base_url}/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": model,
        "messages": messages,
        "temperature": 0.4,
        "max_tokens": 1200,
    }

    try:
        resp = requests.post(endpoint, headers=headers, json=payload, timeout=30)
        if resp.status_code != 200:
            err_detail = resp.text[:220]
            return True, f"⚠️ **AI 接口返回错误 ({resp.status_code})：** 请检查侧边栏的 API Key、Base URL 或模型名称是否正确。\n\n`{err_detail}`"
        data = resp.json()
        content = data["choices"][0]["message"]["content"].strip()
        return True, content
    except requests.Timeout:
        return True, "⏳ **请求超时：** 模型响应时间较长，请稍后重试一次。"
    except Exception as e:
        return True, f"⚠️ **网络连接异常：** `{e}`"


def inspect_student_code(code: str, mission: Dict[str, Any]) -> Dict[str, Any]:
    """Lightweight AST static inspection used for offline fallback & instant diagnostics."""
    info: Dict[str, Any] = {
        "is_unstarted": code.strip() == mission["starter_code"].strip(),
        "syntax_error": None,
        "has_import": False,
        "uses_print_no_return": False,
        "sequential_overwrite": False,
        "returns_b": False,
        "has_modulo": False,
        "uses_true_div": False,
        "returns_list": False,
        "checks_b_zero": False,
    }
    try:
        tree = ast.parse(code)
    except SyntaxError as e:
        info["syntax_error"] = f"line {e.lineno}: {e.msg}"
        return info

    target_fn = None
    for node in ast.walk(tree):
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            info["has_import"] = True
        if isinstance(node, ast.FunctionDef) and node.name == mission["function_name"]:
            target_fn = node

    if target_fn is None:
        return info
    if len(target_fn.body) == 1 and isinstance(target_fn.body[0], ast.Pass):
        info["is_unstarted"] = True
        return info

    has_return = False
    has_print = False
    for node in ast.walk(target_fn):
        if isinstance(node, ast.Return) and node.value is not None:
            has_return = True
            if isinstance(node.value, ast.Name) and node.value.id == "b":
                info["returns_b"] = True
            if isinstance(node.value, ast.List):
                info["returns_list"] = True
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id == "print":
            has_print = True
        if isinstance(node, ast.While):
            for i in range(len(node.body) - 1):
                s1, s2 = node.body[i], node.body[i + 1]
                if (
                    isinstance(s1, ast.Assign)
                    and isinstance(s2, ast.Assign)
                    and len(s1.targets) == 1
                    and isinstance(s1.targets[0], ast.Name)
                    and s1.targets[0].id == "a"
                    and isinstance(s1.value, ast.Name)
                    and s1.value.id == "b"
                    and len(s2.targets) == 1
                    and isinstance(s2.targets[0], ast.Name)
                    and s2.targets[0].id == "b"
                ):
                    info["sequential_overwrite"] = True
        if isinstance(node, ast.BinOp):
            if isinstance(node.op, ast.Mod):
                info["has_modulo"] = True
            if isinstance(node.op, ast.Div):
                info["uses_true_div"] = True
        if isinstance(node, ast.Compare):
            for comp in node.comparators:
                if isinstance(comp, ast.Constant) and comp.value == 0:
                    info["checks_b_zero"] = True

    if has_print and not has_return:
        info["uses_print_no_return"] = True
    return info


def offline_rule_fallback(
    user_msg: str,
    mission: Dict[str, Any],
    code: str,
    feedback: Dict[str, Any] | None,
) -> str:
    """Offline fallback when no LLM API key is provided yet."""
    q = user_msg.strip().lower()
    diag = inspect_student_code(code, mission)
    mid = mission["id"]

    if re.search(r"(write|give|show|solve).*(whole|entire|full|complete|code|solution|answer)|(直接给|完整代码|直接写|帮我写)", q):
        return (
            "🛡️ **防代写护栏：** 我不会直接输出完整答案代码，以免剥夺你独立推导逻辑的机会。\n\n"
            f"- **下一步微提示：** 聚焦 `{mission['function_name']}`，先写出第一行条件判断或 `while` 循环，点击 **▶ Run Code** 后我再帮你逐行诊断！"
        )

    if any(k in q for k in ["复杂度", "complexity", "big o", "log", "欧几里得", "euclid", "原理"]):
        return (
            "📐 **欧几里得算法原理与时间复杂度分析：**\n"
            "1. **数学不变性**：$\\gcd(a, b) = \\gcd(b, a \\bmod b)$。\n"
            "2. **时间复杂度 $O(\\log(\\min(a, b)))$**：每经过至多两步取余迭代，较大的数至少减半（与斐波那契数列相邻项为最坏情况相对应），因此即使输入上亿级整数也只需几十次循环。\n\n"
            "💡 *提示：在左侧边栏填入通义千问或 DeepSeek API Key 后，我可以回答任意复杂度的数学证明与多语言编程问题！*"
        )

    if any(k in q for k in ["归纳", "递归", "循环", "recursion", "while", "loop"]):
        return (
            "🔁 **数学归纳 / 递归 到 循环的转化：**\n"
            "- **递推关系**：$f(a, b) = f(b, a \\bmod b)$，终止边界为 $b = 0$ 时返回 $a$。\n"
            "- **尾递归转迭代**：因为递归调用位于最后一步，只需用 `while b != 0:` 配合同步赋值 `a, b = b, a % b` 即可消除栈空间开销（空间复杂度降至 $O(1)$）。"
        )

    if diag["syntax_error"]:
        return f"🔎 **语法诊断：** Python 在 **{diag['syntax_error']}** 处检测到语法错误，请检查冒号 `:`、括号匹配或 4 空格缩进。"

    if diag["uses_print_no_return"]:
        return "💡 **经典错误提示：** 你在函数中使用了 `print(...)`，但评测系统检查的是 `return` 返回值（当前返回了 `None`）。请改用 `return`。"

    if mid == "gcd" and not diag["is_unstarted"]:
        if diag["sequential_overwrite"]:
            return "⚠️ **变量覆盖警告：** 先执行 `a = b` 会把原来的 `a` 覆盖掉，导致下一行 `b = a % b` 变成 `b % b == 0`。试试 Python 的同步赋值 `a, b = b, a % b`！"
        if diag["returns_b"]:
            return "🤔 当 `while b != 0:` 结束时，`b` 的值一定为 `0`。真正保存最大公约数的是哪一个变量？"

    if feedback and not feedback.get("ok"):
        return f"🔍 **测试反馈诊断：** {feedback.get('message')}\n\n建议代入失败用例手动追踪每一步变量变化。"

    return (
        f"🤖 **当前处于本地规则引擎模式**（未检测到 API Key）。\n\n"
        f"- 针对当前任务 `{mission['function_name']}`：建议先写出核心逻辑并点击 **▶ Run Code** 进行测试。\n"
        "- 若希望体验**完整真实 AI 对话**（自由解答任意高数、线性代数、算法设计、多语言报错分析），请在左侧边栏 **`🤖 AI 引擎配置`** 中填入通义千问或 DeepSeek 的 API Key！"
    )


def generate_assistant_reply(
    user_msg: str,
    mission: Dict[str, Any],
    code: str,
    feedback: Dict[str, Any] | None,
) -> str:
    """Unified entry point: Domain-Lock Guardrail -> Real LLM API -> Offline Fallback."""
    if is_obviously_off_topic(user_msg):
        return (
            "🚫 **学科范围提示：** 我是专注于**数学与编程**的 AI 助理，无法回答生活闲聊、营销文案、绘画或其他非理工科问题。\n\n"
            "你可以向我提问任何**数学推导、算法原理、Python/C++/Java 编程或代码排错**问题！"
        )

    has_key, llm_reply = call_real_llm_api(user_msg, mission, code, feedback)
    if has_key:
        return llm_reply

    return offline_rule_fallback(user_msg, mission, code, feedback)


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
        "ai_provider_choice": "通义千问 Qwen (DashScope)",
        "user_ai_api_key": "",
        "user_ai_base_url": "https://dashscope.aliyuncs.com/compatible-mode/v1",
        "user_ai_model": "qwen-plus",
        "socratic_guard_mode": True,
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
        "chat_histories": {m["id"]: [] for m in MISSIONS},
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
    st.session_state.chat_histories = {m["id"]: [] for m in MISSIONS}
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


def total_ai_dialogue_turns() -> int:
    total = 0
    for msgs in st.session_state.chat_histories.values():
        total += sum(1 for m in msgs if m.get("role") == "user")
    return total


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
            "ai_dialogue_turns": total_ai_dialogue_turns(),
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
        "ai_dialogue_turns": total_ai_dialogue_turns(),
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
                "AI Chats",
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
                "AI Chats": r.get("ai_dialogue_turns", 0),
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
    st.markdown(
        """
        <div class='device-banner'>
            💻 <b>Device Tip:</b> Best experienced on a <b>Laptop / Desktop</b> for side-by-side coding & AI dialogue.
            📱 <b>On Mobile?</b> Start with <b>1. Think</b> to outline your math logic, or scroll down inside the IDE to view the Console & Math/Code AI Assistant.
        </div>
        """,
        unsafe_allow_html=True,
    )


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
            if st.button("🎲 Generate Random ID", use_container_width=True):
                st.session_state.group_id = f"MIT_{random.randint(100, 999)}"
                st.rerun()

            raw_group_id = st.text_input(
                "Anonymous Tester / Group ID",
                value=st.session_state.group_id,
                placeholder="Type a code (e.g., MIT_01) & press Enter",
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

        with st.expander("🤖 AI 引擎配置 (数学与编程专属)", expanded=False):
            api_key_now, _, model_now = get_configured_ai_credentials()
            if api_key_now:
                st.success(f"🟢 真实大模型已连接 (`{model_now}`)")
            else:
                st.warning("🟡 未填入 API Key（当前使用本地规则引擎）")

            provider = st.selectbox(
                "选择模型服务商",
                options=list(AI_PROVIDER_PRESETS.keys()),
                index=list(AI_PROVIDER_PRESETS.keys()).index(st.session_state.ai_provider_choice),
            )
            if provider != st.session_state.ai_provider_choice:
                st.session_state.ai_provider_choice = provider
                st.session_state.user_ai_base_url = AI_PROVIDER_PRESETS[provider]["base_url"]
                st.session_state.user_ai_model = AI_PROVIDER_PRESETS[provider]["model"]
                st.rerun()

            st.session_state.user_ai_api_key = st.text_input(
                "API Key (仅保存在当前浏览器会话)",
                value=st.session_state.user_ai_api_key,
                type="password",
                placeholder="sk-...",
            )
            st.session_state.user_ai_base_url = st.text_input(
                "Base URL",
                value=st.session_state.user_ai_base_url,
            )
            st.session_state.user_ai_model = st.text_input(
                "Model 名称",
                value=st.session_state.user_ai_model,
            )
            st.session_state.socratic_guard_mode = st.checkbox(
                "开启苏格拉底防代写模式（任务代码不直接吐出完整答案）",
                value=st.session_state.socratic_guard_mode,
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
                <span class='muted'>In the left sidebar under <b>Anonymous Setup</b>, click <b>Generate Random ID</b> or type a code like <code>MIT_01</code>.</span>
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
                <span class='muted'>Write your math plan in <b>1. Think</b> & <b>2. Pair</b> and click the large <b>Save Stage</b> button to unlock your synced <i>Logic Blueprint</i>!</span>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with g3:
        st.markdown(
            """
            <div class='guide-card'>
                <div class='guide-step-badge'>STEP 3 · CODE & AI</div><br>
                <b>Solve & Ask Math/Code AI</b><br>
                <span class='muted'>Write Python in <b>💻 Code Lab IDE</b>, ask any math/coding question to the <b>AI助理</b> on the right, and pass tests to unlock badges (🔒 → 🏆)!</span>
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

    st.subheader("🔓 How Saving Answers & Math/Code AI Work")
    u1, u2 = st.columns(2)
    with u1:
        st.markdown(
            """
            <div class='panel-box'>
                <b>1. How Saving Text Answers Unlocks Your Logic Blueprint</b><br><br>
                <ul>
                    <li>Inside <b>📝 1. Think</b> and <b>🤝 2. Pair</b>, click the large blue <b>💾 Save Think Stage</b> / <b>💾 Save Pair Stage</b> button at the bottom of each form.</li>
                    <li>Once saved, the left sidebar updates from <code>⬜</code> to <code>✅</code>, and your notes sync to <b>💻 Code Lab IDE → 🪜 Guide & Notes</b> and the <b>AI助理</b>.</li>
                </ul>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with u2:
        st.markdown(
            """
            <div class='panel-box'>
                <b>2. Domain-Locked Math & Programming AI助理</b><br><br>
                <ul>
                    <li>Powered by real LLM reasoning with strict domain boundaries—answers complex <b>Mathematics & Programming</b> questions while blocking off-topic requests.</li>
                    <li>Automatically reads your current editor code and test results for personalized debugging and LaTeX math explanations.</li>
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

    with st.expander("📖 Student Guide: How to Save Answers, Use Math/Code AI & Unlock Tutorials (Click to expand)", expanded=False):
        gtab1, gtab2, gtab3, gtab4 = st.tabs([
            "1️⃣ Setup & Think/Pair Sync",
            "2️⃣ Code Lab & Math/Code AI",
            "3️⃣ GenAI, Audit & Reflect",
            "4️⃣ Final Submit & Shared Laptop Reset",
        ])

        with gtab1:
            st.markdown(
                """
                * **Step A — Set Anonymous ID (Left Sidebar):** Click **🎲 Generate Random ID** or enter a random code like `MIT_01` under *Anonymous Setup* and press Enter (do **not** use your real name or Student ID).
                * **Step B — Save `📝 1. Think` & `🤝 2. Pair`:** Write your math explanation and pseudocode, then **click the large blue `💾 Save Think Stage` / `💾 Save Pair Stage` button** at the bottom of each form.
                * **Step C — Check Your Unlocked Blueprint:** Once saved, the sidebar turns `✅`, and your notes automatically appear inside **💻 Code Lab IDE → Left Panel → `🪜 Guide & Notes`**.
                """
            )
        with gtab2:
            st.markdown(
                """
                * **Select & Code:** Choose **Mission 1**, **2**, or **3** in the left `📁 Explorer`, write your Python function in the middle editor, and click **`▶ Run Code`**.
                * **Ask AI助理 (Right Panel):** Tap any prompt under **✨ 发现提示词** or type any complex **math or programming** question in **`有问题尽管问我~`**.
                * **Unlock Knowledge Badges (`🔒 → 🏆`):** Passing all public and hidden tests unlocks tutorials in **🌐 Full Knowledge Map**.
                """
            )
        with gtab3:
            st.markdown(
                """
                * **🤖 3. GenAI:** Record why you used AI support, what you asked, and whether you accepted its hint → click **`💾 Save GenAI Stage`**.
                * **🔎 4. Audit:** Tick the checklist to verify code accuracy, edge cases, and independent thinking → click **`💾 Save Audit Stage`**.
                * **🤔 5. Reflect:** Summarize what AI helped with and what required human judgement → click **`💾 Save Reflect Stage`**.
                """
            )
        with gtab4:
            st.markdown(
                """
                * **Permanent Submission:** Tick the **voluntary consent checkbox** in the left sidebar and click **`💾 Submit Progress`** (or **`Submit Current Draft`** at the bottom of `5. Reflect`).
                * **Sharing a Laptop?** Click **`🔄 Reset Current Session`** in the left sidebar to wipe all answers, chat logs, and code buffers for the next student.
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
            st.success("✅ Status: Saved & synced to 'Code Lab IDE → Guide & Notes' and AI助理.")
        else:
            st.info("⬜ Status: Not saved yet — fill in your logic below and click the large **💾 Save Think Stage** button to unlock your Logic Blueprint.")

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
            submitted = st.form_submit_button("💾 Save Think Stage & Unlock Blueprint", type="primary", use_container_width=True)

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
            st.info("⬜ Status: Not saved yet — fill in your pseudocode below and click **💾 Save Pair Stage** to sync it to the IDE.")

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
            submitted = st.form_submit_button("💾 Save Pair Stage & Sync Pseudocode", type="primary", use_container_width=True)

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
            st.info("⬜ Status: Not saved yet — record any AI support below and click **💾 Save GenAI Stage**.")

        with st.form("genai_form"):
            reason = st.text_area("Why are you using AI at this point?", value=st.session_state.genai_reason, height=80)
            prompt = st.text_area("What prompt/question did you ask the AI助理?", value=st.session_state.genai_prompt, height=120)
            output = st.text_area("What did the AI suggest? (summary only)", value=st.session_state.genai_output, height=110)
            use_decision = st.text_area("Did you use the suggestion? Why or why not?", value=st.session_state.genai_use, height=110)
            submitted = st.form_submit_button("💾 Save GenAI Stage", type="primary", use_container_width=True)

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
            st.info("⬜ Status: Not saved yet — complete the audit checklist below and click **💾 Save Audit Stage**.")

        with st.form("audit_form"):
            c1, c2 = st.columns(2)
            with c1:
                accuracy = st.checkbox("We checked mathematical / code correctness", value=st.session_state.audit_accuracy)
                clarity = st.checkbox("We checked whether the explanation is clear", value=st.session_state.audit_clarity)
            with c2:
                edge_cases = st.checkbox("We checked hidden or edge cases", value=st.session_state.audit_edge_cases)
                overreliance = st.checkbox("We discussed whether AI is doing too much thinking for us", value=st.session_state.audit_overreliance)

            judgement = st.text_area("Final judgement about the AI support", value=st.session_state.audit_judgement, height=120)
            submitted = st.form_submit_button("💾 Save Audit Stage", type="primary", use_container_width=True)

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
            st.info("⬜ Status: Not saved yet — write your reflection below and click **💾 Save Reflect Stage**.")

        with st.form("reflect_form"):
            helpful = st.text_area("What did AI help with?", value=st.session_state.reflect_helpful, height=105)
            human = st.text_area("What still required human judgement?", value=st.session_state.reflect_human, height=105)
            next_time = st.text_area("What would you improve next time?", value=st.session_state.reflect_next, height=105)
            submitted = st.form_submit_button("💾 Save Reflect Stage", type="primary", use_container_width=True)

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
            use_container_width=True,
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

    left, middle, right = st.columns([1.1, 1.7, 1.25], gap="medium")

    with left:
        with st.container(height=650):
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
            height=330,
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
        with st.container(height=650):
            top_l, top_r = st.columns([4, 1])
            with top_l:
                st.markdown("<div class='ai-header-pill'>✨ AI助理 · 数学与编程专属</div>", unsafe_allow_html=True)
            with top_r:
                if st.button("🧹", help="清空对话记录", key=f"clear_chat_{mission['id']}"):
                    st.session_state.chat_histories[mission["id"]] = []
                    st.rerun()

            a_tab_chat, a_tab_map = st.tabs(["💬 AI 对话助理", "📚 知识图谱"])

            with a_tab_chat:
                history = st.session_state.chat_histories[mission["id"]]

                if not history:
                    st.markdown(
                        """
                        <div class='ai-greeting-box'>
                            <div class='ai-greeting-title'>👋 Hi, 你好呀</div>
                            <div class='ai-greeting-sub'>专注数学推导与编程答疑 · 实时感知你的代码状态</div>
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )

                    with st.container(border=True):
                        st.markdown("<div class='ai-discover-header'>✨ 发现提示词 &gt;</div>", unsafe_allow_html=True)
                        starter_prompts = [
                            "➕ 帮我诊断当前编辑器里的 Python 代码逻辑",
                            "➕ 欧几里得算法的时间复杂度为什么是 O(log min(a,b))？",
                            "➕ 如何把数学归纳法或递归思想转化为循环代码？",
                        ]
                        for idx, sp in enumerate(starter_prompts):
                            if st.button(sp, use_container_width=True, key=f"discover_{mission['id']}_{idx}"):
                                clean_prompt = sp.replace("➕ ", "")
                                st.session_state.chat_histories[mission["id"]].append(
                                    {"role": "user", "content": clean_prompt}
                                )
                                with st.spinner("思考中..."):
                                    reply = generate_assistant_reply(clean_prompt, mission, code, feedback)
                                st.session_state.chat_histories[mission["id"]].append(
                                    {"role": "assistant", "content": reply}
                                )
                                st.rerun()

                for msg in history:
                    with st.container(border=True):
                        if msg["role"] == "user":
                            st.markdown(f"🧑‍💻 **你：**\n\n{msg['content']}")
                        else:
                            st.markdown(f"🤖 **AI助理：**\n\n{msg['content']}")

                with st.form(key=f"chat_form_{mission['id']}", clear_on_submit=True):
                    user_q = st.text_input(
                        "输入你的数学或编程问题",
                        placeholder="有问题尽管问我~（仅限数学与编程）",
                        label_visibility="collapsed",
                    )
                    send_btn = st.form_submit_button("➤ 发送问题", type="primary", use_container_width=True)

                if send_btn and user_q.strip():
                    clean_q = user_q.strip()
                    st.session_state.chat_histories[mission["id"]].append({"role": "user", "content": clean_q})
                    with st.spinner("AI助理正在推导中..."):
                        reply = generate_assistant_reply(clean_q, mission, code, feedback)
                    st.session_state.chat_histories[mission["id"]].append({"role": "assistant", "content": reply})
                    st.rerun()

                api_key_active, _, model_active = get_configured_ai_credentials()
                if api_key_active:
                    st.caption(f"⚡ Powered by `{model_active}` · 仅限数学与编程领域")
                else:
                    st.caption("💡 提示：在左侧边栏填入通义千问 / DeepSeek API Key 可解锁无限多轮自由推理")

            with a_tab_map:
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
