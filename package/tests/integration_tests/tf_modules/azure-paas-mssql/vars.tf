variable "RESOURCE_GROUP_NAME" {
    type = string
}
variable "LOCATION" {
    type = string
}
variable "SERVER_NAME" {
    type = string
}
variable "SERVER_USERNAME" {
}
variable "SERVER_PASSWORD" {
    sensitive = true
}
variable "DB_NAME" {
}
variable "DB_USERNAME" {
}
variable "DB_PASSWORD" {
    sensitive = true
}

variable "DB_SIZE" {
    description = "Desired Service Level - small (2 v-core) , medium (4), or large (8)"
    default = "small"
    type = string

    validation {
        condition = contains(["small", "medium", "large", "s3", "s4", "s2"], lower(var.DB_SIZE))
        error_message = "Valid Values: small, medium, large."
    }
}

variable "DB_STORAGE" {
    type = number
    default = 50
}

variable "ALLOWED_IPS" {
    description = "List of IPs to be allowed, comma-separated. Example: 192.168.1.1,192.168.1.20,192.168.1.222"
    type = string
}

variable "COLLATION" {
    default = "SQL_LATIN1_GENERAL_CP1_CI_AS"
    type = string
}

variable "RO_PASSWORD" {
    type = string
    sensitive = true
}
variable "RW_PASSWORD" {
    type = string
    sensitive = true
}
variable "O_PASSWORD" {
    type = string
    sensitive = true
}

#TAGS
variable "APP_ID" {
}
variable "APP_OWNER" {
}
variable "APP_NAME" {
}

