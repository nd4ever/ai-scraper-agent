import azure.functions as func
import json
import sys
import os

def main(req: func.HttpRequest) -> func.HttpResponse:
    try:
        root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        sys_path = sys.path.copy()
        
        return func.HttpResponse(
            body=json.dumps({
                "status": "health_ok",
                "root_dir": root_dir,
                "python_version": sys.version,
                "sys.path_count": len(sys_path),
                "cwd": os.getcwd(),
                "env_keys": list(os.environ.keys())[:5]
            }, indent=2),
            mimetype="application/json",
            status_code=200,
        )
    except Exception as exc:
        return func.HttpResponse(
            body=json.dumps({"error": str(exc), "type": type(exc).__name__}),
            mimetype="application/json",
            status_code=500,
        )
