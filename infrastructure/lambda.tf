module "lambda_shutdown_sagemaker" {
    source = "../../i-ai-core-infrastructure//modules/lambda_shutdown_sagemaker"
    function_name = "consultations_sagemaker_shutdown"
    environment_variables = {
        queue_name = "consultations"
    }
    iam_role_name = "lambda_sagemaker_endpoint"
}