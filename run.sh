#!/bin/bash
set -e

ACTION=${1:-}

# -----------------------------
# HELP
# -----------------------------
if [[ "$ACTION" == "--help" || "$ACTION" == "" ]]; then
    echo "Usage:"
    echo "  ./run.sh deploy   -> deploy system"
    echo "  ./run.sh e2e      -> run E2E tests"
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

    TF_DIR="infra/envs/dev"

    terraform -chdir="$TF_DIR" init
    terraform -chdir="$TF_DIR" apply -auto-approve

    API_URL=$(terraform -chdir="$TF_DIR" output -raw api_base_url | xargs)
    TABLE_NAME=$(terraform -chdir="$TF_DIR" output -raw table_name | xargs)
    AWS_REGION=$(terraform -chdir="$TF_DIR" output -raw aws_region | xargs)

    echo "✅ System deployed."
    echo "API_BASE_URL=$API_URL"
    echo "TABLE_NAME=$TABLE_NAME"
    echo "AWS_REGION=$AWS_REGION"

    echo "API_BASE_URL=$API_URL" > .env
    echo "TABLE_NAME=$TABLE_NAME" >> .env
    echo "AWS_REGION=$AWS_REGION" >> .env

    echo "🎯 Ready for tests"
}

# -----------------------------
# DOCKER RUNNER
# -----------------------------
run_e2e() {
    echo "🧪 Running E2E tests"

    docker build -f tests/Dockerfile.e2e -t my-tests tests/

    docker run --rm -it \
        --env-file .env \
        -e TEST_PATH=tests/e2e \
        -v ~/.aws:/root/.aws \
        my-tests
}

run_smoke() {
    echo "🔥 Running SMOKE tests"

    docker build -f tests/Dockerfile.e2e -t my-tests tests/

    docker run --rm -it \
        --env-file .env \
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
    e2e)
        run_e2e
        ;;
    smoke)
        run_smoke
        ;;
    destroy)
        destroy_system
        ;;
    *)
        echo "Usage: $0 [deploy|e2e|smoke|destroy]"
        exit 1
        ;;
esac