#!/bin/bash
set -e

ACTION=${1:-}

# -----------------------------
# HELP
# -----------------------------
if [[ "$ACTION" == "--help" || "$ACTION" == "" ]]; then
    echo "Usage:"
    echo "  ./run.sh deploy   -> deploy system"
    echo "  ./run.sh test     -> run E2E tests"
    echo "  ./run.sh smoke    -> run SMOKE tests"
    echo "  ./run.sh destroy  -> destroy system"
    exit 0
fi

# -----------------------------
# ENV
# -----------------------------
if [ -f ".env" ]; then
    export $(cat .env | xargs)
fi

# -----------------------------
# DEPLOY
# -----------------------------
deploy_system() {
    echo "🚀 Deploying system with Terraform..."
    cd infra/envs/dev

    terraform init
    terraform apply -auto-approve

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
# DOCKER RUNNER
# -----------------------------
run_e2e() {
    echo "🧪 Running E2E tests against $API_BASE_URL"

    docker build -f tests/Dockerfile.e2e -t my-tests tests/

    docker run --rm -it \
        -e API_BASE_URL="$API_BASE_URL" \
        -e TEST_PATH=tests/e2e \
        my-tests
}

run_smoke() {
    echo "🔥 Running SMOKE tests against $API_BASE_URL"

    docker build -f tests/Dockerfile.e2e -t my-tests tests/

    docker run --rm -it \
        -e API_BASE_URL="$API_BASE_URL" \
        -e TEST_PATH=tests/smoke \
        my-tests
}

# -----------------------------
# DESTROY
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
# MAIN
# -----------------------------
case "$ACTION" in
    deploy)
        deploy_system
        ;;
    test)
        run_e2e
        ;;
    smoke)
        run_smoke
        ;;
    destroy)
        destroy_system
        ;;
    *)
        echo "Usage: $0 [deploy|test|smoke|destroy]"
        exit 1
        ;;
esac