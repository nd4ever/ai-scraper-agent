import json
import logging

import azure.functions as func

from src.scraper import (
    fetch_azure_community_blog_headlines,
    fetch_azure_updates,
    fetch_azure_youtube_videos,
    fetch_techcommunity,
    get_previous_week_range,
)


def _to_bool(value: str, default: bool = False) -> bool:
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "y", "on"}


def main(req: func.HttpRequest) -> func.HttpResponse:
    logging.info("ScrapeHttp trigger started")

    try:
        save_output = _to_bool(req.params.get("save"), default=False)
        output_path = req.params.get("out") or "output.json"

        start_date, end_date = get_previous_week_range()
        payload = {
            "week_start": start_date.isoformat(),
            "week_end": end_date.isoformat(),
            "techcommunity": fetch_techcommunity(start_date, end_date),
            "azure_updates": fetch_azure_updates(start_date, end_date),
            "azure_community_blog_headlines": fetch_azure_community_blog_headlines(start_date, end_date),
            "azure_youtube_videos": fetch_azure_youtube_videos(start_date, end_date),
        }

        if save_output:
            Path(output_path).write_text(
                json.dumps(payload, indent=2, ensure_ascii=False),
                encoding="utf-8",
            )

        return func.HttpResponse(
            body=json.dumps(payload, indent=2, ensure_ascii=False),
            mimetype="application/json",
            status_code=200,
        )
    except Exception as exc:
        logging.exception("ScrapeHttp failed")
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
