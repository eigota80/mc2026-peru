# API de Perfil de Usuario

## Descripción General
El sistema de perfiles permite que cada usuario mantenga información completa sobre su identidad, contacto, permisos, departamento, canales, preferencias de localización y personalización de trabajo.

## Estructura del Perfil

```json
{
  "id": 1,
  "user_id": 1,
  
  "photo_url": "https://example.com/photo.jpg",
  "company": "Tech Corp",
  "phone": "+57 1 123 4567",
  "job_title": "Senior Developer",
  
  "department": "Desarrollo",
  
  "permissions": ["read_tickets", "create_tickets", "edit_tickets"],
  "channels": ["email", "slack", "whatsapp"],
  
  "language": "es",
  "timezone": "America/Bogota",
  
  "work_preferences": {
    "notifications_enabled": true,
    "email_on_ticket_assign": true,
    "theme": "dark"
  },
  
  "created_at": "2026-05-03T10:30:00",
  "updated_at": "2026-05-03T11:45:00"
}
```

## Endpoints

### 1. Obtener Mi Perfil
```
GET /api/profile
Authorization: Bearer {token}
```

**Respuesta (200):**
```json
{
  "id": 1,
  "user_id": 1,
  "photo_url": null,
  "company": null,
  "phone": null,
  "job_title": null,
  "department": null,
  "permissions": [],
  "channels": [],
  "language": "es",
  "timezone": "America/Bogota",
  "work_preferences": {},
  "created_at": "2026-05-03T10:30:00",
  "updated_at": "2026-05-03T10:30:00"
}
```

**Notas:**
- Crea automáticamente un perfil si no existe
- Retorna con valores por defecto
- Siempre requiere autenticación

---

### 2. Actualizar Mi Perfil
```
PUT /api/profile
Authorization: Bearer {token}
Content-Type: application/json
```

**Cuerpo de Solicitud:**
```json
{
  "photo_url": "https://example.com/my-photo.jpg",
  "company": "Media Commerce",
  "phone": "+57 315 123 4567",
  "job_title": "Technical Lead",
  "department": "Backend Development",
  "permissions": ["read_tickets", "create_tickets", "edit_tickets", "assign_tickets"],
  "channels": ["email", "slack"],
  "language": "es",
  "timezone": "America/Bogota",
  "work_preferences": {
    "notifications_enabled": true,
    "email_on_ticket_assign": true,
    "theme": "dark",
    "items_per_page": 25
  }
}
```

**Respuesta (200):**
```json
{
  "id": 1,
  "user_id": 1,
  "photo_url": "https://example.com/my-photo.jpg",
  "company": "Media Commerce",
  "phone": "+57 315 123 4567",
  "job_title": "Technical Lead",
  "department": "Backend Development",
  "permissions": ["read_tickets", "create_tickets", "edit_tickets", "assign_tickets"],
  "channels": ["email", "slack"],
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

**Notas:**
- Todos los campos son opcionales
- Solo actualiza los campos enviados
- Los timestamps se actualizan automáticamente

---

### 3. Obtener Perfil de Otro Usuario
```
GET /api/users/{user_id}/profile
Authorization: Bearer {token}
```

**Parámetros:**
- `user_id` (path): ID del usuario cuyo perfil deseas ver

**Respuesta (200):**
Mismo formato que obtener mi perfil

**Errores:**
- `403 Forbidden`: Si no eres admin y no es tu perfil
- `404 Not Found`: Si el usuario no existe

**Notas:**
- Solo administradores pueden ver perfiles de otros usuarios
- Un usuario siempre puede ver su propio perfil
- Si el perfil no existe, se crea automáticamente

---

## Campos Disponibles

### Identidad
| Campo | Tipo | Descripción | Máx. caracteres |
|-------|------|-------------|-----------------| 
| `photo_url` | string | URL de la foto de perfil | 500 |
| `company` | string | Empresa del usuario | 180 |
| `phone` | string | Número telefónico | 20 |
| `job_title` | string | Puesto del usuario | 120 |

### Estructura
| Campo | Tipo | Descripción | Máx. caracteres |
|-------|------|-------------|-----------------| 
| `department` | string | Departamento | 120 |

### Acceso y Comunicación
| Campo | Tipo | Descripción |
|-------|------|-------------|
| `permissions` | array[string] | Lista de permisos (ej: "read_tickets", "create_tickets") | 
| `channels` | array[string] | Canales de comunicación (ej: "email", "slack", "whatsapp") | 

### Localización
| Campo | Tipo | Descripción | Default |
|-------|------|-------------|---------|
| `language` | string | Código de idioma (ej: "es", "en", "fr") | "es" |
| `timezone` | string | Zona horaria IANA (ej: "America/Bogota") | "America/Bogota" |

### Personalización
| Campo | Tipo | Descripción |
|-------|------|-------------|
| `work_preferences` | object | Configuraciones personalizadas (flexible) |

### Ejemplos de `work_preferences`
```json
{
  "notifications_enabled": true,
  "email_on_ticket_assign": true,
  "email_on_ticket_comment": false,
  "theme": "dark",
  "items_per_page": 25,
  "auto_refresh": false,
  "show_resolved_tickets": true,
  "default_priority": "medium"
}
```

---

## Ejemplos de Uso (JavaScript/Frontend)

### Obtener perfil
```javascript
async function getMyProfile(token) {
  const response = await fetch('/api/profile', {
    method: 'GET',
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json'
    }
  });
  return response.json();
}
```

### Actualizar perfil
```javascript
async function updateMyProfile(token, profileData) {
  const response = await fetch('/api/profile', {
    method: 'PUT',
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json'
    },
    body: JSON.stringify(profileData)
  });
  return response.json();
}
```

### Ejemplo completo - Formulario de perfil
```javascript
async function saveProfile(formData) {
  const token = localStorage.getItem('access_token');
  
  const profilePayload = {
    photo_url: formData.photoUrl,
    company: formData.company,
    phone: formData.phone,
    job_title: formData.jobTitle,
    department: formData.department,
    permissions: formData.permissions || [],
    channels: formData.channels || [],
    language: formData.language || 'es',
    timezone: formData.timezone || 'America/Bogota',
    work_preferences: {
      notifications_enabled: formData.notificationsEnabled,
      email_on_ticket_assign: formData.emailOnAssign,
      theme: formData.theme,
      items_per_page: formData.itemsPerPage
    }
  };
  
  try {
    const response = await fetch('/api/profile', {
      method: 'PUT',
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify(profilePayload)
    });
    
    if (!response.ok) {
      throw new Error('Error actualizando perfil');
    }
    
    const updatedProfile = await response.json();
    console.log('Perfil actualizado:', updatedProfile);
    return updatedProfile;
  } catch (error) {
    console.error('Error:', error);
  }
}
```

---

## Códigos de Estado HTTP

| Código | Significado |
|--------|------------|
| 200 | OK - Operación exitosa |
| 201 | Created - Recurso creado |
| 400 | Bad Request - Datos inválidos |
| 401 | Unauthorized - No autenticado |
| 403 | Forbidden - No autorizado |
| 404 | Not Found - Recurso no encontrado |
| 500 | Internal Server Error - Error del servidor |

---

## Notas de Seguridad

- 🔒 Todos los endpoints requieren autenticación (token JWT)
- 👤 Los usuarios solo pueden ver/editar su propio perfil
- 👨‍💼 Los administradores pueden ver perfiles de cualquier usuario
- 🔐 Los permisos son informativos; el servidor valida permisos en cada solicitud
- 📝 Los cambios se auditan con timestamps automáticos

---

## Permisos Sugeridos

Usa estos valores para el campo `permissions`:
- `read_tickets` - Ver tickets
- `create_tickets` - Crear tickets
- `edit_tickets` - Editar tickets
- `delete_tickets` - Eliminar tickets
- `assign_tickets` - Asignar tickets a otros
- `manage_users` - Gestionar usuarios (admin)
- `view_reports` - Ver reportes
- `manage_settings` - Gestionar configuración (admin)

---

## Canales Sugeridos

Usa estos valores para el campo `channels`:
- `email` - Notificaciones por correo
- `slack` - Integración con Slack
- `whatsapp` - Integración con WhatsApp
- `sms` - Notificaciones por SMS
- `in_app` - Notificaciones en la app

---

## Lenguajes y Zonas Horarias

### Lenguajes Soportados
- `es` - Español (defecto)
- `en` - English
- `fr` - Français
- `pt` - Português

### Zonas Horarias Comunes
- `America/Bogota` - Colombia (defecto)
- `America/Mexico_City` - México
- `America/New_York` - USA (Eastern)
- `America/Los_Angeles` - USA (Pacific)
- `Europe/Madrid` - España
- `America/Buenos_Aires` - Argentina
- [Ver lista completa](https://en.wikipedia.org/wiki/List_of_tz_database_time_zones)

---

## Validación

- `photo_url`: máximo 500 caracteres
- `company`: máximo 180 caracteres
- `phone`: máximo 20 caracteres
- `job_title`: máximo 120 caracteres
- `department`: máximo 120 caracteres
- `language`: 2-10 caracteres
- `timezone`: máximo 50 caracteres
- `permissions`: array de strings
- `channels`: array de strings
- `work_preferences`: objeto JSON flexible

