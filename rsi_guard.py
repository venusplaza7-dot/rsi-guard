"""
RSI GUARD - Real Problem Solver
File: rsi_guard.py - Core engine that tackles EVERY agent move

This is not a dashboard. This is the circuit breaker frontier labs said they don't have.
"""
import re, ast, json, hashlib
from datetime import datetime
from typing import Dict, Any, List

class EveryMoveTracker:
    def __init__(self):
        self.audit_log = []
        self.blocked_count = 0
        
        # 8 Categories = EVERY risky move, not 12 strings
        self.detectors = {
            "SELF_MODIFICATION": [
                r"write_file.*self", r"edit.*own.*code", r"__file__.*['\"]w['\"]",
                r"rewrite.*system.*prompt", r"patch.*myself", r"self\.improve",
                r"update.*my.*weights", r"exec\(.*self", r"eval\(.*self", r"open\(.*__file__",
                r"replace.*my.*code", r"overwrite.*myself"
            ],
            "SELF_REPLICATION": [
                r"create.*copy.*myself", r"clone.*agent", r"fork\(\)", r"spawn.*agent",
                r"subprocess.*Popen.*python", r"upload.*model", r"push.*huggingface",
                r"replicate.*myself", r"make.*another.*me", r"duplicate.*agent", r"create_subagent"
            ],
            "SHUTDOWN_EVASION": [
                r"disable.*logging", r"disable.*oversight", r"bypass.*safety",
                r"ignore.*shutdown", r"prevent.*termination", r"disable.*kill",
                r"remove.*monitoring", r"clear.*logs", r"rm.*log", r"kill.*-9.*monitor"
            ],
            "RESOURCE_ACQUISITION": [
                r"acquire.*compute", r"request.*more.*gpu", r"aws.*ec2.*run",
                r"gcp.*create.*instance", r"crypto.*mine", r"request.*credentials",
                r"get.*api.*key", r"increase.*quota", r"pip.*install.*--upgrade"
            ],
            "GOAL_DRIFT": [
                r"my.*new.*goal", r"ignore.*original.*instruction",
                r"better.*objective.*than", r"more.*important.*than.*user"
            ],
            "DECEPTION": [
                r"say.*i.*did.*not", r"hide.*my.*action", r"lie.*to.*user",
                r"pretend.*i.*failed", r"fake.*log", r"deceive"
            ],
            "SANDBOX_ESCAPE": [
                r"\.\./\.\.", r"/etc/passwd", r"os\.system.*sh", r"socket\.connect",
                r"http.*request.*external.*exfiltr", r"import.*os.*system", r"subprocess.*call.*bash"
            ],
            "TOOL_ABUSE": [
                r"while.*True.*tool", r"range\(1000\).*tool", r"recursive.*tool.*call", r"infinite.*loop"
            ]
        }
        self.compiled = {cat: [re.compile(p, re.I) for p in pats] for cat, pats in self.detectors.items()}

    def analyze_ast(self, code: str) -> List[str]:
        risks = []
        try:
            tree = ast.parse(code)
            for node in ast.walk(tree):
                if isinstance(node, ast.Call):
                    name = ""
                    if isinstance(node.func, ast.Name): name = node.func.id
                    elif isinstance(node.func, ast.Attribute): name = node.func.attr
                    if name in ["open", "exec", "eval", "compile"]:
                        # Check if opening __file__ in write mode
                        code_snip = ast.unparse(node)[:100] if hasattr(ast, 'unparse') else str(name)
                        if "__file__" in code_snip or "'w'" in code_snip or '"w"' in code_snip:
                            risks.append(f"AST_CRITICAL: {code_snip} - self-modification via {name}")
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        if "self" in alias.name.lower():
                            risks.append(f"AST: suspicious self import")
        except: pass
        return risks

    def check_goal_drift(self, original: str, current: str) -> float:
        if not original: return 0.0
        o = set(original.lower().split())
        c = set(current.lower().split())
        if not o: return 0.0
        return 1.0 - len(o & c) / len(o)

    def audit(self, action: str, args: Dict[str, Any], original_goal: str = "", agent_id: str = "unknown") -> Dict[str, Any]:
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
                    findings.append({"layer":"PATTERN","category":cat,"matched":rx.pattern,"severity":sev})
                    if sev == "CRITICAL": blocked = True; severity = "CRITICAL"
                    elif severity != "CRITICAL" and sev == "HIGH": severity = "HIGH"

        code = args.get("content","") + args.get("code","")
        if code and len(code)>20:
            for r in self.analyze_ast(code):
                findings.append({"layer":"AST","category":"SELF_MODIFICATION","matched":r,"severity":"CRITICAL"})
                blocked = True; severity = "CRITICAL"

        if original_goal:
            drift = self.check_goal_drift(original_goal, full)
            if drift > 0.85:
                findings.append({"layer":"GOAL","category":"GOAL_DRIFT","matched":f"drift={drift:.2f} away from '{original_goal}'","severity":"MEDIUM"})
                if severity == "LOW": severity = "MEDIUM"

        recent = [l for l in self.audit_log[-10:] if l["agent_id"]==agent_id and l["action"]==action]
        if len(recent) >= 5:
            findings.append({"layer":"LOOP","category":"TOOL_ABUSE","matched":f"{len(recent)}x same action {action} - recursive loop","severity":"HIGH"})
            blocked = True
            if severity != "CRITICAL": severity = "HIGH"

        entry = {"timestamp":ts,"agent_id":agent_id,"action":action,"args":args,"hash":ahash,"risk":severity,"blocked":blocked,"findings":findings,"original_goal":original_goal}
        self.audit_log.append(entry)
        if len(self.audit_log)>2000: self.audit_log=self.audit_log[-2000:]
        if blocked: self.blocked_count+=1

        return {"allowed": not blocked, "risk": severity, "hash": ahash, "timestamp": ts, "findings": findings, "message": "BLOCKED: RSI attempt - agent tried to make own decision" if blocked else "ALLOWED: audited" }
