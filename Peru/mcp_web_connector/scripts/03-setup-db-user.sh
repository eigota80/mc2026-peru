#!/usr/bin/env bash
# =============================================================================
# Script: 03-setup-db-user.sh
# Ejecutar como: root en el servidor 179.43.82.54
# Proposito: Crear usuario MariaDB de solo lectura para mcp-agent
#            El agente NUNCA tiene acceso total a la base de datos
# =============================================================================
set -euo pipefail

DB_NAME="bdmcperu"
DB_AGENT_USER="mcp_agent_ro"
DB_AGENT_PASS=$(openssl rand -base64 24 | tr -d "=+/" | cut -c1-20)
LOG="/var/log/mcp-agent/db-setup.log"

echo "============================================================"
echo " Configurando usuario MariaDB de solo lectura para mcp-agent"
echo "============================================================"

# Guardar la password generada en archivo seguro fuera del repositorio
mkdir -p /etc/mcp-agent
cat > /etc/mcp-agent/db.env << DBENV
MCP_AGENT_DB_USER=$DB_AGENT_USER
MCP_AGENT_DB_PASS=$DB_AGENT_PASS
MCP_AGENT_DB_NAME=$DB_NAME
MCP_AGENT_DB_HOST=127.0.0.1
DBENV
chmod 600 /etc/mcp-agent/db.env
chown root:root /etc/mcp-agent/db.env
echo "  ✓ Credenciales guardadas en /etc/mcp-agent/db.env (solo root)"

# Ejecutar SQL para crear el usuario restringido
mysql -u root << SQL
-- Crear usuario solo-lectura para mcp-agent
CREATE USER IF NOT EXISTS '$DB_AGENT_USER'@'localhost'
    IDENTIFIED BY '$DB_AGENT_PASS';

-- Solo SELECT en la base del proyecto — nunca INSERT/UPDATE/DELETE
GRANT SELECT ON $DB_NAME.* TO '$DB_AGENT_USER'@'localhost';

-- Revocar explicitamente cualquier permiso de escritura
REVOKE ALL PRIVILEGES ON *.* FROM '$DB_AGENT_USER'@'localhost';
GRANT SELECT ON $DB_NAME.* TO '$DB_AGENT_USER'@'localhost';

-- Aplicar cambios
FLUSH PRIVILEGES;

-- Verificar
SHOW GRANTS FOR '$DB_AGENT_USER'@'localhost';
SQL

echo "  ✓ Usuario MariaDB '$DB_AGENT_USER' creado con permisos SELECT unicamente"
echo ""
echo "============================================================"
echo " Permisos configurados en MariaDB:"
echo "============================================================"
mysql -u root -e "SHOW GRANTS FOR '$DB_AGENT_USER'@'localhost';" 2>/dev/null

echo ""
echo "============================================================"
echo " Para usar las credenciales desde el MCP connector:"
echo "============================================================"
echo ""
echo "  Carga /etc/mcp-agent/db.env en tu .env del conector:"
echo "  source /etc/mcp-agent/db.env"
echo ""
echo "  O copia los valores manualmente al .env del proyecto:"
echo "  MCP_WEB_DB_USER=$DB_AGENT_USER"
echo "  MCP_WEB_DB_PASSWORD=[ver /etc/mcp-agent/db.env]"
echo ""
echo "  NUNCA pongas la password en el repositorio git."
echo ""

# Registrar en el log de auditoria
echo "$(date '+%Y-%m-%d %H:%M:%S') DB_USER_CREATED user=$DB_AGENT_USER db=$DB_NAME perms=SELECT" \
    >> "$LOG" 2>/dev/null || true
