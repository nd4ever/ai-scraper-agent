AI Scraper Agent

This project fetches posts from:
- https://techcommunity.microsoft.com/category/azure (past 7 days)
- https://azure.microsoft.com/en-us/updates/ (past 7 days)

Usage:

1. Create a virtual environment and install dependencies:

```bash
python -m venv .venv
.venv\Scripts\activate    # Windows
pip install -r requirements.txt
```

2. Run the agent:

```bash
python -m src.main --days 7 --out output.json
```

Output: JSON file with `techcommunity` and `azure_updates` lists.
Also includes `azure_community_blog_headlines` for the last 7 days from these
Azure Community blog categories:
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

Also includes `azure_youtube_videos` for the last completed Mon-Sun week.
Current channel list under test:
- https://www.youtube.com/@NTFAQGuy/videos

Keep a strict 7-day window:
- Local CLI: use `--days 7` (default is already 7).
- Azure Function: set app setting `DAYS_BACK=7`.

View local page (always refreshes data before serving):

```bash
python serve_web.py --days 7 --port 8000
```

Windows double-click launcher:

```bat
start_web.bat
```

Double-click `start_web.bat` from File Explorer to refresh `output.json` and start the local page.

Then open http://127.0.0.1:8000 to view `index.html`, which renders:
- **Azure Community Blog Headlines** — articles from the specified Azure Community blog categories
- **Azure Updates** — official Azure service announcements
- **Azure Videos** — YouTube video titles from configured Azure-focused channels

Both lists are from the last 7 days. The page regenerates `output.json` on every launch so you always see the latest results.

Scheduling (Windows Task Scheduler / cron): run the above command nightly.

Azure Function deployment (simple):

1. Install Azure CLI and Azure Functions Core Tools.
2. Build a virtualenv and install requirements.
3. From `function_app` folder run:

```bash
func init --worker-runtime python
# (if not already initialized) then
func new --name ScrapeTimer --template "Timer trigger"
pip install -r requirements.txt -t .python_packages/lib/site-packages
func azure functionapp publish <APP_NAME>
```

Environment notes:
- Provide `AzureWebJobsStorage` or `AZURE_STORAGE_CONNECTION_STRING` as a setting.
- Set `OUTPUT_CONTAINER` to the blob container name to store results.
- Set `OUTPUT_BLOB_NAME=output.json` so each run overwrites a stable blob the website can read.
- Set `DAYS_BACK=7` to fetch only the previous 7 days in scheduled runs.

Timer schedule notes:
- `function_app/ScrapeTimer/function.json` uses NCRONTAB format: `{second} {minute} {hour} {day} {month} {day-of-week}`.
- Current schedule is nightly at 02:00 UTC (`0 0 2 * * *`).

Important architecture note:
- `index.html` currently fetches local `output.json` from the Web App package.
- A Function App run does not automatically update that file in the Web App.
- To show nightly-refresh data on the site, point the page to a shared data source (for example blob `output.json` produced by `ScrapeTimer`) or make the page call the Function HTTP endpoint directly.

Azure CLI quick create (example):

```bash
az group create -n my-rg -l eastus
az storage account create -n mystorageacct -g my-rg -l eastus --sku Standard_LRS
az functionapp create -g my-rg -n my-func-app --storage-account mystorageacct --runtime python --functions-version 4
```

