import argparse
import json
from pathlib import Path
from src.scraper import (
    fetch_azure_community_blog_headlines,
    fetch_azure_updates,
    fetch_azure_youtube_videos,
    fetch_techcommunity,
)
from src.scraper import get_previous_week_range


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--out', type=str, default='output.json', help='Output JSON file')
    args = p.parse_args()

    start_date, end_date = get_previous_week_range()
    tech = fetch_techcommunity(start_date, end_date)
    updates = fetch_azure_updates(start_date, end_date)
    azure_blog_headlines = fetch_azure_community_blog_headlines(start_date, end_date)
    azure_youtube_videos = fetch_azure_youtube_videos(start_date, end_date)

    out = {
        'week_start': start_date.isoformat(),
        'week_end': end_date.isoformat(),
        'techcommunity': tech,
        'azure_updates': updates,
        'azure_community_blog_headlines': azure_blog_headlines,
        'azure_youtube_videos': azure_youtube_videos,
    }

    Path(args.out).write_text(json.dumps(out, indent=2, ensure_ascii=False))
    print(
        f'Wrote {len(tech)} techcommunity items, '
        f'{len(updates)} azure updates, and '
        f'{len(azure_blog_headlines)} azure community blog headlines, and '
        f'{len(azure_youtube_videos)} Azure YouTube videos '
        f'to {args.out} (week of {start_date} to {end_date})'
    )


if __name__ == '__main__':
    main()
