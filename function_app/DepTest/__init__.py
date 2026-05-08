import azure.functions as func


def main(req: func.HttpRequest) -> func.HttpResponse:
    try:
        import requests
        import bs4
        import dateutil
        return func.HttpResponse(
            body="All imports successful: requests, bs4, dateutil",
            status_code=200,
        )
    except Exception as e:
        import traceback
        return func.HttpResponse(
            body=f"Error: {type(e).__name__}: {str(e)}\n\n{traceback.format_exc()}",
            status_code=500,
        )
