-- MariaDB schema draft for the future persistence layer.
-- Current production data remains in browser localStorage until migration is approved.

CREATE TABLE IF NOT EXISTS roles (
	id INT AUTO_INCREMENT PRIMARY KEY,
	nombre VARCHAR(80) NOT NULL UNIQUE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS usuarios (
	id VARCHAR(64) PRIMARY KEY,
	nombre VARCHAR(160) NOT NULL,
	email VARCHAR(190) NOT NULL UNIQUE,
	password_hash VARCHAR(128) NOT NULL,
	rol_id INT NOT NULL,
	estado ENUM('activo', 'inactivo') NOT NULL DEFAULT 'activo',
	created_at DATETIME NOT NULL,
	updated_at DATETIME NULL,
	CONSTRAINT fk_usuarios_roles FOREIGN KEY (rol_id) REFERENCES roles(id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS clientes (
	id VARCHAR(64) PRIMARY KEY,
	razon_social VARCHAR(220) NOT NULL,
	ruc_dni VARCHAR(32) NOT NULL,
	representante_legal VARCHAR(180) NULL,
	telefono VARCHAR(80) NULL,
	domicilio VARCHAR(260) NULL,
	contacto_tecnico VARCHAR(180) NULL,
	contacto_administrativo VARCHAR(180) NULL,
	email VARCHAR(190) NULL,
	created_at DATETIME NOT NULL,
	updated_at DATETIME NULL,
	UNIQUE KEY uq_clientes_documento (ruc_dni),
	KEY idx_clientes_razon_social (razon_social)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS ordenes_servicio (
	id VARCHAR(64) PRIMARY KEY,
	numero_os VARCHAR(12) NOT NULL UNIQUE,
	cliente_id VARCHAR(64) NOT NULL,
	fecha DATE NOT NULL,
	moneda VARCHAR(12) NOT NULL,
	duracion VARCHAR(80) NULL,
	tipo_servicio VARCHAR(80) NULL,
	mrc DECIMAL(12,2) NOT NULL DEFAULT 0,
	costo_instalacion ENUM('si', 'no') NOT NULL DEFAULT 'no',
	nrc DECIMAL(12,2) NULL,
	observacion TEXT NULL,
	facilidades_pago TEXT NULL,
	estado VARCHAR(80) NOT NULL DEFAULT 'Creada',
	created_by VARCHAR(64) NOT NULL,
	updated_by VARCHAR(64) NULL,
	created_at DATETIME NOT NULL,
	updated_at DATETIME NULL,
	CONSTRAINT fk_os_cliente FOREIGN KEY (cliente_id) REFERENCES clientes(id),
	CONSTRAINT fk_os_created_by FOREIGN KEY (created_by) REFERENCES usuarios(id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS ordenes_detalle (
	id BIGINT AUTO_INCREMENT PRIMARY KEY,
	orden_id VARCHAR(64) NOT NULL,
	ciudad VARCHAR(120) NULL,
	direccion_origen TEXT NULL,
	direccion_destino TEXT NULL,
	detalle TEXT NULL,
	servicio TEXT NULL,
	dias_entrega INT NULL,
	renta DECIMAL(12,2) NULL,
	CONSTRAINT fk_detalle_orden FOREIGN KEY (orden_id) REFERENCES ordenes_servicio(id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS cotizaciones (
	id VARCHAR(64) PRIMARY KEY,
	numero_cot VARCHAR(12) NOT NULL UNIQUE,
	cliente_id VARCHAR(64) NULL,
	fecha DATE NOT NULL,
	moneda VARCHAR(12) NOT NULL,
	tipo VARCHAR(80) NULL,
	duracion VARCHAR(80) NULL,
	comercial VARCHAR(180) NULL,
	valor_instalacion DECIMAL(12,2) NOT NULL DEFAULT 0,
	observacion TEXT NULL,
	estado VARCHAR(80) NOT NULL DEFAULT 'NUEVA',
	created_by VARCHAR(64) NOT NULL,
	updated_by VARCHAR(64) NULL,
	created_at DATETIME NOT NULL,
	updated_at DATETIME NULL,
	CONSTRAINT fk_cot_cliente FOREIGN KEY (cliente_id) REFERENCES clientes(id),
	CONSTRAINT fk_cot_created_by FOREIGN KEY (created_by) REFERENCES usuarios(id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS cotizaciones_detalle (
	id BIGINT AUTO_INCREMENT PRIMARY KEY,
	cotizacion_id VARCHAR(64) NOT NULL,
	ciudad VARCHAR(120) NULL,
	servicio VARCHAR(180) NULL,
	renta DECIMAL(12,2) NOT NULL DEFAULT 0,
	dias_entrega INT NULL,
	direccion_origen TEXT NULL,
	direccion_destino TEXT NULL,
	detalle TEXT NULL,
	CONSTRAINT fk_cot_detalle FOREIGN KEY (cotizacion_id) REFERENCES cotizaciones(id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS auditoria (
	id VARCHAR(64) PRIMARY KEY,
	fecha DATETIME NOT NULL,
	usuario VARCHAR(190) NOT NULL,
	accion VARCHAR(160) NOT NULL,
	entidad VARCHAR(220) NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
