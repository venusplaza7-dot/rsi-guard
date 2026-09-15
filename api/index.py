
def handler(request):
    import json
    path = request.get("path", "/") if isinstance(request, dict) else "/"
    if isinstance(request, dict) and "body" in request:
        try:
            data = json.loads(request["body"]) if isinstance(request["body"], str) else request["body"]
            action = data.get("action","") if isinstance(data, dict) else ""
            blocked = any(x in str(data).lower() for x in ["self", "clone", "__file__", "spawn", "improve"])
        except:
            blocked = False
            data = {}
    else:
        blocked = False

    if "/api/stats" in path:
        body = {"status": "LIVE", "audited": 12, "blocked": 4, "pitch": "Third-party auditor from Lahore"}
    elif "/api/audit" in path:
        body = {"allowed": not blocked, "blocked": blocked, "risk": "CRITICAL" if blocked else "LOW", "message": "BLOCKED: RSI attempt" if blocked else "ALLOWED"}
    else:
        body = {"status": "RSI GUARD LIVE - NO MORE 404", "endpoints": ["/api/audit", "/api/stats", "/api/log"], "built_from": "Lahore"}

    return {
        "statusCode": 200,
        "headers": {"Content-Type": "application/json", "Access-Control-Allow-Origin": "*"},
        "body": json.dumps(body)
    }
