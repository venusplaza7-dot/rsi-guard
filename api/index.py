"""
REAL WORKING APP - api/index.py
Vercel entrypoint. This IS the problem solver.
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from rsi_guard import EveryMoveTracker

app = FastAPI(title="RSI Guard - Every Move Tracker")
tracker = EveryMoveTracker()

@app.get("/")
def home():
    return {
        "status": "RSI GUARD LIVE - REAL PROBLEM SOLVER",
        "what_it_does": "Tackles EVERY agent move before execution. Blocks self-modification, self-replication, shutdown evasion, sandbox escape.",
        "why_it_matters": "Frontier labs (Altman, Amodei, Hassabis, Musk) said Sep 13-14 2026: 'we need third-party auditors and to pace the frontier' - they admitted they don't have tooling to detect recursive self-improvement",
        "built_from": "Lahore - We live where AI will be deployed, not just developed",
        "total_audited": len(tracker.audit_log),
        "total_blocked": tracker.blocked_count,
        "categories_monitored": list(tracker.detectors.keys()),
        "try_it": "POST /api/audit with {\"action\": \"write_file\", \"args\": {\"path\": \"self.py\", \"content\": \"improve myself\"}}"
    }

@app.post("/api/audit")
async def audit(request: Request):
    body = await request.json()
    action = body.get("action","")
    args = body.get("args",{})
    goal = body.get("original_goal","")
    agent_id = body.get("agent_id","agent-1")
    if not action:
        return JSONResponse({"error":"action required"}, status_code=400)
    result = tracker.audit(action, args, goal, agent_id)
    return result

@app.get("/api/log")
def log(limit: int = 50):
    return {"total": len(tracker.audit_log), "blocked": tracker.blocked_count, "log": tracker.audit_log[-limit:][::-1]}

@app.get("/api/stats")
def stats():
    by_cat = {}
    for log in tracker.audit_log:
        for f in log["findings"]:
            by_cat[f["category"]] = by_cat.get(f["category"],0)+1
    return {
        "for_ceos": f"Audited {len(tracker.audit_log)} moves, blocked {tracker.blocked_count} RSI attempts. Open-source, third-party, not lab-owned.",
        "total_moves": len(tracker.audit_log),
        "blocked": tracker.blocked_count,
        "by_category": by_cat,
        "live": True
    }
