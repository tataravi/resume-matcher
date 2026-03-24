# VPC Outputs
output "vpc_id" {
  description = "ID of the VPC"
  value       = module.vpc.vpc_id
}

output "vpc_cidr_block" {
  description = "CIDR block of the VPC"
  value       = module.vpc.vpc_cidr_block
}

output "public_subnet_ids" {
  description = "IDs of the public subnets"
  value       = module.vpc.public_subnet_ids
}

output "private_subnet_ids" {
  description = "IDs of the private subnets"
  value       = module.vpc.private_subnet_ids
}

# S3 Outputs
output "resume_bucket_name" {
  description = "Name of the resume storage bucket"
  value       = module.s3.resume_bucket_name
}

output "resume_bucket_arn" {
  description = "ARN of the resume storage bucket"
  value       = module.s3.resume_bucket_arn
}

output "logs_bucket_name" {
  description = "Name of the logs bucket"
  value       = module.s3.logs_bucket_name
}

# DynamoDB Outputs
output "dynamodb_table_names" {
  description = "Names of DynamoDB tables"
  value       = module.dynamodb.table_names
}

output "dynamodb_table_arns" {
  description = "ARNs of DynamoDB tables"
  value       = module.dynamodb.table_arns
}

# SQS Outputs
output "sqs_queue_urls" {
  description = "URLs of SQS queues"
  value       = module.sqs.queue_urls
}

output "sqs_queue_arns" {
  description = "ARNs of SQS queues"
  value       = module.sqs.queue_arns
}

output "sqs_dlq_urls" {
  description = "URLs of SQS dead letter queues"
  value       = module.sqs.dlq_urls
}

# ECS Outputs
output "ecs_cluster_id" {
  description = "ID of the ECS cluster"
  value       = module.ecs.cluster_id
}

output "ecs_cluster_name" {
  description = "Name of the ECS cluster"
  value       = module.ecs.cluster_name
}

output "ecs_service_name" {
  description = "Name of the ECS service"
  value       = module.ecs.service_name
}

output "load_balancer_dns_name" {
  description = "DNS name of the load balancer"
  value       = module.ecs.load_balancer_dns_name
}

output "load_balancer_hosted_zone_id" {
  description = "Hosted zone ID of the load balancer"
  value       = module.ecs.load_balancer_zone_id
}

output "application_url" {
  description = "URL of the application"
  value       = var.domain_name != "" ? "https://${var.domain_name}" : "https://${module.ecs.load_balancer_dns_name}"
}

# RDS Outputs
output "rds_instance_id" {
  description = "ID of the RDS instance"
  value       = module.rds.instance_id
}

output "rds_instance_endpoint" {
  description = "RDS instance endpoint"
  value       = module.rds.instance_endpoint
}

output "rds_instance_port" {
  description = "RDS instance port"
  value       = module.rds.instance_port
}

output "database_url" {
  description = "Database connection URL (without password)"
  value       = "postgresql://${var.db_username}@${module.rds.instance_endpoint}:${module.rds.instance_port}/${var.db_name}"
  sensitive   = false
}

# ElastiCache Outputs
output "redis_cluster_id" {
  description = "ID of the Redis cluster"
  value       = module.elasticache.cluster_id
}

output "redis_primary_endpoint" {
  description = "Primary endpoint of the Redis cluster"
  value       = module.elasticache.primary_endpoint
}

output "redis_port" {
  description = "Port of the Redis cluster"
  value       = module.elasticache.port
}

output "redis_url" {
  description = "Redis connection URL"
  value       = "redis://${module.elasticache.primary_endpoint}:${module.elasticache.port}"
}

# IAM Outputs
output "ecs_task_role_arn" {
  description = "ARN of the ECS task role"
  value       = module.iam.ecs_task_role_arn
}

output "ecs_execution_role_arn" {
  description = "ARN of the ECS execution role"
  value       = module.iam.ecs_execution_role_arn
}

output "lambda_execution_role_arn" {
  description = "ARN of the Lambda execution role"
  value       = module.iam.lambda_execution_role_arn
}

# Lambda Outputs
output "lambda_function_names" {
  description = "Names of Lambda functions"
  value       = module.lambda.function_names
}

output "lambda_function_arns" {
  description = "ARNs of Lambda functions"
  value       = module.lambda.function_arns
}

# CloudWatch Outputs
output "cloudwatch_log_groups" {
  description = "CloudWatch log groups"
  value       = module.cloudwatch.log_groups
}

# Route53 Outputs
output "domain_name" {
  description = "Domain name of the application"
  value       = var.domain_name
}

output "route53_record_names" {
  description = "Route53 record names"
  value       = var.create_route53_records ? module.route53[0].record_names : []
}

# Environment Configuration for Application
output "environment_variables" {
  description = "Environment variables for the application"
  value = {
    AWS_REGION                = var.aws_region
    AWS_S3_BUCKET            = module.s3.resume_bucket_name
    AWS_DYNAMODB_TABLE       = keys(module.dynamodb.table_names)[0]
    AWS_SQS_QUEUE_URL        = values(module.sqs.queue_urls)[0]
    DATABASE_URL             = "postgresql://${var.db_username}:PASSWORD@${module.rds.instance_endpoint}:${module.rds.instance_port}/${var.db_name}"
    REDIS_URL                = "redis://${module.elasticache.primary_endpoint}:${module.elasticache.port}"
    LOG_LEVEL                = var.environment == "prod" ? "WARNING" : "INFO"
    DEBUG                    = var.environment == "prod" ? "false" : "true"
  }
  sensitive = false
}

# Security Group IDs (useful for additional configuration)
output "application_security_group_id" {
  description = "Security group ID for the application"
  value       = module.ecs.application_security_group_id
}

output "database_security_group_id" {
  description = "Security group ID for the database"
  value       = module.rds.security_group_id
}

output "redis_security_group_id" {
  description = "Security group ID for Redis"
  value       = module.elasticache.security_group_id
}