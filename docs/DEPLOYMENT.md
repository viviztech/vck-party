# Azure Always Free Deployment Guide for VCK Platform

This guide covers deploying the VCK Platform to Azure using always free services.

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                        Azure Always Free Tier                    │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│   ┌──────────────────┐     ┌─────────────────────────────────┐  │
│   │ Azure Static     │────▶│     Azure App Service           │  │
│   │ Web Apps         │     │     (Python/FastAPI)            │  │
│   │ (React/TypeScript)│     │                                 │  │
│   └──────────────────┘     └─────────────────────────────────┘  │
│         ▲                          │                            │
│         │                          ▼                            │
│   ┌─────────────────────────────────────────────────────────┐  │
│   │              Azure Front Door (Optional)                │  │
│   └─────────────────────────────────────────────────────────┘  │
│                                                                 │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│   ┌──────────────────┐     ┌─────────────────────────────────┐  │
│   │ Azure Database   │     │     Azure Cosmos DB             │  │
│   │ for PostgreSQL   │     │     (MongoDB API) - 12 months   │  │
│   │ Flexible Server  │     │                                 │  │
│   └──────────────────┘     └─────────────────────────────────┘  │
│                                                                 │
│   ┌─────────────────────────────────────────────────────────┐  │
│   │         Azure Cache for Redis (Basic tier - 12 months) │  │
│   └─────────────────────────────────────────────────────────┘  │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

## Prerequisites

1. **Azure Account** with free tier enabled
2. **Azure CLI** installed locally
3. **Git** installed locally
4. **Docker** installed locally (for container builds)

## Step 1: Create Azure Resources

### 1.1 Login to Azure

```bash
az login
az account show  # Verify your subscription
```

### 1.2 Create Resource Group

```bash
# Create a resource group for the VCK platform
az group create \
  --name vck-rg \
  --location eastus
```

### 1.3 Create Azure Database for PostgreSQL (Always Free)

```bash
az postgres flexible-server create \
  --resource-group vck-rg \
  --name vck-postgres \
  --admin-user vck_admin \
  --admin-password '<your-strong-password>' \
  --sku-name Standard_B1ms \
  --tier Burstable \
  --public-access None \
  --database-name vck_db
```

**Note**: The free tier is available for the first 12 months. After that, you can upgrade or switch to a paid tier.

### 1.4 Create Azure Cosmos DB with MongoDB API (Always Free)

```bash
az cosmosdb create \
  --resource-group vck-rg \
  --name vck-cosmos \
  --kind MongoDB \
  --enable-free-tier true

# Create the database
az cosmosdb mongodb database create \
  --resource-group vck-rg \
  --account-name vck-cosmos \
  --name vck_analytics
```

### 1.5 Create Azure Cache for Redis (Always Free)

```bash
az redis create \
  --resource-group vck-rg \
  --name vck-redis \
  --sku Basic \
  --vm-size c0 \
  --enable-non-ssl-port false
```

**Note**: The free tier is available for the first 12 months.

### 1.6 Create Azure App Service (Backend)

```bash
az appservice plan create \
  --resource-group vck-rg \
  --name vck-backend-plan \
  --sku B1 \
  --is-linux

az webapp create \
  --resource-group vck-rg \
  --plan vck-backend-plan \
  --name vck-backend \
  --deployment-container-image-name python:3.11
```

### 1.7 Create Azure Static Web Apps (Frontend)

```bash
az staticwebapp create \
  --resource-group vck-rg \
  --name vck-frontend \
  --sku Free \
  --location eastus \
  --branch main
```

## Step 2: Configure Backend for Azure App Service

### 2.1 Update Environment Variables

Copy the production template and fill in your values:

```bash
cp backend/.env.production.example backend/.env
```

Edit `backend/.env` and update:
- Database connection strings
- Redis connection
- JWT secret key (generate a strong random string)
- CORS origins (update with your Static Web Apps URL)

### 2.2 Deploy Backend to Azure App Service

```bash
# Deploy using Azure CLI
az webapp config appsettings set \
  --resource-group vck-rg \
  --name vck-backend \
  --settings @backend/.env

# Deploy the application
az webapp up \
  --resource-group vck-rg \
  --name vck-backend \
  --src backend/ \
  --runtime "PYTHON:3.11"
```

### 2.3 Alternative: Deploy using Docker

```bash
# Build and push Docker image to Azure Container Registry
az acr create \
  --resource-group vck-rg \
  --name vckregistry \
  --sku Basic

az acr login --name vckregistry

docker build -t vckregistry.azurecr.io/vck-backend:latest ./backend
docker push vckregistry.azurecr.io/vck-backend:latest

# Configure App Service to use the container
az webapp config container set \
  --resource-group vck-rg \
  --name vck-backend \
  --docker-registry-server-password '<your-acr-password>' \
  --docker-registry-server-user vckregistry \
  --docker-custom-image-name vckregistry.azurecr.io/vck-backend:latest
```

## Step 3: Configure Frontend for Azure Static Web Apps

### 3.1 Update Environment Variables

```bash
cp frontend/.env.production frontend/.env.local
```

Edit `frontend/.env.local` and update the API URL to point to your App Service:

```
VITE_API_URL=https://vck-backend.azurewebsites.net/api/v1
```

### 3.2 Build the Frontend

```bash
cd frontend
npm install
npm run build
```

### 3.3 Deploy to Static Web Apps

```bash
# Using Azure Static Web Apps CLI (SWA)
npx @azure/static-web-apps-cli build \
  --output-location dist \
  --app-location frontend

npx @azure/static-web-apps-cli deploy \
  --app-name vck-frontend \
  --resource-group vck-rg \
  --output-location dist \
  --env production
```

### 3.4 Alternative: GitHub Actions Deployment

Create `.github/workflows/azure-static-web-apps.yml`:

```yaml
name: Azure Static Web Apps CI/CD

on:
  push:
    branches:
      - main

jobs:
  build_and_deploy_job:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
        
      - name: Build And Deploy
        uses: Azure/static-web-apps-deploy@v1
        with:
          azure_static_web_apps_api_token: ${{ secrets.AZURE_STATIC_WEB_APPS_API_TOKEN }}
          repo_token: ${{ secrets.GITHUB_TOKEN }}
          action: "upload"
          app_location: "frontend"
          api_location: ""
          skip_app_build: true
          skip_api_build: true
          output_location: "dist"
```

## Step 4: Configure CORS and Networking

### 4.1 Update CORS in Backend

Ensure your backend's CORS settings include your Static Web Apps URL:

```python
# In backend/src/core/config.py
CORS_ORIGINS = [
    "http://localhost:3000",
    "https://<your-frontend-name>.azurestaticapps.net",
]
```

### 4.2 Configure Backend Authentication Settings

```bash
az webapp config appsettings set \
  --resource-group vck-rg \
  --name vck-backend \
  --settings JWT_SECRET_KEY="<your-generated-secret-key>"
```

## Step 5: Verify Deployment

### 5.1 Test Backend API

```bash
# Health check
curl https://vck-backend.azurewebsites.net/health

# Expected response:
# {"status":"healthy","service":"VCK Political Party Management","version":"1.0.0",...}
```

### 5.2 Test Frontend

Open your Static Web Apps URL in a browser:
```
https://<your-frontend-name>.azurestaticapps.net
```

## Step 6: Configure Custom Domain (Optional)

### 6.1 Add Custom Domain to Static Web Apps

```bash
az staticwebapp hostname set \
  --name vck-frontend \
  --resource-group vck-rg \
  --hostname www.your-domain.com
```

### 6.2 Add Custom Domain to App Service

```bash
az webapp config hostname add \
  --resource-group vck-rg \
  --name vck-backend \
  --hostname api.your-domain.com
```

## Cost Estimation (Always Free Tier)

| Service | Free Tier Limit | Estimated Monthly Cost |
|---------|----------------|------------------------|
| Azure Static Web Apps | 100 GB bandwidth, 500 MB storage | $0.00 |
| Azure App Service | 10 App Service plans (B1) | $0.00 (first 12 months) |
| Azure Database for PostgreSQL | 12 months free (B1ms) | $0.00 (first 12 months) |
| Azure Cosmos DB | 400 RU/s, 5 GB storage | $0.00 |
| Azure Cache for Redis | 12 months free (C0) | $0.00 (first 12 months) |
| **Total** | | **$0.00/month** |

**Note**: After the 12-month free period, the estimated cost would be approximately $30-50/month depending on usage.

## Troubleshooting

### Backend Health Check Fails

```bash
# Check application logs
az webapp log tail --resource-group vck-rg --name vck-backend
```

### CORS Errors

Ensure your CORS origins in the backend configuration include your Static Web Apps URL. Update the `CORS_ORIGINS` setting in your `.env` file.

### Database Connection Issues

1. Verify the database is running
2. Check connection strings in environment variables
3. Ensure the App Service can reach the database (may require adding the App Service's outbound IP to the database's firewall)

### Redis Connection Issues

1. Check Redis connection string
2. Verify the Redis firewall allows connections from App Service
3. For Basic tier, ensure you're using the correct port (6380 for SSL)

## Additional Resources

- [Azure Static Web Apps Documentation](https://docs.microsoft.com/azure/static-web-apps/)
- [Azure App Service Python Documentation](https://docs.microsoft.com/azure/app-service/quickstart-python)
- [Azure Database for PostgreSQL](https://docs.microsoft.com/azure/postgresql/)
- [Azure Cosmos DB MongoDB API](https://docs.microsoft.com/azure/cosmos-db/mongodb/)
- [Azure Cache for Redis](https://docs.microsoft.com/azure/azure-cache-for-redis/)
