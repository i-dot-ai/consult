module "lambda" {
  source           = "../../../i-ai-core-infrastructure//modules/lambda"
  file_path        = "${path.module}/../lambda_shutdown_sagemaker/lambda_function.zip"
  function_name    = "consultations_sagemaker_shutdown"
  handler          = "lambda_function.lambda_handler"
  runtime          = "python3.12"
  source_code_hash = data.archive_file.lambda_zip.output_base64sha256
  iam_role_name    = "lambda_sagemaker_endpoint"
}

data "archive_file" "lambda_zip" {
  type        = "zip"
  source_file = "${path.module}/lambda_shutdown_sagemaker/lambda_function.py"
  output_path = "${path.module}/lambda_shutdown_sagemaker/lambda_function.zip"
}
