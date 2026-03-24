terraform {
  required_version = ">= 1.0"
  
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
  
  backend "s3" {
    # Configure this with your actual S3 bucket for Terraform state
    # bucket = "your-terraform-state-bucket"
    # key    = "resume-analyzer/terraform.tfstate"
    # region = "us-east-1"
  }
}

provider "aws" {
  region = var.aws_region
  
  default_tags {
    tags = {
      Project     = var.project_name
      Environment = var.environment
      ManagedBy   = "terraform"
    }
  }
}

# Data sources
data "aws_caller_identity" "current" {}
data "aws_region" "current" {}

# VPC and Networking
module "vpc" {
  source = "./modules/vpc"
  
  project_name = var.project_name
  environment  = var.environment
  vpc_cidr     = var.vpc_cidr
  
  availability_zones = var.availability_zones
  public_subnets     = var.public_subnets
  private_subnets    = var.private_subnets
}

# S3 Buckets
module "s3" {
  source = "./modules/s3"
  
  project_name = var.project_name
  environment  = var.environment
  
  create_resume_bucket = var.create_resume_bucket
  create_logs_bucket   = var.create_logs_bucket
}

# DynamoDB Tables
module "dynamodb" {
  source = "./modules/dynamodb"
  
  project_name = var.project_name
  environment  = var.environment
  
  tables = var.dynamodb_tables
}

# SQS Queues
module "sqs" {
  source = "./modules/sqs"
  
  project_name = var.project_name
  environment  = var.environment
  
  queues = var.sqs_queues
}

# ECS Cluster for containerized applications
module "ecs" {
  source = "./modules/ecs"
  
  project_name = var.project_name
  environment  = var.environment
  
  vpc_id             = module.vpc.vpc_id
  private_subnet_ids = module.vpc.private_subnet_ids
  public_subnet_ids  = module.vpc.public_subnet_ids
  
  # Application configuration
  app_image           = var.app_image
  app_port            = var.app_port
  app_cpu             = var.app_cpu
  app_memory          = var.app_memory
  app_desired_count   = var.app_desired_count
  
  # Load balancer configuration
  certificate_arn = var.certificate_arn
  domain_name     = var.domain_name
  
  # Auto scaling
  enable_autoscaling     = var.enable_autoscaling
  min_capacity           = var.min_capacity
  max_capacity           = var.max_capacity
  target_cpu_utilization = var.target_cpu_utilization
}

# RDS for PostgreSQL database
module "rds" {
  source = "./modules/rds"
  
  project_name = var.project_name
  environment  = var.environment
  
  vpc_id             = module.vpc.vpc_id
  private_subnet_ids = module.vpc.private_subnet_ids
  
  # Database configuration
  engine_version    = var.db_engine_version
  instance_class    = var.db_instance_class
  allocated_storage = var.db_allocated_storage
  storage_encrypted = var.db_storage_encrypted
  
  # Security
  database_name     = var.db_name
  master_username   = var.db_username
  manage_master_user_password = true
  
  # Backup and maintenance
  backup_retention_period = var.db_backup_retention_period
  backup_window          = var.db_backup_window
  maintenance_window     = var.db_maintenance_window
  
  # Monitoring
  monitoring_interval = var.db_monitoring_interval
  
  # Multi-AZ for production
  multi_az = var.environment == "production" ? true : false
}

# ElastiCache for Redis
module "elasticache" {
  source = "./modules/elasticache"
  
  project_name = var.project_name
  environment  = var.environment
  
  vpc_id             = module.vpc.vpc_id
  private_subnet_ids = module.vpc.private_subnet_ids
  
  # Redis configuration
  node_type               = var.redis_node_type
  num_cache_nodes        = var.redis_num_nodes
  parameter_group_name   = var.redis_parameter_group
  
  # Security
  auth_token_enabled = var.redis_auth_token_enabled
  
  # Backup
  snapshot_retention_limit = var.redis_snapshot_retention_limit
  snapshot_window         = var.redis_snapshot_window
}

# IAM roles and policies
module "iam" {
  source = "./modules/iam"
  
  project_name = var.project_name
  environment  = var.environment
  
  # S3 bucket ARNs
  resume_bucket_arn = module.s3.resume_bucket_arn
  logs_bucket_arn   = module.s3.logs_bucket_arn
  
  # DynamoDB table ARNs
  dynamodb_table_arns = module.dynamodb.table_arns
  
  # SQS queue ARNs
  sqs_queue_arns = module.sqs.queue_arns
}

# CloudWatch for monitoring and logging
module "cloudwatch" {
  source = "./modules/cloudwatch"
  
  project_name = var.project_name
  environment  = var.environment
  
  # ECS cluster for monitoring
  ecs_cluster_name = module.ecs.cluster_name
  ecs_service_name = module.ecs.service_name
  
  # RDS instance for monitoring
  rds_instance_id = module.rds.instance_id
  
  # ElastiCache cluster for monitoring
  elasticache_cluster_id = module.elasticache.cluster_id
  
  # Notification settings
  sns_topic_arn     = var.sns_topic_arn
  alarm_actions     = var.cloudwatch_alarm_actions
}

# Lambda functions for background processing
module "lambda" {
  source = "./modules/lambda"
  
  project_name = var.project_name
  environment  = var.environment
  
  # VPC configuration for Lambda
  vpc_id             = module.vpc.vpc_id
  private_subnet_ids = module.vpc.private_subnet_ids
  
  # SQS integration
  sqs_queue_arns = module.sqs.queue_arns
  
  # IAM role for Lambda execution
  lambda_execution_role_arn = module.iam.lambda_execution_role_arn
  
  # Lambda configuration
  lambda_functions = var.lambda_functions
}

# Route53 for DNS (optional)
module "route53" {
  source = "./modules/route53"
  count  = var.create_route53_records ? 1 : 0
  
  project_name = var.project_name
  environment  = var.environment
  
  # Domain configuration
  domain_name     = var.domain_name
  hosted_zone_id  = var.hosted_zone_id
  
  # Load balancer for DNS records
  load_balancer_dns_name = module.ecs.load_balancer_dns_name
  load_balancer_zone_id  = module.ecs.load_balancer_zone_id
}