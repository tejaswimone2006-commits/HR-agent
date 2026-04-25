import streamlit as st
import pandas as pd
import os
import time
import tempfile
import speech_recognition as sr
from gtts import gTTS
from datetime import datetime
import smtplib
from email.mime.text import MIMEText
import ssl

from resume_engine.ranker import rank_candidates
from pipeline.state_manager import PipelineStateManager
from scheduling.scheduler import InterviewScheduler
from leave.policy_engine import LeavePolicyEngine
from escalation.escalation_checker import EscalationEngine


# ------------------------------------------------
# CONFIG
# ------------------------------------------------

st.set_page_config(page_title="HR Autonomous AI Agent", layout="wide")
st.title("🚀 HR Autonomous AI Agent")

# 🔐 CHANGE THESE
SENDER_EMAIL = ""
SENDER_PASSWORD = ""  # Gmail App Password


# ------------------------------------------------
# EMAIL FUNCTION (FULLY FIXED)
# ------------------------------------------------

def send_email(to_email, subject, body):
    try:
        context = ssl.create_default_context()

        server = smtplib.SMTP("smtp.gmail.com", 587)
        server.ehlo()
        server.starttls(context=context)
        server.ehlo()
        server.login(SENDER_EMAIL, SENDER_PASSWORD)

        message = f"Subject: {subject}\n\n{body}"
        server.sendmail(SENDER_EMAIL, to_email, message)
        server.quit()

        return True

    except Exception as e:
        st.error(f"Email Error: {e}")
        return False


# ------------------------------------------------
# DATASET PREP
# ------------------------------------------------

def convert_dataset(file_path):
    df = pd.read_csv(file_path)
    df["candidate_id"] = ["C" + str(i+1) for i in range(len(df))]
    df["resume_text"] = df.astype(str).agg(" ".join, axis=1)
    df = df[["candidate_id", "resume_text"]]
    df.to_csv(file_path, index=False)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
resume_path = os.path.join(BASE_DIR, "data", "resume_dataset_1200.csv")
jd_path = os.path.join(BASE_DIR, "data", "job_descriptions.csv")

convert_dataset(resume_path)

# ------------------------------------------------
# RANKING
# ------------------------------------------------

st.header("📊 Candidate Ranking")

ranking_results = rank_candidates(resume_path, jd_path)
st.dataframe(pd.DataFrame(ranking_results), use_container_width=True)

candidate_ids = [c["candidate_id"] for c in ranking_results]
selected_candidate = st.selectbox("Select Candidate", candidate_ids)

# ------------------------------------------------
# VOICE INTERVIEW
# ------------------------------------------------

st.header("🎤 Voice Interview")

QUESTION_BANK = {
    "Python": {
        "OOP": {
            "question": "Explain OOP principles in Python.",
            "keywords": ["encapsulation", "inheritance", "polymorphism", "abstraction"]
        }
    },
    "SQL": {
        "Joins": {
            "question": "Explain INNER JOIN.",
            "keywords": ["matching", "two tables", "common"]
        }
    }
}

selected_subject = st.selectbox("Select Subject", list(QUESTION_BANK.keys()))
selected_subtopic = st.selectbox(
    "Select Subtopic",
    list(QUESTION_BANK[selected_subject].keys())
)

if st.button("Start Interview"):

    recognizer = sr.Recognizer()
    question_data = QUESTION_BANK[selected_subject][selected_subtopic]
    question = question_data["question"]
    keywords = question_data["keywords"]

    st.write(question)

    tts = gTTS(question)
    with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as tmp:
        tts.save(tmp.name)
        st.audio(open(tmp.name, "rb").read())

    time.sleep(5)

    try:
        with sr.Microphone(sample_rate=16000) as source:
            recognizer.adjust_for_ambient_noise(source, duration=1)
            audio = recognizer.listen(source, timeout=10, phrase_time_limit=15)

        answer_text = recognizer.recognize_google(audio, language="en-IN")
        st.write("Answer:", answer_text)

    except:
        st.error("Voice recognition failed.")
        st.stop()

    score = sum(1 for word in keywords if word.lower() in answer_text.lower())
    st.write(f"Interview Score: {score}/{len(keywords)}")

# ------------------------------------------------
# PIPELINE
# ------------------------------------------------

st.header("🔁 Pipeline")

manager = PipelineStateManager()
manager.initialize_candidate(selected_candidate)
manager.transition(selected_candidate, "shortlisted")
manager.transition(selected_candidate, "interviewed")

st.dataframe(pd.DataFrame(manager.export_history()), use_container_width=True)

# ------------------------------------------------
# DAILY SCHEDULING
# ------------------------------------------------

st.header("📅 Interview Scheduling")

scheduler = InterviewScheduler()

selected_date = st.date_input("Select Date")
start_time = st.time_input("Start Time")
end_time = st.time_input("End Time")

if st.button("Schedule Interview"):

    start_dt = datetime.combine(selected_date, start_time)
    end_dt = datetime.combine(selected_date, end_time)

    candidate_slots = [(start_dt, end_dt)]
    interviewer_slots = [(start_dt, end_dt)]

    success, result = scheduler.schedule(
        candidate_id=selected_candidate,
        interviewer_id="I1",
        candidate_slots=candidate_slots,
        interviewer_slots=interviewer_slots
    )

    st.dataframe(pd.DataFrame(scheduler.get_schedule_log()), use_container_width=True)

    if success:
        st.success("Interview Scheduled!")

        body = f"""
Dear {selected_candidate},

Your interview is scheduled on {selected_date}
from {start_time} to {end_time}.

Regards,
HR Team
"""
        send_email("saideekshitha2111@gmail.com", "Interview Scheduled", body)

# ------------------------------------------------
# LEAVE APPROVAL
# ------------------------------------------------

st.header("🏖 Leave Approval")

employee_leave_data = {
    "E1": {"casual": 5, "sick": 3, "earned": 10},
    "E2": {"casual": 2, "sick": 5, "earned": 8}
}

employee_emails = {
    "E1": "employee1@gmail.com",
    "E2": "employee2@gmail.com"
}

manager_email = "manager@gmail.com"

selected_employee = st.selectbox(
    "Select Employee",
    list(employee_leave_data.keys())
)

leave_type = st.selectbox("Leave Type", ["casual", "sick", "earned"])
start_date = st.date_input("Leave Start")
end_date = st.date_input("Leave End")

if st.button("Submit Leave"):

    leave_engine = LeavePolicyEngine(employee_leave_data, [])

    leave_decision = leave_engine.evaluate_request(
        employee_id=selected_employee,
        role="employee",
        leave_type=leave_type,
        start_date=str(start_date),
        end_date=str(end_date)
    )

    decision = leave_decision["decision"]
    st.write("Decision:", decision)

    # Employee Mail
    body_emp = f"""
Dear {selected_employee},

Your leave request from {start_date} to {end_date}
has been {decision.upper()}.

Regards,
HR Department
"""
    send_email(employee_emails[selected_employee],
               "Leave Request Update",
               body_emp)

    # Manager Mail
    body_mgr = f"""
Employee: {selected_employee}
Leave Type: {leave_type}
Dates: {start_date} to {end_date}
Decision: {decision.upper()}
"""
    send_email(manager_email,
               "Employee Leave Notification",
               body_mgr)

# ------------------------------------------------
# ESCALATION
# ------------------------------------------------

st.header("🚨 Escalation")

escalation_engine = EscalationEngine()

pipeline_check = escalation_engine.check_pipeline_case(
    manager.transition(selected_candidate, "shortlisted")
)

for key, value in {"pipeline": pipeline_check}.items():
    st.write(f"**{key.capitalize()}**")
    st.write("Escalate:", value.get("escalate", False))
    st.write("Reason:", value.get("reason", "No issue"))
    st.write("---")