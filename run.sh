#!/bin/bash
set -e

# -----------------------------
# Usage:
#   ./run.sh deploy   -> deploy system
#   ./run.sh test     -> run E2E tests
#   ./run.sh destroy  -> destroy system
# -----------------------------

ACTION=${1:-}

# -----------------------------
# Show help and exit immediately
# -----------------------------
if [[ "$ACTION" == "--help" || "$ACTION" == "" ]]; then
    echo "Usage:"
    echo "  ./run.sh deploy   -> deploy system"
    echo "  ./run.sh test     -> run E2E tests"
    echo "  ./run.sh destroy  -> destroy system"
    echo "  ./run.sh --help   -> show this help"
    exit 0
fi

# Load environment variables if exists
if [ -f ".env" ]; then
    export $(cat .env | xargs)
fi

# -----------------------------
# Deploy system
# -----------------------------
deploy_system() {
    echo "🚀 Deploying system with Terraform..."
    cd infra/envs/dev

    terraform init
    terraform apply -auto-approve

    # Save API URL to .env
    API_URL=$(terraform output -raw api_base_url | xargs)
    cd ../../../

    echo "✅ System deployed. API_BASE_URL=$API_URL"

    if grep -q '^API_BASE_URL=' .env 2>/dev/null; then
        sed -i'' -e "s|^API_BASE_URL=.*|API_BASE_URL=$API_URL|" .env
    else
        echo "API_BASE_URL=$API_URL" >> .env
    fi

    export API_BASE_URL=$API_URL
}

# -----------------------------
# Run E2E tests
# -----------------------------
run_tests() {
    if [ -z "$API_BASE_URL" ]; then
        echo "❌ API_BASE_URL not set. Deploy first."
        exit 1
    fi

    echo "🧪 Running E2E tests against $API_BASE_URL"
    docker build -f tests/Dockerfile.e2e -t my-e2e-tests tests/
    docker run --rm -it -e API_BASE_URL="$API_BASE_URL" my-e2e-tests pytest -v --disable-warnings
}

# -----------------------------
# Destroy system
# -----------------------------
destroy_system() {
    echo "🗑️ Destroying system with Terraform..."
    cd infra/envs/dev

    terraform destroy -auto-approve
    cd ../../../

    echo "✅ All resources destroyed."
    if [ -f ".env" ]; then
        sed -i'' -e '/^API_BASE_URL=/d' .env
        echo "✅ API_BASE_URL removed from .env"
    fi
}

# -----------------------------
# Main
# -----------------------------
case "$ACTION" in
    deploy)
        deploy_system
        ;;
    test)
        run_tests
        ;;
    destroy)
        destroy_system
        ;;
    *)
        echo "Usage: $0 [deploy|test|destroy]"
        exit 1
        ;;
esac