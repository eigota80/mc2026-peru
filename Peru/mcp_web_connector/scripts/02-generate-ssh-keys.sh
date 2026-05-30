#!/usr/bin/env bash
# =============================================================================
# Script: 02-generate-ssh-keys.sh
# Ejecutar como: USUARIO LOCAL en tu Mac (no en el servidor)
# Proposito: Generar par de claves SSH RSA para el mcp-agent
# =============================================================================
set -euo pipefail

KEY_NAME="${KEY_NAME:-mcp-agent-mcperu-rsa}"
KEY_DIR="$HOME/.ssh/mc2026"
KEY_BITS="${KEY_BITS:-4096}"
SERVER="179.43.82.54"
SERVER_USER="mcp-agent"

echo "============================================================"
echo " Generando SSH Key RSA para mcp-agent"
echo "============================================================"

mkdir -p "$KEY_DIR"
chmod 700 "$KEY_DIR"

if [ -f "$KEY_DIR/$KEY_NAME" ]; then
    echo "  La clave $KEY_NAME ya existe en $KEY_DIR"
    echo "  Para regenerarla: rm $KEY_DIR/$KEY_NAME $KEY_DIR/$KEY_NAME.pub"
    echo ""
else
    ssh-keygen \
        -t rsa \
        -b "$KEY_BITS" \
        -o \
        -a 100 \
        -C "mcp-agent-rsa@mcperu.pe-$(date +%Y%m%d)" \
        -f "$KEY_DIR/$KEY_NAME" \
        -N "${KEY_PASSPHRASE:-}"

    chmod 600 "$KEY_DIR/$KEY_NAME"
    chmod 644 "$KEY_DIR/$KEY_NAME.pub"
    echo "  ✓ Clave privada: $KEY_DIR/$KEY_NAME"
    echo "  ✓ Clave publica: $KEY_DIR/$KEY_NAME.pub"
fi

echo ""
echo "============================================================"
echo " Clave publica a instalar en el servidor:"
echo "============================================================"
cat "$KEY_DIR/$KEY_NAME.pub"

echo ""
echo "============================================================"
echo " PASOS PARA INSTALAR LA CLAVE EN EL SERVIDOR:"
echo "============================================================"
echo ""
echo "1. Conectate al servidor como root:"
echo "   ssh root@$SERVER"
echo ""
echo "2. Pega la clave publica en authorized_keys del agente:"
echo "   echo '$(cat $KEY_DIR/$KEY_NAME.pub)' >> /home/$SERVER_USER/.ssh/authorized_keys"
echo ""
echo "3. Verifica permisos:"
echo "   chmod 600 /home/$SERVER_USER/.ssh/authorized_keys"
echo "   chown $SERVER_USER:$SERVER_USER /home/$SERVER_USER/.ssh/authorized_keys"
echo ""
echo "4. Prueba la conexion (desde tu Mac):"
echo "   ssh -i $KEY_DIR/$KEY_NAME $SERVER_USER@$SERVER"
echo ""

# Crear config SSH en el Mac para facilitar la conexion
SSH_CONFIG="$HOME/.ssh/config"

touch "$SSH_CONFIG"
chmod 600 "$SSH_CONFIG"

if grep -qE '^Host[[:space:]]+mcperu-agent$' "$SSH_CONFIG" 2>/dev/null; then
    BACKUP="$SSH_CONFIG.backup.$(date +%Y%m%d%H%M%S)"
    cp "$SSH_CONFIG" "$BACKUP"
    awk '
        /^Host[[:space:]]+mcperu-agent$/ { skip = 1; next }
        /^Host[[:space:]]+/ { skip = 0 }
        !skip { print }
    ' "$BACKUP" > "$SSH_CONFIG"
    echo "  Entrada anterior mcperu-agent respaldada en: $BACKUP"
fi

cat >> "$SSH_CONFIG" << SSHCONF

Host mcperu-agent
    HostName $SERVER
    User $SERVER_USER
    IdentityFile $KEY_DIR/$KEY_NAME
    IdentitiesOnly yes
    ServerAliveInterval 60
    ServerAliveCountMax 3
    StrictHostKeyChecking accept-new
SSHCONF
chmod 600 "$SSH_CONFIG"
echo "  ✓ Entrada agregada a ~/.ssh/config"
echo "     Ahora puedes conectarte con: ssh mcperu-agent"

echo ""
echo "============================================================"
echo " GITHUB ACTIONS SECRET"
echo "============================================================"
echo ""
echo "Para que GitHub Actions use esta clave, agrega el contenido"
echo "de la clave PRIVADA como secret en GitHub."
echo "Por seguridad, este script no imprime la clave privada."
echo ""
echo "  Nombre del secret: MCP_AGENT_SSH_PRIVATE_KEY"
echo "  Archivo local: $KEY_DIR/$KEY_NAME"
echo ""
echo "  En GitHub: Settings → Secrets → Actions → New repository secret"
echo ""
