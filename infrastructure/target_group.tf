resource "aws_lb_target_group" "target_group" {
  name        = local.tg_name
  port        = var.container_port
  protocol    = "HTTP"
  target_type = "ip"
  vpc_id      = data.terraform_remote_state.vpc.outputs.vpc_id

  health_check {
    healthy_threshold   = local.health_check.healthy_threshold
    interval            = 300
    protocol            = "HTTP"
    matcher             = local.health_check.accepted_response
    timeout             = local.health_check.timeout
    path                = local.health_check.path
    unhealthy_threshold = local.health_check.unhealthy_threshold
  }

  lifecycle {
    create_before_destroy = true
  }
}
