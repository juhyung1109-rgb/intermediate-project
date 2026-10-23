# SEMI-GUARD Cloud Run & PWA Automated Deployment Script
param(
    [string]$DatasetBucket = "",
    [string]$ProjectId = "iceu-songpa03",
    [string]$ServiceName = "semiguard-app",
    [string]$Region = "us-central1"
)

$ErrorActionPreference = "Stop"

$Timestamp = Get-Date -Format "yyyyMMdd-HHmmss"
$ImageTag = "gcr.io/$ProjectId/semiguard-app:$Timestamp"

Write-Host "=========================================================="
Write-Host " [SEMI-GUARD] Cloud Run & PWA Mobile WebApp Deploy"
Write-Host " Project: $ProjectId | Service: $ServiceName | Region: $Region"
Write-Host " Image: $ImageTag"
Write-Host "=========================================================="

# 1. Project Selection
gcloud config set project $ProjectId

# 2. Container Build via Google Cloud Build
Write-Host "`n[1/2] Building container image via Cloud Build..."
gcloud builds submit --tag $ImageTag .

# 3. Cloud Run Service Deployment
Write-Host "`n[2/2] Deploying container to Cloud Run..."
$DeployArgs = @("run", "deploy", $ServiceName, "--image", $ImageTag,
    "--region", $Region, "--platform", "managed", "--allow-unauthenticated",
    "--memory", "2Gi", "--cpu", "1", "--port", "8080", "--min-instances", "0", "--max-instances", "3")

$EnvVars = @("GOOGLE_CLOUD_PROJECT=$ProjectId", "GOOGLE_CLOUD_REGION=$Region")
if ($DatasetBucket -ne "") {
    $EnvVars += "DATASET_STORAGE=gcs,DATASET_BUCKET=$DatasetBucket"
} else {
    $EnvVars += "DATASET_STORAGE=sqlite"
}

$ApiKey = if ($env:GEMINI_API_KEY) { $env:GEMINI_API_KEY } elseif ($env:GOOGLE_API_KEY) { $env:GOOGLE_API_KEY } else { "" }
if ($ApiKey -ne "") {
    $EnvVars += "GEMINI_API_KEY=$ApiKey"
}

if ($EnvVars.Count -gt 0) {
    $DeployArgs += @("--set-env-vars", ($EnvVars -join ","))
}

gcloud @DeployArgs

# 4. Fetch service URL
$ServiceUrl = gcloud run services describe $ServiceName --region $Region --format="value(status.url)"
Write-Host "`n=========================================================="
Write-Host " [SUCCESS] SEMI-GUARD PWA successfully deployed!"
Write-Host " Live Web URL: $ServiceUrl"
Write-Host "=========================================================="
