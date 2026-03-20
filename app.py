"""Main Entry Module"""


import re
import traceback

import gradio as gr

from src.graph.log_analysis_workflow import create_workflow

app = create_workflow()

SAMPLE_LOG = """
[2024-06-01 10:23:44] TESTCASE: test_login FAILED
Error: Timeout waiting for response
Stacktrace: file.py line 22
------------------------------------------------
[2024-06-01 10:23:50] TESTCASE: test_signup PASSED
"""

FAILED_SAMPLE_LOG = """
[2024-06-01 10:23:44] TESTCASE: test_login FAILED
Error: Timeout waiting for response
Stacktrace: file.py line 22
"""

PASSED_SAMPLE_LOG = """
[2024-06-01 10:23:50] TESTCASE: test_signup PASSED
[2024-06-01 10:23:52] TESTCASE: test_profile_update PASSED
"""

# ------------- HELPERS (unchanged) -------------
def extract_failed_from_logs(log_text):
    return re.findall(r"TESTCASE:\s*(.*?)\s*FAILED", log_text)

def format_jira_tickets(jira_list):
    if not jira_list:
        return "### 🔗 Jira Tickets\n✔ No Jira Tickets Created"

    out = "### 🔗 Jira Tickets\n"
    for t in jira_list:
        ticket_id = t.get("ticket_id", "N/A")
        summary = t.get("summary", "")
        status = t.get("status", "")
        description = t.get("description", "")
        details_section = ""

        if "details" in t:
            details_section = f"\n**Details:**\n{t['details']}\n"
        elif "error_details" in t:
            details_section = f"\n**Details:**\n{t['error_details']}\n"

        out += f"""
#### 🧾 Ticket: **{ticket_id}**

**Summary:** {summary}
**Status:** {status}

**Description:**
{description}

{details_section}
---
"""
    return out

# ---------------- LOADERS ----------------
def load_sample():
    return SAMPLE_LOG

def load_failed_sample():
    return FAILED_SAMPLE_LOG

def load_passed_sample():
    return PASSED_SAMPLE_LOG

# ------------ MAIN LOGIC (unchanged) ------------
def analyze_logs(log_text: str):
    if not log_text.strip():
        return ("⚠️ Please paste some logs first.", "", "", "")

    try:
        initial_state = {
            "log_content": log_text,
            "test_status": None,
            "failed_testcases": None,
            "summary_report": None,
            "failure_report": None,
            "jira_tickets": None,
            "messages": [],
        }

        result = app.invoke(initial_state)

        status = result.get("test_status", "unknown")
        failed = result.get("failed_testcases")

        if (not failed) and isinstance(result.get("per_test"), dict):
            failed = [
                t for t, s in result["per_test"].items()
                if "FAIL" in str(s).upper()
            ]

        if not failed:
            failed = extract_failed_from_logs(log_text)

        failed = failed or []

        summary = result.get("summary_report")
        failure = result.get("failure_report") or ""
        jira = result.get("jira_tickets") or []

        if failed:
            failed_md = "### ❌ Failed Testcases\n" + "\n".join(f"- {t}" for t in failed)
        else:
            failed_md = "### ✔ No Failed Tests"

        status_md = f"""
### 🧪 Test Status
**{status.upper()}**

{failed_md}
"""

        # Success Report (renamed from Summary Report)
        summary_md = (
            f"### ✅ Success Report\n{summary}"
            if summary else
            "### ✅ Success Report\n✔ No Success Report Generated"
        )

        failure_md = (
            f"### 🛑 Failure Report\n{failure}"
            if failure.strip()
            else
            "### 🛑 Failure Report\n✔ No Failure Report Generated"
        )

        jira_md = format_jira_tickets(jira)

        return (status_md, summary_md, failure_md, jira_md)

    except Exception:
        return (
            f"❌ Internal Error:\n```\n{traceback.format_exc()}\n```",
            "",
            "",
            "",
        )

# ---- Wrapper to support optional file input (kept minimal) ----
def analyze_logs_from_inputs(log_text: str, log_file):
    """
    If a file is uploaded, its contents take precedence over the textbox.
    Otherwise, use the textbox content as-is.
    """
    try:
        if log_file is not None:
            # gr.File with type='binary' returns bytes
            if isinstance(log_file, bytes):
                content = log_file.decode("utf-8", errors="ignore")
            else:
                # Some gradio versions pass a dict-like or tempfile; attempt .read()
                try:
                    content = log_file.read().decode("utf-8", errors="ignore")
                except Exception:
                    # Fallback: treat as str path
                    path = str(log_file)
                    with open(path, "rb") as f:
                        content = f.read().decode("utf-8", errors="ignore")
        else:
            content = log_text or ""

        return analyze_logs(content)
    except Exception:
        return (
            f"❌ Error reading uploaded file:\n```\n{traceback.format_exc()}\n```",
            "",
            "",
            "",
        )

# ------------------- UI -------------------
with gr.Blocks() as demo:

    gr.Markdown("# 🧭 Test Log Analyzer")

    with gr.Group():
        log_input = gr.Textbox(label="Paste Test Logs", lines=6)
        # File attachment input
        log_file = gr.File(label="Or upload a log file (.txt/.log)", file_types=[".txt", ".log"], type="binary")

        with gr.Row():
            run_btn = gr.Button("🚀 Generate Analysis", variant="primary")
            # Sample buttons removed per request

    # Wrap analysis area with an element ID so we can scroll to it
    with gr.Column(elem_id="analysis_section"):
        with gr.Tabs():
            with gr.Tab("Status"):
                status_out = gr.Markdown()
            with gr.Tab("Success Report"):
                summary_out = gr.Markdown()
            with gr.Tab("Failure Report"):
                failure_out = gr.Markdown()
            with gr.Tab("Jira Tickets"):
                jira_msg_out = gr.Markdown()

    def disable_button():
        return gr.update(value="⏳ Processing...", interactive=False)

    def enable_button():
        return gr.update(value="🚀 Generate Analysis", interactive=True)

    # After analysis, clear the uploaded file input
    def reset_file_input():
        return gr.update(value=None)

    run_btn.click(disable_button, None, [run_btn]).then(
        analyze_logs_from_inputs, [log_input, log_file],
        [status_out, summary_out, failure_out, jira_msg_out]
    ).then(
        reset_file_input, None, [log_file]
    ).then(
        enable_button, None, [run_btn]
    ).then(
        # NEW: Smoothly scroll to the analysis section after everything completes
        None, None, None,
        js="""
() => {
  const el = document.getElementById('analysis_section');
  if (el && el.scrollIntoView) {
    el.scrollIntoView({ behavior: 'smooth', block: 'start' });
  }
}
"""
    )

demo.launch(server_name="localhost", server_port=7860, theme=gr.themes.Soft())
