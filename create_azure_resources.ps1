# Azure CLI commands to create storage account and container
# Make sure you have Azure CLI installed and are logged in

# Login to Azure (if not already logged in)
# az login

# Set variables
$resourceGroup = "insurance-ai-rg"
$storageAccount = "insuranceaistorage$(Get-Random -Maximum 9999)"
$containerName = "insurance-emails"
$location = "East US"

Write-Host "Creating Azure resources..." -ForegroundColor Green

# Create resource group
Write-Host "Creating resource group: $resourceGroup" -ForegroundColor Yellow
az group create --name $resourceGroup --location $location

# Create storage account
Write-Host "Creating storage account: $storageAccount" -ForegroundColor Yellow
az storage account create `
    --name $storageAccount `
    --resource-group $resourceGroup `
    --location $location `
    --sku Standard_LRS `
    --kind StorageV2

# Get connection string
Write-Host "Getting connection string..." -ForegroundColor Yellow
$connectionString = az storage account show-connection-string `
    --name $storageAccount `
    --resource-group $resourceGroup `
    --query connectionString `
    --output tsv

# Create container
Write-Host "Creating container: $containerName" -ForegroundColor Yellow
az storage container create `
    --name $containerName `
    --connection-string $connectionString `
    --public-access off

Write-Host "✅ Azure resources created successfully!" -ForegroundColor Green
Write-Host ""
Write-Host "📝 Save these details for your application:" -ForegroundColor Cyan
Write-Host "Storage Account Name: $storageAccount" -ForegroundColor White
Write-Host "Container Name: $containerName" -ForegroundColor White
Write-Host "Connection String: $connectionString" -ForegroundColor White
Write-Host ""
Write-Host "🔗 Azure Portal URL:" -ForegroundColor Cyan
Write-Host "https://portal.azure.com/#@/resource/subscriptions/$((az account show --query id -o tsv))/resourceGroups/$resourceGroup/providers/Microsoft.Storage/storageAccounts/$storageAccount" -ForegroundColor Blue
