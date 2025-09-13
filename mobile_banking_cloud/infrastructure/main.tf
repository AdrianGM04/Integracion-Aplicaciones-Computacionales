# Configuración de infraestructura para aplicación de banca móvil
# Arquitectura híbrida con AWS y componentes serverless

terraform {
  required_version = ">= 1.0"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
  
  backend "s3" {
    bucket = "mobile-banking-terraform-state"
    key    = "infrastructure/terraform.tfstate"
    region = "us-east-1"
  }
}

# Configuración del proveedor AWS
provider "aws" {
  region = var.aws_region
  
  default_tags {
    tags = {
      Project     = "Mobile Banking Cloud"
      Environment = var.environment
      ManagedBy   = "Terraform"
    }
  }
}

# Variables
variable "aws_region" {
  description = "Región de AWS"
  type        = string
  default     = "us-east-1"
}

variable "environment" {
  description = "Ambiente de despliegue"
  type        = string
  default     = "dev"
}

variable "project_name" {
  description = "Nombre del proyecto"
  type        = string
  default     = "mobile-banking"
}

# VPC y Networking
resource "aws_vpc" "main" {
  cidr_block           = "10.0.0.0/16"
  enable_dns_hostnames = true
  enable_dns_support   = true

  tags = {
    Name = "${var.project_name}-vpc"
  }
}

resource "aws_internet_gateway" "main" {
  vpc_id = aws_vpc.main.id

  tags = {
    Name = "${var.project_name}-igw"
  }
}

resource "aws_subnet" "public" {
  count = 2

  vpc_id                  = aws_vpc.main.id
  cidr_block              = "10.0.${count.index + 1}.0/24"
  availability_zone       = data.aws_availability_zones.available.names[count.index]
  map_public_ip_on_launch = true

  tags = {
    Name = "${var.project_name}-public-subnet-${count.index + 1}"
  }
}

resource "aws_subnet" "private" {
  count = 2

  vpc_id            = aws_vpc.main.id
  cidr_block        = "10.0.${count.index + 10}.0/24"
  availability_zone = data.aws_availability_zones.available.names[count.index]

  tags = {
    Name = "${var.project_name}-private-subnet-${count.index + 1}"
  }
}

data "aws_availability_zones" "available" {
  state = "available"
}

# Security Groups
resource "aws_security_group" "lambda" {
  name_prefix = "${var.project_name}-lambda-"
  vpc_id      = aws_vpc.main.id

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name = "${var.project_name}-lambda-sg"
  }
}

resource "aws_security_group" "rds" {
  name_prefix = "${var.project_name}-rds-"
  vpc_id      = aws_vpc.main.id

  ingress {
    from_port       = 5432
    to_port         = 5432
    protocol        = "tcp"
    security_groups = [aws_security_group.lambda.id]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name = "${var.project_name}-rds-sg"
  }
}

# DynamoDB Tables
resource "aws_dynamodb_table" "users" {
  name           = "${var.project_name}-users"
  billing_mode   = "PAY_PER_REQUEST"
  hash_key       = "username"

  attribute {
    name = "username"
    type = "S"
  }

  attribute {
    name = "user_id"
    type = "S"
  }

  global_secondary_index {
    name     = "user-id-index"
    hash_key = "user_id"
  }

  tags = {
    Name = "${var.project_name}-users-table"
  }
}

resource "aws_dynamodb_table" "sessions" {
  name           = "${var.project_name}-sessions"
  billing_mode   = "PAY_PER_REQUEST"
  hash_key       = "session_id"

  attribute {
    name = "session_id"
    type = "S"
  }

  attribute {
    name = "user_id"
    type = "S"
  }

  global_secondary_index {
    name     = "user-id-index"
    hash_key = "user_id"
  }

  ttl {
    attribute_name = "ttl"
    enabled        = true
  }

  tags = {
    Name = "${var.project_name}-sessions-table"
  }
}

resource "aws_dynamodb_table" "accounts" {
  name           = "${var.project_name}-accounts"
  billing_mode   = "PAY_PER_REQUEST"
  hash_key       = "account_id"

  attribute {
    name = "account_id"
    type = "S"
  }

  tags = {
    Name = "${var.project_name}-accounts-table"
  }
}

resource "aws_dynamodb_table" "transactions" {
  name           = "${var.project_name}-transactions"
  billing_mode   = "PAY_PER_REQUEST"
  hash_key       = "transaction_id"

  attribute {
    name = "transaction_id"
    type = "S"
  }

  attribute {
    name = "from_account"
    type = "S"
  }

  global_secondary_index {
    name     = "from-account-index"
    hash_key = "from_account"
  }

  tags = {
    Name = "${var.project_name}-transactions-table"
  }
}

resource "aws_dynamodb_table" "balances" {
  name           = "${var.project_name}-balances"
  billing_mode   = "PAY_PER_REQUEST"
  hash_key       = "account_id"

  attribute {
    name = "account_id"
    type = "S"
  }

  tags = {
    Name = "${var.project_name}-balances-table"
  }
}

resource "aws_dynamodb_table" "notifications" {
  name           = "${var.project_name}-notifications"
  billing_mode   = "PAY_PER_REQUEST"
  hash_key       = "notification_id"

  attribute {
    name = "notification_id"
    type = "S"
  }

  attribute {
    name = "user_id"
    type = "S"
  }

  global_secondary_index {
    name     = "user-id-index"
    hash_key = "user_id"
  }

  tags = {
    Name = "${var.project_name}-notifications-table"
  }
}

resource "aws_dynamodb_table" "audit_logs" {
  name           = "${var.project_name}-audit-logs"
  billing_mode   = "PAY_PER_REQUEST"
  hash_key       = "audit_id"

  attribute {
    name = "audit_id"
    type = "S"
  }

  attribute {
    name = "user_id"
    type = "S"
  }

  global_secondary_index {
    name     = "user-id-index"
    hash_key = "user_id"
  }

  tags = {
    Name = "${var.project_name}-audit-logs-table"
  }
}

resource "aws_dynamodb_table" "user_preferences" {
  name           = "${var.project_name}-user-preferences"
  billing_mode   = "PAY_PER_REQUEST"
  hash_key       = "user_id"

  attribute {
    name = "user_id"
    type = "S"
  }

  tags = {
    Name = "${var.project_name}-user-preferences-table"
  }
}

# RDS PostgreSQL Database
resource "aws_db_subnet_group" "main" {
  name       = "${var.project_name}-db-subnet-group"
  subnet_ids = aws_subnet.private[*].id

  tags = {
    Name = "${var.project_name}-db-subnet-group"
  }
}

resource "aws_db_instance" "main" {
  identifier = "${var.project_name}-db"

  engine         = "postgres"
  engine_version = "15.4"
  instance_class = "db.t3.micro"

  allocated_storage     = 20
  max_allocated_storage = 100
  storage_type          = "gp2"
  storage_encrypted     = true

  db_name  = "mobilebanking"
  username = "dbadmin"
  password = var.db_password

  vpc_security_group_ids = [aws_security_group.rds.id]
  db_subnet_group_name   = aws_db_subnet_group.main.name

  backup_retention_period = 7
  backup_window          = "03:00-04:00"
  maintenance_window     = "sun:04:00-sun:05:00"

  skip_final_snapshot = var.environment == "dev" ? true : false
  deletion_protection = var.environment == "prod" ? true : false

  tags = {
    Name = "${var.project_name}-database"
  }
}

variable "db_password" {
  description = "Contraseña de la base de datos"
  type        = string
  sensitive   = true
}

# ElastiCache Redis
resource "aws_elasticache_subnet_group" "main" {
  name       = "${var.project_name}-cache-subnet"
  subnet_ids = aws_subnet.private[*].id
}

resource "aws_elasticache_replication_group" "main" {
  replication_group_id       = "${var.project_name}-redis"
  description                = "Redis cluster for mobile banking"

  node_type                  = "cache.t3.micro"
  port                       = 6379
  parameter_group_name       = "default.redis7"

  num_cache_clusters         = 2
  automatic_failover_enabled = true
  multi_az_enabled          = true

  subnet_group_name = aws_elasticache_subnet_group.main.name
  security_group_ids = [aws_security_group.redis.id]

  at_rest_encryption_enabled = true
  transit_encryption_enabled = true

  tags = {
    Name = "${var.project_name}-redis"
  }
}

resource "aws_security_group" "redis" {
  name_prefix = "${var.project_name}-redis-"
  vpc_id      = aws_vpc.main.id

  ingress {
    from_port       = 6379
    to_port         = 6379
    protocol        = "tcp"
    security_groups = [aws_security_group.lambda.id]
  }

  tags = {
    Name = "${var.project_name}-redis-sg"
  }
}

# SQS Queues
resource "aws_sqs_queue" "transaction_queue" {
  name                      = "${var.project_name}-transaction-queue"
  delay_seconds             = 0
  max_message_size          = 262144
  message_retention_seconds = 1209600
  receive_wait_time_seconds = 10

  tags = {
    Name = "${var.project_name}-transaction-queue"
  }
}

resource "aws_sqs_queue" "notification_queue" {
  name                      = "${var.project_name}-notification-queue"
  delay_seconds             = 0
  max_message_size          = 262144
  message_retention_seconds = 1209600
  receive_wait_time_seconds = 10

  tags = {
    Name = "${var.project_name}-notification-queue"
  }
}

resource "aws_sqs_queue" "audit_queue" {
  name                      = "${var.project_name}-audit-queue"
  delay_seconds             = 0
  max_message_size          = 262144
  message_retention_seconds = 1209600
  receive_wait_time_seconds = 10

  tags = {
    Name = "${var.project_name}-audit-queue"
  }
}

# SNS Topics
resource "aws_sns_topic" "push_notifications" {
  name = "${var.project_name}-push-notifications"

  tags = {
    Name = "${var.project_name}-push-notifications"
  }
}

resource "aws_sns_topic" "email_notifications" {
  name = "${var.project_name}-email-notifications"

  tags = {
    Name = "${var.project_name}-email-notifications"
  }
}

# API Gateway
resource "aws_api_gateway_rest_api" "main" {
  name        = "${var.project_name}-api"
  description = "API Gateway for Mobile Banking Application"

  endpoint_configuration {
    types = ["REGIONAL"]
  }

  tags = {
    Name = "${var.project_name}-api-gateway"
  }
}

resource "aws_api_gateway_deployment" "main" {
  rest_api_id = aws_api_gateway_rest_api.main.id
  stage_name  = var.environment

  depends_on = [
    aws_api_gateway_method.auth_login,
    aws_api_gateway_method.banking_balance,
    aws_api_gateway_method.notifications_send
  ]
}

# Lambda Functions
resource "aws_lambda_function" "auth" {
  filename         = "functions/auth_lambda.zip"
  function_name    = "${var.project_name}-auth"
  role            = aws_iam_role.lambda_role.arn
  handler         = "auth_lambda.lambda_handler"
  runtime         = "python3.9"
  timeout         = 30

  environment {
    variables = {
      USERS_TABLE     = aws_dynamodb_table.users.name
      SESSIONS_TABLE  = aws_dynamodb_table.sessions.name
      JWT_SECRET      = var.jwt_secret
    }
  }

  vpc_config {
    subnet_ids         = aws_subnet.private[*].id
    security_group_ids = [aws_security_group.lambda.id]
  }

  tags = {
    Name = "${var.project_name}-auth-lambda"
  }
}

resource "aws_lambda_function" "banking" {
  filename         = "functions/banking_lambda.zip"
  function_name    = "${var.project_name}-banking"
  role            = aws_iam_role.lambda_role.arn
  handler         = "banking_lambda.lambda_handler"
  runtime         = "python3.9"
  timeout         = 30

  environment {
    variables = {
      ACCOUNTS_TABLE      = aws_dynamodb_table.accounts.name
      TRANSACTIONS_TABLE  = aws_dynamodb_table.transactions.name
      BALANCES_TABLE      = aws_dynamodb_table.balances.name
      TRANSACTION_QUEUE_URL = aws_sqs_queue.transaction_queue.url
      NOTIFICATION_QUEUE_URL = aws_sqs_queue.notification_queue.url
    }
  }

  vpc_config {
    subnet_ids         = aws_subnet.private[*].id
    security_group_ids = [aws_security_group.lambda.id]
  }

  tags = {
    Name = "${var.project_name}-banking-lambda"
  }
}

resource "aws_lambda_function" "notifications" {
  filename         = "functions/notifications_lambda.zip"
  function_name    = "${var.project_name}-notifications"
  role            = aws_iam_role.lambda_role.arn
  handler         = "notifications_lambda.lambda_handler"
  runtime         = "python3.9"
  timeout         = 30

  environment {
    variables = {
      NOTIFICATIONS_TABLE    = aws_dynamodb_table.notifications.name
      AUDIT_LOGS_TABLE       = aws_dynamodb_table.audit_logs.name
      USER_PREFERENCES_TABLE = aws_dynamodb_table.user_preferences.name
      NOTIFICATION_QUEUE_URL = aws_sqs_queue.notification_queue.url
      AUDIT_QUEUE_URL        = aws_sqs_queue.audit_queue.url
      PUSH_NOTIFICATION_TOPIC = aws_sns_topic.push_notifications.arn
      EMAIL_NOTIFICATION_TOPIC = aws_sns_topic.email_notifications.arn
    }
  }

  vpc_config {
    subnet_ids         = aws_subnet.private[*].id
    security_group_ids = [aws_security_group.lambda.id]
  }

  tags = {
    Name = "${var.project_name}-notifications-lambda"
  }
}

variable "jwt_secret" {
  description = "Secreto para JWT"
  type        = string
  sensitive   = true
}

# IAM Roles
resource "aws_iam_role" "lambda_role" {
  name = "${var.project_name}-lambda-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "lambda.amazonaws.com"
        }
      }
    ]
  })
}

resource "aws_iam_role_policy" "lambda_policy" {
  name = "${var.project_name}-lambda-policy"
  role = aws_iam_role.lambda_role.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "logs:CreateLogGroup",
          "logs:CreateLogStream",
          "logs:PutLogEvents"
        ]
        Resource = "arn:aws:logs:*:*:*"
      },
      {
        Effect = "Allow"
        Action = [
          "dynamodb:GetItem",
          "dynamodb:PutItem",
          "dynamodb:UpdateItem",
          "dynamodb:DeleteItem",
          "dynamodb:Query",
          "dynamodb:Scan"
        ]
        Resource = [
          aws_dynamodb_table.users.arn,
          aws_dynamodb_table.sessions.arn,
          aws_dynamodb_table.accounts.arn,
          aws_dynamodb_table.transactions.arn,
          aws_dynamodb_table.balances.arn,
          aws_dynamodb_table.notifications.arn,
          aws_dynamodb_table.audit_logs.arn,
          aws_dynamodb_table.user_preferences.arn
        ]
      },
      {
        Effect = "Allow"
        Action = [
          "sqs:SendMessage",
          "sqs:ReceiveMessage",
          "sqs:DeleteMessage",
          "sqs:GetQueueAttributes"
        ]
        Resource = [
          aws_sqs_queue.transaction_queue.arn,
          aws_sqs_queue.notification_queue.arn,
          aws_sqs_queue.audit_queue.arn
        ]
      },
      {
        Effect = "Allow"
        Action = [
          "sns:Publish"
        ]
        Resource = [
          aws_sns_topic.push_notifications.arn,
          aws_sns_topic.email_notifications.arn
        ]
      },
      {
        Effect = "Allow"
        Action = [
          "ec2:CreateNetworkInterface",
          "ec2:DescribeNetworkInterfaces",
          "ec2:DeleteNetworkInterface"
        ]
        Resource = "*"
      }
    ]
  })
}

# CloudWatch Log Groups
resource "aws_cloudwatch_log_group" "auth_lambda" {
  name              = "/aws/lambda/${aws_lambda_function.auth.function_name}"
  retention_in_days = 14
}

resource "aws_cloudwatch_log_group" "banking_lambda" {
  name              = "/aws/lambda/${aws_lambda_function.banking.function_name}"
  retention_in_days = 14
}

resource "aws_cloudwatch_log_group" "notifications_lambda" {
  name              = "/aws/lambda/${aws_lambda_function.notifications.function_name}"
  retention_in_days = 14
}

# Outputs
output "api_gateway_url" {
  description = "URL del API Gateway"
  value       = "https://${aws_api_gateway_rest_api.main.id}.execute-api.${var.aws_region}.amazonaws.com/${var.environment}"
}

output "database_endpoint" {
  description = "Endpoint de la base de datos RDS"
  value       = aws_db_instance.main.endpoint
  sensitive   = true
}

output "redis_endpoint" {
  description = "Endpoint de Redis"
  value       = aws_elasticache_replication_group.main.primary_endpoint_address
}

output "vpc_id" {
  description = "ID de la VPC"
  value       = aws_vpc.main.id
}


