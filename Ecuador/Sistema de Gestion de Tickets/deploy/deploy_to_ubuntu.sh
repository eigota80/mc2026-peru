#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'EOF'
Uso:
  ./deploy/deploy_to_ubuntu.sh usuario@IP [ruta_remota]

Ejemplos:
  ./deploy/deploy_to_ubuntu.sh ubuntu@203.0.113.10
  ./deploy/deploy_to_ubuntu.sh root@203.0.113.10 /opt/tickets

La ruta remota por defecto es /opt/tickets.
EOF
}

if [[ "${1:-}" == "-h" || "${1:-}" == "--help" ]]; then
  usage
  exit 0
fi

if [[ $# -lt 1 || $# -gt 2 ]]; then
  usage
  exit 1
fi

REMOTE="$1"
REMOTE_DIR="${2:-/opt/tickets}"
REMOTE_TMP="/tmp/tickets-deploy-$(date +%Y%m%d%H%M%S)"

EXCLUDES=(
  --exclude ".git/"
  --exclude ".venv/"
  --exclude "backend/.venv/"
  --exclude "backend/.env"
  --exclude "backend/*.db"
  --exclude "backend/uploads/"
  --exclude "__pycache__/"
  --exclude "*.pyc"
  --exclude ".DS_Store"
)

echo "Verificando rsync en el servidor..."
ssh "$REMOTE" "command -v rsync >/dev/null 2>&1 || { echo 'Instala rsync en el servidor: sudo apt install -y rsync' >&2; exit 1; }"

echo "Preparando carpeta temporal en $REMOTE:$REMOTE_TMP..."
ssh "$REMOTE" "rm -rf '$REMOTE_TMP' && mkdir -p '$REMOTE_TMP'"

echo "Transfiriendo proyecto..."
rsync -az --delete "${EXCLUDES[@]}" ./ "$REMOTE:$REMOTE_TMP/"

echo "Instalando archivos en $REMOTE_DIR..."
ssh "$REMOTE" "REMOTE_DIR='$REMOTE_DIR' REMOTE_TMP='$REMOTE_TMP' bash -s" <<'REMOTE_SCRIPT'
set -euo pipefail

if ! id tickets >/dev/null 2>&1; then
  sudo useradd --system --home "$REMOTE_DIR" --shell /usr/sbin/nologin tickets
fi

sudo mkdir -p "$REMOTE_DIR"
sudo rsync -a --delete \
  --exclude ".venv/" \
  --exclude "backend/.venv/" \
  --exclude "backend/.env" \
  --exclude "backend/*.db" \
  --exclude "backend/uploads/" \
  "$REMOTE_TMP/" "$REMOTE_DIR/"

sudo chown -R tickets:tickets "$REMOTE_DIR"
rm -rf "$REMOTE_TMP"
REMOTE_SCRIPT

cat <<EOF

Transferencia lista.

Siguiente paso en el servidor:
  ssh $REMOTE
  cd $REMOTE_DIR/backend
  sudo -u tickets python3 -m venv .venv
  sudo -u tickets $REMOTE_DIR/backend/.venv/bin/pip install -r requirements.txt

Luego crea $REMOTE_DIR/backend/.env y activa el servicio systemd con la guia:
  $REMOTE_DIR/deploy/UBUNTU_BACKEND_SYSTEMD.md
EOF
