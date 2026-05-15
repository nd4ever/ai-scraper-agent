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
from src.scraper import get_previous_week_range


def refresh_output(output_path: str) -> dict:
    start_date, end_date = get_previous_week_range()
    tech = fetch_techcommunity(start_date, end_date)
    updates = fetch_azure_updates(start_date, end_date)
    azure_blog_headlines = fetch_azure_community_blog_headlines(start_date, end_date)
    azure_youtube_videos = fetch_azure_youtube_videos(start_date, end_date)

    payload = {
        "week_start": start_date.isoformat(),
        "week_end": end_date.isoformat(),
        "techcommunity": tech,
        "azure_updates": updates,
        "azure_community_blog_headlines": azure_blog_headlines,
        "azure_youtube_videos": azure_youtube_videos,
    }

    Path(output_path).write_text(
        json.dumps(payload, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    return payload


class UnifiedHandler(SimpleHTTPRequestHandler):
    """Unified handler that serves tabbed interface or static files."""
    
    def do_GET(self):
        # Route root path to the tabbed interface
        if self.path in {'/', ''}:
            self.path = '/index.html'
        return super().do_GET()


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Refresh output.json and serve unified tabbed web dashboard."
    )
    parser.add_argument("--out", type=str, default="output.json", help="Output JSON path")
    parser.add_argument("--port", type=int, default=8000, help="HTTP server port")
    parser.add_argument("--bind", type=str, default="127.0.0.1", help="Address to bind")
    args = parser.parse_args()

    start_date, end_date = get_previous_week_range()
    print(f"Refreshing data for week of {start_date} to {end_date}...")
    payload = refresh_output(args.out)
    print(
        "Wrote "
        f"{len(payload['techcommunity'])} techcommunity items, "
        f"{len(payload['azure_updates'])} azure updates, "
        f"{len(payload['azure_community_blog_headlines'])} azure community blog headlines, "
        f"{len(payload['azure_youtube_videos'])} Azure YouTube videos "
        f"to {args.out}"
    )

    server = ThreadingHTTPServer((args.bind, args.port), UnifiedHandler)
    print(f"Serving unified dashboard at http://{args.bind}:{args.port}/")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopping server...")
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
