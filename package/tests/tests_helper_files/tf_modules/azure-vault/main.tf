terraform {
  required_providers {
    azurerm = {
      source  = "hashicorp/azurerm"
      version = "=2.46.0"
    }
  }
}

provider "azurerm" {
  features {}
}

data "azurerm_key_vault" "keyvault" {
  name                = var.KEYVAULT_NAME
  resource_group_name = var.KEYVAULT_RG
}

data "azurerm_key_vault_secret" "keyvault_get" {
  name         = var.SECRET_NAME
  key_vault_id = data.azurerm_key_vault.keyvault.id
}

output "SECRET_VALUE"{
  value = data.azurerm_key_vault_secret.keyvault_get.value
  sensitive = true
}

output "SECRET_VALUE_2" {
  value = "my_secret"
  sensitive = true
}

output "BLA1" {
  value = "bla1"
}
output "BLA2" {
  value = "bla2"
}