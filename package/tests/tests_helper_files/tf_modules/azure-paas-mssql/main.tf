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
