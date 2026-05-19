(function () {
	'use strict';

	const USERS_KEY = 'mcperu_os_users';
	const USERS_SEED_VERSION_KEY = 'mcperu_os_users_seed_version';
	const SESSION_KEY = 'mcperu_os_session';
	const AUDIT_KEY = 'mcperu_os_audit';
	const CLIENTS_KEY = 'mcperu_os_clients';
	const USER_SEED_VERSION = 'cotizaciones-mediacommerce-20260518-v2';

	const seedUsers = [
		{ nombre: 'Renato Mejia', email: 'renato.mejia@mcperu.pe', password: 'MejiaRenato2023+', rol: 'comercial' },
		{ nombre: 'Milagros Ravenna', email: 'milagros.ravenna@mcperu.pe', password: 'RAVENNA2025+', rol: 'comercial' },
		{ nombre: 'Natanael Vargas', email: 'natanael.vargas@mcperu.pe', password: 'VarNata2023+', rol: 'comercial' },
		{ nombre: 'Jorge Hesse', email: 'jorge.hesse@mcperu.pe', password: 'hessejorge2024+', rol: 'comercial' },
		{ nombre: 'Eider Gonzalez', email: 'eider.gonzalez@mcperu.pe', password: 'GonzalezEider2024+', rol: 'administrador' },
		{ nombre: 'Gianpierre Velasquez', email: 'gianpierre.velasquez@mcperu.pe', password: 'GianVelasquez2024+', rol: 'comercial' },
		{ nombre: 'Gene Quispe', email: 'gene.quispe@mcperu.pe', password: 'MCPERU123', rol: 'comercial' }
	];

	const legacySeedEmails = [
		'admin@mediacommerce.pe',
		'comercial@mediacommerce.pe',
		'operaciones@mediacommerce.pe',
		'facturacion@mediacommerce.pe'
	];

	function readStore(key, fallback) {
		try {
			const value = JSON.parse(localStorage.getItem(key) || 'null');
			return value === null ? fallback : value;
		} catch (e) {
			return fallback;
		}
	}

	function writeStore(key, value) {
		localStorage.setItem(key, JSON.stringify(value));
	}

	function makeId(prefix) {
		return `${prefix}_${Date.now().toString(36)}_${Math.random().toString(36).slice(2, 8)}`;
	}

	async function hashPassword(password) {
		const raw = String(password || '');
		if (window.crypto && window.crypto.subtle && window.TextEncoder) {
			const encoded = new TextEncoder().encode(raw);
			const digest = await window.crypto.subtle.digest('SHA-256', encoded);
			return Array.from(new Uint8Array(digest)).map((b) => b.toString(16).padStart(2, '0')).join('');
		}
		let hash = 2166136261;
		for (let i = 0; i < raw.length; i += 1) {
			hash ^= raw.charCodeAt(i);
			hash += (hash << 1) + (hash << 4) + (hash << 7) + (hash << 8) + (hash << 24);
		}
		return `local-${(hash >>> 0).toString(16)}`;
	}

	async function seedUserRecord(user, existing) {
		const now = new Date().toISOString();
		const data = {
			nombre: user.nombre,
			email: user.email.toLowerCase(),
			password_hash: await hashPassword(user.password),
			rol: user.rol,
			estado: 'activo'
		};
		return existing
			? Object.assign({}, existing, data, { updated_at: now })
			: Object.assign({ id: makeId('usr'), created_at: now }, data);
	}

	async function ensureSeedData() {
		let users = readStore(USERS_KEY, []);
		const storedVersion = localStorage.getItem(USERS_SEED_VERSION_KEY);
		users = users.filter((u) => !legacySeedEmails.includes(String(u.email || '').toLowerCase()));
		for (const user of seedUsers) {
			const email = user.email.toLowerCase();
			const index = users.findIndex((u) => String(u.email || '').toLowerCase() === email);
			if (storedVersion !== USER_SEED_VERSION || index < 0) {
				const record = await seedUserRecord(user, index >= 0 ? users[index] : null);
				if (index >= 0) {
					users[index] = record;
				} else {
					users.push(record);
				}
			}
		}
		writeStore(USERS_KEY, users);
		localStorage.setItem(USERS_SEED_VERSION_KEY, USER_SEED_VERSION);

		const clients = readStore(CLIENTS_KEY, []);
		if (!clients.length) {
			writeStore(CLIENTS_KEY, [
				{
					id: makeId('cli'),
					razon_social: 'CIRION TECHNOLOGIES PERU S.A.',
					ruc_dni: '20552504641',
					representante_legal: '',
					telefono: '(+51) 748-4200',
					domicilio: 'Lima, Peru',
					contacto_tecnico: '',
					contacto_administrativo: '',
					email: '',
					created_at: new Date().toISOString()
				},
				{
					id: makeId('cli'),
					razon_social: 'MEDIA COMMERCE ECUADOR',
					ruc_dni: '1792225906001',
					representante_legal: '',
					telefono: '',
					domicilio: 'Quito, Ecuador',
					contacto_tecnico: '',
					contacto_administrativo: '',
					email: '',
					created_at: new Date().toISOString()
				}
			]);
		}
	}

	function setMessage(text, type) {
		const el = document.getElementById('loginMessage');
		if (!el) {
			return;
		}
		el.textContent = text || '';
		el.dataset.type = type || 'info';
		el.hidden = !text;
	}

	async function login(event) {
		event.preventDefault();
		const email = document.getElementById('loginEmail').value.trim().toLowerCase();
		const password = document.getElementById('loginPassword').value;
		const passwordHash = await hashPassword(password);
		let users = readStore(USERS_KEY, []);
		let user = users.find((u) => u.email === email && u.estado === 'activo');

		if ((!user || user.password_hash !== passwordHash) && seedUsers.some((u) => u.email.toLowerCase() === email && u.password === password)) {
			const seedUser = seedUsers.find((u) => u.email.toLowerCase() === email);
			const index = users.findIndex((u) => u.email === email);
			user = await seedUserRecord(seedUser, index >= 0 ? users[index] : null);
			if (index >= 0) {
				users[index] = user;
			} else {
				users.push(user);
			}
			writeStore(USERS_KEY, users);
			localStorage.setItem(USERS_SEED_VERSION_KEY, USER_SEED_VERSION);
		}

		if (!user || user.password_hash !== passwordHash) {
			setMessage('Credenciales invalidas o usuario inactivo.', 'error');
			return;
		}

		const audit = readStore(AUDIT_KEY, []);
		audit.unshift({
			id: makeId('aud'),
			fecha: new Date().toISOString(),
			usuario: user.email,
			accion: 'inicio sesion',
			entidad: user.email
		});
		writeStore(AUDIT_KEY, audit.slice(0, 300));
		writeStore(SESSION_KEY, { user_id: user.id, started_at: new Date().toISOString() });

		window.location.href = 'index.html';
	}

	async function init() {
		const session = readStore(SESSION_KEY, null);
		if (session) {
			const users = readStore(USERS_KEY, []);
			const active = users.find((u) => u.id === session.user_id && u.estado === 'activo');
			if (active) {
				window.location.href = 'index.html';
				return;
			}
		}
		await ensureSeedData();
		document.getElementById('loginForm').addEventListener('submit', login);
	}

	document.addEventListener('DOMContentLoaded', init);
}());
