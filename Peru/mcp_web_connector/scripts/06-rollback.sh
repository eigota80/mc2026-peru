#!/usr/bin/env bash
# =============================================================================
# Script: 06-rollback.sh
# Ejecutar como: mcp-agent (o root) en el servidor
# Proposito: Revertir el sitio web al commit anterior si algo falla
# Uso: sudo /usr/local/bin/rollback-mcperu.sh [produccion|staging] [commit|steps]
# =============================================================================
set -euo pipefail

ENV="${1:-staging}"
TARGET="${2:-1}"        # numero de commits a revertir O hash de commit
WEB_PROD="/home/mcp-agent/apps/mcperu"
WEB_STAGING="/home/mcp-agent/apps/mcperu-staging"
LOG="/var/log/mcp-agent/rollback.log"
TS=$(date '+%Y-%m-%d %H:%M:%S')

log() { echo "[$TS] $*" | tee -a "$LOG"; }

echo "============================================================"
echo " ROLLBACK — Media Commerce Peru"
echo " Entorno: $ENV | Target: $TARGET"
echo "============================================================"

# Seleccionar directorio segun entorno
if [ "$ENV" = "production" ]; then
    WEB_DIR="$WEB_PROD"
    log "ROLLBACK PRODUCCION iniciado por $(id -un) desde $SSH_CLIENT"
elif [ "$ENV" = "staging" ]; then
    WEB_DIR="$WEB_STAGING"
    log "ROLLBACK STAGING iniciado por $(id -un)"
else
    echo "ERROR: Entorno invalido. Usar: produccion o staging"
    exit 1
fi

cd "$WEB_DIR"

# Mostrar estado actual
CURRENT_COMMIT=$(git log -1 --format="%h — %s (%ai)")
log "Commit actual: $CURRENT_COMMIT"

echo ""
echo "Ultimos 10 commits disponibles:"
git log --oneline -10
echo ""

# Determinar commit objetivo
if [[ "$TARGET" =~ ^[0-9]+$ ]]; then
    # Es un numero de pasos
    TARGET_COMMIT=$(git log --format="%h" | sed -n "${TARGET}p")
    log "Revirtiendo $TARGET commit(s) atras → $TARGET_COMMIT"
elif [[ "$TARGET" =~ ^[0-9a-f]{7,40}$ ]]; then
    # Es un hash de commit
    TARGET_COMMIT="$TARGET"
    log "Revirtiendo a commit especifico: $TARGET_COMMIT"
else
    echo "ERROR: TARGET debe ser numero de pasos o hash de commit"
    exit 1
fi

# Confirmar el rollback
echo ""
echo "Commit objetivo: $(git log -1 --format='%h — %s (%ai)' $TARGET_COMMIT)"
echo ""
read -r -p "Confirmar rollback a este commit? [s/N]: " CONFIRM
if [[ ! "$CONFIRM" =~ ^[sS]$ ]]; then
    log "Rollback cancelado por el usuario"
    echo "Rollback cancelado."
    exit 0
fi

# Ejecutar rollback
git checkout "$TARGET_COMMIT" -- .
git stash 2>/dev/null || true

# Recargar el servidor web
sudo /bin/systemctl reload nginx 2>/dev/null || \
sudo /bin/systemctl reload apache2 2>/dev/null || \
echo "  AVISO: No se pudo recargar el servidor web — hacerlo manualmente"

log "ROLLBACK completado. Commit activo: $(git log -1 --format='%h — %s')"

echo ""
echo "============================================================"
echo " ROLLBACK COMPLETADO"
echo "============================================================"
echo " Entorno:       $ENV"
echo " Commit activo: $(git log -1 --format='%h — %s (%ai)')"
echo " Log:           $LOG"
echo ""
echo " Para volver a produccion normal:"
echo "   git checkout main && git pull origin main"
echo "============================================================"
