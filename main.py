import os
from datetime import datetime

from resume_engine.ranker import rank_candidates
from pipeline.state_manager import PipelineStateManager
from interview.question_generator import InterviewQuestionGenerator
from scheduling.scheduler import InterviewScheduler
from leave.policy_engine import LeavePolicyEngine
from escalation.escalation_checker import EscalationEngine
from export.expoter import ResultsExporter


BASE_DIR = os.path.dirname(os.path.abspath(__file__))

resume_path = os.path.join(BASE_DIR, "data", "resumes.csv")
jd_path = os.path.join(BASE_DIR, "data", "job_descriptions.csv")

# ---------- Resume Ranking ----------
ranking_results = rank_candidates(resume_path, jd_path)

# ---------- Pipeline ----------
manager = PipelineStateManager()
manager.initialize_candidate("C1")
manager.transition("C1", "shortlisted")
manager.transition("C1", "interviewed")
pipeline_history = manager.export_history()

# ---------- Interview Questions ----------
generator = InterviewQuestionGenerator()
top_candidate = ranking_results[0]
interview_questions = generator.generate(
    candidate_id=top_candidate["candidate_id"],
    skills=top_candidate["skills"],
    jd_text="Python developer with ML"
)

# ---------- Scheduling ----------
scheduler = InterviewScheduler()

candidate_slots = [
    (datetime(2026, 3, 1, 10, 0), datetime(2026, 3, 1, 12, 0))
]

interviewer_slots = [
    (datetime(2026, 3, 1, 11, 0), datetime(2026, 3, 1, 15, 0))
]

success, schedule_result = scheduler.schedule(
    candidate_id="C1",
    interviewer_id="I1",
    candidate_slots=candidate_slots,
    interviewer_slots=interviewer_slots
)

schedule_log = scheduler.get_schedule_log()

# ---------- Leave Policy ----------
leave_balances = {
    "E1": {"casual": 5, "sick": 3, "earned": 10}
}

existing_leaves = [
    {"employee_id": "E2", "start": "2026-03-02", "end": "2026-03-04"}
]

leave_engine = LeavePolicyEngine(leave_balances, existing_leaves)

leave_decision = leave_engine.evaluate_request(
    employee_id="E1",
    role="employee",
    leave_type="casual",
    start_date="2026-03-05",
    end_date="2026-03-06"
)

# ---------- Escalation ----------
escalation_engine = EscalationEngine()

escalation_results = {
    "pipeline": escalation_engine.check_pipeline_case(
        manager.transition("C1", "shortlisted")
    ),
    "leave": escalation_engine.check_leave_case(leave_decision),
    "scheduling": escalation_engine.check_scheduling_case(
        (success, schedule_result)
    )
}

# ---------- Export ----------
exporter = ResultsExporter(
    ranking_results,
    interview_questions,
    schedule_log,
    pipeline_history,
    leave_decision,
    escalation_results
)

final_output = exporter.export_results()

print("\nFINAL EXPORTED RESULTS:")
print(final_output)