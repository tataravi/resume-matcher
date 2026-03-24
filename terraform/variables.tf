# General Variables
variable "project_name" {
  description = "Name of the project"
  type        = string
  default     = "resume-analyzer"
}

variable "environment" {
  description = "Environment (dev, staging, prod)"
  type        = string
  default     = "dev"
  
  validation {
    condition     = contains(["dev", "staging", "prod"], var.environment)
    error_message = "Environment must be dev, staging, or prod."
  }
}

variable "aws_region" {
  description = "AWS region"
  type        = string
  default     = "us-east-1"
}

# VPC Configuration
variable "vpc_cidr" {
  description = "CIDR block for VPC"
  type        = string
  default     = "10.0.0.0/16"
}

variable "availability_zones" {
  description = "Availability zones"
  type        = list(string)
  default     = ["us-east-1a", "us-east-1b", "us-east-1c"]
}

variable "public_subnets" {
  description = "Public subnet CIDR blocks"
  type        = list(string)
  default     = ["10.0.1.0/24", "10.0.2.0/24", "10.0.3.0/24"]
}

variable "private_subnets" {
  description = "Private subnet CIDR blocks"
  type        = list(string)
  default     = ["10.0.11.0/24", "10.0.12.0/24", "10.0.13.0/24"]
}

# S3 Configuration
variable "create_resume_bucket" {
  description = "Whether to create S3 bucket for resume storage"
  type        = bool
  default     = true
}

variable "create_logs_bucket" {
  description = "Whether to create S3 bucket for logs"
  type        = bool
  default     = true
}

# DynamoDB Configuration
variable "dynamodb_tables" {
  description = "DynamoDB tables configuration"
  type = map(object({
    hash_key        = string
    range_key       = optional(string)
    billing_mode    = optional(string, "PAY_PER_REQUEST")
    read_capacity   = optional(number, 5)
    write_capacity  = optional(number, 5)
    stream_enabled  = optional(bool, false)
    stream_view_type = optional(string, "NEW_AND_OLD_IMAGES")
    
    attributes = list(object({
      name = string
      type = string
    }))
    
    global_secondary_indexes = optional(list(object({
      name     = string
      hash_key = string
      range_key = optional(string)
      projection_type = optional(string, "ALL")
      read_capacity  = optional(number, 5)
      write_capacity = optional(number, 5)
    })), [])
  }))
  
  default = {
    "resume-analysis-results" = {
      hash_key = "analysis_id"
      range_key = "user_id"
      
      attributes = [
        { name = "analysis_id", type = "S" },
        { name = "user_id", type = "S" },
        { name = "created_at", type = "S" }
      ]
      
      global_secondary_indexes = [
        {
          name     = "user-created-index"
          hash_key = "user_id"
          range_key = "created_at"
        }
      ]
    }
  }
}

# SQS Configuration
variable "sqs_queues" {
  description = "SQS queues configuration"
  type = map(object({
    delay_seconds             = optional(number, 0)
    max_message_size         = optional(number, 262144)
    message_retention_seconds = optional(number, 1209600)
    visibility_timeout_seconds = optional(number, 30)
    receive_wait_time_seconds = optional(number, 0)
    fifo_queue               = optional(bool, false)
    content_based_deduplication = optional(bool, false)
    
    dlq_enabled              = optional(bool, true)
    dlq_max_receive_count    = optional(number, 3)
  }))
  
  default = {
    "resume-analysis" = {
      visibility_timeout_seconds = 300
      message_retention_seconds  = 1209600  # 14 days
      dlq_enabled               = true
      dlq_max_receive_count     = 3
    }
  }
}

# ECS Configuration
variable "app_image" {
  description = "Docker image for the application"
  type        = string
  default     = "resume-analyzer:latest"
}

variable "app_port" {
  description = "Port the application listens on"
  type        = number
  default     = 8000
}

variable "app_cpu" {
  description = "CPU units for the application (1024 = 1 vCPU)"
  type        = number
  default     = 512
}

variable "app_memory" {
  description = "Memory for the application in MB"
  type        = number
  default     = 1024
}

variable "app_desired_count" {
  description = "Desired number of application instances"
  type        = number
  default     = 2
}

# Auto Scaling Configuration
variable "enable_autoscaling" {
  description = "Whether to enable auto scaling"
  type        = bool
  default     = true
}

variable "min_capacity" {
  description = "Minimum number of instances"
  type        = number
  default     = 1
}

variable "max_capacity" {
  description = "Maximum number of instances"
  type        = number
  default     = 10
}

variable "target_cpu_utilization" {
  description = "Target CPU utilization for auto scaling"
  type        = number
  default     = 70
}

# Load Balancer Configuration
variable "certificate_arn" {
  description = "ARN of the SSL certificate for HTTPS"
  type        = string
  default     = ""
}

variable "domain_name" {
  description = "Domain name for the application"
  type        = string
  default     = ""
}

# RDS Configuration
variable "db_engine_version" {
  description = "PostgreSQL engine version"
  type        = string
  default     = "15.4"
}

variable "db_instance_class" {
  description = "RDS instance class"
  type        = string
  default     = "db.t3.micro"
}

variable "db_allocated_storage" {
  description = "Allocated storage for RDS in GB"
  type        = number
  default     = 20
}

variable "db_storage_encrypted" {
  description = "Whether to encrypt RDS storage"
  type        = bool
  default     = true
}

variable "db_name" {
  description = "Database name"
  type        = string
  default     = "resume_analyzer"
}

variable "db_username" {
  description = "Database master username"
  type        = string
  default     = "postgres"
}

variable "db_backup_retention_period" {
  description = "Database backup retention period in days"
  type        = number
  default     = 7
}

variable "db_backup_window" {
  description = "Database backup window"
  type        = string
  default     = "03:00-04:00"
}

variable "db_maintenance_window" {
  description = "Database maintenance window"
  type        = string
  default     = "sun:04:00-sun:05:00"
}

variable "db_monitoring_interval" {
  description = "Database monitoring interval in seconds"
  type        = number
  default     = 60
}

# Redis Configuration
variable "redis_node_type" {
  description = "ElastiCache Redis node type"
  type        = string
  default     = "cache.t3.micro"
}

variable "redis_num_nodes" {
  description = "Number of Redis nodes"
  type        = number
  default     = 1
}

variable "redis_parameter_group" {
  description = "Redis parameter group"
  type        = string
  default     = "default.redis7"
}

variable "redis_auth_token_enabled" {
  description = "Whether to enable Redis auth token"
  type        = bool
  default     = true
}

variable "redis_snapshot_retention_limit" {
  description = "Redis snapshot retention limit"
  type        = number
  default     = 5
}

variable "redis_snapshot_window" {
  description = "Redis snapshot window"
  type        = string
  default     = "03:00-05:00"
}

# CloudWatch Configuration
variable "sns_topic_arn" {
  description = "SNS topic ARN for alerts"
  type        = string
  default     = ""
}

variable "cloudwatch_alarm_actions" {
  description = "CloudWatch alarm actions"
  type        = list(string)
  default     = []
}

# Lambda Configuration
variable "lambda_functions" {
  description = "Lambda functions configuration"
  type = map(object({
    filename         = string
    function_name    = string
    handler         = string
    runtime         = string
    memory_size     = optional(number, 128)
    timeout         = optional(number, 30)
    environment_vars = optional(map(string), {})
    
    # SQS trigger configuration
    sqs_trigger = optional(object({
      queue_name           = string
      batch_size          = optional(number, 10)
      maximum_batching_window_in_seconds = optional(number, 0)
    }))
  }))
  
  default = {
    "resume-processor" = {
      filename      = "../lambda/resume_processor.zip"
      function_name = "resume-processor"
      handler      = "main.lambda_handler"
      runtime      = "python3.11"
      memory_size  = 512
      timeout      = 300
      
      sqs_trigger = {
        queue_name = "resume-analysis"
        batch_size = 5
      }
    }
  }
}

# Route53 Configuration
variable "create_route53_records" {
  description = "Whether to create Route53 DNS records"
  type        = bool
  default     = false
}

variable "hosted_zone_id" {
  description = "Route53 hosted zone ID"
  type        = string
  default     = ""
}