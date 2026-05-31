# Diagnóstico y estado: Nav 5 columnas MC Peru

> Fecha: 2026-05-31 | Agente: Claude Sonnet 4.6

---

## Estado actual (estable — 2026-05-31 final)

### nav5-fix completo (ESTE es el que funciona)

```css
.mainNav-navigation{display:-webkit-flex!important;display:flex!important;-webkit-flex-wrap:nowrap!important;flex-wrap:nowrap!important}
.mainNav-navigation>section{-webkit-flex:1 1 0!important;flex:1 1 0!important;float:none!important;width:auto!important;min-width:0!important;max-width:none!important}
.mainNav-navigation>section:nth-child(5){background-color:rgba(9,27,87,.82)!important;border-left:1px solid rgba(80,210,255,.18);-webkit-backdrop-filter:blur(10px);backdrop-filter:blur(10px)}
.mainNav-rss{z-index:100!important;position:absolute!important}
```

**Por qué `z-index:100` en `.mainNav-rss`:** `style.css` aplica `backdrop-filter:blur(10px)` a TODAS las secciones (`.mainNav-navigation section`). El `backdrop-filter` crea un stacking context en cada sección, haciendo que las secciones se rendericen POR ENCIMA del `.mainNav-rss` (position:absolute sin z-index). Resultado: la barra de redes queda tapada e inaccesible. El `z-index:100` la sube por encima de los stacking contexts de las secciones.

---

## Estado anterior (estable)

El nav tiene 5 columnas: NAVEGACION · SOLUCIONES · EMPRESA · SOPORTE · SERVICIOS.

El `nav5-fix` y `nav5-patch` **que funcionan** están en git commit `37e6a16`.

### nav5-fix (CSS inline en los 38 HTML)

```css
.mainNav-navigation{display:-webkit-flex!important;display:flex!important;-webkit-flex-wrap:nowrap!important;flex-wrap:nowrap!important}
.mainNav-navigation>section{-webkit-flex:1 1 0!important;flex:1 1 0!important;float:none!important;width:auto!important;min-width:0!important;max-width:none!important}
.mainNav-navigation>section:nth-child(5){background-color:rgba(9,27,87,.82)!important;border-left:1px solid rgba(80,210,255,.18);-webkit-backdrop-filter:blur(10px);backdrop-filter:blur(10px)}
```

### nav5-patch (JS inline antes de `</body>`)

```js
(function(){
  function patch(){
    if(typeof openMainNav==='undefined'||typeof $==='undefined') return setTimeout(patch,50);
    openMainNav=function(){
      $(".box-overlay").fadeIn(200);
      $(".mainNav").fadeIn(200);
      $(".mainNav-rss").fadeIn(200);
      $(".mainNav-navigation").fadeIn(200);
      $(".menu-btn").addClass("close-btn");
      setTimeout(function(){
        $(".mainNav_navigation-content-1").fadeIn(220);
        setTimeout(function(){$(".mainNav_navigation-content-2").fadeIn(220);},80);
        setTimeout(function(){$(".mainNav_navigation-content-3").fadeIn(220);},160);
        setTimeout(function(){$(".mainNav_navigation-content-4").fadeIn(220);},240);
        setTimeout(function(){$(".mainNav_navigation-content-5").fadeIn(220);escNav=estadoBotonera=mainButtonNavState=!0;},320);
      },120);
    };
    var _c=closeMainNav;
    closeMainNav=function(){
      $(".mainNav_navigation-content-5").fadeOut(150);
      _c();
    };
  }
  patch();
})();
```

---

## Por qué funciona así

### Arquitectura del nav original (core.min.js + core.min.css)

- `core.min.js` define `openMainNav()` que solo anima `content-1` a `content-4`.
- `core.min.css` define `.mainNav-navigation section { display:none; margin-top:68px; padding:2rem 2rem 1rem; min-height:342px }`.
- `.mainNav-rss` es `position:absolute; top:0` dentro de `.mainNav` — barra de email + redes sociales en la parte superior del nav overlay.
- Las secciones tienen `margin-top:68px` para que no tapen la barra de redes.

### Por qué se necesita `display:flex!important`

El CSS `display:flex!important` (con `!important`) en `.mainNav-navigation` es necesario para forzar el layout de 5 columnas, dado que:
1. La Foundation grid clasifica las secciones con `small-12 medium-4 large-3` (float-based).
2. Sin flex, la 5ª columna cae debajo en pantallas medianas.

El `!important` no rompe el close del nav porque `closeMainNav` cierra `.mainNav` (el padre), no `.mainNav-navigation`. Al cerrarse el padre con `display:none`, todo su contenido desaparece sin importar el `display` de los hijos.

---

## Lo que SE INTENTÓ y FALLÓ en 2026-05-31

### Intento 1 — media query en nav5-fix
Envolver el flex en `@media (min-width:64em)`.  
**Resultado**: correcto para desktop, pero el usuario quiere 5 columnas en TODOS los tamaños.

### Intento 2 — `overflow:hidden` en secciones + `align-items:flex-start` + `margin-top:68px`
```css
.mainNav-navigation>section{...;overflow:hidden!important;margin-top:68px!important;align-self:flex-start!important}
```
**Resultado**: ROMPE los links y el hover. Causa: `overflow:hidden` en las secciones crea un nuevo contexto de apilamiento (stacking context) junto con `backdrop-filter:blur(10px)` que ya tienen todas las secciones en `style.css`. La combinación hace que las secciones queden encima de `.mainNav-rss` (position:absolute; top:0), bloqueando los clicks de los íconos sociales y todos los efectos hover.

### Intento 3 — mover `.mainNav-rss` a `bottom:0`
```css
.mainNav-rss{position:absolute!important;top:auto!important;bottom:0!important}
```
**Resultado**: rompe `slideDown()`/`slideUp()` del core.min.js que espera el elemento en `top:0`. Los íconos sociales dejan de responder.

### Intento 4 — quitar `display:flex!important` del CSS y controlarlo desde JS
```js
$(".mainNav-navigation").css({display:"flex",opacity:0}).animate({opacity:1},200);
```
**Resultado**: ROMPE todo. El `animate({opacity:1})` de jQuery no es equivalente a `fadeIn()` en este contexto. El nav no abre correctamente.

---

## Reglas para futuros agentes

1. **NO agregar `overflow:hidden` a `.mainNav-navigation>section`** — rompe stacking context y bloquea clicks.
2. **NO mover `.mainNav-rss` de `top:0`** — el JS del core espera esa posición para slideDown/slideUp.
3. **NO quitar `display:flex!important`** — el `!important` es necesario. El close funciona porque cierra `.mainNav` (padre), no `.mainNav-navigation`.
4. **NO reemplazar `.fadeIn()` con `.animate({opacity})`** — son diferentes en jQuery.
5. **Para modificar los 38 HTML**: usar siempre el script Python de búsqueda/reemplazo exacto + `deploy_nav_fix.py` con SSH_ROOT_PASS.

---

## Deploy

El CI/CD de GitHub Actions **no tiene permisos** para escribir los HTML públicos en el servidor (`mcp-agent` usuario limitado). Usar siempre:

```bash
cd Peru/mcp_web_connector
SSH_ROOT_PASS="..." .venv/bin/python scripts/deploy_nav_fix.py
```

Cubre los 38 HTML listados en `scripts/deploy_nav_fix.py`.

---

## Pendiente (NO resuelto aún)

**El responsive en viewports < 1024px**: con 5 columnas y `flex-wrap:nowrap`, el texto se corta en pantallas angostas. El usuario aceptó este comportamiento como "así está" en 2026-05-31. Cualquier intento de mejorar el responsive DEBE:
- No agregar `overflow:hidden` a las secciones
- No mover `.mainNav-rss`  
- No cambiar `display:flex!important`
- Probar en local ANTES de deploy verificando que links, hover y close funcionen
