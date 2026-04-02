#################################################
# 1️⃣ Build the PyJWT Layer ZIP using the script
#################################################
resource "null_resource" "build_pyjwt_layer" {
  triggers = {
    source_hash = filesha256("${var.app_path}/layers/pyjwt/requirements.txt")
  }

  provisioner "local-exec" {
    command = "${var.app_path}/layers/pyjwt/build_layer.sh"
    working_dir = "${var.app_path}/layers/pyjwt"
  }
}

#################################################
# 2️⃣ Upload the Lambda Layer
#################################################
resource "aws_lambda_layer_version" "pyjwt_layer" {
  layer_name          = "pyjwt_layer"
  description         = "Shared PyJWT library for Lambdas"
  compatible_runtimes = ["python3.11"]
  filename            = "${var.app_path}/layers/pyjwt/pyjwt_layer.zip"
  # This acts like a trigger: if ZIP or requirements.txt change, a new layer version is created
  source_code_hash = filesha256("${var.app_path}/layers/pyjwt/requirements.txt")

  depends_on = [null_resource.build_pyjwt_layer]
}