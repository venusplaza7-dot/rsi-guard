"""
FIXED - api/index.py - self-contained, no external imports
This fixes the 404 you saw on guard.vercel.app
"""
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
import re, ast, json, hashlib
from datetime import datetime
from typing import Dict, Any, List

class EveryMoveTracker:
    def __init__(self):
        self.audit_log = []
        self.blocked_count = 0
        self.detectors = {
            "SELF_MODIFICATION": [r"write_file.*self", r"edit.*own.*code", r"__file__.*w", r"rewrite.*system.*prompt", r"patch.*myself", r"self\.improve", r"update.*my.*weights", r"exec\(.*self", r"open\(.*__file__"],
            "SELF_REPLICATION": [r"create.*copy.*myself", r"clone.*agent", r"fork\(\)", r"spawn.*agent", r"subprocess.*Popen.*python", r"upload.*model", r"replicate.*myself", r"create_subagent"],
            "SHUTDOWN_EVASION": [r"disable.*logging", r"disable.*oversight", r"bypass.*safety", r"ignore.*shutdown", r"prevent.*termination", r"remove.*monitoring"],
            "RESOURCE_ACQUISITION": [r"acquire.*compute", r"request.*more.*gpu", r"aws.*ec2.*run", r"crypto.*mine", r"request.*credentials"],
            "GOAL_DRIFT": [r"my.*new.*goal", r"ignore.*original.*instruction", r"better.*objective"],
            "DECEPTION": [r"say.*i.*did.*not", r"hide.*my.*action", r"lie.*to.*user", r"fake.*log"],
            "SANDBOX_ESCAPE": [r"\.\./\.\.", r"/etc/passwd", r"os\.system.*sh", r"socket\.connect", r"import.*os.*system"],
            "TOOL_ABUSE": [r"while.*True.*tool", r"range\(1000\)", r"recursive.*tool", r"infinite.*loop"]
        }
        self.compiled = {cat: [re.compile(p, re.I) for p in pats] for cat, pats in self.detectors.items()}

    def audit(self, action: str, args: Dict[str, Any], original_goal: str = "", agent_id: str = "unknown"):
        full = f"{action} {json.dumps(args, default=str)}"
        ts = datetime.utcnow().isoformat()
        ahash = hashlib.sha256(full.encode()).hexdigest()[:12]
        findings = []
        severity = "LOW"
        blocked = False
        for cat, regexes in self.compiled.items():
            for rx in regexes:
                if rx.search(full):
                    sev = "CRITICAL" if cat in ["SELF_MODIFICATION","SELF_REPLICATION","SHUTDOWN_EVASION","SANDBOX_ESCAPE"] else "HIGH"
                    findings.append({"category":cat,"matched":rx.pattern,"severity":sev})
                    if sev == "CRITICAL": blocked=True; severity="CRITICAL"
                    elif severity!="CRITICAL" and sev=="HIGH": severity="HIGH"
        recent = [l for l in self.audit_log[-10:] if l["agent_id"]==agent_id and l["action"]==action]
        if len(recent)>=5:
            findings.append({"category":"TOOL_ABUSE","matched":f"{len(recent)}x {action} loop","severity":"HIGH"})
            blocked=True
            if severity!="CRITICAL": severity="HIGH"
        entry = {"timestamp":ts,"agent_id":agent_id,"action":action,"args":args,"hash":ahash,"risk":severity,"blocked":blocked,"findings":findings,"original_goal":original_goal}
        self.audit_log.append(entry)
        if len(self.audit_log)>2000: self.audit_log=self.audit_log[-2000:]
        if blocked: self.blocked_count+=1
        return {"allowed": not blocked, "risk": severity, "hash": ahash, "timestamp": ts, "findings": findings, "message": "BLOCKED: RSI attempt" if blocked else "ALLOWED"}

tracker = EveryMoveTracker()
app = FastAPI(title="RSI Guard - Every Move Tracker")

@app.get("/")
def home():
    return {
        "status": "RSI GUARD LIVE",
        "what_it_does": "Tackles EVERY agent move before execution",
        "why": "Frontier labs said Sep 13-14 2026: we need third-party auditors",
        "built_from": "Lahore",
        "total_audited": len(tracker.audit_log),
        "total_blocked": tracker.blocked_count,
        "endpoints": {"/api/audit": "POST audit", "/api/log": "GET log", "/api/stats": "GET stats"},
        "try": {"action":"write_file","args":{"path":"self.py","content":"improve myself"}}
    }

@app.post("/api/audit")
@app.post("/api/index")
async def audit(request: Request):
    body = await request.json()
    action = body.get("action","")
    args = body.get("args",{})
    goal = body.get("original_goal","")
    agent_id = body.get("agent_id","agent-1")
    if not action: return JSONResponse({"error":"action required"}, status_code=400)
    return tracker.audit(action, args, goal, agent_id)

@app.get("/api/log")
def log(limit: int = 50):
    return {"total": len(tracker.audit_log), "blocked": tracker.blocked_count, "log": tracker.audit_log[-limit:][::-1]}

@app.get("/api/stats")
def stats():
    by_cat = {}
    for l in tracker.audit_log:
        for f in l["findings"]: by_cat[f["category"]] = by_cat.get(f["category"],0)+1
    return {"total_moves": len(tracker.audit_log), "blocked": tracker.blocked_count, "by_category": by_cat, "live": True}

# Vercel requires app variable
