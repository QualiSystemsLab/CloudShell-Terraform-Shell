output "DB_HOSTNAME" {
  value = azurerm_mssql_server.default.fully_qualified_domain_name
}
output "DB_USER" {
  value = var.DB_USERNAME
}
output "DB_NAME" {
  value = var.DB_NAME
}
