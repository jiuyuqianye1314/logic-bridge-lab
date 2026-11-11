import streamlit as st
import pandas as pd
import json
import os
from datetime import datetime

# =========================
# Page Config
# =========================
st.set_page_config(
    page_title="Logic Bridge Lab",
    page_icon="🌉",
    layout="wide",
    initial_sidebar_state="expanded"
)

# =========================
# Custom CSS
# =========================
st.markdown("""
<style>
    .stApp {
        background: #0b1020;
        color: #f3f6fb;
    }

    .block-container {
        padding-top: 2rem;
        padding-bottom: 2rem;
        max-width: 1200px;
    }

    h1, h2, h3, h4, h5, h6 {
        color: #f7f9fc !important;
        font-weight: 700 !important;
    }

    p, li, div, label, span {
        color: #dfe7f5;
    }

    .hero-box {
        background: linear-gradient(135deg, #284b96 0%, #3e61ac 100%);
        color: white;
        padding: 1.6rem 1.8rem;
        border-radius: 18px;
        margin-bottom: 1.2rem;
        box-shadow: 0 10px 28px rgba(0, 0, 0, 0.22);
        border: 1px solid rgba(255,255,255,0.08);
    }

    .card {
        background: #151b2d;
        border: 1px solid #25304d;
        border-radius: 16px;
        padding: 1rem 1rem;
        box-shadow: 0 6px 18px rgba(0,0,0,0.16);
        margin-bottom: 1rem;
    }

    .mini-card {
        background: #12192a;
        border: 1px solid #263250;
        border-radius: 14px;
        padding: 0.85rem 1rem;
        margin-bottom: 0.8rem;
    }

    .good-box {
        background: #163327;
        border-left: 5px solid #47c98b;
        padding: 0.95rem 1rem;
        border-radius: 10px;
        margin-bottom: 0.8rem;
    }

    .warn-box {
        background: #3d2d13;
        border-left: 5px solid #f2b84b;
        padding: 0.95rem 1rem;
        border-radius: 10px;
        margin-bottom: 0.8rem;
    }

    .danger-box {
        background: #462121;
        border-left: 5px solid #ff7d7d;
        padding: 0.95rem 1rem;
        border-radius: 10px;
        margin-bottom: 0.8rem;
    }

    .badge {
        display: inline-block;
        padding: 0.28rem 0.7rem;
        border-radius: 999px;
        background: rgba(255,255,255,0.9);
        color: #20407f !important;
        font-weight: 700;
        font-size: 0.82rem;
        margin-right: 0.45rem;
        margin-top: 0.25rem;
    }

    .small-note {
        color: #aab8d1 !important;
        font-size: 0.92rem;
    }

    .stTextInput input, .stTextArea textarea, .stNumberInput input {
        background-color: #1d2436 !important;
        color: #f5f7fb !important;
        border: 1px solid #33415f !important;
        border-radius: 10px !important;
    }

    div[data-baseweb="select"] > div {
        background-color: #1d2436 !important;
        color: #f5f7fb !important;
        border: 1px solid #33415f !important;
        border-radius: 10px !important;
    }

    .stRadio label, .stCheckbox label {
        color: #e4ebf7 !important;
    }

    .stButton button {
        border-radius: 10px;
        border: 1px solid #42547d;
        background: #1d2d55;
        color: white;
        font-weight: 600;
    }

    .stButton button:hover {
        background: #2a3f73;
        border-color: #5b75b8;
    }

    [data-testid="stSidebar"] {
        background: #171b29;
        border-right: 1px solid #2a3146;
    }

    [data-testid="stMetricValue"] {
        color: #ffffff !important;
    }

    .caption-text {
        color: #a9b6ce;
        font-size: 0.95rem;
        margin-top: -0.5rem;
        margin-bottom: 1rem;
    }

    .section-title {
        margin-top: 0.4rem;
        margin-bottom: 0.3rem;
        font-size: 1.15rem;
        font-weight: 700;
        color: #f3f7ff;
    }
</style>
""", unsafe_allow_html=True)

# =========================
# Data Utilities
# =========================
DATA_FILE = "logic_bridge_lab_submissions.json"

def load_submissions():
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return []
    return []

def save_submissions(submissions):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(submissions, f, ensure_ascii=False, indent=2)

def init_current():
    return {
        "meta": {
            "group_id": "",
            "class_id": "",
            "student_count": 3,
            "date": str(datetime.now().date()),
            "timestamp": ""
        },
        "roles": {
            "designer": "",
            "coder": "",
            "auditor": ""
        },
        "think": {
            "input_desc": "",
            "output_desc": "",
            "repeat_steps": "",
            "stop_condition": "",
            "pseudocode": ""
        },
        "pair": {
            "refined_logic": "",
            "missing_edge_cases": "",
            "peer_feedback": ""
        },
        "genai": {
            "use_purpose": "",
            "prompt_used": "",
            "ai_response": "",
            "ai_summary": "",
            "used_or_not": "",
            "reason": ""
        },
        "audit": {
            "q_clear_question": False,
            "q_attempted_first": False,
            "q_used_for_support": False,
            "r_answered_actual_question": False,
            "r_preserved_logic": False,
            "r_understandable": False,
            "r_no_reasoning_skips": False,
            "r_no_edge_case_ignore": False,
            "j_tested_before_accepting": False,
            "j_rejected_part": False,
            "j_can_explain_final_code": False,
            "j_know_own_vs_ai_parts": False,
            "final_judgement": "",
            "short_note": "",
            "audit_reason": ""
        },
        "reflect": {
            "hardest_part": "",
            "ai_helped": "",
            "human_judgement": "",
            "learned": "",
            "next_time": ""
        },
        "status": {
            "think_done": False,
            "pair_done": False,
            "genai_done": False,
            "audit_done": False,
            "reflect_done": False,
            "submitted": False
        }
    }

def status_count(status):
    keys = ["think_done", "pair_done", "genai_done", "audit_done", "reflect_done"]
    return sum(1 for k in keys if status.get(k))

def safe_metric_text(value, fallback="Not set"):
    return value if value else fallback

def build_summary_dataframe(submissions):
    flat_rows = []
    for s in submissions:
        completeness = sum([
            s["status"].get("think_done", False),
            s["status"].get("pair_done", False),
            s["status"].get("genai_done", False),
            s["status"].get("audit_done", False),
            s["status"].get("reflect_done", False),
        ])
        flat_rows.append({
            "timestamp": s["meta"].get("timestamp", ""),
            "group_id": s["meta"].get("group_id", ""),
            "class_id": s["meta"].get("class_id", ""),
            "student_count": s["meta"].get("student_count", ""),
            "think_done": s["status"].get("think_done", False),
            "pair_done": s["status"].get("pair_done", False),
            "genai_done": s["status"].get("genai_done", False),
            "audit_done": s["status"].get("audit_done", False),
            "reflect_done": s["status"].get("reflect_done", False),
            "completeness_score": f"{completeness}/5",
            "final_judgement": s["audit"].get("final_judgement", ""),
            "hardest_part": s["reflect"].get("hardest_part", ""),
            "ai_use_purpose": s["genai"].get("use_purpose", "")
        })
    return pd.DataFrame(flat_rows)

# =========================
# Session State Init
# =========================
if "submissions" not in st.session_state:
    st.session_state.submissions = load_submissions()

if "current" not in st.session_state:
    st.session_state.current = init_current()

# =========================
# Sidebar
# =========================
st.sidebar.title("Logic Bridge Lab")
st.sidebar.caption("Pedagogy-led AI support for the logic-to-code transition")

page = st.sidebar.radio(
    "Navigation",
    [
        "1. Home",
        "2. Think",
        "3. Pair",
        "4. GenAI Support",
        "5. Audit",
        "6. Reflect",
        "7. Teacher Dashboard"
    ]
)

with st.sidebar.expander("Current Group Setup", expanded=True):
    st.session_state.current["meta"]["group_id"] = st.text_input(
        "Group ID",
        value=st.session_state.current["meta"]["group_id"]
    )
    st.session_state.current["meta"]["class_id"] = st.text_input(
        "Class / Tutorial Group",
        value=st.session_state.current["meta"]["class_id"]
    )
    st.session_state.current["meta"]["student_count"] = st.number_input(
        "Number of Students in Group",
        min_value=1,
        max_value=10,
        value=st.session_state.current["meta"]["student_count"]
    )

st.sidebar.markdown("---")
st.sidebar.markdown("### Progress")
progress = status_count(st.session_state.current["status"]) / 5
st.sidebar.caption(f"{int(progress * 100)}% completed")
st.sidebar.progress(progress)

for label, key in [
    ("Think", "think_done"),
    ("Pair", "pair_done"),
    ("GenAI", "genai_done"),
    ("Audit", "audit_done"),
    ("Reflect", "reflect_done"),
]:
    mark = "✅" if st.session_state.current["status"][key] else "⬜"
    st.sidebar.write(f"{mark} {label}")

st.sidebar.markdown("---")

if st.sidebar.button("Reset Current Draft"):
    st.session_state.current = init_current()
    st.sidebar.success("Current draft reset.")

# =========================
# Header
# =========================
st.markdown("""
<div class="hero-box">
    <h1 style="margin-bottom:0.35rem;">🌉 Logic Bridge Lab</h1>
    <div style="font-size:1.02rem;">
        A structured learning platform for translating mathematical reasoning into executable Python code
    </div>
    <div style="margin-top:0.75rem;">
        <span class="badge">Think</span>
        <span class="badge">Pair</span>
        <span class="badge">GenAI Support</span>
        <span class="badge">Audit</span>
        <span class="badge">Reflect</span>
    </div>
</div>
""", unsafe_allow_html=True)

# =========================
# Page 1: Home
# =========================
if page == "1. Home":
    col1, col2 = st.columns([2, 1])

    with col1:
        st.subheader("Learning Rule")
        st.info("Think → Pair → GenAI → Audit → Reflect")

        st.write("""
This prototype operationalises the lesson design by guiding students through a structured sequence:
1. **Think**: articulate the mathematical logic first  
2. **Pair**: compare and refine logic collaboratively  
3. **GenAI Support**: use AI strategically for checking, debugging, and testing  
4. **Audit**: critically evaluate AI outputs before accepting them  
5. **Reflect**: identify what AI helped with and what still required human judgement
        """)

        st.markdown("""
<div class="good-box">
<strong>Pedagogical principle:</strong> AI is used as a scaffold, not as an answer engine.
</div>
<div class="warn-box">
<strong>Classroom rule:</strong> Students should attempt the task before using AI.
</div>
        """, unsafe_allow_html=True)

        st.subheader("This lesson task")
        st.write("""
Students use the **Euclidean Algorithm** to write:
- `gcd(a, b)`
- `simplify_fraction(a, b)`

Sample test cases:
- `8/12 → 2/3`
- `7/13 → 7/13`
- `5/0 → What should happen?`
        """)

        st.markdown("""
<div class="mini-card">
<strong>Alignment with lesson materials:</strong> the app supports pseudocode drafting, structured GenAI use, auditing, and reflection, which match the handout, auditor checklist, AI-use log, and exit reflection design.
</div>
        """, unsafe_allow_html=True)

    with col2:
        st.subheader("Current Draft Summary")
        meta = st.session_state.current["meta"]
        st.metric("Group ID", safe_metric_text(meta["group_id"]))
        st.metric("Class", safe_metric_text(meta["class_id"]))
        st.metric("Completed Stages", f"{status_count(st.session_state.current['status'])}/5")

        st.subheader("Evidence Alignment")
        st.write("""
This app can support collection of:
- pseudocode drafts
- AI-use logs
- auditor decisions
- reflection data
- submission summaries
        """)

# =========================
# Page 2: Think
# =========================
elif page == "2. Think":
    st.subheader("🧠 Phase 1: Think First (No AI Yet)")
    st.caption("Start by making the mathematical logic visible before asking for assistance.")

    think = st.session_state.current["think"]

    st.write("### Step A. Describe the problem in your own words")

    col1, col2 = st.columns(2)
    with col1:
        think["input_desc"] = st.text_area(
            "What is the input?",
            value=think["input_desc"],
            height=100,
            placeholder="Example: two integers representing the numerator and denominator, or two numbers for gcd(a, b)"
        )
        think["repeat_steps"] = st.text_area(
            "What steps are repeated?",
            value=think["repeat_steps"],
            height=120,
            placeholder="Example: repeatedly replace a and b until the remainder becomes 0"
        )

    with col2:
        think["output_desc"] = st.text_area(
            "What is the output?",
            value=think["output_desc"],
            height=100,
            placeholder="Example: the gcd or the simplified fraction"
        )
        think["stop_condition"] = st.text_area(
            "When does the process stop?",
            value=think["stop_condition"],
            height=120,
            placeholder="Example: when b becomes 0"
        )

    st.write("### Step B. Draft the pseudocode")
    think["pseudocode"] = st.text_area(
        "Your pseudocode draft",
        value=think["pseudocode"],
        height=240,
        placeholder="Input: ...\nWhile ...\n    ...\nReturn ..."
    )

    if st.button("Save Think Draft"):
        st.session_state.current["status"]["think_done"] = True
        st.success("Think stage saved successfully.")

# =========================
# Page 3: Pair
# =========================
elif page == "3. Pair":
    st.subheader("👥 Phase 2: Pair and Refine")
    st.caption("Compare your logic, assign roles, and refine your plan before using AI.")

    pair = st.session_state.current["pair"]
    roles = st.session_state.current["roles"]

    st.write("### Group Roles")
    col1, col2, col3 = st.columns(3)
    with col1:
        roles["designer"] = st.text_input("Designer", value=roles["designer"], placeholder="Name / role holder")
    with col2:
        roles["coder"] = st.text_input("Coder", value=roles["coder"], placeholder="Name / role holder")
    with col3:
        roles["auditor"] = st.text_input("Auditor", value=roles["auditor"], placeholder="Name / role holder")

    st.write("### Collaborative Refinement")
    pair["refined_logic"] = st.text_area(
        "Refined group logic / improved pseudocode",
        value=pair["refined_logic"],
        height=180,
        placeholder="What did your group revise after discussion?"
    )

    col1, col2 = st.columns(2)
    with col1:
        pair["missing_edge_cases"] = st.text_area(
            "Possible missing edge cases",
            value=pair["missing_edge_cases"],
            height=120,
            placeholder="Example: denominator = 0; already simplified fraction"
        )
    with col2:
        pair["peer_feedback"] = st.text_area(
            "Partner / group feedback",
            value=pair["peer_feedback"],
            height=120,
            placeholder="What did your peer point out?"
        )

    if st.button("Save Pair Stage"):
        st.session_state.current["status"]["pair_done"] = True
        st.success("Pair stage saved successfully.")

# =========================
# Page 4: GenAI Support
# =========================
elif page == "4. GenAI Support":
    st.subheader("🤖 Phase 3: Structured GenAI Support")
    st.caption("Use AI strategically for checking, debugging, and improving your work.")

    genai = st.session_state.current["genai"]

    st.write("### Prompt Bank")
    prompt_option = st.selectbox(
        "Choose a prompt purpose",
        [
            "Check whether our pseudocode misses any steps",
            "Point out possible bugs without rewriting everything",
            "Suggest testing cases for this function",
            "Explain why this loop might fail",
            "Help us improve the logic, not just give a final answer"
        ]
    )

    st.code(prompt_option, language="text")

    st.write("### AI Interaction Log")
    purpose_options = [
        "",
        "Understand and check logic",
        "Fix syntax or bugs",
        "Generate test cases",
        "Clarify why code failed",
        "Get an answer quickly"
    ]
    genai["use_purpose"] = st.selectbox(
        "Why do you use AI?",
        purpose_options,
        index=purpose_options.index(genai["use_purpose"]) if genai["use_purpose"] in purpose_options else 0
    )

    genai["prompt_used"] = st.text_area(
        "What prompt did you use?",
        value=genai["prompt_used"],
        height=120,
        placeholder="Paste or type the exact prompt you used"
    )

    genai["ai_response"] = st.text_area(
        "Paste AI response here",
        value=genai["ai_response"],
        height=220,
        placeholder="Paste the AI-generated explanation / code / suggestions"
    )

    col1, col2 = st.columns(2)
    with col1:
        genai["ai_summary"] = st.text_area(
            "What did AI suggest?",
            value=genai["ai_summary"],
            height=120,
            placeholder="Summarise the key AI suggestion"
        )
    with col2:
        use_options = ["", "Used all of it", "Used part of it", "Rejected it"]
        genai["used_or_not"] = st.selectbox(
            "Did you use the AI suggestion?",
            use_options,
            index=use_options.index(genai["used_or_not"]) if genai["used_or_not"] in use_options else 0
        )
        genai["reason"] = st.text_area(
            "Why or why not?",
            value=genai["reason"],
            height=120,
            placeholder="Explain your judgement"
        )

    if st.button("Save GenAI Stage"):
        st.session_state.current["status"]["genai_done"] = True
        st.success("GenAI interaction saved successfully.")

# =========================
# Page 5: Audit
# =========================
elif page == "5. Audit":
    st.subheader("🕵️ Phase 4: Critical Audit")
    st.caption("Do not accept AI output blindly. Test it, trace it, and justify your decision.")

    audit = st.session_state.current["audit"]

    st.write("### AI Response Under Review")
    st.code(st.session_state.current["genai"]["ai_response"] or "No AI response saved yet.", language="python")

    st.write("### A. About our question")
    audit["q_clear_question"] = st.checkbox("We asked AI a clear and specific question.", value=audit["q_clear_question"])
    audit["q_attempted_first"] = st.checkbox("We first attempted the task ourselves before using AI.", value=audit["q_attempted_first"])
    audit["q_used_for_support"] = st.checkbox("We asked AI for explanation, checking, debugging, or test cases rather than only for a full answer.", value=audit["q_used_for_support"])

    st.write("### B. About the AI response")
    audit["r_answered_actual_question"] = st.checkbox("The AI response answered our actual question.", value=audit["r_answered_actual_question"])
    audit["r_preserved_logic"] = st.checkbox("The AI preserved the mathematical logic of the problem.", value=audit["r_preserved_logic"])
    audit["r_understandable"] = st.checkbox("The AI response was understandable to our group.", value=audit["r_understandable"])
    audit["r_no_reasoning_skips"] = st.checkbox("The AI response did not skip important reasoning steps.", value=audit["r_no_reasoning_skips"])
    audit["r_no_edge_case_ignore"] = st.checkbox("The AI response did not ignore edge cases.", value=audit["r_no_edge_case_ignore"])

    st.write("### C. About our judgement")
    audit["j_tested_before_accepting"] = st.checkbox("We tested the AI suggestion before accepting it.", value=audit["j_tested_before_accepting"])
    audit["j_rejected_part"] = st.checkbox("We rejected at least one part of the AI output because it was incorrect, unnecessary, or unclear.", value=audit["j_rejected_part"])
    audit["j_can_explain_final_code"] = st.checkbox("We can explain the final code in our own words.", value=audit["j_can_explain_final_code"])
    audit["j_know_own_vs_ai_parts"] = st.checkbox("We know which part came from our own reasoning and which part was revised after AI support.", value=audit["j_know_own_vs_ai_parts"])

    judgement_options = ["Very helpful", "Partly helpful", "Limited", "Misleading"]
    col1, col2 = st.columns(2)
    with col1:
        audit["final_judgement"] = st.radio(
            "Final judgement",
            judgement_options,
            index=judgement_options.index(audit["final_judgement"]) if audit["final_judgement"] in judgement_options else 0
        )
    with col2:
        audit["short_note"] = st.text_area(
            "What was one important thing your group had to judge for itself?",
            value=audit["short_note"],
            height=120
        )

    audit["audit_reason"] = st.text_area(
        "Overall reason for the audit decision",
        value=audit["audit_reason"],
        height=140,
        placeholder="Explain why the AI output was accepted, partly accepted, or rejected."
    )

    if st.button("Save Audit Stage"):
        st.session_state.current["status"]["audit_done"] = True
        st.success("Audit stage saved successfully.")

# =========================
# Page 6: Reflect
# =========================
elif page == "6. Reflect":
    st.subheader("📝 Phase 5: Exit Reflection")
    st.caption("Identify what AI helped with and what still required your own judgement.")

    reflect = st.session_state.current["reflect"]

    hardest_options = [
        "Understanding the mathematical logic",
        "Writing pseudocode",
        "Writing Python syntax",
        "Evaluating AI output",
        "Working in a group"
    ]

    reflect["hardest_part"] = st.radio(
        "What was the most difficult part of today’s lesson?",
        hardest_options,
        index=hardest_options.index(reflect["hardest_part"]) if reflect["hardest_part"] in hardest_options else 0
    )

    reflect["ai_helped"] = st.text_area(
        "What did AI help you with most today?",
        value=reflect["ai_helped"],
        height=120
    )
    reflect["human_judgement"] = st.text_area(
        "What did you still have to judge by yourself?",
        value=reflect["human_judgement"],
        height=120
    )
    reflect["learned"] = st.text_area(
        "One thing I learned about turning logic into code is:",
        value=reflect["learned"],
        height=120
    )
    reflect["next_time"] = st.text_area(
        "One thing I would do differently next time is:",
        value=reflect["next_time"],
        height=120
    )

    col1, col2, col3 = st.columns(3)

    with col1:
        if st.button("Save Reflection"):
            st.session_state.current["status"]["reflect_done"] = True
            st.success("Reflection saved successfully.")

    with col2:
        if st.button("Finalize & Submit Group Record"):
            st.session_state.current["status"]["reflect_done"] = True
            st.session_state.current["status"]["submitted"] = True
            st.session_state.current["meta"]["timestamp"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            st.session_state.submissions.append(json.loads(json.dumps(st.session_state.current)))
            save_submissions(st.session_state.submissions)
            st.success("Group record submitted and archived successfully.")
            st.balloons()

    with col3:
        if st.button("Submit & Start New Group"):
            st.session_state.current["status"]["reflect_done"] = True
            st.session_state.current["status"]["submitted"] = True
            st.session_state.current["meta"]["timestamp"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            st.session_state.submissions.append(json.loads(json.dumps(st.session_state.current)))
            save_submissions(st.session_state.submissions)
            st.success("Current group archived. Ready for a new group.")
            st.session_state.current = init_current()

# =========================
# Page 7: Teacher Dashboard
# =========================
elif page == "7. Teacher Dashboard":
    st.subheader("📊 Teacher Dashboard")
    st.caption("Monitor progress, review audit outcomes, and export pilot evidence.")

    submissions = st.session_state.submissions
    current = st.session_state.current

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Archived Submissions", len(submissions))
    col2.metric("Current Draft Stages", f"{status_count(current['status'])}/5")
    col3.metric("Current Group", safe_metric_text(current["meta"]["group_id"]))
    col4.metric("Submitted?", "Yes" if current["status"]["submitted"] else "No")

    st.write("### Current Draft Snapshot")
    st.json(current)

    if submissions:
        df = build_summary_dataframe(submissions)

        st.write("### Submission Table")
        st.dataframe(df, use_container_width=True)

        csv = df.to_csv(index=False).encode("utf-8")
        st.download_button(
            "Download Submission Summary (CSV)",
            data=csv,
            file_name="logic_bridge_lab_submission_summary.csv",
            mime="text/csv"
        )

        raw_json = json.dumps(submissions, ensure_ascii=False, indent=2)
        st.download_button(
            "Download Full Evidence Archive (JSON)",
            data=raw_json,
            file_name="logic_bridge_lab_full_archive.json",
            mime="application/json"
        )
    else:
        st.info("No archived submissions yet. Finalize a group record on the Reflect page first.")