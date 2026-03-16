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

Scheduling (Windows Task Scheduler / cron): run the above command weekly.

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
- Set `OUTPUT_CONTAINER` to the blob container name to store results; otherwise results are written to the function filesystem.

Azure CLI quick create (example):

```bash
az group create -n my-rg -l eastus
az storage account create -n mystorageacct -g my-rg -l eastus --sku Standard_LRS
az functionapp create -g my-rg -n my-func-app --storage-account mystorageacct --runtime python --functions-version 4
```

