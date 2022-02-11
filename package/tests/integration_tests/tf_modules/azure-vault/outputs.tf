output "SECRET_VALUE"{
  value = data.azurerm_key_vault_secret.keyvault_get.value
  sensitive = true
}

### mock outputs for testing
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