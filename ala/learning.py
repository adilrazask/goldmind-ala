"""Experience-based task selection and improvement tracking (not model-weight training)."""
from __future__ import annotations
import json
from collections import defaultdict
from .memory import MemoryStore
from .strategy_lab import generate_candidates

def choose_next_candidate(memory: MemoryStore) -> dict:
    history=memory.candidate_history(500)
    tried=set()
    family_stats=defaultdict(lambda:{"n":0,"mean_score":0.0,"passed":0})
    for item in history:
        spec=item.get("spec_json") or {}; key=json.dumps(spec,sort_keys=True); tried.add(key)
        stat=family_stats[item["family"]]; stat["n"]+=1
        if item.get("score") is not None: stat["mean_score"]+=float(item["score"])
        if item["status"]=="CANDIDATE_FOR_FURTHER_VALIDATION": stat["passed"]+=1
    for fam,st in family_stats.items():
        if st["n"]: st["mean_score"]/=st["n"]
    remaining=[c for c in generate_candidates() if json.dumps(c,sort_keys=True) not in tried]
    if not remaining:
        # Revisit only when all candidate specs were tried; keep explicit record that this is a repeat.
        remaining=generate_candidates()
    # Prefer under-explored families first; after minimum exploration, use measured mean score as tie-breaker.
    remaining.sort(key=lambda c:(family_stats[c["family"]]["n"], -family_stats[c["family"]]["mean_score"], c["family"], json.dumps(c,sort_keys=True)))
    return remaining[0]

def record_experience(memory: MemoryStore, report) -> None:
    result=report.to_dict()
    memory.save_candidate(report.candidate_id,report.family,report.parameters,report.decision,report.score,result)
    lesson=report.lesson
    memory.add_example(f"Experiment {report.family} {report.candidate_id[:8]}", lesson)
    state={"last_family":report.family,"last_decision":report.decision,"last_score":report.score,"last_lesson":lesson}
    memory.set_state("latest_learning_state",json.dumps(state))
