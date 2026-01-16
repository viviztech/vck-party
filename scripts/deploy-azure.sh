#!/bin/bash

# =============================================================================
# Azure Deployment Script for VCK Platform
# This script helps you deploy the VCK Platform to Azure Always Free tier
# =============================================================================

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Functions for colored output
print_status() {
    echo -e "${GREEN}[✓]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[!]${NC} $1"
}

print_error() {
    echo -e "${RED}[✗]${NC} $1"
}

# Check prerequisites
check_prerequisites() {
    print_status "Checking prerequisites..."
    
    # Check Azure CLI
    if ! command -v az &> /dev/null; then
        print_error "Azure CLI not found. Please install it first:"
        echo "  brew install azure-cli"
        exit 1
    fi
    
    # Check Docker
    if ! command -v docker &> /dev/null; then
        print_warning "Docker not found. Some deployment options may not be available."
    fi
    
    # Check Git
    if ! command -v git &> /dev/null; then
        print_error "Git not found. Please install it first."
        exit 1
    fi
    
    print_status "All prerequisites are met!"
}

# Login to Azure
azure_login() {
    print_status "Logging in to Azure..."
    az login
    print_status "Logged in successfully!"
}

# Create resource group
create_resource_group() {
    print_status "Creating resource group..."
    az group create \
        --name vck-rg \
        --location eastus \
        --output table
    print_status "Resource group created!"
}

# Create PostgreSQL database
create_postgres() {
    print_status "Creating Azure Database for PostgreSQL..."
    
    read -p "Enter PostgreSQL admin username: " POSTGRES_USER
    read -s -p "Enter PostgreSQL admin password: " POSTGRES_PASSWORD
    echo
    
    az postgres flexible-server create \
        --resource-group vck-rg \
        --name vck-postgres \
        --admin-user "$POSTGRES_USER" \
        --admin-password "$POSTGRES_PASSWORD" \
        --sku-name Standard_B1ms \
        --tier Burstable \
        --public-access None \
        --database-name vck_db \
        --output table
    
    print_status "PostgreSQL created! Connection string saved to backend/.env"
}

# Create Cosmos DB with MongoDB API
create_cosmos() {
    print_status "Creating Azure Cosmos DB with MongoDB API..."
    
    az cosmosdb create \
        --resource-group vck-rg \
        --name vck-cosmos \
        --kind MongoDB \
        --enable-free-tier \
        --output table
    
    az cosmosdb mongodb database create \
        --resource-group vck-rg \
        --account-name vck-cosmos \
        --name vck_analytics \
        --output table
    
    print_status "Cosmos DB created!"
}

# Create Redis cache
create_redis() {
    print_status "Creating Azure Cache for Redis..."
    
    az redis create \
        --resource-group vck-rg \
        --name vck-redis \
        --sku Basic \
        --vm-size c0 \
        --enable-non-ssl-port false \
        --output table
    
    print_status "Redis cache created!"
}

# Create App Service for backend
create_app_service() {
    print_status "Creating Azure App Service for backend..."
    
    az appservice plan create \
        --resource-group vck-rg \
        --name vck-backend-plan \
        --sku B1 \
        --is-linux \
        --output table
    
    az webapp create \
        --resource-group vck-rg \
        --plan vck-backend-plan \
        --name vck-backend \
        --deployment-container-image-name python:3.11 \
        --output table
    
    print_status "App Service created!"
}

# Create Static Web Apps for frontend
create_static_web_app() {
    print_status "Creating Azure Static Web Apps for frontend..."
    
    az staticwebapp create \
        --resource-group vck-rg \
        --name vck-frontend \
        --sku Free \
        --location eastus \
        --branch main \
        --output table
    
    print_status "Static Web App created!"
}

# Deploy backend to App Service
deploy_backend() {
    print_status "Deploying backend to Azure App Service..."
    
    # Update environment variables
    read -p "Enter your environment file path (or press Enter to use default): " ENV_FILE
    ENV_FILE=${ENV_FILE:-"backend/.env"}
    
    if [ -f "$ENV_FILE" ]; then
        print_status "Setting environment variables from $ENV_FILE..."
        while IFS= read -r line || [[ -n "$line" ]]; do
            if [[ ! "$line" =~ ^# ]] && [[ -n "$line" ]]; then
                key=$(echo "$line" | cut -d'=' -f1)
                value=$(echo "$line" | cut -d'=' -f2-)
                az webapp config appsettings set \
                    --resource-group vck-rg \
                    --name vck-backend \
                    --settings "$key=$value" \
                    --output none
            fi
        done < "$ENV_FILE"
    fi
    
    # Deploy using az webapp up
    print_status "Deploying application..."
    cd backend
    az webapp up \
        --resource-group vck-rg \
        --name vck-backend \
        --src . \
        --runtime "PYTHON:3.11" \
        --output table
    
    print_status "Backend deployed successfully!"
}

# Deploy frontend to Static Web Apps
deploy_frontend() {
    print_status "Deploying frontend to Azure Static Web Apps..."
    
    # Build frontend
    print_status "Building frontend..."
    cd frontend
    npm install
    npm run build
    
    # Deploy using SWA CLI
    print_status "Uploading to Static Web Apps..."
    npx @azure/static-web-apps-cli deploy \
        --app-name vck-frontend \
        --resource-group vck-rg \
        --output-location dist \
        --env production \
        --output table
    
    print_status "Frontend deployed successfully!"
}

# Configure CORS
configure_cors() {
    print_status "Configuring CORS settings..."
    
    FRONTEND_URL=$(az staticwebapp show \
        --name vck-frontend \
        --resource-group vck-rg \
        --query "defaultHostname" \
        --output tsv)
    
    az webapp cors add \
        --resource-group vck-rg \
        --name vck-backend \
        --allowed-origins "https://$FRONTEND_URL" \
        --output table
    
    print_status "CORS configured!"
}

# Show deployment summary
show_summary() {
    echo ""
    echo "=============================================="
    echo "       Deployment Summary"
    echo "=============================================="
    echo ""
    
    BACKEND_URL=$(az webapp show \
        --name vck-backend \
        --resource-group vck-rg \
        --query "defaultHostName" \
        --output tsv)
    
    FRONTEND_URL=$(az staticwebapp show \
        --name vck-frontend \
        --resource-group vck-rg \
        --query "defaultHostname" \
        --output tsv)
    
    echo "Backend API:     https://$BACKEND_URL"
    echo "Backend Health:  https://$BACKEND_URL/health"
    echo "Frontend App:    https://$FRONTEND_URL"
    echo ""
    echo "=============================================="
    echo ""
    print_status "Deployment completed successfully!"
}

# Main menu
show_menu() {
    echo ""
    echo "=============================================="
    echo "   Azure Deployment Script for VCK Platform"
    echo "=============================================="
    echo ""
    echo "1. Check prerequisites"
    echo "2. Login to Azure"
    echo "3. Create all Azure resources"
    echo "4. Deploy backend"
    echo "5. Deploy frontend"
    echo "6. Configure CORS"
    echo "7. Show deployment summary"
    echo "8. Exit"
    echo ""
    read -p "Enter your choice (1-8): " choice
    echo ""
    
    case $choice in
        1)
            check_prerequisites
            ;;
        2)
            azure_login
            ;;
        3)
            create_resource_group
            create_postgres
            create_cosmos
            create_redis
            create_app_service
            create_static_web_app
            ;;
        4)
            deploy_backend
            ;;
        5)
            deploy_frontend
            ;;
        6)
            configure_cors
            ;;
        7)
            show_summary
            ;;
        8)
            echo "Goodbye!"
            exit 0
            ;;
        *)
            print_error "Invalid choice!"
            ;;
    esac
    
    show_menu
}

# Main execution
main() {
    if [ "$1" == "--help" ] || [ "$1" == "-h" ]; then
        echo "Usage: ./deploy-azure.sh [command]"
        echo ""
        echo "Commands:"
        echo "  check       Check prerequisites"
        echo "  login       Login to Azure"
        echo "  create      Create all Azure resources"
        echo "  deploy-be   Deploy backend to App Service"
        echo "  deploy-fe   Deploy frontend to Static Web Apps"
        echo "  cors        Configure CORS settings"
        echo "  summary     Show deployment summary"
        echo "  all         Run complete deployment"
        echo ""
        exit 0
    fi
    
    if [ "$1" == "all" ]; then
        check_prerequisites
        azure_login
        create_resource_group
        create_postgres
        create_cosmos
        create_redis
        create_app_service
        create_static_web_app
        deploy_backend
        deploy_frontend
        configure_cors
        show_summary
    else
        show_menu
    fi
}

main "$@"
