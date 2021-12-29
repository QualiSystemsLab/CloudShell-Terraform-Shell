terraform {
  required_providers {
    azurerm = {
      version = "2.61"
    }
  }
}

provider azurerm {
  features {}
}

locals {
  sizeMap = { 
    "small" = "GP_Gen5_2",
    "medium" = "GP_GEN5_4",
    "large" = "GP_GEN5_8",
    "extra-large" = "GP_GEN5_16",
    "s2" = "S2",
    "s3" = "S3",
    "s4" = "S4"
  }

  mgmtServer1 = "165.204.84.17" 
  mgmtServer2 = "165.204.88.17"
  listOfIps = var.ALLOWED_IPS
  ipList = compact(split(",", var.ALLOWED_IPS))

  sanitizedRG = replace(var.RESOURCE_GROUP_NAME, "_", "") #Server Name cannot contain anything other than letters, numbers, and hyphens
  serverName = lower("${var.SERVER_NAME}-${local.sanitizedRG}")

  customTags = {
    "APPID" = var.APP_ID,
    "APPLICATION OWNER" = var.APP_OWNER,
    "APPLICATION NAME" = var.APP_NAME
  }
}

resource "azurerm_mssql_server" "default" {
  name                         = local.serverName
  resource_group_name          = var.RESOURCE_GROUP_NAME
  location                     = var.LOCATION
  version                      = "12.0"
  public_network_access_enabled = true
  administrator_login          = var.SERVER_USERNAME
  administrator_login_password = var.SERVER_PASSWORD

  azuread_administrator {
    login_username = "ITDBA Admin"
    object_id = "ed6204e1-a9c4-408c-bb5e-bcc0d076b3bd"
    tenant_id = "3dd8961f-e488-4e60-8e11-a82d994e183d"
  }
}

resource "azurerm_sql_firewall_rule" "ip_list" {
  for_each            = { for x in local.ipList : x => x }
  name                = "${each.key}-Requested-IP-Allowance"
  resource_group_name = var.RESOURCE_GROUP_NAME
  server_name         = azurerm_mssql_server.default.name
  start_ip_address    = trimspace(each.key)
  end_ip_address      = trimspace(each.key)
  depends_on = [ azurerm_mssql_server.default ]
}

resource "azurerm_sql_firewall_rule" "allow_controlserver_one" {
  name                = "Allow-Control-Server"
  resource_group_name = var.RESOURCE_GROUP_NAME
  server_name         = azurerm_mssql_server.default.name
  start_ip_address    = local.mgmtServer1
  end_ip_address      = local.mgmtServer1
  depends_on = [ azurerm_mssql_server.default ]
}

resource "azurerm_sql_firewall_rule" "allow_controlserver_two" {
  name                = "Allow-ControlServer-2"
  resource_group_name = var.RESOURCE_GROUP_NAME
  server_name         = azurerm_mssql_server.default.name
  start_ip_address    = local.mgmtServer2
  end_ip_address      = local.mgmtServer2
  depends_on = [ azurerm_mssql_server.default ]
}

resource "azurerm_sql_firewall_rule" "allow_azure_services" {
  name                = "AllowAzureServices"
  resource_group_name = var.RESOURCE_GROUP_NAME
  server_name         = azurerm_mssql_server.default.name
  start_ip_address    = "0.0.0.0"
  end_ip_address      = "0.0.0.0"
  depends_on = [ azurerm_mssql_server.default ]
}

resource "azurerm_mssql_database" "default" {
  name                = var.DB_NAME
  server_id           = azurerm_mssql_server.default.id
  sku_name            = lookup(local.sizeMap, lower(var.DB_SIZE), "GP_Gen5_2")
  create_mode         = "Default"
  collation           = var.COLLATION
  max_size_gb         = var.DB_STORAGE
  depends_on = [ azurerm_mssql_server.default ]

  short_term_retention_policy {
    retention_days = 35
  }
  
  tags = merge(local.customTags)
}

/* Commented out while we are deciding on proper password handling procedures
resource "random_password" "RO_PASSWORD" { 
  length = 24
  special = true
  override_special = "_%@"
  min_special = 1
  min_lower = 1
  min_upper = 1
  min_numeric = 1
}

resource "random_password" "RW_PASSWORD" { 
  length = 24
  special = true
  override_special = "_%@"
  min_special = 1
  min_lower = 1
  min_upper = 1
  min_numeric = 1
}

resource "random_password" "WO_PASSWORD" { 
  length = 24
  special = true
  override_special = "_%@"
  min_special = 1
  min_lower = 1
  min_upper = 1
  min_numeric = 1
}
*/

# resource "null_resource" "addUsers" {
#   depends_on = [ azurerm_mssql_database.default ]

#   provisioner "local-exec" {
#     on_failure = fail
#     command = "chmod +x runSQLCMD.sh && ./runSQLCMD.sh ${var.DB_PASSWORD} ${var.RO_PASSWORD} ${var.RW_PASSWORD}"
#     interpreter = ["/bin/bash", "-c"]

#     environment = {
#       FQDN = azurerm_mssql_server.default.fully_qualified_domain_name
#       SERVER_USERNAME = var.SERVER_USERNAME
#       SERVER_PASSWORD = var.SERVER_PASSWORD
#       DB_NAME = var.DB_NAME
#       DB_USER = var.DB_USERNAME
#       // DB_PASSWORD = var.DB_PASSWORD
#       RO_USER = "${var.APP_NAME}_RO"
#       RW_USER = "${var.APP_NAME}_RW"
#       O_USER = "${var.APP_NAME}_O"
#       RO_PASS = var.RO_PASSWORD
#       RW_PASS = var.RW_PASSWORD
#       O_PASS = var.O_PASSWORD
#     }
#   }
# }


output "DB_HOSTNAME" {
  value = azurerm_mssql_server.default.fully_qualified_domain_name
}
output "DB_USER" {
  value = var.DB_USERNAME
}
output "DB_NAME" {
  value = var.DB_NAME
}
