import argparse
import json
import sys
from pathlib import Path

from src.scraper import (
    fetch_azure_community_blog_headlines,
    fetch_azure_updates,
    fetch_azure_youtube_videos,
    fetch_techcommunity,
)
from src.scraper import get_previous_week_range


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Update output.json with latest scraped results."
    )
    parser.add_argument("--out", type=str, default="output.json", help="Output JSON path")
    args = parser.parse_args()

    try:
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

        out_path = Path(args.out)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        if not out_path.exists():
            out_path.touch()

        out_path.write_text(
            json.dumps(payload, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )

        print(
            f"Updated {args.out}: "
            f"{len(tech)} techcommunity items, "
            f"{len(updates)} azure updates, "
            f"{len(azure_blog_headlines)} azure community blog headlines, "
            f"{len(azure_youtube_videos)} Azure YouTube videos "
            f"(week of {start_date} to {end_date})."
        )
        return 0
    except Exception as exc:
        print(f"Update failed: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
