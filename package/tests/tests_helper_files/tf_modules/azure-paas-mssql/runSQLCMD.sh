apt install gnupg -y

curl https://packages.microsoft.com/keys/microsoft.asc | apt-key add -
curl https://packages.microsoft.com/config/debian/10/prod.list | tee /etc/apt/sources.list.d/msprod.list


apt update

export ACCEPT_EULA=y 
export DEBIAN_FRONTEND=noninteractive
apt-get install -y --no-install-recommends mssql-tools unixodbc-dev

export PATH=$PATH:/opt/mssql-tools/bin

#We create the query like this because sqlcmd on Debian 10 does not support -v
cat << EOF > addUsers.sql
CREATE USER [$O_USER] WITH PASSWORD = "$O_PASS" , DEFAULT_SCHEMA = dbo; 
ALTER ROLE db_owner ADD MEMBER [$O_USER]; 
GO

CREATE USER [$RO_USER] WITH PASSWORD = "$RO_PASS" , DEFAULT_SCHEMA = dbo; 
ALTER ROLE db_datareader ADD MEMBER [$RO_USER]; 
GO

CREATE USER [$RW_USER] WITH PASSWORD = "$RW_PASS" , DEFAULT_SCHEMA = dbo; 
ALTER ROLE db_datawriter ADD MEMBER [$RW_USER];
GO

CREATE USER [$DB_USER] WITH PASSWORD = "$DB_PASS" , DEFAULT_SCHEMA = dbo;
ALTER ROLE db_owner ADD MEMBER [$DB_USER]
GO
EOF

sqlcmd -C -S $FQDN -d $DB_NAME -U $SERVER_USERNAME -P $SERVER_PASSWORD -i addUsers.sql 