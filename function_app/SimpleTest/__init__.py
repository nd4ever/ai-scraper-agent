import azure.functions as func


def main(req: func.HttpRequest) -> func.HttpResponse:
    return func.HttpResponse(
        body="Hello from SimpleTest",
        status_code=200,
    )
