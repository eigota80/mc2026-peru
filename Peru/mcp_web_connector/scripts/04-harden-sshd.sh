#!/usr/bin/env bash
# =============================================================================
# Script: 04-harden-sshd.sh
# Ejecutar como: root en el servidor 179.43.82.54
# Proposito: Restringir SSH para el usuario mcp-agent
#            - Solo autenticacion por clave
#            - Reenvio TCP local permitido (necesario para tunel SSH → MySQL)
#            - Sin X11, sin agent forwarding, sin tunnel TUN/TAP
# ATENCION: Hacer backup de /etc/ssh/sshd_config antes de ejecutar
# =============================================================================
set -euo pipefail

SSHD_CONFIG="/etc/ssh/sshd_config"
BACKUP="$SSHD_CONFIG.backup.$(date +%Y%m%d%H%M%S)"
BLOCK_MARKER="# ─── Restricciones para mcp-agent (WebOps CI/CD)"

echo "============================================================"
echo " Hardening SSH para mcp-agent"
echo "============================================================"

# Backup obligatorio
cp "$SSHD_CONFIG" "$BACKUP"
echo "  ✓ Backup guardado en: $BACKUP"

# Si ya existe el bloque, eliminar desde el marcador hasta el final del archivo.
# El bloque siempre es lo último en sshd_config (lo agrega este mismo script).
if grep -qF "$BLOCK_MARKER" "$SSHD_CONFIG"; then
    echo "  Bloque mcp-agent ya existe — eliminando para reescribir..."
    LINE=$(grep -nF "$BLOCK_MARKER" "$SSHD_CONFIG" | cut -d: -f1 | head -1)
    head -n $((LINE - 1)) "$SSHD_CONFIG" > "${SSHD_CONFIG}.tmp"
    mv "${SSHD_CONFIG}.tmp" "$SSHD_CONFIG"
    echo "  ✓ Bloque anterior eliminado"
fi

# Agregar bloque de restriccion especifica para mcp-agent al final del archivo.
#
# NOTAS DE DISEÑO:
#   AllowTcpForwarding local — necesario para el tunel SSH que usa el MCP connector
#     para acceder a MySQL (equivalente a ssh -L). Sin esto las consultas DB fallan.
#     "local" permite solo port-forwarding saliente; no permite remote forwarding.
#
#   ChrootDirectory — ELIMINADO. Requiere que todos los binarios (/bin, /usr/bin,
#     /lib, etc.) existan dentro del chroot, lo que es incompatible con la ejecucion
#     de comandos remotos (ssh_health, remote_list, remote_read_text).
#     Para confinamiento real usar namespaces/containers, no sshd ChrootDirectory.
#
cat >> "$SSHD_CONFIG" << 'SSHBLOCK'

# ─── Restricciones para mcp-agent (WebOps CI/CD) ─────────────────────────────
Match User mcp-agent
    # Solo autenticacion por clave SSH — nunca password
    PasswordAuthentication no
    PubkeyAuthentication yes
    AuthenticationMethods publickey

    # Reenvio TCP local permitido: el MCP connector abre un tunel SSH hacia MySQL.
    # "local" = solo -L (local port forward); bloquea -R (remote forward).
    AllowTcpForwarding local
    X11Forwarding no
    AllowAgentForwarding no
    # PermitTunnel controla TUN/TAP (VPN) — no afecta port forwarding TCP.
    PermitTunnel no

    # Tiempo maximo de sesion sin actividad: 30 minutos
    ClientAliveInterval 300
    ClientAliveCountMax 6

    # Logging extra para auditoria de este usuario
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
