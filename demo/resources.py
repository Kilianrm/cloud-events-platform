"""Maps Terraform resource addresses to the nodes drawn on the architecture diagram."""

LAMBDAS = ("authentication", "authorization", "validation", "ingestion", "read")

# Lambda name in Terraform -> diagram node id
LAMBDA_NODES = {
    "authentication": "authn",
    "authorization": "authz",
    "validation": "validation",
    "ingestion": "ingestion",
    "read": "read",
}


def node_for(addr: str) -> str | None:
    """
    Returns the diagram node that owns a resource, e.g.
    module.events.aws_lambda_function.ingestion -> "ingestion".

    Data sources are ignored: they are read during planning and never
    created or destroyed, so they would skew the per-node counters.
    """
    parts = addr.split(".")
    while parts and parts[0] == "module":
        parts = parts[2:]
    if not parts or parts[0] == "data" or len(parts) < 2:
        return None

    rtype, name = parts[0], parts[1].split("[")[0]

    if rtype.startswith("aws_apigatewayv2_"):
        return "apigw"
    if rtype == "aws_sqs_queue":
        return "dlq" if "dlq" in name else "sqs"
    if rtype == "aws_lambda_event_source_mapping":
        return "ingestion"
    if rtype == "aws_dynamodb_table":
        return "dynamodb"
    if rtype.startswith("aws_secretsmanager_"):
        return "secrets"
    if rtype.startswith("aws_cloudwatch_"):
        return "cloudwatch"
    if rtype in ("null_resource", "aws_lambda_layer_version"):
        return "layer"

    for lambda_name in LAMBDAS:
        if name == lambda_name or name.startswith(f"{lambda_name}_"):
            return LAMBDA_NODES[lambda_name]

    return "other"


def short_name(addr: str) -> str:
    """module.events.aws_lambda_function.ingestion -> aws_lambda_function.ingestion"""
    parts = addr.split(".")
    while parts and parts[0] == "module":
        parts = parts[2:]
    return ".".join(parts)
