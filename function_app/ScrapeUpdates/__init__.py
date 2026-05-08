import json
import logging

import azure.functions as func

from src.scraper import fetch_azure_updates, get_previous_week_range


def main(req: func.HttpRequest) -> func.HttpResponse:
    logging.info("ScrapeUpdates trigger started")

    try:
        start_date, end_date = get_previous_week_range()
        updates = fetch_azure_updates(start_date, end_date)

        payload = {
            "week_start": start_date.isoformat(),
            "week_end": end_date.isoformat(),
            "azure_updates": updates,
        }

        return func.HttpResponse(
            body=json.dumps(payload, indent=2, ensure_ascii=False),
            mimetype="application/json",
            status_code=200,
        )
    except Exception as exc:
        logging.exception("ScrapeUpdates failed")
        import traceback
        return func.HttpResponse(
            body=json.dumps({
                "error": str(exc),
                "type": type(exc).__name__,
                "traceback": traceback.format_exc()
            }),
            mimetype="application/json",
            status_code=500,
        )
