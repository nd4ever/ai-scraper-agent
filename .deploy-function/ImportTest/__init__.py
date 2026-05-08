import azure.functions as func


def main(req: func.HttpRequest) -> func.HttpResponse:
    try:
        from src.scraper import get_previous_week_range
        result = get_previous_week_range()
        return func.HttpResponse(
            body=f"Success: {result}",
            status_code=200,
        )
    except Exception as e:
        import traceback
        return func.HttpResponse(
            body=f"Error: {type(e).__name__}: {str(e)}\n\n{traceback.format_exc()}",
            status_code=500,
        )
