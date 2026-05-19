#!/usr/bin/env bash
# =============================================================================
# Script: 05-setup-staging.sh
# Ejecutar como: root en el servidor 179.43.82.54
# Proposito: Configurar entorno de staging en el servidor
#            Staging = copia exacta de produccion para preview antes de merge
# =============================================================================
set -euo pipefail

AGENT_USER="mcp-agent"
WEB_PROD="/home/mcp-agent/apps/mcperu"
WEB_STAGING="/home/mcp-agent/apps/mcperu-staging"
NGINX_CONF="/etc/nginx/sites-available"
SERVER_IP="179.43.82.54"

echo "============================================================"
echo " Configurando entorno Staging para Media Commerce Peru"
echo "============================================================"

# ─── 1. Inicializar repositorio git en staging ───────────────────────────────
echo ""
echo "[1/4] Preparando directorio de staging..."

if [ ! -d "$WEB_STAGING/.git" ]; then
    sudo -u "$AGENT_USER" git clone \
        https://github.com/TU_ORG/MC_2026.git \
        "$WEB_STAGING" 2>/dev/null || {
        echo "  (remote git no configurado aun — creando directorio base)"
        mkdir -p "$WEB_STAGING"
        chown -R "$AGENT_USER:$AGENT_USER" "$WEB_STAGING"
    }
else
    echo "  Repositorio git ya clonado en staging"
fi

# ─── 2. Configurar Nginx para staging ───────────────────────────────────────
echo ""
echo "[2/4] Configurando Nginx para staging..."

cat > "$NGINX_CONF/mcperu-staging" << NGINX
server {
    listen 8080;
    server_name staging.mcperu.pe $SERVER_IP;

    root $WEB_STAGING/Peru;
    index index.html;

    # Acceso restringido — no es sitio publico
    # Descomentar para restringir por IP:
    # allow 200.x.x.x;  # IP de la oficina
    # deny all;

    location / {
        try_files \$uri \$uri/ =404;
    }

    location ~* \.(js|css|png|jpg|jpeg|gif|svg|ico|woff|woff2)$ {
        expires 1h;
        add_header Cache-Control "no-store";
    }

    # Header para identificar que es staging
    add_header X-Environment "staging" always;

    access_log /var/log/nginx/mcperu-staging-access.log;
    error_log  /var/log/nginx/mcperu-staging-error.log;
}
NGINX

# Habilitar el sitio
ln -sf "$NGINX_CONF/mcperu-staging" /etc/nginx/sites-enabled/mcperu-staging
nginx -t && systemctl reload nginx
echo "  ✓ Nginx staging configurado en puerto 8080"
echo "  ✓ Preview disponible en: http://$SERVER_IP:8080"

# ─── 3. Crear script de actualizacion de staging ────────────────────────────
echo ""
echo "[3/4] Creando script de actualizacion de staging..."

cat > /usr/local/bin/update-staging.sh << 'UPDATESCRIPT'
#!/usr/bin/env bash
# Actualiza staging desde la branch indicada
set -euo pipefail

BRANCH="${1:-develop}"
WEB_STAGING="/home/mcp-agent/apps/mcperu-staging"
LOG="/var/log/mcp-agent/staging.log"
TS=$(date '+%Y-%m-%d %H:%M:%S')

echo "[$TS] Actualizando staging desde branch: $BRANCH" | tee -a "$LOG"

cd "$WEB_STAGING"
git fetch --all
git checkout "$BRANCH"
git pull origin "$BRANCH"

sudo /bin/systemctl reload nginx

echo "[$TS] Staging actualizado — branch: $BRANCH" | tee -a "$LOG"
echo ""
echo "Preview: http://179.43.82.54:8080"
echo "Branch:  $BRANCH"
echo "Commit:  $(git log -1 --format='%h %s')"
UPDATESCRIPT

chmod 755 /usr/local/bin/update-staging.sh
chown root:root /usr/local/bin/update-staging.sh

# Agregar al sudoers del agente
echo "mcp-agent ALL=(ALL) NOPASSWD: /usr/local/bin/update-staging.sh" \
    >> /etc/sudoers.d/mcp-agent
visudo -c -f /etc/sudoers.d/mcp-agent
echo "  ✓ Script de staging listo"

# ─── 4. Crear webhook simple para GitHub Actions ────────────────────────────
echo ""
echo "[4/4] Instrucciones para webhook de GitHub Actions..."

echo ""
echo "============================================================"
echo " Staging configurado correctamente"
echo "============================================================"
echo " Produccion:  /home/mcp-agent/apps/mcperu        (puerto 80)"
echo " Staging:     /home/mcp-agent/apps/mcperu-staging (puerto 8080)"
echo " Preview URL: http://$SERVER_IP:8080"
echo ""
echo " Para actualizar staging manualmente:"
echo "   sudo /usr/local/bin/update-staging.sh nombre-de-branch"
echo ""
echo " En GitHub Actions el job 'preview' llama este script"
echo " automaticamente al abrir un Pull Request."
echo "============================================================"
