"""5-Tier Autonomous Learning Memory and Procedure Improvement Engine."""
from __future__ import annotations
import uuid
import json
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
from backend.app.database.session import SessionLocal
from backend.app.models.entities import (
    Instruction, Demonstration, Lesson, MemoryRecord, 
    ResearchProcedure, ResearchProcedureVersion, ImprovementProposal
)

class AutonomousMemorySystem:
    def __init__(self):
        from backend.app.database.session import init_db
        init_db()
        self._ensure_default_instructions()
        self._ensure_default_procedure()

    def _ensure_default_instructions(self):
        db = SessionLocal()
        try:
            count = db.query(Instruction).count()
            if count == 0:
                defaults = [
                    ("Never treat backtest returns as proof of future profitability.", "SAFETY"),
                    ("Never execute arbitrary AI-generated code; all strategies must adhere to allowlisted declarative DSL schemas.", "SAFETY"),
                    ("Autonomous loop operates in DEMO or RESEARCH_ONLY modes; live execution requires explicit owner opt-in, verification, and separate auth.", "RISK"),
                    ("Never bypass deterministic risk gates or alter safety thresholds autonomously.", "RISK"),
                    ("A signal generated from bar t must only be applied at bar t+1 to eliminate look-ahead bias.", "RESEARCH"),
                    ("Reject or revise strategies failing walk-forward or transaction-cost stress tests; do not repeatedly optimize against the same holdout sample.", "RESEARCH"),
                    ("Do not accept a strategy candidate based solely on its raw total return.", "GENERAL")
                ]
                for text, cat in defaults:
                    db.add(Instruction(instruction=text, category=cat, active=True))
                db.commit()
        finally:
            db.close()

    def _ensure_default_procedure(self):
        db = SessionLocal()
        try:
            proc = db.query(ResearchProcedure).filter_by(id="PROC-STANDARD-01").first()
            if not proc:
                proc = ResearchProcedure(
                    id="PROC-STANDARD-01",
                    name="Standard Quantitative Research Procedure v1",
                    description="Baseline multi-stage research and validation workflow.",
                    active_version_id="VER-1"
                )
                db.add(proc)
                ver = ResearchProcedureVersion(
                    id="VER-1",
                    procedure_id="PROC-STANDARD-01",
                    version_number=1,
                    definition_json={
                        "train_ratio": 0.50,
                        "validation_ratio": 0.25,
                        "out_of_sample_ratio": 0.25,
                        "walk_forward_windows": 3,
                        "min_trades_required": 5,
                        "max_drawdown_tolerance": 0.18,
                        "stress_test_multiplier": 2.0
                    },
                    change_rationale="Initial baseline quantitative research procedure.",
                    promoted=True
                )
                db.add(ver)
                db.commit()
        finally:
            db.close()

    # Tier 1: Instruction Memory
    def get_instructions(self) -> List[Dict[str, Any]]:
        db = SessionLocal()
        try:
            items = db.query(Instruction).filter_by(active=True).all()
            return [{"id": i.id, "instruction": i.instruction, "category": i.category, "created_at": i.created_at.isoformat()} for i in items]
        finally:
            db.close()

    def add_instruction(self, text: str, category: str = "GENERAL") -> Dict[str, Any]:
        db = SessionLocal()
        try:
            item = Instruction(instruction=text, category=category, active=True)
            db.add(item)
            db.commit()
            return {"id": item.id, "instruction": item.instruction, "category": item.category}
        finally:
            db.close()

    # Tier 2: Demonstration Memory
    def get_demonstrations(self) -> List[Dict[str, Any]]:
        db = SessionLocal()
        try:
            items = db.query(Demonstration).all()
            return [{
                "id": d.id,
                "title": d.title,
                "input_context": d.input_context,
                "example_decision": d.example_decision,
                "explanation": d.explanation,
                "feedback_label": d.feedback_label,
                "created_at": d.created_at.isoformat()
            } for d in items]
        finally:
            db.close()

    def add_demonstration(self, title: str, example_decision: str, explanation: str = "", feedback_label: str = "DESIRABLE") -> Dict[str, Any]:
        db = SessionLocal()
        try:
            demo = Demonstration(
                title=title,
                example_decision=example_decision,
                explanation=explanation,
                feedback_label=feedback_label
            )
            db.add(demo)
            db.commit()
            return {"id": demo.id, "title": demo.title, "feedback_label": demo.feedback_label}
        finally:
            db.close()

    # Tier 3: Experience Memory (Lessons)
    def record_lesson(
        self,
        observation: str,
        evidence: str,
        source_experiment_id: Optional[str] = None,
        confidence: float = 0.85,
        applicable_conditions: str = "XAUUSD M15"
    ) -> str:
        db = SessionLocal()
        try:
            lesson_id = f"LES-{uuid.uuid4().hex[:8].upper()}"
            lesson = Lesson(
                id=lesson_id,
                source_experiment_id=source_experiment_id,
                observation=observation,
                evidence=evidence,
                confidence=confidence,
                applicable_conditions=applicable_conditions,
                verification_status="UNVERIFIED"
            )
            db.add(lesson)
            db.commit()
            return lesson_id
        finally:
            db.close()

    def get_lessons(self, limit: int = 50) -> List[Dict[str, Any]]:
        db = SessionLocal()
        try:
            lessons = db.query(Lesson).order_by(Lesson.created_at.desc()).limit(limit).all()
            return [{
                "lesson_id": l.id,
                "source_experiment_id": l.source_experiment_id,
                "observation": l.observation,
                "evidence": l.evidence,
                "confidence": l.confidence,
                "applicable_conditions": l.applicable_conditions,
                "verification_status": l.verification_status,
                "owner_feedback": l.owner_feedback,
                "owner_notes": l.owner_notes,
                "created_at": l.created_at.isoformat()
            } for l in lessons]
        finally:
            db.close()

    def apply_owner_feedback(self, lesson_id: str, feedback: str, notes: Optional[str] = None) -> bool:
        db = SessionLocal()
        try:
            lesson = db.query(Lesson).filter_by(id=lesson_id).first()
            if not lesson:
                return False
            lesson.owner_feedback = feedback
            if notes:
                lesson.owner_notes = notes
            if feedback in {"GOOD_RESEARCH", "USEFUL_FINDING"}:
                lesson.verification_status = "VERIFIED"
                lesson.confidence = min(0.98, lesson.confidence + 0.1)
            elif feedback in {"INVALID_CONCLUSION", "OVERFITTED", "POOR_DESIGN"}:
                lesson.verification_status = "REFUTED"
                lesson.confidence = max(0.1, lesson.confidence - 0.4)
            db.commit()
            return True
        finally:
            db.close()

    # Tier 4: Verified Knowledge Memory
    def store_verified_knowledge(self, key: str, knowledge_data: Dict[str, Any], confidence: float = 0.95) -> str:
        db = SessionLocal()
        try:
            record_id = f"KNOW-{uuid.uuid4().hex[:8].upper()}"
            rec = MemoryRecord(
                id=record_id,
                category="VERIFIED_KNOWLEDGE",
                key=key,
                value_json=knowledge_data,
                confidence=confidence
            )
            db.add(rec)
            db.commit()
            return record_id
        finally:
            db.close()

    def get_verified_knowledge(self) -> List[Dict[str, Any]]:
        db = SessionLocal()
        try:
            recs = db.query(MemoryRecord).filter_by(category="VERIFIED_KNOWLEDGE").all()
            return [{"id": r.id, "key": r.key, "data": r.value_json, "confidence": r.confidence, "created_at": r.created_at.isoformat()} for r in recs]
        finally:
            db.close()

    # Tier 5: Research-Improvement Memory
    def propose_procedure_improvement(self, target_component: str, change_desc: str, rationale: str) -> Dict[str, Any]:
        db = SessionLocal()
        try:
            prop_id = f"PROP-{uuid.uuid4().hex[:8].upper()}"
            prop = ImprovementProposal(
                id=prop_id,
                target_component=target_component,
                proposed_change=change_desc,
                rationale=rationale,
                status="PROPOSED"
            )
            db.add(prop)
            db.commit()
            return {"id": prop.id, "status": prop.status, "change": change_desc}
        finally:
            db.close()

    def get_improvement_proposals(self) -> List[Dict[str, Any]]:
        db = SessionLocal()
        try:
            props = db.query(ImprovementProposal).order_by(ImprovementProposal.created_at.desc()).all()
            return [{
                "id": p.id,
                "target_component": p.target_component,
                "proposed_change": p.proposed_change,
                "rationale": p.rationale,
                "status": p.status,
                "created_at": p.created_at.isoformat()
            } for p in props]
        finally:
            db.close()
