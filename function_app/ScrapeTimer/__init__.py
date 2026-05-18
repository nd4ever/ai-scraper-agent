import logging
import json
import os
from datetime import datetime

import azure.functions as func

from src.scraper import (
    fetch_azure_community_blog_headlines,
    fetch_azure_updates,
    fetch_azure_youtube_videos,
    fetch_techcommunity,
    get_previous_week_range,
)


def _write_local(filename: str, content: str) -> str:
    path = os.path.join(os.getcwd(), filename)
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
    return path


def _upload_blob(conn_str: str, container: str, filename: str, content: str):
    from azure.storage.blob import BlobServiceClient
    bsc = BlobServiceClient.from_connection_string(conn_str)
    container_client = bsc.get_container_client(container)
    try:
        container_client.create_container()
    except Exception:
        pass
    blob_client = container_client.get_blob_client(filename)
    blob_client.upload_blob(content, overwrite=True)


def main(mytimer: func.TimerRequest) -> None:
    logging.info('ScrapeTimer trigger started')
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
    out_json = json.dumps(out, indent=2, ensure_ascii=False)

    timestamp = datetime.utcnow().strftime('%Y%m%dT%H%M%SZ')
    archive_filename = f'results-{timestamp}.json'
    latest_filename = os.getenv('OUTPUT_BLOB_NAME') or 'output.json'

    conn = os.getenv('AZURE_STORAGE_CONNECTION_STRING') or os.getenv('AzureWebJobsStorage')
    container = os.getenv('OUTPUT_CONTAINER') or 'scraper-output'

    if conn:
        try:
            _upload_blob(conn, container, archive_filename, out_json)
            _upload_blob(conn, container, latest_filename, out_json)
            logging.info(
                f'Uploaded results to container {container} '
                f'as {archive_filename} and {latest_filename}'
            )
            return
        except Exception as e:
            logging.warning(f'Blob upload failed: {e}')

    path = _write_local(latest_filename, out_json)
    logging.info(f'Wrote results locally to {path}')
