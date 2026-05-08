param(
  [Parameter(Mandatory = $true)]
  [string]$ResourceGroup,

  [Parameter(Mandatory = $true)]
  [string]$FunctionAppName
)

$ErrorActionPreference = "Stop"

$stagingRoot = Join-Path $PSScriptRoot ".deploy-function"
$zipPath = Join-Path $PSScriptRoot "function-deploy.zip"

if (Test-Path $stagingRoot) {
  Remove-Item $stagingRoot -Recurse -Force
}
if (Test-Path $zipPath) {
  Remove-Item $zipPath -Force
}

New-Item -Path $stagingRoot -ItemType Directory | Out-Null

Copy-Item -Path (Join-Path $PSScriptRoot "function_app\*") -Destination $stagingRoot -Recurse -Force
Copy-Item -Path (Join-Path $PSScriptRoot "src") -Destination (Join-Path $stagingRoot "src") -Recurse -Force

Compress-Archive -Path (Join-Path $stagingRoot "*") -DestinationPath $zipPath -Force

az functionapp config appsettings set --resource-group $ResourceGroup --name $FunctionAppName --settings SCM_DO_BUILD_DURING_DEPLOYMENT=true | Out-Null
az functionapp deployment source config-zip --resource-group $ResourceGroup --name $FunctionAppName --src $zipPath

Write-Host "Function App deployment completed: https://$FunctionAppName.azurewebsites.net"
