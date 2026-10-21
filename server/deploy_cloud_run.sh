#!/bin/bash
# ==============================================================================
# SEMI-GUARD: Google Cloud Run One-Click Deployment Script
# Project ID: iceu-songpa03
# ==============================================================================

PROJECT_ID="iceu-songpa03"
SERVICE_NAME="semiguard-app"
REGION="us-central1"

echo "🚀 [1/3] Setting Google Cloud Project: $PROJECT_ID..."
gcloud config set project $PROJECT_ID

echo "📦 [2/3] Building container image via Google Cloud Build..."
cd ..
gcloud builds submit --tag gcr.io/$PROJECT_ID/$SERVICE_NAME:latest .

echo "🌐 [3/3] Deploying Container to Google Cloud Run..."
gcloud run deploy $SERVICE_NAME \
  --image gcr.io/$PROJECT_ID/$SERVICE_NAME:latest \
  --region $REGION \
  --platform managed \
  --allow-unauthenticated \
  --memory 1Gi \
  --cpu 1 \
  --port 8080 \
  --min-instances 0 \
  --max-instances 3

echo "✅ [3/3] Deployment Complete! Your Cloud Run Service URL is shown above."
