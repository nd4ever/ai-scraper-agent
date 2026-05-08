param(
  [Parameter(Mandatory = $true)]
  [string]$ResourceGroup,

  [Parameter(Mandatory = $true)]
  [string]$WebAppName,

  [string]$StartupFile = "bash startup_web.sh"
)

$ErrorActionPreference = "Stop"

$zipPath = Join-Path $PSScriptRoot "webapp-deploy.zip"
if (Test-Path $zipPath) {
  Remove-Item $zipPath -Force
}

$exclude = @(
  ".git",
  ".venv",
  "__pycache__",
  "function_app",
  "webapp-deploy.zip",
  "function-deploy.zip",
  ".deploy-function"
)

$items = Get-ChildItem -Path $PSScriptRoot -Force | Where-Object {
  $name = $_.Name
  -not ($exclude -contains $name)
}

Compress-Archive -Path ($items.FullName) -DestinationPath $zipPath -Force

az webapp config appsettings set --resource-group $ResourceGroup --name $WebAppName --settings SCM_DO_BUILD_DURING_DEPLOYMENT=true | Out-Null
az webapp config set --resource-group $ResourceGroup --name $WebAppName --startup-file $StartupFile | Out-Null
az webapp deploy --resource-group $ResourceGroup --name $WebAppName --src-path $zipPath --type zip

Write-Host "Web App deployment completed: https://$WebAppName.azurewebsites.net"
