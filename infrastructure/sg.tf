resource "aws_security_group" "lambda_sg" {
  name_prefix = "${local.name}-lambda-sg"
  vpc_id      = data.terraform_remote_state.vpc.outputs.vpc_id

  egress {
    from_port   = 6379
    to_port     = 6379  
    protocol    = "tcp"
    cidr_blocks = [data.terraform_remote_state.vpc.outputs.vpc_cidr_block]
    description = "Redis access"
  }
}