#!/bin/bash
# scripts/setup_gcp.sh
# Unk Agent - GCP Infrastructure Setup
# Who Visions LLC

set -e

# ═══════════════════════════════════════════════════════════════════════════
# CONFIGURATION
# ═══════════════════════════════════════════════════════════════════════════

PROJECT_ID="${GOOGLE_CLOUD_PROJECT:-who-visions-llc}"
REGION="${GCP_REGION:-us-central1}"
SERVICE_NAME="unk-agent"
SERVICE_ACCOUNT="${SERVICE_NAME}-sa"

echo "╔═══════════════════════════════════════════════════════════════════════════╗"
echo "║                    UNK AGENT - GCP SETUP                                  ║"
echo "╠═══════════════════════════════════════════════════════════════════════════╣"
echo "║  Project:  $PROJECT_ID"
echo "║  Region:   $REGION"
echo "║  Service:  $SERVICE_NAME"
echo "╚═══════════════════════════════════════════════════════════════════════════╝"

# ═══════════════════════════════════════════════════════════════════════════
# PRE-FLIGHT CHECKS
# ═══════════════════════════════════════════════════════════════════════════

echo ""
echo "► Checking prerequisites..."

# Check gcloud
if ! command -v gcloud &> /dev/null; then
    echo "ERROR: gcloud CLI not found. Install from https://cloud.google.com/sdk"
    exit 1
fi

# Check project
gcloud config set project "$PROJECT_ID"

echo "  ✓ gcloud CLI available"
echo "  ✓ Project set to $PROJECT_ID"

# ═══════════════════════════════════════════════════════════════════════════
# ENABLE APIS
# ═══════════════════════════════════════════════════════════════════════════

echo ""
echo "► Enabling required APIs..."

APIS=(
    "run.googleapis.com"
    "cloudbuild.googleapis.com"
    "artifactregistry.googleapis.com"
    "firestore.googleapis.com"
    "aiplatform.googleapis.com"
    "secretmanager.googleapis.com"
    "logging.googleapis.com"
    "monitoring.googleapis.com"
)

for api in "${APIS[@]}"; do
    echo "  Enabling $api..."
    gcloud services enable "$api" --quiet
done

echo "  ✓ All APIs enabled"

# ═══════════════════════════════════════════════════════════════════════════
# CREATE SERVICE ACCOUNT
# ═══════════════════════════════════════════════════════════════════════════

echo ""
echo "► Setting up service account..."

SA_EMAIL="${SERVICE_ACCOUNT}@${PROJECT_ID}.iam.gserviceaccount.com"

# Create service account if it doesn't exist
if ! gcloud iam service-accounts describe "$SA_EMAIL" &> /dev/null; then
    gcloud iam service-accounts create "$SERVICE_ACCOUNT" \
        --display-name="Unk Agent Service Account" \
        --description="Service account for Unk Agent Cloud Run service"
    echo "  ✓ Service account created"
else
    echo "  ✓ Service account exists"
fi

# Grant roles
ROLES=(
    "roles/aiplatform.user"
    "roles/datastore.user"
    "roles/secretmanager.secretAccessor"
    "roles/logging.logWriter"
    "roles/monitoring.metricWriter"
)

for role in "${ROLES[@]}"; do
    gcloud projects add-iam-policy-binding "$PROJECT_ID" \
        --member="serviceAccount:$SA_EMAIL" \
        --role="$role" \
        --quiet
done

echo "  ✓ IAM roles granted"

# ═══════════════════════════════════════════════════════════════════════════
# SETUP FIRESTORE
# ═══════════════════════════════════════════════════════════════════════════

echo ""
echo "► Configuring Firestore..."

# Create Firestore database if not exists (Native mode)
if ! gcloud firestore databases describe --database="(default)" &> /dev/null 2>&1; then
    gcloud firestore databases create \
        --location="$REGION" \
        --type=firestore-native
    echo "  ✓ Firestore database created"
else
    echo "  ✓ Firestore database exists"
fi

# Create vector index for memory collection
echo "  Creating vector index (this may take a few minutes)..."
cat > /tmp/vector-index.json << 'EOF'
{
  "collectionGroup": "unk_memory",
  "queryScope": "COLLECTION",
  "fields": [
    {
      "fieldPath": "embedding",
      "vectorConfig": {
        "dimension": 768,
        "flat": {}
      }
    },
    {
      "fieldPath": "user_id",
      "order": "ASCENDING"
    },
    {
      "fieldPath": "memory_type",
      "order": "ASCENDING"
    }
  ]
}
EOF

# Note: gcloud firestore indexes composite create doesn't support vector configs yet
# Use Firebase CLI or REST API in production
echo "  ⚠ Vector index must be created via Firebase Console or REST API"
echo "    Collection: unk_memory"
echo "    Vector field: embedding (768 dimensions)"

# ═══════════════════════════════════════════════════════════════════════════
# CREATE ARTIFACT REGISTRY
# ═══════════════════════════════════════════════════════════════════════════

echo ""
echo "► Setting up Artifact Registry..."

REPO_NAME="unk-agent-repo"

if ! gcloud artifacts repositories describe "$REPO_NAME" --location="$REGION" &> /dev/null 2>&1; then
    gcloud artifacts repositories create "$REPO_NAME" \
        --repository-format=docker \
        --location="$REGION" \
        --description="Docker repository for Unk Agent"
    echo "  ✓ Artifact Registry created"
else
    echo "  ✓ Artifact Registry exists"
fi

# Configure Docker auth
gcloud auth configure-docker "${REGION}-docker.pkg.dev" --quiet
echo "  ✓ Docker authentication configured"

# ═══════════════════════════════════════════════════════════════════════════
# BUILD AND PUSH CONTAINER
# ═══════════════════════════════════════════════════════════════════════════

echo ""
echo "► Building container image..."

IMAGE_URL="${REGION}-docker.pkg.dev/${PROJECT_ID}/${REPO_NAME}/${SERVICE_NAME}:latest"

# Build using Cloud Build
gcloud builds submit \
    --tag "$IMAGE_URL" \
    --quiet \
    .

echo "  ✓ Container image built and pushed"

# ═══════════════════════════════════════════════════════════════════════════
# DEPLOY TO CLOUD RUN
# ═══════════════════════════════════════════════════════════════════════════

echo ""
echo "► Deploying to Cloud Run..."

gcloud run deploy "$SERVICE_NAME" \
    --image "$IMAGE_URL" \
    --platform managed \
    --region "$REGION" \
    --service-account "$SA_EMAIL" \
    --memory 2Gi \
    --cpu 2 \
    --timeout 300 \
    --concurrency 80 \
    --min-instances 0 \
    --max-instances 100 \
    --set-env-vars "ENV=production,GOOGLE_CLOUD_PROJECT=$PROJECT_ID,GCP_LOCATION=$REGION" \
    --allow-unauthenticated \
    --quiet

# Get service URL
SERVICE_URL=$(gcloud run services describe "$SERVICE_NAME" \
    --platform managed \
    --region "$REGION" \
    --format 'value(status.url)')

echo "  ✓ Service deployed"

# ═══════════════════════════════════════════════════════════════════════════
# SUMMARY
# ═══════════════════════════════════════════════════════════════════════════

echo ""
echo "╔═══════════════════════════════════════════════════════════════════════════╗"
echo "║                    DEPLOYMENT COMPLETE                                    ║"
echo "╠═══════════════════════════════════════════════════════════════════════════╣"
echo "║"
echo "║  Service URL:     $SERVICE_URL"
echo "║  Health Check:    ${SERVICE_URL}/health"
echo "║  API Docs:        ${SERVICE_URL}/docs (disabled in production)"
echo "║"
echo "║  Next Steps:"
echo "║  1. Create Firestore vector index via Firebase Console"
echo "║  2. Configure custom domain (optional)"
echo "║  3. Set up monitoring alerts"
echo "║  4. Test the /chat endpoint"
echo "║"
echo "╚═══════════════════════════════════════════════════════════════════════════╝"

# Test health endpoint
echo ""
echo "► Testing health endpoint..."
curl -s "${SERVICE_URL}/health" | python3 -m json.tool

echo ""
echo "Done! 🚀"
