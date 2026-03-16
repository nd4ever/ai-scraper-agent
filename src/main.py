import argparse
import json
from pathlib import Path
from src.scraper import fetch_techcommunity, fetch_azure_updates


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--days', type=int, default=7, help='How many days back to fetch')
    p.add_argument('--out', type=str, default='output.json', help='Output JSON file')
    args = p.parse_args()

    tech = fetch_techcommunity(args.days)
    updates = fetch_azure_updates(args.days)

    out = {'techcommunity': tech, 'azure_updates': updates}

    Path(args.out).write_text(json.dumps(out, indent=2, ensure_ascii=False))
    print(f'Wrote {len(tech)} techcommunity items and {len(updates)} azure updates to {args.out}')


if __name__ == '__main__':
    main()
