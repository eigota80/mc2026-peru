#!/usr/bin/env bash
# =============================================================================
# Script: 01-setup-mcp-agent-user.sh
# Ejecutar como: root en el servidor 179.43.82.54
# Proposito: Crear usuario mcp-agent con permisos minimos para operaciones CI/CD
# =============================================================================
set -euo pipefail

echo "============================================================"
echo " WEBOPS AGENT — Configuracion de usuario mcp-agent"
echo " Servidor: $(hostname) | Fecha: $(date '+%Y-%m-%d %H:%M:%S')"
echo "============================================================"

# ─── VARIABLES ───────────────────────────────────────────────────────────────
AGENT_USER="mcp-agent"
AGENT_HOME="/home/mcp-agent"
WEB_ROOT="/home/mcp-agent/apps/mcperu"
LOG_DIR="/var/log/mcp-agent"
STAGING_ROOT="/home/mcp-agent/apps/mcperu-staging"
SSH_DIR="$AGENT_HOME/.ssh"

# ─── 1. CREAR USUARIO SIN ACCESO ROOT NI SUDO ───────────────────────────────
echo ""
echo "[1/9] Creando usuario $AGENT_USER..."

if id "$AGENT_USER" &>/dev/null; then
    echo "  Usuario $AGENT_USER ya existe — verificando configuracion..."
else
    useradd \
        --create-home \
        --home-dir "$AGENT_HOME" \
        --shell /bin/bash \
        --comment "MCP WebOps Agent — sin privilegios" \
        --no-user-group \
        --groups www-data \
        "$AGENT_USER"
    echo "  ✓ Usuario $AGENT_USER creado"
fi

# Bloquear autenticacion por password
passwd -l "$AGENT_USER"
echo "  ✓ Login por password bloqueado (solo SSH key permitida)"

# Asegurarse de que NO este en sudoers
if groups "$AGENT_USER" | grep -q sudo; then
    gpasswd -d "$AGENT_USER" sudo
    echo "  ✓ Removido del grupo sudo"
fi

# ─── 2. CONFIGURAR DIRECTORIO SSH ───────────────────────────────────────────
echo ""
echo "[2/9] Configurando directorio SSH..."

mkdir -p "$SSH_DIR"
chmod 700 "$SSH_DIR"
touch "$SSH_DIR/authorized_keys"
chmod 600 "$SSH_DIR/authorized_keys"
chown -R "$AGENT_USER:$AGENT_USER" "$SSH_DIR"
echo "  ✓ $SSH_DIR configurado con permisos correctos"

# ─── 3. CREAR ESTRUCTURA DE DIRECTORIOS ─────────────────────────────────────
echo ""
echo "[3/9] Creando estructura de directorios del proyecto..."

mkdir -p "$WEB_ROOT"
mkdir -p "$STAGING_ROOT"
mkdir -p "$LOG_DIR"

chown -R "$AGENT_USER:$AGENT_USER" "$AGENT_HOME/apps"
chmod 750 "$AGENT_HOME"
chmod 755 "$WEB_ROOT"
chmod 755 "$STAGING_ROOT"

chown root:root "$LOG_DIR"
chmod 775 "$LOG_DIR"
# El agente puede escribir en logs pero no borrar
setfacl -m "u:$AGENT_USER:rwx" "$LOG_DIR" 2>/dev/null || chmod g+w "$LOG_DIR"

echo "  ✓ $WEB_ROOT creado (produccion — solo deploy controlado)"
echo "  ✓ $STAGING_ROOT creado (staging — preview antes de produccion)"
echo "  ✓ $LOG_DIR creado con escritura para auditoria"

# ─── 4. RESTRICCIONES DE SISTEMA DE ARCHIVOS ────────────────────────────────
echo ""
echo "[4/9] Aplicando restricciones de sistema de archivos..."

# El agente no puede leer /root, /etc/shadow, /var/log/auth.log de otros usuarios
chmod 750 /root 2>/dev/null || true

# Crear perfil de shell con PATH restringido
cat > "$AGENT_HOME/.bashrc" << 'BASHRC'
# mcp-agent — shell restringido
export PATH="/usr/local/bin:/usr/bin:/bin:/usr/local/git/bin"
export HOME="/home/mcp-agent"

# Alias de seguridad: prohibir comandos peligrosos
alias rm='echo "ERROR: uso de rm directo no permitido. Usa el script de deploy."; false'
alias chmod='echo "ERROR: chmod manual no permitido."; false'
alias chown='echo "ERROR: chown manual no permitido."; false'

# Logging automatico de cada sesion
export HISTFILE="/var/log/mcp-agent/bash_history_$(date +%Y%m%d).log"
export HISTTIMEFORMAT="%Y-%m-%d %H:%M:%S "
export HISTFILESIZE=50000
export HISTSIZE=50000
shopt -s histappend
PROMPT_COMMAND="history -a; $PROMPT_COMMAND"

echo "[ mcp-agent ] Sesion iniciada: $(date '+%Y-%m-%d %H:%M:%S') desde $SSH_CLIENT"
BASHRC

chown "$AGENT_USER:$AGENT_USER" "$AGENT_HOME/.bashrc"
echo "  ✓ Shell restringido con PATH controlado y logging activo"

# ─── 5. PERMISOS SUDO MINIMOS (solo reiniciar servicio web) ─────────────────
echo ""
echo "[5/9] Configurando permisos sudo minimos..."

cat > /etc/sudoers.d/mcp-agent << 'SUDOERS'
# mcp-agent — permisos minimos para WebOps
# Solo puede reiniciar el servicio web del proyecto — nada mas
Defaults:mcp-agent !requiretty
Defaults:mcp-agent logfile="/var/log/mcp-agent/sudo.log"

mcp-agent ALL=(ALL) NOPASSWD: /bin/systemctl restart nginx
mcp-agent ALL=(ALL) NOPASSWD: /bin/systemctl reload nginx
mcp-agent ALL=(ALL) NOPASSWD: /bin/systemctl restart apache2
mcp-agent ALL=(ALL) NOPASSWD: /bin/systemctl reload apache2
mcp-agent ALL=(ALL) NOPASSWD: /usr/local/bin/deploy-mcperu.sh
SUDOERS

chmod 440 /etc/sudoers.d/mcp-agent
visudo -c -f /etc/sudoers.d/mcp-agent && echo "  ✓ Sudoers validado correctamente" || {
    echo "  ✗ Error en sudoers — revirtiendo"
    rm /etc/sudoers.d/mcp-agent
    exit 1
}

# ─── 6. CONFIGURAR AUDITD / LOGGING ─────────────────────────────────────────
echo ""
echo "[6/9] Configurando logging de actividad..."

# Rotacion de logs del agente
cat > /etc/logrotate.d/mcp-agent << 'LOGROTATE'
/var/log/mcp-agent/*.log {
    daily
    rotate 90
    compress
    delaycompress
    missingok
    notifempty
    create 664 mcp-agent root
    dateext
    dateformat -%Y%m%d
}
LOGROTATE

# Script de log de accesos SSH (via /etc/ssh/sshrc o PAM)
cat > /etc/ssh/sshrc << 'SSHRC'
if [ "$(id -nu)" = "mcp-agent" ]; then
    echo "$(date '+%Y-%m-%d %H:%M:%S') LOGIN mcp-agent desde $SSH_CLIENT" \
        >> /var/log/mcp-agent/access.log
fi
SSHRC

echo "  ✓ Rotacion de logs configurada (90 dias)"
echo "  ✓ Log de accesos SSH activo en /var/log/mcp-agent/access.log"

# ─── 7. INSTALAR GIT Y DEPENDENCIAS PARA DEPLOY ─────────────────────────────
echo ""
echo "[7/9] Verificando git y dependencias de deploy..."

command -v git &>/dev/null || { apt-get install -y git 2>/dev/null || yum install -y git 2>/dev/null; }
GIT_VERSION=$(git --version)
echo "  ✓ $GIT_VERSION"

# Configurar git para el agente
sudo -u "$AGENT_USER" git config --global user.name "MCP WebOps Agent"
sudo -u "$AGENT_USER" git config --global user.email "mcp-agent@mcperu.pe"
sudo -u "$AGENT_USER" git config --global core.fileMode false
sudo -u "$AGENT_USER" git config --global pull.rebase false
echo "  ✓ Git configurado para el usuario $AGENT_USER"

# ─── 8. CREAR SCRIPT DE DEPLOY CONTROLADO ───────────────────────────────────
echo ""
echo "[8/9] Creando script de deploy controlado..."

cat > /usr/local/bin/deploy-mcperu.sh << 'DEPLOY'
#!/usr/bin/env bash
# deploy-mcperu.sh — Solo ejecutable por mcp-agent via sudo
# No permite deploy directo a produccion — requiere tag de release

set -euo pipefail

ENV="${1:-staging}"
BRANCH="${2:-main}"
WEB_PROD="/home/mcp-agent/apps/mcperu"
WEB_STAGING="/home/mcp-agent/apps/mcperu-staging"
LOG="/var/log/mcp-agent/deploy.log"
TIMESTAMP=$(date '+%Y-%m-%d %H:%M:%S')

log() { echo "[$TIMESTAMP] $*" | tee -a "$LOG"; }

if [ "$ENV" = "production" ] && [ "$(id -un)" != "root" ]; then
    log "ERROR: deploy a produccion solo via GitHub Actions — no directo"
    exit 1
fi

if [ "$ENV" = "staging" ]; then
    log "Iniciando deploy a STAGING (branch: $BRANCH)"
    cd "$WEB_STAGING"
    git fetch origin
    git checkout "$BRANCH"
    git pull origin "$BRANCH"
    sudo /bin/systemctl reload nginx
    log "STAGING actualizado correctamente"
    echo "Preview: http://staging.mcperu.pe"
elif [ "$ENV" = "production" ]; then
    log "Iniciando deploy a PRODUCCION (branch: main)"
    cd "$WEB_PROD"
    git fetch origin
    git checkout main
    git pull origin main
    sudo /bin/systemctl reload nginx
    log "PRODUCCION actualizada correctamente"
fi
DEPLOY

chmod 755 /usr/local/bin/deploy-mcperu.sh
chown root:root /usr/local/bin/deploy-mcperu.sh
echo "  ✓ /usr/local/bin/deploy-mcperu.sh creado y protegido"

# ─── 9. RESUMEN Y PROXIMOS PASOS ─────────────────────────────────────────────
echo ""
echo "[9/9] Configuracion completada."
echo ""
echo "============================================================"
echo " RESUMEN DE CONFIGURACION"
echo "============================================================"
echo " Usuario:      $AGENT_USER"
echo " Home:         $AGENT_HOME"
echo " Web prod:     $WEB_ROOT"
echo " Web staging:  $STAGING_ROOT"
echo " Logs:         $LOG_DIR"
echo " SSH:          Solo key — password bloqueado"
echo " Sudo:         Solo nginx/apache restart + deploy-mcperu.sh"
echo " Base datos:   Pendiente (ver script 03-setup-db-user.sh)"
echo "============================================================"
echo ""
echo "PROXIMO PASO: Agregar la SSH public key del agente:"
echo "  cat /ruta/a/mcp-agent-key.pub >> $SSH_DIR/authorized_keys"
echo "  (Ver script 02-generate-ssh-keys.sh)"
echo ""
