import json
from datetime import datetime


# ==============================
# STATE MACHINE CONFIGURATION
# ==============================

VALID_TRANSITIONS = {
    "applied": ["screening", "rejected"],
    "screening": ["interview", "rejected"],
    "interview": ["selected", "rejected"],
    "selected": ["offer", "rejected"],
    "offer": ["hired", "rejected"],
    "hired": [],
    "rejected": []
}


# ==============================
# HR AUTONOMOUS AGENT
# ==============================

class HRAgent:

    def __init__(self):
        self.logs = {
            "ranking_results": [],
            "scheduled_interviews": [],
            "leave_decisions": [],
            "state_logs": []
        }

    # --------------------------
    # Resume Parsing
    # --------------------------
    def parse_resume(self, resume_text):
        known_skills = ["Python", "SQL", "Django", "Machine Learning"]
        return [
            skill for skill in known_skills
            if skill.lower() in resume_text.lower()
        ]

    # --------------------------
    # Resume Ranking
    # --------------------------
    def rank_candidate(self, candidate, job_description):

        required = set(job_description.get("skills", []))
        candidate_skills = set(candidate.get("skills", []))

        if not required:
            score = 0
            matched = []
        else:
            matched = sorted(list(required & candidate_skills))
            score = (len(matched) / len(required)) * 100

        result = {
            "candidate_id": candidate["id"],
            "match_score": round(score, 2),
            "matched_skills": matched,
            "timestamp": str(datetime.now())
        }

        self.logs["ranking_results"].append(result)
        return result

    # --------------------------
    # Interview Generation
    # --------------------------
    def generate_interview_questions(self, candidate):

        questions = [
            f"Explain advanced concepts in {skill}."
            for skill in candidate.get("skills", [])
        ]

        questions.append("Describe a challenging project.")
        questions.append("How do you resolve conflicts?")

        return questions

    # --------------------------
    # Scheduling (UPDATED WITH DATE + TIME)
    # --------------------------
    def schedule_interview(self, candidate_id, available_slots, booked_slots):

        for slot in available_slots:
            if slot not in booked_slots:
                decision = {
                    "candidate_id": candidate_id,
                    "scheduled_slot": slot,  # Now includes date + time
                    "timestamp": str(datetime.now())
                }
                self.logs["scheduled_interviews"].append(decision)
                return decision

        return {"message": "No Available Slot"}

    # --------------------------
    # FSM State Management
    # --------------------------
    def update_candidate_state(self, candidate, new_state):

        current = candidate["state"]

        if new_state not in VALID_TRANSITIONS.get(current, []):
            raise ValueError("Invalid State Transition")

        candidate["state"] = new_state

        log = {
            "candidate_id": candidate["id"],
            "previous_state": current,
            "new_state": new_state,
            "timestamp": str(datetime.now()),
            "validated": True
        }

        self.logs["state_logs"].append(log)
        return True

    # --------------------------
    # Leave Management
    # --------------------------
    def dates_overlap(self, s1, e1, s2, e2):
        return s1 <= e2 and s2 <= e1

    def evaluate_leave_request(self, employee, leave_request, team_records):

        if employee["leave_balance"] < leave_request["days"]:
            return self._leave_decision(
                employee["id"], "REJECTED", "LP-01",
                "Insufficient Leave Balance"
            )

        if leave_request["leave_type"] not in employee["eligible_leave_types"]:
            return self._leave_decision(
                employee["id"], "REJECTED", "LP-02",
                "Leave Type Not Eligible"
            )

        for record in team_records:
            if self.dates_overlap(
                leave_request["start_date"],
                leave_request["end_date"],
                record["start_date"],
                record["end_date"]
            ):
                return self._leave_decision(
                    employee["id"], "REJECTED", "LP-03",
                    "Date Overlap Conflict"
                )

        return self._leave_decision(
            employee["id"], "APPROVED", "LP-VALID-01",
            "All Conditions Satisfied"
        )

    def _leave_decision(self, emp_id, decision, rule, reason):

        result = {
            "employee_id": emp_id,
            "decision_type": decision,
            "applied_policy_rule": rule,
            "reason": reason,
            "timestamp": str(datetime.now())
        }

        self.logs["leave_decisions"].append(result)
        return result

    # --------------------------
    # Query Escalation
    # --------------------------
    def escalate_query(self, text):
        keywords = ["legal", "harassment", "salary negotiation"]

        if any(word in text.lower() for word in keywords):
            return "ESCALATED TO HUMAN HR"

        return "AUTO-RESOLVED"

    # --------------------------
    # Export Results
    # --------------------------
    def export_results(self):
        return json.dumps(self.logs, indent=4)


# ==============================
# MAIN EXECUTION BLOCK
# ==============================

if __name__ == "__main__":

    agent = HRAgent()

    # Resume Parsing
    resume_text = "I have experience in Python, SQL, Django and Machine Learning."
    skills = agent.parse_resume(resume_text)

    candidate = {
        "id": 101,
        "skills": skills,
        "state": "applied"
    }

    job_description = {
        "skills": ["Python", "Machine Learning", "Django", "SQL"]
    }

    print("Ranking Result:")
    print(agent.rank_candidate(candidate, job_description))
    print()

    # State Transition
    agent.update_candidate_state(candidate, "screening")

    # UPDATED Scheduling with Date + Time
    available_slots = [
        "2026-03-05 10:00 AM",
        "2026-03-05 11:00 AM",
        "2026-03-05 02:00 PM"
    ]

    booked_slots = ["2026-03-05 10:00 AM"]

    print("Scheduling Result:")
    print(agent.schedule_interview(candidate["id"], available_slots, booked_slots))
    print()

    # Leave Evaluation
    employee = {
        "id": 501,
        "leave_balance": 10,
        "eligible_leave_types": ["sick", "casual"]
    }

    leave_request = {
        "days": 3,
        "leave_type": "sick",
        "start_date": 1,
        "end_date": 3
    }

    team_records = [
        {"start_date": 5, "end_date": 7}
    ]

    print("Leave Decision:")
    print(agent.evaluate_leave_request(employee, leave_request, team_records))
    print()

    print("Final Exported JSON:")
    print(agent.export_results())