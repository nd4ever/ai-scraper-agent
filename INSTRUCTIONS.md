# AI Scraper Agent - Requirements & Instructions

## Project Overview

The AI Scraper Agent is a web scraper and dashboard application that collects and displays Azure-related content from multiple sources. It scrapes recent posts and updates from Microsoft Azure community channels and official announcements, then displays them in a local web dashboard.

## Data Sources

The application scrapes from two primary sources:

### 1. Azure Community Tech Blog Headlines
- **URL**: https://techcommunity.microsoft.com/category/azure
- **Content**: Blog post headlines from Azure Community blog categories
- **Categories to Extract**:
  - Azure Arc Blog
  - Azure Architecture Blog
  - Azure Compute Blog
  - Azure Governance and Management
  - Azure Infrastructure Blog
  - Azure Integration Services Blog
  - Azure Migration and Modernization
  - Azure Networking Blog
  - Azure Observability Blog
  - Azure Storage Blog
  - Azure Tools Blog
  - FinOps Blog
- **Metadata**: Each blog post should include:
  - Title
  - URL (clickable link to the blog post)
  - Category (which blog it belongs to)
  - Publication date (parsed from page metadata)

### 2. Azure Official Updates
- **URL**: https://azure.microsoft.com/en-us/updates/
- **Content**: Official Azure service announcements, feature releases, and service retirements
- **Metadata**: Each update should include:
  - Title
  - URL (link to the update)
  - Publication date

### 3. Azure TechCommunity General Posts
- **URL**: https://techcommunity.microsoft.com/category/azure
- **Content**: General discussion posts from the Azure community
- **Metadata**: Each post should include:
  - Title
  - URL
  - Publication date

## Output Format

The application generates a JSON file (`output.json`) with the following structure:

```json
{
  "techcommunity": [
    {
      "title": "Post title",
      "url": "https://techcommunity.microsoft.com/...",
      "date": "2026-04-24T09:11:09.170+00:00"
    }
  ],
  "azure_updates": [
    {
      "title": "Update title",
      "url": "https://azure.microsoft.com/updates?id=...",
      "date": "2026-04-24T14:30:50"
    }
  ],
  "azure_community_blog_headlines": [
    {
      "category": "Azure Architecture Blog",
      "title": "Blog post title",
      "url": "https://techcommunity.microsoft.com/blog/azurearchitectureblog/...",
      "date": "2026-04-24T09:11:09.170+00:00"
    }
  ]
}
```

## Core Requirements

### Data Collection
- Scrape the last **7 days** of content by default (configurable via `--days` parameter)
- Filter results to include only items within the specified date window
- Remove duplicate entries (deduplicate by URL + title combination)
- Handle date parsing robustly, including timezone handling
- Normalize whitespace in titles
- Exclude low-quality items (titles shorter than 4 characters, generic phrases like "Read more")

### Web UI
- Display a local web dashboard at `http://127.0.0.1:8000` (configurable port)
- Show two main sections:
  1. **Azure Community Blog Headlines** - with clickable article titles and category/date metadata
  2. **Azure Updates** - official Azure announcements with titles and dates
- Include a "Refresh" button to reload data from output.json without restarting
- Display loading status and item counts
- Show friendly date/time formatting for all timestamps
- Graceful error handling if output.json is missing or malformed

### CLI Interfaces
- **`update_output.py`**: Scrapes data and writes to output.json
  - `--days`: Number of days back to fetch (default: 7)
  - `--out`: Output file path (default: output.json)
  - Exit with code 0 on success, 1 on failure
  - Print status message with item counts
  - Auto-create output directory and file if missing

- **`src/main.py`**: Alternative CLI interface with same parameters as `update_output.py`
  - Same functionality as update_output.py

- **`serve_web.py`**: Local web server that refreshes data on startup
  - `--days`: Number of days back to fetch (default: 7)
  - `--out`: Output file path (default: output.json)
  - `--port`: HTTP server port (default: 8000)
  - `--bind`: Address to bind to (default: 127.0.0.1)

### Windows Batch Scripts
- **`update_output.bat`**: Double-click to update output.json
  - Auto-detect Python 3.12 installation
  - Run update_output.py with default parameters
  - Display success/failure messages
  - Pause on error for user visibility

- **`start_web.bat`**: Double-click to start local server
  - Auto-detect Python 3.12 installation
  - Refresh data before starting server
  - Open instructions to visit http://127.0.0.1:8000
  - Display stop instructions (Ctrl+C)

### Azure Function Deployment
- Implement as Azure Functions timer-triggered function
- Environment variables:
  - `DAYS_BACK`: Number of days to fetch (default: 7)
  - `OUTPUT_CONTAINER`: Blob container for results (optional; writes to filesystem if not set)
  - `AZURE_STORAGE_CONNECTION_STRING` or `AzureWebJobsStorage`: Storage connection
- Output filename format: `results-{timestamp}.json` (e.g., `results-20260424T091109Z.json`)
- Log execution details (items scraped, destination)

## Technical Constraints

- **Date Handling**: 
  - Parse dates from various formats (ISO 8601, RSS timestamps, human-readable strings)
  - Normalize to ISO 8601 for consistency
  - Handle timezone-aware and naive datetimes
  - Suppress timezone parsing warnings for unknown abbreviations (e.g., PDT)

- **HTML Parsing**:
  - Use BeautifulSoup for parsing
  - Extract dates from:
    - `<time>` tags with `datetime` attributes
    - Title attributes on clickable elements
    - Date spans with class names containing 'date', 'posted', 'published', 'timestamp'
    - Parent element attributes and hierarchies
  - Support multiple selectors for robustness (fallback strategies)

- **Web Scraping**:
  - Use HTTP User-Agent header: `Mozilla/5.0 (compatible)`
  - 15-second timeout per request
  - Suppress XML parsing warnings from BeautifulSoup
  - Handle connection errors gracefully (return empty list on failure)

- **Deduplication**:
  - Use (URL, lowercase-title) as dedup key
  - Skip entries with empty or identical URLs
  - Preserve order (most recent first)

## Dependencies

- `requests`: HTTP client for fetching pages
- `beautifulsoup4`: HTML parsing
- `python-dateutil`: Robust date parsing
- `azure-functions`: For Azure Function deployment
- `azure-storage-blob`: For blob storage integration

## Configuration Defaults

- **Days back**: 7 days
- **Output file**: `output.json` in current directory
- **Web server port**: 8000
- **Web server bind address**: 127.0.0.1
- **HTTP timeout**: 15 seconds
- **User-Agent**: `Mozilla/5.0 (compatible)`

## Error Handling

- **Missing output.json**: Web dashboard shows "No items found" message
- **Invalid JSON**: Web dashboard displays error with HTTP status
- **Network errors**: Scraper catches exceptions and returns empty list for that source
- **Date parsing failures**: Items without valid dates are filtered out
- **Failed scrape**: CLI returns exit code 1 with error message to stderr

## Success Criteria

1. ✅ Scrapes Azure Community blog headlines from all 12 specified categories
2. ✅ Scrapes official Azure Updates from releases API
3. ✅ Scrapes general Azure TechCommunity posts
4. ✅ Filters to last 7 days (configurable)
5. ✅ Outputs valid JSON to specified path
6. ✅ Web dashboard displays blog headlines with clickable links and category metadata
7. ✅ Web dashboard displays Azure updates with titles and dates
8. ✅ Refresh button reloads data without restarting server
9. ✅ Windows batch scripts work without manual Python path configuration
10. ✅ Azure Function deployment compatible
11. ✅ All timestamps in ISO 8601 format
12. ✅ No duplicate entries in output
13. ✅ Graceful error handling throughout
