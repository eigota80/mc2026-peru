#!/usr/bin/env bash
# =============================================================================
# Script: 07-install-rsa-public-key.sh
# Ejecutar como: root en el servidor 179.43.82.54
# Proposito: Instalar una clave publica RSA para mcp-agent en authorized_keys.
#
# Uso recomendado:
#   PUBLIC_KEY_FILE=/tmp/id_rsa.pub bash 07-install-rsa-public-key.sh
#
# Para dejar SOLO esa clave autorizada (reemplaza authorized_keys con backup):
#   REPLACE_AUTHORIZED_KEYS=1 PUBLIC_KEY_FILE=/tmp/id_rsa.pub bash 07-install-rsa-public-key.sh
# =============================================================================
set -euo pipefail

AGENT_USER="${AGENT_USER:-mcp-agent}"
AGENT_HOME="${AGENT_HOME:-/home/$AGENT_USER}"
SSH_DIR="$AGENT_HOME/.ssh"
AUTHORIZED_KEYS="$SSH_DIR/authorized_keys"
PUBLIC_KEY_FILE="${PUBLIC_KEY_FILE:-}"
PUBLIC_KEY_TEXT="${PUBLIC_KEY_TEXT:-}"
REPLACE_AUTHORIZED_KEYS="${REPLACE_AUTHORIZED_KEYS:-0}"

echo "============================================================"
echo " Instalando clave publica RSA para $AGENT_USER"
echo "============================================================"

if ! id "$AGENT_USER" >/dev/null 2>&1; then
    echo "ERROR: el usuario $AGENT_USER no existe. Ejecuta primero 01-setup-mcp-agent-user.sh"
    exit 1
fi

AGENT_GROUP="$(id -gn "$AGENT_USER")"

if [ -n "$PUBLIC_KEY_TEXT" ]; then
    KEY_LINE="$PUBLIC_KEY_TEXT"
elif [ -n "$PUBLIC_KEY_FILE" ] && [ -f "$PUBLIC_KEY_FILE" ]; then
    KEY_LINE="$(sed -n '1p' "$PUBLIC_KEY_FILE" | tr -d '\r\n')"
else
    echo "ERROR: define PUBLIC_KEY_FILE=/ruta/id_rsa.pub o PUBLIC_KEY_TEXT='ssh-rsa ...'"
    exit 1
fi

case "$KEY_LINE" in
    ssh-rsa\ *) ;;
    *)
        echo "ERROR: la clave publica debe iniciar con 'ssh-rsa'."
        exit 1
        ;;
esac

mkdir -p "$SSH_DIR"
chmod 700 "$SSH_DIR"
touch "$AUTHORIZED_KEYS"
chmod 600 "$AUTHORIZED_KEYS"
chown -R "$AGENT_USER:$AGENT_GROUP" "$SSH_DIR"

if [ "$REPLACE_AUTHORIZED_KEYS" = "1" ]; then
    BACKUP="$AUTHORIZED_KEYS.backup.$(date +%Y%m%d%H%M%S)"
    cp "$AUTHORIZED_KEYS" "$BACKUP"
    printf '%s\n' "$KEY_LINE" > "$AUTHORIZED_KEYS"
    echo "  authorized_keys reemplazado. Backup: $BACKUP"
elif grep -qxF "$KEY_LINE" "$AUTHORIZED_KEYS"; then
    echo "  La clave ya estaba instalada."
else
    printf '%s\n' "$KEY_LINE" >> "$AUTHORIZED_KEYS"
    echo "  Clave agregada a authorized_keys."
fi

chmod 600 "$AUTHORIZED_KEYS"
chown "$AGENT_USER:$AGENT_GROUP" "$AUTHORIZED_KEYS"
passwd -l "$AGENT_USER" >/dev/null 2>&1 || true

echo ""
echo "Fingerprint instalado:"
if command -v ssh-keygen >/dev/null 2>&1; then
    TMP_KEY="$(mktemp)"
    printf '%s\n' "$KEY_LINE" > "$TMP_KEY"
    ssh-keygen -lf "$TMP_KEY" -E sha256
    rm -f "$TMP_KEY"
else
    echo "  ssh-keygen no disponible para mostrar fingerprint"
fi

echo ""
echo "Listo. Prueba desde tu equipo antes de cerrar la sesion root:"
echo "  ssh -i ~/.ssh/mc2026/mcp-agent-mcperu-rsa -o PasswordAuthentication=no $AGENT_USER@179.43.82.54"
