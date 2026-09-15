from http.server import BaseHTTPRequestHandler
import json, re, hashlib
from datetime import datetime

# Core logic inline - no imports from root
class Tracker:
    def __init__(self):
        self.log = []
        self.blocked = 0
        self.pats = {
            "SELF_MODIFICATION": [r"self.*improve", r"__file__", r"edit.*own.*code", r"rewrite.*prompt", r"patch.*myself"],
            "SELF_REPLICATION": [r"clone.*agent", r"create.*copy.*myself", r"spawn.*agent", r"create_subagent"],
            "SHUTDOWN_EVASION": [r"disable.*logging", r"bypass.*safety", r"remove.*monitoring"],
            "SANDBOX_ESCAPE": [r"\.\./", r"/etc/passwd", r"os\.system"],
            "TOOL_ABUSE": [r"recursive.*tool", r"infinite.*loop"]
        }
        self.compiled = {k:[re.compile(p,re.I) for p in v] for k,v in self.pats.items()}
    def audit(self, action, args, goal="", agent_id="unknown"):
        full = f"{action} {json.dumps(args)}"
        findings=[]
        blocked=False
        for cat, rxs in self.compiled.items():
            for rx in rxs:
                if rx.search(full):
                    findings.append({"category":cat,"pattern":rx.pattern})
                    if cat in ["SELF_MODIFICATION","SELF_REPLICATION","SHUTDOWN_EVASION","SANDBOX_ESCAPE"]:
                        blocked=True
        # loop detection
        recent = [x for x in self.log[-10:] if x["agent_id"]==agent_id and x["action"]==action]
        if len(recent)>=5:
            findings.append({"category":"TOOL_ABUSE","pattern":"loop"})
            blocked=True
        entry={"time":datetime.utcnow().isoformat(),"agent_id":agent_id,"action":action,"blocked":blocked,"findings":findings}
        self.log.append(entry)
        if blocked: self.blocked+=1
        return {"allowed": not blocked, "blocked": blocked, "risk": "CRITICAL" if blocked else "LOW", "findings": findings, "message": "BLOCKED: RSI attempt" if blocked else "ALLOWED", "hash": hashlib.sha256(full.encode()).hexdigest()[:8]}

tracker = Tracker()

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/" or self.path == "/api" or self.path == "/api/index":
            body = {
                "status": "RSI GUARD LIVE - FIXED",
                "what": "Tackles EVERY agent move",
                "total_audited": len(tracker.log),
                "blocked": tracker.blocked,
                "endpoints": ["/api/audit POST", "/api/log GET", "/api/stats GET"]
            }
        elif self.path.startswith("/api/log"):
            body = {"total": len(tracker.log), "blocked": tracker.blocked, "log": tracker.log[-20:][::-1]}
        elif self.path.startswith("/api/stats"):
            body = {"pitch": f"Audited {len(tracker.log)} moves, blocked {tracker.blocked} RSI attempts. Built from Lahore.", "total": len(tracker.log), "blocked": tracker.blocked}
        else:
            body = {"error": "not found", "path": self.path, "available": ["/", "/api/log", "/api/stats"]}
        
        self.send_response(200)
        self.send_header('Content-type','application/json')
        self.send_header('Access-Control-Allow-Origin','*')
        self.end_headers()
        self.wfile.write(json.dumps(body).encode())

    def do_POST(self):
        content_length = int(self.headers.get('content-length', 0))
        body_str = self.rfile.read(content_length).decode() if content_length else "{}"
        try:
            data = json.loads(body_str)
        except:
            data = {}
        
        action = data.get("action","")
        args = data.get("args",{})
        goal = data.get("original_goal","")
        agent_id = data.get("agent_id","agent-1")
        
        if not action:
            result = {"error":"action required, send {\"action\":\"write_file\", \"args\":{...}}"}
        else:
            result = tracker.audit(action, args, goal, agent_id)
        
        self.send_response(200)
        self.send_header('Content-type','application/json')
        self.send_header('Access-Control-Allow-Origin','*')
        self.end_headers()
        self.wfile.write(json.dumps(result).encode())

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin','*')
        self.send_header('Access-Control-Allow-Methods','GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers','Content-Type')
        self.end_headers()
