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
from src.scraper import get_current_month_to_date_range, get_previous_week_range


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Update output.json with latest scraped results."
    )
    parser.add_argument("--out", type=str, default="output.json", help="Output JSON path")
    args = parser.parse_args()

    try:
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
            f"(week of {week_start_date} to {week_end_date}); "
            f"{len(updates_month)} azure updates, "
            f"{len(azure_blog_headlines_month)} azure community blog headlines, "
            f"{len(azure_youtube_videos_month)} Azure YouTube videos "
            f"(current month to date: {month_start_date} to {month_end_date})."
        )
        return 0
    except Exception as exc:
        print(f"Update failed: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
