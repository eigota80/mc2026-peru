CREATE TABLE IF NOT EXISTS roles (
	id INT UNSIGNED NOT NULL AUTO_INCREMENT,
	nombre VARCHAR(50) NOT NULL,
	created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
	PRIMARY KEY (id),
	UNIQUE KEY uq_roles_nombre (nombre)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS usuarios (
	id INT UNSIGNED NOT NULL AUTO_INCREMENT,
	nombre VARCHAR(160) NOT NULL,
	email VARCHAR(190) NOT NULL,
	password_hash VARCHAR(255) NOT NULL,
	rol_id INT UNSIGNED NOT NULL,
	estado ENUM('activo', 'inactivo') NOT NULL DEFAULT 'activo',
	created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
	updated_at TIMESTAMP NULL DEFAULT NULL ON UPDATE CURRENT_TIMESTAMP,
	PRIMARY KEY (id),
	UNIQUE KEY uq_usuarios_email (email),
	KEY idx_usuarios_rol_id (rol_id),
	CONSTRAINT fk_usuarios_roles
		FOREIGN KEY (rol_id) REFERENCES roles (id)
		ON UPDATE CASCADE
		ON DELETE RESTRICT
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS clientes (
	id INT UNSIGNED NOT NULL AUTO_INCREMENT,
	razon_social VARCHAR(220) NOT NULL,
	ruc_dni VARCHAR(30) NOT NULL,
	representante_legal VARCHAR(180) NULL,
	telefono VARCHAR(60) NULL,
	domicilio VARCHAR(255) NULL,
	contacto_tecnico VARCHAR(180) NULL,
	contacto_administrativo VARCHAR(180) NULL,
	email VARCHAR(190) NULL,
	created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
	updated_at TIMESTAMP NULL DEFAULT NULL ON UPDATE CURRENT_TIMESTAMP,
	PRIMARY KEY (id),
	UNIQUE KEY uq_clientes_ruc_dni (ruc_dni),
	KEY idx_clientes_razon_social (razon_social)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS ordenes_servicio (
	id INT UNSIGNED NOT NULL AUTO_INCREMENT,
	numero_os VARCHAR(20) NOT NULL,
	cliente_id INT UNSIGNED NOT NULL,
	fecha DATE NOT NULL,
	moneda VARCHAR(12) NOT NULL DEFAULT 'USD',
	duracion VARCHAR(80) NULL,
	tipo_servicio VARCHAR(80) NOT NULL,
	mrc DECIMAL(12,2) NOT NULL DEFAULT 0.00,
	costo_instalacion ENUM('si', 'no') NOT NULL DEFAULT 'no',
	nrc DECIMAL(12,2) NOT NULL DEFAULT 0.00,
	observacion TEXT NULL,
	facilidades_pago TEXT NULL,
	estado ENUM('Creada', 'En validacion', 'Instalacion validada', 'Facturacion validada', 'Activada', 'Anulada') NOT NULL DEFAULT 'Creada',
	created_by INT UNSIGNED NOT NULL,
	created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
	updated_by INT UNSIGNED NULL,
	updated_at TIMESTAMP NULL DEFAULT NULL ON UPDATE CURRENT_TIMESTAMP,
	PRIMARY KEY (id),
	UNIQUE KEY uq_ordenes_numero_os (numero_os),
	KEY idx_ordenes_cliente_id (cliente_id),
	KEY idx_ordenes_created_by (created_by),
	KEY idx_ordenes_estado (estado),
	CONSTRAINT fk_ordenes_clientes
		FOREIGN KEY (cliente_id) REFERENCES clientes (id)
		ON UPDATE CASCADE
		ON DELETE RESTRICT,
	CONSTRAINT fk_ordenes_created_by
		FOREIGN KEY (created_by) REFERENCES usuarios (id)
		ON UPDATE CASCADE
		ON DELETE RESTRICT,
	CONSTRAINT fk_ordenes_updated_by
		FOREIGN KEY (updated_by) REFERENCES usuarios (id)
		ON UPDATE CASCADE
		ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS ordenes_detalle (
	id INT UNSIGNED NOT NULL AUTO_INCREMENT,
	orden_id INT UNSIGNED NOT NULL,
	ciudad VARCHAR(120) NULL,
	direccion_origen TEXT NULL,
	direccion_destino TEXT NULL,
	detalle TEXT NULL,
	servicio TEXT NULL,
	dias_entrega INT UNSIGNED NULL,
	renta DECIMAL(12,2) NOT NULL DEFAULT 0.00,
	nrc DECIMAL(12,2) NOT NULL DEFAULT 0.00,
	created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
	PRIMARY KEY (id),
	KEY idx_detalle_orden_id (orden_id),
	CONSTRAINT fk_detalle_ordenes
		FOREIGN KEY (orden_id) REFERENCES ordenes_servicio (id)
		ON UPDATE CASCADE
		ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS auditoria_cambios (
	id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
	usuario_id INT UNSIGNED NULL,
	entidad VARCHAR(80) NOT NULL,
	entidad_id VARCHAR(80) NULL,
	accion VARCHAR(120) NOT NULL,
	datos_previos JSON NULL,
	datos_nuevos JSON NULL,
	created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
	PRIMARY KEY (id),
	KEY idx_auditoria_usuario_id (usuario_id),
	KEY idx_auditoria_entidad (entidad, entidad_id),
	CONSTRAINT fk_auditoria_usuarios
		FOREIGN KEY (usuario_id) REFERENCES usuarios (id)
		ON UPDATE CASCADE
		ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

INSERT INTO roles (nombre)
VALUES ('administrador'), ('comercial'), ('operaciones'), ('facturacion')
ON DUPLICATE KEY UPDATE nombre = VALUES(nombre);
