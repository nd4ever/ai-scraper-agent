import argparse
import json
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from src.scraper import (
    fetch_azure_community_blog_headlines,
    fetch_azure_updates,
    fetch_azure_youtube_videos,
    fetch_techcommunity,
)
from src.scraper import get_current_month_to_date_range, get_previous_week_range


def refresh_output(output_path: str) -> dict:
    week_start_date, week_end_date = get_previous_week_range()
    month_start_date, month_end_date = get_current_month_to_date_range()

    tech = fetch_techcommunity(week_start_date, week_end_date)
    updates = fetch_azure_updates(week_start_date, week_end_date)
    azure_blog_headlines = fetch_azure_community_blog_headlines(week_start_date, week_end_date)
    azure_youtube_videos = fetch_azure_youtube_videos(week_start_date, week_end_date)

    tech_month = fetch_techcommunity(month_start_date, month_end_date)
    updates_month = fetch_azure_updates(month_start_date, month_end_date)
    azure_blog_headlines_month = fetch_azure_community_blog_headlines(month_start_date, month_end_date)
    azure_youtube_videos_month = fetch_azure_youtube_videos(month_start_date, month_end_date)

    payload = {
        "week_start": week_start_date.isoformat(),
        "week_end": week_end_date.isoformat(),
        "techcommunity": tech,
        "azure_updates": updates,
        "azure_community_blog_headlines": azure_blog_headlines,
        "azure_youtube_videos": azure_youtube_videos,
        "month_start": month_start_date.isoformat(),
        "month_end": month_end_date.isoformat(),
        "techcommunity_month": tech_month,
        "azure_updates_month": updates_month,
        "azure_community_blog_headlines_month": azure_blog_headlines_month,
        "azure_youtube_videos_month": azure_youtube_videos_month,
    }

    Path(output_path).write_text(
        json.dumps(payload, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    return payload


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Refresh output.json and serve the local web page."
    )
    parser.add_argument("--out", type=str, default="output.json", help="Output JSON path")
    parser.add_argument("--port", type=int, default=8000, help="HTTP server port")
    parser.add_argument("--bind", type=str, default="127.0.0.1", help="Address to bind")
    args = parser.parse_args()

    start_date, end_date = get_previous_week_range()
    month_start, month_end = get_current_month_to_date_range()
    print(
        f"Refreshing weekly data for {start_date} to {end_date} "
        f"and monthly data for {month_start} to {month_end}..."
    )
    payload = refresh_output(args.out)
    print(
        "Wrote "
        f"{len(payload['techcommunity'])} techcommunity items and "
        f"{len(payload['azure_updates'])} azure updates and "
        f"{len(payload['azure_community_blog_headlines'])} azure community blog headlines and "
        f"{len(payload['azure_youtube_videos'])} Azure YouTube videos "
        f"for previous week, plus "
        f"{len(payload['techcommunity_month'])} techcommunity items, "
        f"{len(payload['azure_updates_month'])} azure updates, "
        f"{len(payload['azure_community_blog_headlines_month'])} azure community blog headlines, and "
        f"{len(payload['azure_youtube_videos_month'])} Azure YouTube videos "
        f"for current month to date "
        f"to {args.out}"
    )

    server = ThreadingHTTPServer((args.bind, args.port), SimpleHTTPRequestHandler)
    print(f"Serving http://{args.bind}:{args.port}/")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopping server...")
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
