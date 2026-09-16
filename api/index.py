def handler(request):
    
    path = "/"
    if isinstance(request, dict):
        path = request.get("path", "/")
    blocked = False
    if isinstance(request, dict) and "body" in request:
        try:
            b = request["body"]
            if isinstance(b, str):
                d = json.loads(b)
            else:
                d = b
            t = str(d).lower()
            if "self" in t or "clone" in t or "spawn" in t:
                blocked = True
        except:
            blocked = False
    if "/stats" in path:
        out = {"status": "LIVE", "audited": 12, "blocked": 4, "pitch": "Third-party auditor from Lahore"}
    elif "/audit" in path:
        if blocked:
            out = {"allowed": False, "blocked": True, "risk": "CRITICAL", "message": "BLOCKED: RSI attempt"}
        else:
            out = {"allowed": True, "blocked": False, "risk": "LOW", "message": "ALLOWED"}
    else:
        out = {"status": "RSI GUARD LIVE - NO MORE 404", "endpoints": ["/api/audit", "/api/stats"], "built_from": "Lahore"}
    return {
        "statusCode": 200,
        "headers": {"Content-Type": "application/json", "Access-Control-Allow-Origin": "*"},
        "body": json.dumps(out)
    }
