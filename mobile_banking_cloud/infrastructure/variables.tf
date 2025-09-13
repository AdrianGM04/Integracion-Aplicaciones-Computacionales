# Variables de configuración para Terraform
# Archivo: variables.tf

variable "aws_region" {
  description = "Región de AWS donde se desplegará la infraestructura"
  type        = string
  default     = "us-east-1"
  
  validation {
    condition = can(regex("^[a-z0-9-]+$", var.aws_region))
    error_message = "La región debe ser válida."
  }
}

variable "environment" {
  description = "Ambiente de despliegue (dev, staging, prod)"
  type        = string
  default     = "dev"
  
  validation {
    condition     = contains(["dev", "staging", "prod"], var.environment)
    error_message = "El ambiente debe ser dev, staging o prod."
  }
}

variable "project_name" {
  description = "Nombre del proyecto para recursos"
  type        = string
  default     = "mobile-banking"
  
  validation {
    condition     = length(var.project_name) >= 3 && length(var.project_name) <= 20
    error_message = "El nombre del proyecto debe tener entre 3 y 20 caracteres."
  }
}

variable "db_password" {
  description = "Contraseña para la base de datos PostgreSQL"
  type        = string
  sensitive   = true
  
  validation {
    condition     = length(var.db_password) >= 8
    error_message = "La contraseña debe tener al menos 8 caracteres."
  }
}

variable "jwt_secret" {
  description = "Secreto para firmar tokens JWT"
  type        = string
  sensitive   = true
  
  validation {
    condition     = length(var.jwt_secret) >= 32
    error_message = "El secreto JWT debe tener al menos 32 caracteres."
  }
}

variable "allowed_cors_origins" {
  description = "Orígenes permitidos para CORS"
  type        = list(string)
  default     = ["*"]
}

variable "backup_retention_days" {
  description = "Días de retención de backups de RDS"
  type        = number
  default     = 7
  
  validation {
    condition     = var.backup_retention_days >= 1 && var.backup_retention_days <= 35
    error_message = "Los días de retención deben estar entre 1 y 35."
  }
}

variable "lambda_timeout" {
  description = "Timeout para funciones Lambda en segundos"
  type        = number
  default     = 30
  
  validation {
    condition     = var.lambda_timeout >= 1 && var.lambda_timeout <= 900
    error_message = "El timeout debe estar entre 1 y 900 segundos."
  }
}

variable "enable_monitoring" {
  description = "Habilitar monitoreo detallado"
  type        = bool
  default     = true
}

variable "enable_encryption" {
  description = "Habilitar encriptación en reposo"
  type        = bool
  default     = true
}

variable "notification_email" {
  description = "Email para notificaciones de sistema"
  type        = string
  default     = ""
  
  validation {
    condition     = var.notification_email == "" || can(regex("^[^@]+@[^@]+\\.[^@]+$", var.notification_email))
    error_message = "El email debe tener un formato válido."
  }
}

variable "log_retention_days" {
  description = "Días de retención de logs en CloudWatch"
  type        = number
  default     = 14
  
  validation {
    condition     = contains([1, 3, 5, 7, 14, 30, 60, 90, 120, 150, 180, 365, 400, 545, 731, 1096, 1827, 3653], var.log_retention_days)
    error_message = "Los días de retención deben ser uno de los valores permitidos por CloudWatch."
  }
}

variable "instance_types" {
  description = "Tipos de instancia para diferentes componentes"
  type = object({
    rds_instance_class    = string
    redis_node_type       = string
    lambda_memory_size    = number
  })
  default = {
    rds_instance_class = "db.t3.micro"
    redis_node_type    = "cache.t3.micro"
    lambda_memory_size = 256
  }
}

variable "scaling_config" {
  description = "Configuración de escalado automático"
  type = object({
    min_capacity = number
    max_capacity = number
    target_utilization = number
  })
  default = {
    min_capacity = 1
    max_capacity = 10
    target_utilization = 70
  }
}

variable "security_groups_rules" {
  description = "Reglas adicionales para security groups"
  type = list(object({
    type        = string
    from_port   = number
    to_port     = number
    protocol    = string
    cidr_blocks = list(string)
    description = string
  }))
  default = []
}

variable "tags" {
  description = "Tags adicionales para todos los recursos"
  type        = map(string)
  default     = {}
}


