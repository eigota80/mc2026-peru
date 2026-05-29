# Sistema de Perfil de Usuario - Implementación Completa

## 📋 Resumen

Se ha implementado un sistema completo de **perfiles de usuario** que permite a cada usuario mantener información detallada sobre su identidad, contacto, permisos, departamento, canales, idioma/zona horaria y personalización de trabajo.

## ✨ Características Principales

### 1. **Información de Identidad**
- Foto de perfil
- Empresa
- Teléfono
- Cargo/Puesto

### 2. **Estructura Organizacional**
- Departamento

### 3. **Control de Acceso**
- Sistema flexible de permisos (JSON array)
- Canales de comunicación configurables

### 4. **Localización**
- Idioma seleccionable (es, en, fr, pt)
- Zona horaria configurable

### 5. **Personalización**
- Preferencias de trabajo (JSON object)
- Tema (claro, oscuro, automático)
- Configuración de notificaciones
- Elementos por página

## 🛠️ Cambios Implementados

### Backend (Python/FastAPI)

#### 1. **Modelo: `UserProfile`** (`models.py`)
```python
class UserProfile(Base):
    __tablename__ = "user_profiles"
    
    id: int (PK)
    user_id: int (FK, unique)
    
    # Identidad
    photo_url: str (max 500)
    company: str (max 180)
    phone: str (max 20)
    job_title: str (max 120)
    
    # Departamento
    department: str (max 120)
    
    # Permisos y Canales
    permissions: JSON array
    channels: JSON array
    
    # Localización
    language: str (default: "es")
    timezone: str (default: "America/Bogota")
    
    # Personalización
    work_preferences: JSON object
    
    # Auditoría
    created_at: datetime
    updated_at: datetime
```

#### 2. **Schemas de Pydantic** (`schemas.py`)
- `UserProfileBase` - Schema base con validaciones
- `UserProfileCreate` - Para crear perfiles
- `UserProfileUpdate` - Para actualizar (todos los campos opcionales)
- `UserProfileRead` - Para leer perfiles con auditoría
- `UserReadWithProfile` - User con perfil anidado

#### 3. **CRUD Operations** (`crud.py`)
```python
create_user_profile(db, user_id, payload)      # Crear nuevo perfil
get_user_profile(db, user_id)                   # Obtener perfil
update_user_profile(db, profile, payload)       # Actualizar perfil
delete_user_profile(db, profile)                # Eliminar perfil
get_or_create_user_profile(db, user_id)         # Obtener o crear con defaults
```

#### 4. **Endpoints REST** (`main.py`)

**GET /profile** - Obtener mi perfil
```bash
curl -H "Authorization: Bearer TOKEN" \
     http://localhost:8000/api/profile
```

**PUT /profile** - Actualizar mi perfil
```bash
curl -X PUT -H "Authorization: Bearer TOKEN" \
     -H "Content-Type: application/json" \
     -d '{...}' \
     http://localhost:8000/api/profile
```

**GET /users/{user_id}/profile** - Obtener perfil de usuario (admin)
```bash
curl -H "Authorization: Bearer TOKEN" \
     http://localhost:8000/api/users/1/profile
```

### Frontend (HTML/JavaScript)

#### **Interfaz de Perfil** (`profile.html`)
Página completa con:
- ✅ Carga de perfil existente
- ✅ Edición en tiempo real
- ✅ Vista previa de foto
- ✅ Gestión de tags (permisos, canales)
- ✅ Validación de formularios
- ✅ Alertas de éxito/error
- ✅ Responsive design (móvil & desktop)

## 📊 Estructura de Datos

### Ejemplo de Perfil Completo

```json
{
  "id": 1,
  "user_id": 42,
  "photo_url": "https://example.com/photo.jpg",
  "company": "Tech Corp",
  "phone": "+57 315 1234567",
  "job_title": "Senior Developer",
  "department": "Backend Development",
  "permissions": [
    "read_tickets",
    "create_tickets",
    "edit_tickets",
    "assign_tickets"
  ],
  "channels": [
    "email",
    "slack"
  ],
  "language": "es",
  "timezone": "America/Bogota",
  "work_preferences": {
    "notifications_enabled": true,
    "email_on_ticket_assign": true,
    "theme": "dark",
    "items_per_page": 25
  },
  "created_at": "2026-05-03T10:30:00",
  "updated_at": "2026-05-03T11:50:00"
}
```

## 🚀 Cómo Usar

### 1. **En el Backend**

Migración de base de datos (automática en FastAPI):
- Al iniciar la aplicación, SQLAlchemy crea la tabla `user_profiles` automáticamente

### 2. **En el Frontend**

Acceder a la página de perfil:
```
http://localhost:8002/profile.html
```

### 3. **Mediante API**

**JavaScript:**
```javascript
// Obtener perfil
const response = await fetch('/api/profile', {
  headers: { 'Authorization': `Bearer ${token}` }
});
const profile = await response.json();

// Actualizar perfil
await fetch('/api/profile', {
  method: 'PUT',
  headers: {
    'Authorization': `Bearer ${token}`,
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    job_title: "Lead Developer",
    department: "Desarrollo",
    language: "es",
    timezone: "America/Bogota"
  })
});
```

## 🔐 Seguridad

- ✅ **Autenticación JWT** requerida en todos los endpoints
- ✅ **Autorización** - Users solo ven su perfil; admins ven todos
- ✅ **Validación** de entrada en todos los campos
- ✅ **Timestamps** automáticos para auditoría
- ✅ **Cascade delete** - Al eliminar usuario, se elimina su perfil

## 📁 Archivos Modificados/Creados

### Modificados:
1. `backend/app/models.py` - Agregado modelo `UserProfile` y relación en `User`
2. `backend/app/schemas.py` - Agregados schemas de perfil
3. `backend/app/crud.py` - Agregadas operaciones CRUD
4. `backend/app/main.py` - Agregados endpoints

### Creados:
1. `frontend/profile.html` - Interfaz web de perfil
2. `PERFIL_API.md` - Documentación completa de API
3. Este archivo: `PERFIL_IMPLEMENTACION.md`

## 🧪 Testing

### Test Manual en cURL

**1. Obtener perfil:**
```bash
curl -H "Authorization: Bearer eyJ..." \
     http://localhost:8000/api/profile
```

**2. Crear/Actualizar perfil:**
```bash
curl -X PUT \
  -H "Authorization: Bearer eyJ..." \
  -H "Content-Type: application/json" \
  -d '{
    "photo_url": "https://example.com/photo.jpg",
    "company": "My Corp",
    "phone": "+57 315 123 4567",
    "job_title": "Developer",
    "department": "Desarrollo",
    "permissions": ["read_tickets", "create_tickets"],
    "channels": ["email", "slack"],
    "language": "es",
    "timezone": "America/Bogota",
    "work_preferences": {
      "notifications_enabled": true,
      "theme": "dark"
    }
  }' \
  http://localhost:8000/api/profile
```

## 📚 Documentación

- **API completa**: Ver `PERFIL_API.md`
- **Ejemplos de uso**: Ver `PERFIL_API.md` (sección "Ejemplos de Uso")
- **Validaciones**: Ver `PERFIL_API.md` (sección "Validación")

## 🎯 Próximos Pasos

Sugerencias para mejoras futuras:

1. **Upload de Foto**
   - Permitir subir foto directamente (no solo URL)
   - Guardar en servidor y generar URL

2. **Notificaciones**
   - Integración real con email, Slack, WhatsApp
   - Validar canales configurados

3. **Permisos Dinámicos**
   - Validar permisos en cada endpoint
   - Sistema RBAC completo

4. **Preferencias Avanzadas**
   - Sincronizar tema con sistema operativo
   - Guardar columnas visibles en tablas

5. **Integración Social**
   - Vincular GitHub, LinkedIn, etc.
   - Importar foto de perfil de redes sociales

## ✅ Checklist de Verificación

- [x] Modelo de base de datos creado
- [x] Migraciones automáticas configuradas
- [x] Schemas de Pydantic validados
- [x] CRUD operations implementadas
- [x] Endpoints REST creados
- [x] Autenticación y autorización
- [x] Interfaz web funcional
- [x] Documentación completa
- [x] Sin errores de sintaxis
- [x] Responsive design

## 🐛 Troubleshooting

**Error: "Table 'user_profiles' not found"**
- Asegúrate de reiniciar el servidor de FastAPI
- SQLAlchemy crea la tabla automáticamente

**Error: 401 Unauthorized**
- Verifica que el token JWT sea válido
- El token debe enviarse con el header `Authorization: Bearer {token}`

**Error: 403 Forbidden**
- Solo users o admins pueden ver sus perfiles
- Admins pueden ver cualquier perfil

**Error al cargar foto en preview**
- Verifica que la URL sea válida
- La imagen debe ser accesible públicamente

## 📞 Soporte

Para preguntas sobre la implementación, consulta:
- `PERFIL_API.md` - Documentación de API
- `backend/app/models.py` - Estructura de modelo
- `frontend/profile.html` - Código frontend

---

**Fecha de Implementación**: 3 de mayo de 2026  
**Versión**: 1.0  
**Estado**: ✅ Completo y funcional
