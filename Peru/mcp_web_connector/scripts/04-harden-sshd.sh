#!/usr/bin/env bash
# =============================================================================
# Script: 04-harden-sshd.sh
# Ejecutar como: root en el servidor 179.43.82.54
# Proposito: Restringir SSH para el usuario mcp-agent
#            - Solo autenticacion por clave
#            - Sin reenvio de puertos
#            - Sin acceso X11
# ATENCION: Hacer backup de /etc/ssh/sshd_config antes de ejecutar
# =============================================================================
set -euo pipefail

SSHD_CONFIG="/etc/ssh/sshd_config"
BACKUP="$SSHD_CONFIG.backup.$(date +%Y%m%d%H%M%S)"

echo "============================================================"
echo " Hardening SSH para mcp-agent"
echo "============================================================"

# Backup obligatorio
cp "$SSHD_CONFIG" "$BACKUP"
echo "  ✓ Backup guardado en: $BACKUP"

# Verificar si ya existe el bloque para mcp-agent
if grep -q "Match User mcp-agent" "$SSHD_CONFIG"; then
    echo "  Bloque Match User mcp-agent ya existe — actualizando..."
    # Remover bloque existente para reescribir
    sed -i '/^Match User mcp-agent/,/^Match /{ /^Match User mcp-agent/d; /^Match /!d }' "$SSHD_CONFIG" 2>/dev/null || true
fi

# Agregar bloque de restriccion especifica para mcp-agent al final del archivo
cat >> "$SSHD_CONFIG" << 'SSHBLOCK'

# ─── Restricciones para mcp-agent (WebOps CI/CD) ─────────────────────────────
Match User mcp-agent
    # Solo autenticacion por clave SSH — nunca password
    PasswordAuthentication no
    PubkeyAuthentication yes
    AuthenticationMethods publickey

    # Sin reenvio de trafico — solo operaciones git/deploy
    AllowTcpForwarding no
    X11Forwarding no
    AllowAgentForwarding no
    PermitTunnel no

    # Directorio de trabajo restringido al proyecto
    ChrootDirectory /home/mcp-agent

    # Tiempo maximo de sesion sin actividad: 30 minutos
    ClientAliveInterval 300
    ClientAliveCountMax 6

    # Logging extra para este usuario
    LogLevel VERBOSE
SSHBLOCK

# Verificar sintaxis antes de recargar
sshd -t && echo "  ✓ Sintaxis de sshd_config validada" || {
    echo "  ✗ Error en sshd_config — restaurando backup"
    cp "$BACKUP" "$SSHD_CONFIG"
    exit 1
}

# Recargar el servicio SSH sin cerrar sesiones activas
systemctl reload sshd && echo "  ✓ SSH recargado con nueva configuracion" || {
    echo "  ✗ Error al recargar SSH — restaurando backup"
    cp "$BACKUP" "$SSHD_CONFIG"
    systemctl reload sshd
    exit 1
}

echo ""
echo "============================================================"
echo " Configuracion SSH aplicada para mcp-agent:"
echo "============================================================"
grep -A 20 "Match User mcp-agent" "$SSHD_CONFIG"
echo ""
echo "============================================================"
echo " Para revertir si algo falla:"
echo "   cp $BACKUP $SSHD_CONFIG"
echo "   systemctl reload sshd"
echo "============================================================"
