import os
import pandas as pd
from datetime import datetime

print("🚀 MAIN1 FILE EXECUTING...")

from resume_engine.ranker import rank_candidates
from pipeline.state_manager import PipelineStateManager
from interview.question_generator import InterviewQuestionGenerator
from scheduling.scheduler import InterviewScheduler
from leave.policy_engine import LeavePolicyEngine
from escalation.escalation_checker import EscalationEngine
from export.expoter import ResultsExporter


def convert_dataset_to_resume_format(file_path):
    """
    Converts structured dataset into required format:
    candidate_id, resume_text
    WITHOUT changing ranking engine.
    """

    df = pd.read_csv(file_path)

    print("Original Columns:", df.columns.tolist())

    # Create candidate_id
    df["candidate_id"] = ["C" + str(i + 1) for i in range(len(df))]

    # Create resume_text from available fields
    df["resume_text"] = (
        df["Skills"].astype(str) + " " +
        df["Education_Level"].astype(str) + " " +
        df["Experience_Years"].astype(str) + " years experience " +
        df["Certifications"].astype(str) + " " +
        df["Field_of_Study"].astype(str)
    )

    # Keep only required columns
    df = df[["candidate_id", "resume_text"]]

    # Overwrite same file
    df.to_csv(file_path, index=False)

    print("✅ Dataset converted successfully.\n")


def main():

    BASE_DIR = os.path.dirname(os.path.abspath(__file__))

    resume_path = os.path.join(BASE_DIR, "data", "resume_dataset_1200.csv")
    jd_path = os.path.join(BASE_DIR, "data", "job_descriptions.csv")

    # 🔥 Convert dataset before ranking
    convert_dataset_to_resume_format(resume_path)

    # ---------- Resume Ranking ----------
    print("Step 1: Ranking Candidates...")
    ranking_results = rank_candidates(resume_path, jd_path)

    # ---------- Pipeline ----------
    print("Step 2: Managing Pipeline...")
    manager = PipelineStateManager()
    manager.initialize_candidate("C1")
    manager.transition("C1", "shortlisted")
    manager.transition("C1", "interviewed")
    pipeline_history = manager.export_history()

    # ---------- Interview Generator ----------
    generator = InterviewQuestionGenerator()
    top_candidate = ranking_results[0]

    # ---------- Static Questions ----------
    print("\nStep 3: Static Interview Questions")
    interview_questions = generator.generate(
        candidate_id=top_candidate["candidate_id"],
        skills=top_candidate["skills"],
        jd_text="Python developer with ML"
    )
    print(interview_questions)

    # ---------- Dynamic Skill ----------
    print("\nStep 4: Dynamic Single Skill Generation")
    user_skill = input("Enter any skill: ")

    additional_questions = generator.generate(
        candidate_id=top_candidate["candidate_id"],
        skills=top_candidate["skills"],
        jd_text=user_skill
    )

    print("\nGenerated Questions:")
    print(additional_questions)

    # ---------- Structured Topic ----------
    print("\nStep 5: Structured Topic Selection")

    concept_map = {
        "python": ["OOP", "Decorators", "Generators", "Exception Handling"],
        "java": ["OOP", "JVM Architecture", "Collections Framework"],
        "machine learning": ["Supervised Learning", "Linear Regression", "Random Forest"],
        "artificial intelligence": ["Neural Networks", "Deep Learning"],
        "data structures and algorithms": ["Arrays", "Linked List", "Trees", "Dynamic Programming"]
    }

    print("\nAvailable Main Concepts:")
    for concept in concept_map.keys():
        print("-", concept.title())

    selected_main = input("\nEnter main concept name: ").strip().lower()

    if selected_main in concept_map:
        subtopics = concept_map[selected_main]

        print("\nAvailable Subtopics:")
        for topic in subtopics:
            print("-", topic)

        selected_topic = input("\nEnter subtopic exactly as shown: ").strip()

        if selected_topic in subtopics:
            print(f"\nGenerating questions for {selected_topic}...\n")

            structured_questions = generator.generate(
                candidate_id=top_candidate["candidate_id"],
                skills=top_candidate["skills"],
                jd_text=selected_topic
            )

            print(structured_questions)
        else:
            print("Invalid subtopic selected.")
    else:
        print("Invalid main concept selected.")

    # ---------- Scheduling ----------
    print("\nStep 6: Scheduling Interview...")
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
    print("\nStep 7: Leave Evaluation...")
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
    print("\nStep 8: Escalation Check...")
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
    print("\nStep 9: Exporting Results...")
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


if __name__ == "__main__":
    main()