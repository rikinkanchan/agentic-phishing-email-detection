import io
import json
import time
from html import escape
from contextlib import redirect_stdout
from urllib.error import URLError

import streamlit as st
from agent_loop import investigate
from email_loader import load_eml

st.set_page_config(
    page_title="PhishLens | Email Investigator",
    page_icon="🛡️",
    layout="wide"
)

st.markdown("""
<style>
.stApp {
    background: radial-gradient(ellipse at top left, #123039 0%, #080f1c 55%);
    color: #e6edf7;
}
.block-container {max-width: 1280px; padding-top: 2.5rem;}
[data-testid="stHeader"] {background: transparent;}
h1, h2, h3, p, label {color: #e6edf7;}
[data-testid="stCaptionContainer"] p {color: #95a8bf;}
[data-testid="stText"] {color: #dce6f2; font-family: inherit;}
[data-testid="stTextArea"] textarea {
    background: #0b1423; color: #dce6f2;
    border: 1px solid #26394d; border-radius: 12px;
    font-family: monospace; font-size: 14px;
}
[data-testid="stFileUploaderDropzone"] {
    background: #0b1423; color: #dce6f2;
    border: 1px dashed #345063; border-radius: 12px;
}
[data-testid="stVerticalBlockBorderWrapper"] > div {
    border-color: #243449 !important; border-radius: 18px;
}
.stButton button[kind="primary"] {
    background: #55e1c4; color: #07251f;
    border: none; border-radius: 10px; font-weight: 700;
}
.stButton button[kind="primary"]:hover {
    background: #8af0da; color: #07251f;
}
.stButton button[kind="secondary"],
.stDownloadButton button {
    background: #142235; color: #dce6f2;
    border: 1px solid #2c4158; border-radius: 10px;
}
.hero {padding: 12px 0 30px;}
.brand {font-size: 13px; letter-spacing: 3px; font-weight: 700; color: #55e1c4;}
.hero h1 {font-size: clamp(34px, 5vw, 58px); letter-spacing: -2px;
          line-height: 1.1; margin: 16px 0;}
.hero p {color: #a7b8cc; max-width: 650px; font-size: 17px;}
.pills {display: flex; flex-wrap: wrap; gap: 8px; margin-top: 20px;}
.pill {border: 1px solid #284353; background: #102632;
       color: #a9dfd4; padding: 6px 12px; border-radius: 30px; font-size: 12px;}
.verdict {padding: 24px; border: 1px solid #756038; border-radius: 16px;
          background: linear-gradient(120deg, #302719, #18202c); margin-bottom: 20px;}
.verdict.neutral {border-color: #315676; background: #102337;}
.eyebrow {font-size: 11px; letter-spacing: 2px; color: #afbac9; font-weight: 700;}
.verdict h2 {font-size: 28px; margin: 8px 0; color: #f5cf87;}
.verdict.neutral h2 {color: #a5d6f7;}
.verdict p {font-size: 14px; color: #c0c9d5; margin: 0;}
.evidence {background: #111d2e; border: 1px solid #25374b;
           border-left: 3px solid #55e1c4; border-radius: 12px;
           padding: 15px 18px; margin-bottom: 10px; overflow-wrap: anywhere;}
.evidence .number {font-size: 11px; color: #55e1c4; letter-spacing: 1px;}
.evidence p {font-size: 14px; line-height: 1.6; margin: 6px 0 0;}
.empty {padding: 65px 25px; text-align: center;}
.empty .symbol {font-size: 58px; color: #55e1c4; margin-bottom: 20px;}
.empty h3 {font-size: 23px;}
.empty p {color: #95a8bf; font-size: 15px; line-height: 1.7;}
.footer {border-top: 1px solid #213246; padding: 18px 0;
         margin-top: 28px; color: #8295ad; font-size: 12px;}
</style>
<div class="hero">
  <div class="brand">◈ PHISHLENS / EMAIL INVESTIGATOR</div>
  <h1>Inspect the email.<br>Understand the signals.</h1>
  <p>A local AI agent investigates warning signs and turns evidence
     into a clear, actionable report.</p>
  <div class="pills">
    <span class="pill">Local AI</span>
    <span class="pill">Evidence-based explanations</span>
    <span class="pill">Links never opened</span>
  </div>
</div>
""", unsafe_allow_html=True)

SAMPLE = (
    "From: Example Bank <alerts@bank.example>\n"
    "Reply-To: support@account-help.example\n"
    "Subject: Urgent account notice\n\n"
    "Verify your account and enter your password here:\n"
    "http://192.0.2.10/login"
)

left, right = st.columns([1, 1.15], gap="large")
email_text = ""
input_error = None

with left:
    with st.container(border=True):
        st.subheader("Investigate an email")
        st.caption("Choose a source, then let the agent inspect the evidence.")
        source = st.radio(
            "Email source", ["Paste email", "Upload .eml"],
            horizontal=True, label_visibility="collapsed"
        )

        if source == "Paste email":
            if st.button("Load demo email", use_container_width=True):
                st.session_state["email_input"] = SAMPLE
            email_text = st.text_area(
                "Email headers and message",
                key="email_input",
                height=300,
                max_chars=6000,
                placeholder="From: sender@example.com\nSubject: Message\n\nPaste the email body..."
            )
            st.caption("Include From, Reply-To and Subject when available. No END needed.")
        else:
            uploaded = st.file_uploader("Choose an email file", type=["eml"])
            st.caption("Up to 1 MB • Plain-text body required • Attachments excluded")
            if uploaded is not None:
                try:
                    email_text = load_eml(uploaded.getvalue())
                    with st.expander("Preview extracted email"):
                        st.text(email_text)
                except (ValueError, LookupError) as error:
                    input_error = str(error)
                    st.error(input_error)

        analyse = st.button(
            "Investigate email →",
            type="primary",
            use_container_width=True,
            disabled=bool(input_error)
        )

    st.caption(
        "Prototype for review assistance. Sender authentication and "
        "link reputation are not tested."
    )

if analyse:
    st.session_state.pop("analysis", None)
    if not email_text.strip():
        with left:
            st.warning("Paste an email or upload an .eml file first.")
    else:
        trace = io.StringIO()
        started = time.perf_counter()
        try:
            with right:
                with st.spinner("Agent is choosing tools and reviewing evidence…"):
                    with redirect_stdout(trace):
                        report = investigate(email_text)

            if report is None:
                with right:
                    st.error("The step limit was reached. Investigation is incomplete.")
            else:
                st.session_state["analysis"] = {
                    "input": email_text,
                    "source": source,
                    "report": report,
                    "trace": trace.getvalue(),
                    "seconds": time.perf_counter() - started
                }
        except (URLError, TimeoutError, ValueError, KeyError) as error:
            with right:
                st.error("Investigation could not finish.")
                st.text(str(error))
        if "analysis" not in st.session_state:
            with right:
                with st.expander("Investigation details"):
                    st.code(trace.getvalue(), language=None)

saved = st.session_state.get("analysis")
current = saved and saved["input"] == email_text and saved["source"] == source

with right:
    if current:
        report = saved["report"]
        suspicious = report["verdict"] == "suspicious"
        label = "Suspicious — review required" if suspicious else "Inconclusive"
        detail = (
            "Warning signs were found. Verify the request independently."
            if suspicious else
            "No configured warning signs found. This does not establish safety."
        )
        kind = "" if suspicious else "neutral"
        st.markdown(
            f'<div class="verdict {kind}"><div class="eyebrow">INVESTIGATION RESULT</div>'
            f'<h2>{label}</h2><p>{detail}</p></div>',
            unsafe_allow_html=True
        )

        a, b, c = st.columns(3)
        a.metric("Warning signs", len(report["findings"]))
        b.metric("Tools used", len(report["tools_used"]))
        c.metric("Analysis time", f'{saved["seconds"]:.1f}s')

        st.subheader("Evidence")
        if report["findings"]:
            for index, finding in enumerate(report["findings"], 1):
                st.markdown(
                    '<div class="evidence">'
                    f'<div class="number">SIGNAL {index:02d}</div>'
                    f'<p>{escape(finding)}</p></div>',
                    unsafe_allow_html=True
                )
        else:
            st.info("The configured checks returned no findings.")

        with st.expander("Why these signals matter", expanded=False):
            st.text(report["explanation"])

        with st.container(border=True):
            st.subheader("Your next step")
            st.text(
                "Avoid the email's links and do not reply with sensitive information. "
                "Verify the request through a known official channel."
                if suspicious else
                "Independently verify unexpected requests before acting. "
                "An inconclusive result is not a safety guarantee."
            )

        with st.expander("Agent activity"):
            st.caption("Tools: " + ", ".join(report["tools_used"]))
            st.code(saved["trace"], language=None)

        st.download_button(
            "Download report ↓",
            data=json.dumps(report, indent=2),
            file_name="phishlens_report.json",
            mime="application/json",
            use_container_width=True
        )
    elif not analyse:
        with st.container(border=True):
            st.markdown("""
            <div class="empty">
              <div class="symbol">◈</div>
              <div class="eyebrow">READY TO INVESTIGATE</div>
              <h3>Your evidence starts here.</h3>
              <p>Paste an email or upload a message.<br>
              Review its warning signs, understand their meaning,<br>
              and decide your next step.</p>
            </div>
            """, unsafe_allow_html=True)

st.markdown(
    '<div class="footer">PHISHLENS · Local investigation · '
    'Rule-based verdicts · Evidence-template explanations</div>',
    unsafe_allow_html=True
)
