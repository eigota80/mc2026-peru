# Release v2026.05.18 — Media Commerce Peru

## Estado: APROBADO ✅

## Commits incluidos

| Hash | Descripcion |
|---|---|
| 405efe5 | feat: base del sitio web Peru con navegacion completa |
| 288433c | feat: sistema de Ordenes de Servicio — modulo comercial completo |
| 7dc520d | feat: WebOps Agent — GitHub Actions CI/CD + MCP web connector + scripts |

## Tag: v2026.05.18

## Cambios entregados

- [x] Navegacion EMPRESA con enlace "Ordenes de servicio" en 33 paginas
- [x] Sistema de Ordenes de Servicio (login + app + PDF nativo)
- [x] Logo embebido como base64 (sin errores en file://)
- [x] PDF: firmas corregidas (Representante Legal x=188)
- [x] PDF: campos corporativos eliminados (solo logo en header)
- [x] PDF: orden correcto (tabla → observaciones → facilidades → firmas)
- [x] sitemap.xml actualizado con Ordenes de servicio
- [x] robots.txt creado
- [x] GitHub Actions CI/CD workflow
- [x] Scripts mcp-agent (6 scripts de infraestructura)
- [x] MCP web connector documentado
- [x] SSH key generada: ~/.ssh/mc2026/mcp-agent-mcperu

## Pendiente para activar CI/CD en produccion

```bash
# 1. Crear repositorio en GitHub y conectar
git remote add origin https://github.com/TU_ORG/MC_2026.git
git push -u origin main
git push --tags

# 2. En el servidor (como root) — ejecutar en orden:
bash Peru/mcp_web_connector/scripts/01-setup-mcp-agent-user.sh
bash Peru/mcp_web_connector/scripts/03-setup-db-user.sh
bash Peru/mcp_web_connector/scripts/04-harden-sshd.sh
bash Peru/mcp_web_connector/scripts/05-setup-staging.sh

# 3. Instalar clave publica en el servidor:
echo "ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIFlTW1ICfZTOCime/9WkdVyFTTcj+UVywj2hYGrObmsr mcp-agent@mcperu.pe-20260518" \
  >> /home/mcp-agent/.ssh/authorized_keys

# 4. Agregar secrets en GitHub:
#    MCP_AGENT_SSH_PRIVATE_KEY = contenido de ~/.ssh/mc2026/mcp-agent-mcperu

# 5. Proteger rama main en GitHub → Settings → Branches
```

## Rollback disponible

```bash
# Manual en el servidor:
sudo /usr/local/bin/rollback-mcperu.sh produccion 1

# Via GitHub:
# Ir al merge commit → Revert → Merge el PR de reversion
```
