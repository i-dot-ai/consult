# SQS Queue Resource
resource "aws_sqs_queue" "batch_job_queue" {
  name                      = "${local.name}-batch-job-queue"
  delay_seconds             = 0
  max_message_size          = 262144  # 256 KB
  message_retention_seconds = 345600  # 4 days
  receive_wait_time_seconds = 0
  visibility_timeout_seconds = 900

  kms_master_key_id = data.terraform_remote_state.platform.outputs.kms_key_arn


  # Dead Letter Queue Configuration
  redrive_policy = jsonencode({
    deadLetterTargetArn = aws_sqs_queue.batch_job_dlq.arn
    maxReceiveCount     = 3
  })

  tags = var.universal_tags
}

# Dead Letter Queue
resource "aws_sqs_queue" "batch_job_dlq" {
  name                      = "${local.name}-batch-job-dlq"
  message_retention_seconds = 1209600  # 14 days

  tags = var.universal_tags
}