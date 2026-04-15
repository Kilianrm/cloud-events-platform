#!/bin/bash
set -e

ACTION=${1:-}
TF_DIR="infra/envs/dev"

# -----------------------------
# HELP
# -----------------------------
if [[ "$ACTION" == "--help" || "$ACTION" == "" ]]; then
    echo "Usage:"
    echo "  ./run.sh deploy   -> deploy system"
    echo "  ./run.sh test     -> run post_deploy tests"
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


    terraform -chdir="$TF_DIR" init
    terraform -chdir="$TF_DIR" apply -auto-approve

    API_URL=$(terraform -chdir="$TF_DIR" output -raw api_base_url | xargs)
    TABLE_NAME=$(terraform -chdir="$TF_DIR" output -raw table_name | xargs)
    AWS_REGION=$(terraform -chdir="$TF_DIR" output -raw aws_region | xargs)
    QUEUE_URL=$(terraform -chdir="$TF_DIR" output -raw queue_url | xargs)
    DLQ_URL=$(terraform -chdir="$TF_DIR" output -raw dlq_url | xargs)

    echo "✅ System deployed."
    echo "API_BASE_URL=$API_URL"
    echo "TABLE_NAME=$TABLE_NAME"
    echo "AWS_REGION=$AWS_REGION"
    echo "QUEUE_URL=$QUEUE_URL"
    echo "DLQ_URL=$DLQ_URL"

    echo "API_BASE_URL=$API_URL" > .env
    echo "TABLE_NAME=$TABLE_NAME" >> .env
    echo "AWS_REGION=$AWS_REGION" >> .env
    echo "QUEUE_URL=$QUEUE_URL" >> .env
    echo "DLQ_URL=$DLQ_URL" >> .env

    echo "🎯 Ready for tests"
}

# -----------------------------
# DOCKER RUNNER
# -----------------------------

run_tests() {
    echo "🔥 Running tests"

    docker build -f tests/Dockerfile.e2e -t my-tests tests/

    docker run --rm -it \
        --env-file .env \
        -e TEST_PATH=tests/post_deploy \
        -v ~/.aws:/root/.aws \
        my-tests
}

# -----------------------------
# DESTROY
# -----------------------------
destroy_system() {
    echo "🗑️ Destroying system with Terraform..."

    terraform -chdir="$TF_DIR" destroy -auto-approve

    echo "✅ All resources destroyed."

    if [ -f ".env" ]; then
        rm -f .env
        echo "🗑️ .env file removed"
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