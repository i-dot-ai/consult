resource "aws_iam_role" "ecs_instance_role" {
  name               = "${var.prefix}-${var.project_name}-${terraform.workspace}-ecs-execution-task-role"
  assume_role_policy = data.aws_iam_policy_document.ecs_assume_role_policy.json
}

resource "aws_iam_policy" "ecs_instance_policy" {
  name        = "consult_batch_execution_policy"
  description = "Let batch invoke a sagemaker endpoint"
  policy      = data.aws_iam_policy_document.ecs_instance_policy_document.json
}

resource "aws_iam_instance_profile" "ecs_instance_profile" {
  name = "${var.prefix}-${var.project_name}-${terraform.workspace}-ecs-execution-task-role"
  role = aws_iam_role.ecs_instance_role.name
}

resource "aws_iam_policy" "ecs_assume_batch_policy" {
  name        = "${var.prefix}-${var.project_name}-${terraform.workspace}-ecs-assume-batch-policy"
  description = "Policy to allow ECS role to assume AWS Batch role"
  policy      = data.aws_iam_policy_document.ecs_assume_batch_policy_document.json
}

data "aws_iam_policy_document" "ecs_assume_batch_policy_document" {
  statement {
    actions = ["sts:AssumeRole"]
    resources = [
      "arn:aws:iam::671657536603:role/AWSServiceRoleForBatch"
    ]
    effect = "Allow"
  }
}

resource "aws_iam_role_policy_attachment" "ecs_assume_batch_policy_attachment" {
  role       = aws_iam_role.ecs_instance_role.name
  policy_arn = aws_iam_policy.ecs_assume_batch_policy.arn
}

data "aws_iam_policy_document" "ecs_instance_policy_document" {
  statement {
    actions = [
      "ec2:DescribeTags",
      "ecs:CreateCluster",
      "ecs:DeregisterContainerInstance",
      "ecs:DiscoverPollEndpoint",
      "ecs:Poll",
      "ecs:RegisterContainerInstance",
      "ecs:StartTelemetrySession",
      "ecs:UpdateContainerInstancesState",
      "ecs:Submit*",
      "ecr:GetAuthorizationToken",
      "ecr:BatchCheckLayerAvailability",
      "ecr:GetDownloadUrlForLayer",
      "ecr:BatchGetImage",
      "logs:CreateLogStream",
      "logs:PutLogEvents",
      "sagemaker:CreateEndpoint",
      "sagemaker:InvokeEndpoint"
    ]
    effect    = "Allow"
    resources = ["*"]
  }
}

data "aws_iam_policy_document" "ecs_assume_role_policy" {
  statement {
    actions = [
      "sts:AssumeRole"
    ]
    effect = "Allow"
    principals {
      type        = "Service"
      identifiers = ["ecs-tasks.amazonaws.com"]
    }
  }
}