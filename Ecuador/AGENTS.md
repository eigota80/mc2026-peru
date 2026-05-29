# Guia para agentes - Media Commerce Ecuador

## Regla principal

Todo cambio en produccion de `www.mediacommerce.ec` debe hacerse por el MCP `mcecuador-web`. No usar SSH, SFTP, FTP, rsync, cPanel File Manager ni otros accesos directos.

## Flujo de trabajo

1. Editar localmente dentro de `Ecuador/`.
2. Revisar que no se mezclen cambios de Peru ni de otros modulos.
3. Verificar el sitio localmente antes de desplegar.
4. Desplegar con `mcecuador-web`: primero `config_summary`, luego `ssh_health`, despues `remote_deploy_files`.
5. Confirmar en produccion con `remote_list` o una revision HTTP.
6. Hacer commit solo con los archivos relacionados.

## Hero del home

El hero de `Ecuador/index.html` se controla desde CSS:

- HTML: `Ecuador/index.html`
- Selector: `.home-hero`
- CSS: `Ecuador/style.css`
- Imagen actual: `Ecuador/images/custom/index/home/hero_ecu.png`
- Ruta en produccion: `/home/mediaco2/public_html/images/custom/index/home/hero_ecu.png`

Para cambiar la imagen del hero:

1. Copiar el nuevo archivo a `Ecuador/images/custom/index/home/`.
2. Actualizar `background-image` en `.home-hero` dentro de `Ecuador/style.css`.
3. Cambiar el query string `?v=...` de la imagen para evitar cache viejo.
4. Cambiar tambien el query string del link a `style.css` en `Ecuador/index.html`.
5. Desplegar como minimo `index.html`, `style.css` y la imagen nueva.

## Deploy minimo para el hero

Usar `remote_deploy_files` con estos destinos:

```json
[
  {
    "local": "/Users/eidergonzaleztamara/Documents/web side/MC_2026/Ecuador/index.html",
    "remote": "/home/mediaco2/public_html/index.html"
  },
  {
    "local": "/Users/eidergonzaleztamara/Documents/web side/MC_2026/Ecuador/style.css",
    "remote": "/home/mediaco2/public_html/style.css"
  },
  {
    "local": "/Users/eidergonzaleztamara/Documents/web side/MC_2026/Ecuador/images/custom/index/home/hero_ecu.png",
    "remote": "/home/mediaco2/public_html/images/custom/index/home/hero_ecu.png"
  }
]
```

## Notas de contenido

- Dominio Ecuador: `https://www.mediacommerce.ec/`
- GA4: `G-5GEKHX28YV`
- GTM: `GTM-N4SCNV2`
- WhatsApp Ecuador: `593987592186`
- No copiar datos de Peru: regulador, telefonos, dominio, moneda y WhatsApp son distintos.
