resource "aws_iam_role" "ecsInstanceRole" {
  name               = "${var.prefix}-${var.project_name}-${terraform.workspace}-ecs-execution-task-role"
  assume_role_policy = data.aws_iam_policy_document.batchAssumeRole.json
}

resource "aws_iam_policy" "ecsInstancePolicy" {
  name        = "consult_batch_execution_policy"
  description = "Let batch inovke a sagemaker endpoint"
  policy      = data.aws_iam_policy_document.ecsInstancePolicyDocument.json
}

data "aws_iam_policy_document" "ecsInstancePolicyDocument" {
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
                "sagemaker:InvokeEndpoint",
      
    ]
    effect    = "Allow"
    resources = ["*"]
  }
}

data "aws_iam_policy_document" "batchAssumeRole" {
  statement {
    actions = [
        "sts:AssumeRole"
    ]
    effect    = "Allow"
    resources = ["*"]
    principals {
      type        = "Service"
      identifiers = ["batch.amazonaws.com"]
    }
  }
}

resource "aws_iam_role_policy_attachment" "ecsTaskExecutionRole_policy" {
  role       = aws_iam_role.ecsInstanceRole.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AmazonEC2ContainerServiceforEC2Role"
}
