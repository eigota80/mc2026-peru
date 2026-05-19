(function () {
	'use strict';

	const STORAGE_KEY = 'mcperu_service_order_next_number';
	const DRAFT_KEY = 'mcperu_service_order_draft';
	const SESSION_KEY = 'mcperu_os_session';
	const USERS_KEY = 'mcperu_os_users';
	const USERS_SEED_VERSION_KEY = 'mcperu_os_users_seed_version';
	const CLIENTS_KEY = 'mcperu_os_clients';
	const ORDERS_KEY = 'mcperu_os_orders';
	const AUDIT_KEY = 'mcperu_os_audit';
	const START_NUMBER = 700;
	const USER_SEED_VERSION = 'cotizaciones-mediacommerce-20260518-v2';
	const LOGO_PATH = 'images/controls/brand/logo-media-commerce.png';
	const PAGE = { width: 595.276, height: 841.89 };
	const CP1252 = {
		'€': 128,
		'‚': 130,
		'ƒ': 131,
		'„': 132,
		'…': 133,
		'†': 134,
		'‡': 135,
		'ˆ': 136,
		'‰': 137,
		'Š': 138,
		'‹': 139,
		'Œ': 140,
		'Ž': 142,
		'‘': 145,
		'’': 146,
		'“': 147,
		'”': 148,
		'•': 149,
		'–': 150,
		'—': 151,
		'˜': 152,
		'™': 153,
		'š': 154,
		'›': 155,
		'œ': 156,
		'ž': 158,
		'Ÿ': 159
	};

	const roles = {
		administrador: {
			label: 'Administrador',
			permissions: ['manage_users', 'create_clients', 'create_orders', 'update_orders', 'validate_billing', 'print_pdf']
		},
		comercial: {
			label: 'Comercial',
			permissions: ['create_clients', 'create_orders', 'print_pdf']
		},
		operaciones: {
			label: 'Operaciones',
			permissions: ['update_orders', 'print_pdf']
		},
		facturacion: {
			label: 'Facturacion',
			permissions: ['validate_billing', 'print_pdf']
		}
	};

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

	const orderFields = [
		'fecha',
		'direccion',
		'telefono',
		'moneda',
		'duracion',
		'tipoServicio',
		'ciudad',
		'diasEntrega',
		'direccionOrigen',
		'direccionDestino',
		'detalle',
		'servicio',
		'mrc',
		'costoInstalacion',
		'nrc',
		'observacion',
		'facilidadesPago'
	];

	let currentUser = null;
	let selectedClientId = null;
	let lastClientSearch = '';
	let logoImagePromise = null;

	const els = {};

	function byId(id) {
		return document.getElementById(id);
	}

	function readStore(key, fallback) {
		try {
			const value = JSON.parse(localStorage.getItem(key) || 'null');
			return value === null ? fallback : value;
		} catch (error) {
			return fallback;
		}
	}

	function writeStore(key, value) {
		localStorage.setItem(key, JSON.stringify(value));
	}

	function makeId(prefix) {
		return `${prefix}_${Date.now().toString(36)}_${Math.random().toString(36).slice(2, 8)}`;
	}

	function normalize(value) {
		return String(value || '')
			.normalize('NFD')
			.replace(/[\u0300-\u036f]/g, '')
			.replace(/[^a-z0-9]/gi, '')
			.toLowerCase();
	}

	function escapeHtml(value) {
		return String(value || '')
			.replace(/&/g, '&amp;')
			.replace(/</g, '&lt;')
			.replace(/>/g, '&gt;')
			.replace(/"/g, '&quot;')
			.replace(/'/g, '&#039;');
	}

	function parseMoney(value) {
		const parsed = parseFloat(String(value || '0').replace(',', '.'));
		return Number.isFinite(parsed) ? parsed : 0;
	}

	function formatMoney(value) {
		return parseMoney(value).toLocaleString('en-US', {
			minimumFractionDigits: 2,
			maximumFractionDigits: 2
		});
	}

	function hasInstallationCost(value) {
		if (!value) {
			return false;
		}
		return String(value).toLowerCase() === 'si';
	}

	function todayISO() {
		const now = new Date();
		const offset = now.getTimezoneOffset();
		const local = new Date(now.getTime() - offset * 60000);
		return local.toISOString().slice(0, 10);
	}

	function getRole(user) {
		return roles[(user && user.rol) || ''] || roles.comercial;
	}

	function hasPermission(permission) {
		if (!currentUser) {
			return false;
		}
		return getRole(currentUser).permissions.includes(permission);
	}

	function setMessage(element, text, type) {
		if (!element) {
			return;
		}
		element.textContent = text || '';
		element.dataset.type = type || 'info';
		element.hidden = !text;
	}

	async function hashPassword(password) {
		const raw = String(password || '');
		if (window.crypto && window.crypto.subtle && window.TextEncoder) {
			const encoded = new TextEncoder().encode(raw);
			const digest = await window.crypto.subtle.digest('SHA-256', encoded);
			return Array.from(new Uint8Array(digest)).map((byte) => byte.toString(16).padStart(2, '0')).join('');
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
		return existing ? Object.assign({}, existing, data, { updated_at: now }) : Object.assign({ id: makeId('usr'), created_at: now }, data);
	}

	async function ensureSeedData() {
		let users = readStore(USERS_KEY, []);
		const storedSeedVersion = localStorage.getItem(USERS_SEED_VERSION_KEY);
		users = users.filter((user) => !legacySeedEmails.includes(String(user.email || '').toLowerCase()));
		for (const user of seedUsers) {
			const email = user.email.toLowerCase();
			const index = users.findIndex((item) => String(item.email || '').toLowerCase() === email);
			const shouldRefreshSeed = storedSeedVersion !== USER_SEED_VERSION || index < 0;
			if (shouldRefreshSeed) {
				const existing = index >= 0 ? users[index] : null;
				const record = await seedUserRecord(user, existing);
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

	function audit(action, entity) {
		const items = readStore(AUDIT_KEY, []);
		items.unshift({
			id: makeId('aud'),
			fecha: new Date().toISOString(),
			usuario: currentUser ? currentUser.email : 'sistema',
			accion: action,
			entidad: entity
		});
		writeStore(AUDIT_KEY, items.slice(0, 300));
	}

	function getUsers() {
		return readStore(USERS_KEY, []);
	}

	function saveUsers(users) {
		writeStore(USERS_KEY, users);
	}

	function getClients() {
		return readStore(CLIENTS_KEY, []);
	}

	function saveClients(clients) {
		writeStore(CLIENTS_KEY, clients);
	}

	function getOrders() {
		return readStore(ORDERS_KEY, []);
	}

	function getVisibleOrders() {
		const orders = getOrders();
		if (hasPermission('manage_users')) {
			return orders;
		}
		return orders.filter((order) => order.created_by === currentUser.id);
	}

	function saveOrders(orders) {
		writeStore(ORDERS_KEY, orders);
	}

	function findClient(id) {
		return getClients().find((client) => client.id === id) || null;
	}

	function padOrderNumber(value) {
		const clean = String(value || '').replace(/\D/g, '');
		const parsed = parseInt(clean || START_NUMBER, 10);
		return String(parsed).padStart(6, '0');
	}

	function getNextNumber() {
		const saved = parseInt(localStorage.getItem(STORAGE_KEY), 10);
		if (Number.isFinite(saved) && saved >= 0) {
			return saved;
		}
		localStorage.setItem(STORAGE_KEY, String(START_NUMBER));
		return START_NUMBER;
	}

	function setNextNumber(value) {
		const parsed = parseInt(String(value || '').replace(/\D/g, ''), 10);
		const next = Number.isFinite(parsed) ? parsed : START_NUMBER;
		localStorage.setItem(STORAGE_KEY, String(next));
		updateCounterView();
		audit('actualizo consecutivo', `OS ${padOrderNumber(next)}`);
	}

	function updateCounterView() {
		if (!els.preview || !els.nextInput) {
			return;
		}
		const formatted = padOrderNumber(getNextNumber());
		els.preview.textContent = formatted;
		els.nextInput.value = formatted;
	}

	function getOrderFormData() {
		return orderFields.reduce((data, name) => {
			const el = byId(name);
			data[name] = el ? String(el.value || '').trim() : '';
			return data;
		}, {});
	}

	function saveDraft() {
		writeStore(DRAFT_KEY, {
			selectedClientId,
			fields: getOrderFormData()
		});
	}

	function restoreDraft() {
		const draft = readStore(DRAFT_KEY, {});
		const data = draft.fields || {};
		orderFields.forEach((name) => {
			const el = byId(name);
			if (el && Object.prototype.hasOwnProperty.call(data, name)) {
				el.value = data[name];
			}
		});
		if (draft.selectedClientId && findClient(draft.selectedClientId)) {
			selectedClientId = draft.selectedClientId;
		}
		if (byId('fecha') && !byId('fecha').value) {
			byId('fecha').value = todayISO();
		}
		updateInstallationCostState(false);
		renderSelectedClient();
	}

	function clearOrderForm() {
		if (!window.confirm('Limpiar los datos de la orden?')) {
			return;
		}
		els.orderForm.reset();
		byId('fecha').value = todayISO();
		selectedClientId = null;
		localStorage.removeItem(DRAFT_KEY);
		updateInstallationCostState(false);
		renderSelectedClient();
	}

	function updateInstallationCostState(shouldSave) {
		const select = byId('costoInstalacion');
		const nrc = byId('nrc');
		if (!select || !nrc) {
			return;
		}
		const enabled = hasInstallationCost(select.value);
		nrc.disabled = !enabled;
		nrc.required = enabled;
		if (!enabled) {
			nrc.value = '';
		}
		if (shouldSave) {
			saveDraft();
		}
	}

	function showApp() {
		els.loginView.hidden = true;
		els.appView.hidden = false;
		els.sessionName.textContent = currentUser.nombre;
		els.sessionRole.textContent = getRole(currentUser).label;
		applyPermissions();
		renderAll();
	}

	function showLogin() {
		els.appView.hidden = true;
		els.loginView.hidden = false;
		els.loginForm.reset();
		setMessage(els.loginMessage, '', 'info');
	}

	function setView(name) {
		if (['usuarios', 'auditoria'].includes(name) && !hasPermission('manage_users')) {
			return;
		}
		let activeView = null;
		document.querySelectorAll('.os-view').forEach((view) => {
			const active = view.id === `${name}View`;
			view.classList.toggle('is-active', active);
			view.hidden = !active;
			if (active) {
				els.viewTitle.textContent = view.dataset.title || 'Dashboard';
				activeView = view;
			}
		});
		document.querySelectorAll('.os-nav-button').forEach((button) => {
			button.classList.toggle('is-active', button.dataset.view === name);
		});
		if (activeView) {
			window.scrollTo({ top: 0, behavior: 'smooth' });
		}
	}

	function applyPermissions() {
		document.querySelectorAll('[data-permission]').forEach((element) => {
			const allowed = hasPermission(element.dataset.permission);
			element.hidden = !allowed;
			if ('disabled' in element) {
				element.disabled = !allowed;
			}
		});
		if (!hasPermission('create_orders')) {
			els.orderForm.querySelectorAll('input, select, textarea').forEach((field) => {
				field.disabled = true;
			});
		} else {
			els.orderForm.querySelectorAll('input, select, textarea').forEach((field) => {
				field.disabled = false;
			});
		}
	}

	async function login(event) {
		event.preventDefault();
		const email = els.loginEmail.value.trim().toLowerCase();
		const password = els.loginPassword.value;
		const passwordHash = await hashPassword(password);
		let user = getUsers().find((item) => item.email === email && item.estado === 'activo');
		if ((!user || user.password_hash !== passwordHash) && seedUsers.some((item) => item.email.toLowerCase() === email && item.password === password)) {
			const seedUser = seedUsers.find((item) => item.email.toLowerCase() === email);
			const users = getUsers();
			const index = users.findIndex((item) => item.email === email);
			user = await seedUserRecord(seedUser, index >= 0 ? users[index] : null);
			if (index >= 0) {
				users[index] = user;
			} else {
				users.push(user);
			}
			saveUsers(users);
			localStorage.setItem(USERS_SEED_VERSION_KEY, USER_SEED_VERSION);
		}
		if (!user || user.password_hash !== passwordHash) {
			setMessage(els.loginMessage, 'Credenciales invalidas o usuario inactivo.', 'error');
			return;
		}
		currentUser = user;
		writeStore(SESSION_KEY, { user_id: user.id, started_at: new Date().toISOString() });
		audit('inicio sesion', user.email);
		showApp();
		setView('dashboard');
	}

	function resumeSession() {
		const session = readStore(SESSION_KEY, null);
		const user = session ? getUsers().find((item) => item.id === session.user_id && item.estado === 'activo') : null;
		if (!user) {
			showLogin();
			return;
		}
		currentUser = user;
		showApp();
		setView('dashboard');
	}

	function logout() {
		audit('cerro sesion', currentUser ? currentUser.email : '');
		localStorage.removeItem(SESSION_KEY);
		currentUser = null;
		showLogin();
	}

	function searchClients(query) {
		const term = normalize(query);
		if (!term) {
			return [];
		}
		return getClients().filter((client) => {
			return normalize(client.ruc_dni).includes(term) || normalize(client.razon_social).includes(term);
		});
	}

	function renderClientResults(results) {
		if (!lastClientSearch) {
			els.clientResults.innerHTML = '';
			els.clientSearchState.textContent = 'Busqueda requerida';
			return;
		}
		els.clientSearchState.textContent = results.length ? `${results.length} resultado(s)` : 'Sin coincidencias';
		if (!results.length) {
			els.clientResults.innerHTML = '<p class="os-empty">No se encontraron clientes con ese criterio.</p>';
			return;
		}
		els.clientResults.innerHTML = results.map((client) => `
			<article class="os-result-card">
				<div>
					<strong>${escapeHtml(client.razon_social)}</strong>
					<span>${escapeHtml(client.ruc_dni)} | ${escapeHtml(client.telefono || 'Sin telefono')}</span>
				</div>
				<button type="button" class="os-button os-button-secondary" data-select-client="${escapeHtml(client.id)}">Usar cliente</button>
			</article>
		`).join('');
	}

	function handleClientSearch(event) {
		event.preventDefault();
		lastClientSearch = els.clientSearch.value.trim();
		renderClientResults(searchClients(lastClientSearch));
	}

	function fillClientForm(client) {
		byId('clienteId').value = client ? client.id : '';
		byId('clienteRazonSocial').value = client ? client.razon_social : '';
		byId('clienteDocumento').value = client ? client.ruc_dni : '';
		byId('clienteRepresentante').value = client ? client.representante_legal : '';
		byId('clienteTelefono').value = client ? client.telefono : '';
		byId('clienteDomicilio').value = client ? client.domicilio : '';
		byId('clienteEmail').value = client ? client.email : '';
		byId('clienteContactoTecnico').value = client ? client.contacto_tecnico : '';
		byId('clienteContactoAdministrativo').value = client ? client.contacto_administrativo : '';
		byId('clientFormTitle').textContent = client ? 'Editar cliente' : 'Crear cliente';
	}

	function selectClient(id) {
		const client = findClient(id);
		if (!client) {
			return;
		}
		selectedClientId = client.id;
		fillClientForm(client);
		renderSelectedClient();
		saveDraft();
		setMessage(els.clientMessage, 'Cliente seleccionado para la orden.', 'success');
	}

	function renderSelectedClient() {
		const client = selectedClientId ? findClient(selectedClientId) : null;
		if (!els.selectedClientBox) {
			return;
		}
		if (!client) {
			els.selectedClientBox.innerHTML = '<strong>Sin cliente seleccionado</strong><span>La orden requiere un cliente reutilizado o creado desde el modulo Clientes.</span>';
			return;
		}
		els.selectedClientBox.innerHTML = `
			<strong>${escapeHtml(client.razon_social)}</strong>
			<span>${escapeHtml(client.ruc_dni)} | ${escapeHtml(client.domicilio || 'Sin domicilio')}</span>
		`;
	}

	function newClient() {
		fillClientForm(null);
		setMessage(els.clientMessage, '', 'info');
	}

	function getClientFormData() {
		return {
			id: byId('clienteId').value,
			razon_social: byId('clienteRazonSocial').value.trim(),
			ruc_dni: byId('clienteDocumento').value.trim(),
			representante_legal: byId('clienteRepresentante').value.trim(),
			telefono: byId('clienteTelefono').value.trim(),
			domicilio: byId('clienteDomicilio').value.trim(),
			email: byId('clienteEmail').value.trim(),
			contacto_tecnico: byId('clienteContactoTecnico').value.trim(),
			contacto_administrativo: byId('clienteContactoAdministrativo').value.trim()
		};
	}

	function findDuplicateClient(data, clients) {
		const doc = normalize(data.ruc_dni);
		const name = normalize(data.razon_social);
		return clients.find((client) => {
			if (client.id === data.id) {
				return false;
			}
			return normalize(client.ruc_dni) === doc || normalize(client.razon_social) === name;
		});
	}

	function saveClient(event) {
		event.preventDefault();
		if (!hasPermission('create_clients')) {
			setMessage(els.clientMessage, 'Tu rol no permite guardar clientes.', 'error');
			return;
		}
		if (!els.clientForm.reportValidity()) {
			return;
		}
		const data = getClientFormData();
		const clients = getClients();
		const duplicate = findDuplicateClient(data, clients);
		if (duplicate) {
			selectClient(duplicate.id);
			setMessage(els.clientMessage, 'Ya existe un cliente con ese RUC/DNI o razon social. Se reutilizo el registro existente.', 'error');
			return;
		}
		if (data.id) {
			const index = clients.findIndex((client) => client.id === data.id);
			if (index >= 0) {
				clients[index] = Object.assign({}, clients[index], data, { updated_at: new Date().toISOString() });
				audit('actualizo cliente', data.razon_social);
			}
		} else {
			data.id = makeId('cli');
			data.created_at = new Date().toISOString();
			clients.unshift(data);
			audit('creo cliente', data.razon_social);
		}
		saveClients(clients);
		selectedClientId = data.id;
		renderSelectedClient();
		renderClientResults(searchClients(lastClientSearch || data.ruc_dni || data.razon_social));
		renderAll();
		saveDraft();
		setMessage(els.clientMessage, 'Cliente guardado y seleccionado.', 'success');
	}

	function preparePdfData(order, client) {
		return {
			fecha: order.fecha,
			direccion: order.direccion,
			telefono: order.telefono,
			razonSocial: client ? client.razon_social : '',
			documento: client ? client.ruc_dni : '',
			representante: client ? client.representante_legal : '',
			domicilio: client ? client.domicilio : '',
			contactoTecnico: client ? client.contacto_tecnico : '',
			contactoAdministrativo: client ? client.contacto_administrativo : '',
			celular: '',
			telefonoCliente: client ? client.telefono : '',
			moneda: order.moneda,
			duracion: order.duracion,
			tipoServicio: order.tipo_servicio,
			ciudad: order.ciudad,
			diasEntrega: order.dias_entrega,
			direccionOrigen: order.direccion_origen,
			direccionDestino: order.direccion_destino,
			detalle: order.detalle,
			servicio: order.servicio,
			mrc: order.mrc,
			costoInstalacion: order.costo_instalacion || 'no',
			nrc: hasInstallationCost(order.costo_instalacion) ? order.nrc : '',
			subtotalMensual: order.mrc,
			totalInstalacion: hasInstallationCost(order.costo_instalacion) ? order.nrc : '',
			observacion: order.observacion,
			facilidadesPago: order.facilidades_pago
		};
	}

	function orderFromForm(orderNumber) {
		const data = getOrderFormData();
		return {
			id: makeId('ord'),
			numero_os: orderNumber,
			cliente_id: selectedClientId,
			fecha: data.fecha,
			moneda: data.moneda,
			duracion: data.duracion,
			tipo_servicio: data.tipoServicio,
			direccion: data.direccion,
			telefono: data.telefono,
			ciudad: data.ciudad,
			direccion_origen: data.direccionOrigen,
			direccion_destino: data.direccionDestino,
			detalle: data.detalle,
			servicio: data.servicio,
			dias_entrega: data.diasEntrega,
			mrc: data.mrc,
			costo_instalacion: hasInstallationCost(data.costoInstalacion) ? 'si' : 'no',
			nrc: hasInstallationCost(data.costoInstalacion) ? data.nrc : '',
			observacion: data.observacion,
			facilidades_pago: data.facilidadesPago,
			estado: 'Creada',
			created_by: currentUser.id,
			created_at: new Date().toISOString()
		};
	}

	async function createOrder(event) {
		event.preventDefault();
		if (!hasPermission('create_orders')) {
			window.alert('Tu rol no permite crear ordenes.');
			return;
		}
		if (!selectedClientId || !findClient(selectedClientId)) {
			window.alert('Selecciona o crea un cliente antes de crear la orden.');
			setView('clientes');
			return;
		}
		if (!els.orderForm.reportValidity()) {
			return;
		}
		const next = getNextNumber();
		const orderNumber = padOrderNumber(next);
		const order = orderFromForm(orderNumber);
		const orders = getOrders();
		orders.unshift(order);
		saveOrders(orders);
		localStorage.setItem(STORAGE_KEY, String(next + 1));
		updateCounterView();
		audit('creo orden', `OS ${orderNumber}`);
		saveDraft();
		await downloadOrderPdf(order);
		renderAll();
	}

	async function openPreview() {
		const client = selectedClientId ? findClient(selectedClientId) : null;
		const order = orderFromForm(padOrderNumber(getNextNumber()));
		const previewWindow = window.open('about:blank', '_blank');
		const blob = await createPdfBlob(preparePdfData(order, client), order.numero_os);
		const url = URL.createObjectURL(blob);
		if (previewWindow) {
			previewWindow.location.href = url;
		} else {
			window.open(url, '_blank', 'noopener');
		}
	}

	async function downloadOrderPdf(order) {
		const client = findClient(order.cliente_id);
		const data = preparePdfData(order, client);
		const blob = await createPdfBlob(data, order.numero_os);
		const link = document.createElement('a');
		link.href = URL.createObjectURL(blob);
		link.download = `OS ${order.numero_os} ${slugFileName(data.razonSocial)}.pdf`;
		document.body.appendChild(link);
		link.click();
		link.remove();
		setTimeout(() => URL.revokeObjectURL(link.href), 1000);
	}

	function updateOrderStatus(id, status) {
		const orders = getOrders();
		const index = orders.findIndex((order) => order.id === id);
		if (index < 0) {
			return;
		}
		orders[index].estado = status;
		orders[index].updated_by = currentUser.id;
		orders[index].updated_at = new Date().toISOString();
		saveOrders(orders);
		audit('actualizo estado', `OS ${orders[index].numero_os} -> ${status}`);
		renderAll();
	}

	function renderMetrics() {
		const clients = getClients();
		const orders = getVisibleOrders();
		els.metricClientes.textContent = String(clients.length);
		els.metricOrdenes.textContent = String(orders.length);
		els.metricMrc.textContent = formatMoney(orders.reduce((sum, order) => sum + parseMoney(order.mrc), 0));
		els.metricNrc.textContent = formatMoney(orders.reduce((sum, order) => sum + (hasInstallationCost(order.costo_instalacion) ? parseMoney(order.nrc) : 0), 0));
	}

	function orderRow(order, compact) {
		const client = findClient(order.cliente_id);
		const owner = getUsers().find((user) => user.id === order.created_by);
		const actions = compact ? '' : orderActions(order);
		return `
			<tr>
				<td><strong>${escapeHtml(order.numero_os)}</strong></td>
				<td>${escapeHtml(client ? client.razon_social : 'Cliente no encontrado')}</td>
				<td>${escapeHtml(order.fecha || '')}</td>
				<td><span class="os-status">${escapeHtml(order.estado)}</span></td>
				${compact ? '' : `<td>${escapeHtml(owner ? owner.nombre : '')}</td>`}
				${compact ? `<td>${escapeHtml(order.moneda)} ${formatMoney(order.mrc)}</td><td>${hasInstallationCost(order.costo_instalacion) ? `${escapeHtml(order.moneda)} ${formatMoney(order.nrc)}` : ''}</td>` : `<td>${actions}</td>`}
			</tr>
		`;
	}

	function orderActions(order) {
		const buttons = [
			`<button type="button" class="os-icon-button" data-pdf-order="${escapeHtml(order.id)}" aria-label="PDF OS ${escapeHtml(order.numero_os)}" title="PDF"><i class="far fa-file-pdf" aria-hidden="true"></i></button>`
		];
		if (hasPermission('update_orders') && order.estado !== 'Instalacion validada') {
			buttons.push(`<button type="button" class="os-button os-button-secondary" data-status-order="${escapeHtml(order.id)}" data-status-value="Instalacion validada">Validar instalacion</button>`);
		}
		if (hasPermission('validate_billing') && order.estado !== 'Facturacion validada' && order.estado !== 'Activada') {
			buttons.push(`<button type="button" class="os-button os-button-secondary" data-status-order="${escapeHtml(order.id)}" data-status-value="Facturacion validada">Validar MRC/NRC</button>`);
		}
		if (hasPermission('manage_users') && order.estado !== 'Activada') {
			buttons.push(`<button type="button" class="os-button os-button-primary" data-status-order="${escapeHtml(order.id)}" data-status-value="Activada">Activar</button>`);
		}
		return `<div class="os-row-actions">${buttons.join('')}</div>`;
	}

	function renderOrders() {
		const status = els.statusFilter.value;
		const visible = getVisibleOrders();
		const orders = visible.filter((order) => !status || order.estado === status);
		els.ordersBody.innerHTML = orders.length ? orders.map((order) => orderRow(order, false)).join('') : '<tr><td colspan="6" class="os-empty">Sin ordenes registradas.</td></tr>';
		const recent = visible.slice(0, 5);
		els.recentOrdersBody.innerHTML = recent.length ? recent.map((order) => orderRow(order, true)).join('') : '<tr><td colspan="6" class="os-empty">Sin ordenes registradas.</td></tr>';
	}

	function renderUsers() {
		const users = getUsers();
		els.usersBody.innerHTML = users.map((user) => `
			<tr>
				<td>${escapeHtml(user.nombre)}</td>
				<td>${escapeHtml(user.email)}</td>
				<td>${escapeHtml(getRole(user).label)}</td>
				<td><span class="os-status">${escapeHtml(user.estado)}</span></td>
				<td>
					<button type="button" class="os-button os-button-secondary" data-toggle-user="${escapeHtml(user.id)}" ${user.id === currentUser.id ? 'disabled' : ''}>
						${user.estado === 'activo' ? 'Inactivar' : 'Activar'}
					</button>
				</td>
			</tr>
		`).join('');
	}

	function renderAudit() {
		const items = readStore(AUDIT_KEY, []);
		els.auditBody.innerHTML = items.length ? items.map((item) => `
			<tr>
				<td>${escapeHtml(new Date(item.fecha).toLocaleString('es-PE'))}</td>
				<td>${escapeHtml(item.usuario)}</td>
				<td>${escapeHtml(item.accion)}</td>
				<td>${escapeHtml(item.entidad)}</td>
			</tr>
		`).join('') : '<tr><td colspan="4" class="os-empty">Sin movimientos registrados.</td></tr>';
	}

	function renderAll() {
		renderMetrics();
		renderOrders();
		if (hasPermission('manage_users')) {
			renderUsers();
			renderAudit();
		}
		renderSelectedClient();
		updateCounterView();
	}

	async function createUser(event) {
		event.preventDefault();
		if (!hasPermission('manage_users')) {
			return;
		}
		const email = byId('userEmail').value.trim().toLowerCase();
		const users = getUsers();
		if (users.some((user) => user.email === email)) {
			window.alert('Ya existe un usuario con ese email.');
			return;
		}
		const user = {
			id: makeId('usr'),
			nombre: byId('userName').value.trim(),
			email,
			password_hash: await hashPassword(byId('userPassword').value),
			rol: byId('userRole').value,
			estado: 'activo',
			created_at: new Date().toISOString()
		};
		users.push(user);
		saveUsers(users);
		els.userForm.reset();
		audit('creo usuario', user.email);
		renderAll();
	}

	function toggleUser(id) {
		if (!hasPermission('manage_users') || id === currentUser.id) {
			return;
		}
		const users = getUsers();
		const index = users.findIndex((user) => user.id === id);
		if (index < 0) {
			return;
		}
		users[index].estado = users[index].estado === 'activo' ? 'inactivo' : 'activo';
		saveUsers(users);
		audit('cambio estado usuario', users[index].email);
		renderAll();
	}

	function wireEvents() {
		els.loginForm.addEventListener('submit', login);
		els.logoutBtn.addEventListener('click', logout);
		document.querySelectorAll('.os-nav-button').forEach((button) => {
			button.addEventListener('click', () => setView(button.dataset.view));
		});
		document.querySelectorAll('[data-shortcut]').forEach((button) => {
			button.addEventListener('click', () => setView(button.dataset.shortcut));
		});
		els.clientSearchForm.addEventListener('submit', handleClientSearch);
		els.clientResults.addEventListener('click', (event) => {
			const button = event.target.closest('[data-select-client]');
			if (button) {
				selectClient(button.dataset.selectClient);
			}
		});
		els.newClientBtn.addEventListener('click', newClient);
		els.clientForm.addEventListener('submit', saveClient);
		els.orderForm.addEventListener('submit', createOrder);
		els.orderForm.addEventListener('input', saveDraft);
		els.orderForm.addEventListener('change', saveDraft);
		byId('costoInstalacion').addEventListener('change', () => updateInstallationCostState(true));
		els.saveCounterBtn.addEventListener('click', () => setNextNumber(els.nextInput.value));
		els.nextInput.addEventListener('input', () => {
			els.nextInput.value = els.nextInput.value.replace(/\D/g, '').slice(0, 6);
		});
		els.nextInput.addEventListener('blur', () => {
			els.nextInput.value = padOrderNumber(els.nextInput.value);
		});
		els.previewPdfBtn.addEventListener('click', openPreview);
		els.clearFormBtn.addEventListener('click', clearOrderForm);
		els.statusFilter.addEventListener('change', renderOrders);
		els.ordersBody.addEventListener('click', (event) => {
			const pdfButton = event.target.closest('[data-pdf-order]');
			const statusButton = event.target.closest('[data-status-order]');
			if (pdfButton) {
				const order = getOrders().find((item) => item.id === pdfButton.dataset.pdfOrder);
				if (order) {
					downloadOrderPdf(order);
				}
			}
			if (statusButton) {
				updateOrderStatus(statusButton.dataset.statusOrder, statusButton.dataset.statusValue);
			}
		});
		els.userForm.addEventListener('submit', createUser);
		els.usersBody.addEventListener('click', (event) => {
			const button = event.target.closest('[data-toggle-user]');
			if (button) {
				toggleUser(button.dataset.toggleUser);
			}
		});
	}

	function cacheElements() {
		Object.assign(els, {
			loginView: byId('loginView'),
			appView: byId('appView'),
			loginForm: byId('loginForm'),
			loginEmail: byId('loginEmail'),
			loginPassword: byId('loginPassword'),
			loginMessage: byId('loginMessage'),
			sessionName: byId('sessionName'),
			sessionRole: byId('sessionRole'),
			logoutBtn: byId('logoutBtn'),
			viewTitle: byId('viewTitle'),
			metricClientes: byId('metricClientes'),
			metricOrdenes: byId('metricOrdenes'),
			metricMrc: byId('metricMrc'),
			metricNrc: byId('metricNrc'),
			recentOrdersBody: byId('recentOrdersBody'),
			clientSearchForm: byId('clientSearchForm'),
			clientSearch: byId('clientSearch'),
			clientSearchState: byId('clientSearchState'),
			clientResults: byId('clientResults'),
			clientForm: byId('clientForm'),
			clientMessage: byId('clientMessage'),
			newClientBtn: byId('newClientBtn'),
			selectedClientBox: byId('selectedClientBox'),
			orderForm: byId('serviceOrderForm'),
			preview: byId('orderNumberPreview'),
			nextInput: byId('nextOrderNumber'),
			saveCounterBtn: byId('saveCounterBtn'),
			previewPdfBtn: byId('previewPdfBtn'),
			clearFormBtn: byId('clearFormBtn'),
			statusFilter: byId('statusFilter'),
			ordersBody: byId('ordersBody'),
			userForm: byId('userForm'),
			usersBody: byId('usersBody'),
			auditBody: byId('auditBody')
		});
	}

	async function init() {
		cacheElements();
		await ensureSeedData();
		restoreDraft();
		updateCounterView();
		wireEvents();
		resumeSession();
	}

	function asciiBytes(value) {
		const bytes = [];
		for (let i = 0; i < value.length; i += 1) {
			bytes.push(value.charCodeAt(i) & 255);
		}
		return bytes;
	}

	function cp1252Bytes(value) {
		const bytes = [];
		String(value || '').replace(/\r\n/g, '\n').replace(/\r/g, '\n').split('').forEach((char) => {
			const code = char.charCodeAt(0);
			if (char === '\\') {
				bytes.push(92, 92);
			} else if (char === '(') {
				bytes.push(92, 40);
			} else if (char === ')') {
				bytes.push(92, 41);
			} else if (char === '\n') {
				bytes.push(32);
			} else if (CP1252[char]) {
				bytes.push(CP1252[char]);
			} else if (code <= 255) {
				bytes.push(code);
			} else {
				bytes.push(63);
			}
		});
		return bytes;
	}

	function byteLength(value) {
		return value.length;
	}

	function streamWriter() {
		const bytes = [];
		return {
			bytes,
			ascii(value) {
				bytes.push(...asciiBytes(value));
			},
			textBytes(value) {
				bytes.push(...cp1252Bytes(value));
			}
		};
	}

	function estimateTextWidth(value, size, bold) {
		let width = 0;
		String(value || '').split('').forEach((char) => {
			if (char === ' ') {
				width += .28;
			} else if ('il.,:;!|'.includes(char)) {
				width += .23;
			} else if ('MW@%#'.includes(char)) {
				width += .82;
			} else if (/[A-Z0-9]/.test(char)) {
				width += .58;
			} else {
				width += .5;
			}
		});
		return width * size * (bold ? 1.03 : 1);
	}

	function wrapText(value, size, maxWidth, maxLines) {
		const text = String(value || '').replace(/\r\n/g, '\n').replace(/\r/g, '\n');
		const paragraphs = text.split('\n');
		const lines = [];
		paragraphs.forEach((paragraph) => {
			const words = paragraph.split(/\s+/).filter(Boolean);
			if (!words.length) {
				if (lines.length < maxLines) {
					lines.push('');
				}
				return;
			}
			let line = '';
			words.forEach((word) => {
				const candidate = line ? `${line} ${word}` : word;
				if (estimateTextWidth(candidate, size, false) <= maxWidth) {
					line = candidate;
					return;
				}
				if (line && lines.length < maxLines) {
					lines.push(line);
				}
				line = word;
				while (estimateTextWidth(line, size, false) > maxWidth && line.length > 4 && lines.length < maxLines) {
					let cut = line.length - 1;
					while (cut > 3 && estimateTextWidth(`${line.slice(0, cut)}-`, size, false) > maxWidth) {
						cut -= 1;
					}
					lines.push(`${line.slice(0, cut)}-`);
					line = line.slice(cut);
				}
			});
			if (line && lines.length < maxLines) {
				lines.push(line);
			}
		});
		if (lines.length > maxLines) {
			lines.length = maxLines;
		}
		if (lines.length === maxLines && paragraphs.join(' ').length > lines.join(' ').length) {
			const last = lines[maxLines - 1] || '';
			lines[maxLines - 1] = last.length > 3 ? `${last.slice(0, Math.max(1, last.length - 3))}...` : '...';
		}
		return lines;
	}

	function formatAmount(value) {
		return formatMoney(value);
	}

	function blobFromCanvas(canvas, type, quality) {
		return new Promise((resolve, reject) => {
			canvas.toBlob((blob) => {
				if (blob) {
					resolve(blob);
				} else {
					reject(new Error('No se pudo preparar el logo para PDF.'));
				}
			}, type, quality);
		});
	}

	function loadImage(src) {
		return new Promise((resolve, reject) => {
			const image = new Image();
			image.onload = () => resolve(image);
			image.onerror = () => reject(new Error('No se pudo cargar el logo.'));
			image.src = src;
		});
	}

	async function getPdfLogoImage() {
		if (!logoImagePromise) {
			logoImagePromise = (async () => {
				const response = await fetch(LOGO_PATH, { cache: 'force-cache' });
				if (!response.ok) {
					throw new Error('No se encontro el logo de Media Commerce.');
				}
				const blob = await response.blob();
				const pngUrl = URL.createObjectURL(blob);
				try {
					const image = await loadImage(pngUrl);
					const width = 900;
					const height = Math.round(width * image.naturalHeight / image.naturalWidth);
					const canvas = document.createElement('canvas');
					canvas.width = width;
					canvas.height = height;
					const context = canvas.getContext('2d');
					context.fillStyle = '#ffffff';
					context.fillRect(0, 0, width, height);
					context.drawImage(image, 0, 0, width, height);
					const jpegBlob = await blobFromCanvas(canvas, 'image/jpeg', .96);
					return {
						width,
						height,
						bytes: new Uint8Array(await jpegBlob.arrayBuffer())
					};
				} finally {
					URL.revokeObjectURL(pngUrl);
				}
			})();
		}
		try {
			return await logoImagePromise;
		} catch (error) {
			logoImagePromise = null;
			return null;
		}
	}

	function slugFileName(value) {
		return String(value || 'CLIENTE')
			.normalize('NFD')
			.replace(/[\u0300-\u036f]/g, '')
			.replace(/[^a-z0-9]+/gi, ' ')
			.trim()
			.toUpperCase()
			.slice(0, 56) || 'CLIENTE';
	}

	function buildServiceOrderContent(data, orderNumber, hasLogo) {
		const out = streamWriter();
		const W = PAGE.width;
		const H = PAGE.height;

		function num(value) {
			return Number(value).toFixed(3);
		}

		function y(top) {
			return H - top;
		}

		function fill(hex) {
			const clean = hex.replace('#', '');
			const r = parseInt(clean.slice(0, 2), 16) / 255;
			const g = parseInt(clean.slice(2, 4), 16) / 255;
			const b = parseInt(clean.slice(4, 6), 16) / 255;
			out.ascii(`${num(r)} ${num(g)} ${num(b)} rg\n`);
		}

		function stroke(hex) {
			const clean = hex.replace('#', '');
			const r = parseInt(clean.slice(0, 2), 16) / 255;
			const g = parseInt(clean.slice(2, 4), 16) / 255;
			const b = parseInt(clean.slice(4, 6), 16) / 255;
			out.ascii(`${num(r)} ${num(g)} ${num(b)} RG\n`);
		}

		function rect(x, top, width, height, color, strokeColor) {
			if (color) {
				fill(color);
			}
			if (strokeColor) {
				stroke(strokeColor);
				out.ascii('.650 w\n');
			}
			out.ascii(`${num(x)} ${num(y(top + height))} ${num(width)} ${num(height)} re ${color && strokeColor ? 'B' : color ? 'f' : 'S'}\n`);
		}

		function line(x1, top1, x2, top2, color, width) {
			stroke(color || '#000000');
			out.ascii(`${num(width || .65)} w\n`);
			out.ascii(`${num(x1)} ${num(y(top1))} m ${num(x2)} ${num(y(top2))} l S\n`);
		}

		function image(x, top, width, height) {
			out.ascii(`q ${num(width)} 0 0 ${num(height)} ${num(x)} ${num(y(top + height))} cm /Im1 Do Q\n`);
		}

		function text(x, top, value, options) {
			const opts = Object.assign({
				font: 'F1',
				size: 9,
				color: '#000000',
				align: 'left'
			}, options || {});
			const content = String(value || '');
			let tx = x;
			if (opts.align !== 'left') {
				const width = estimateTextWidth(content, opts.size, opts.font === 'F2');
				tx = opts.align === 'center' ? x - width / 2 : x - width;
			}
			fill(opts.color);
			out.ascii(`BT /${opts.font} ${num(opts.size)} Tf 1 0 0 1 ${num(tx)} ${num(y(top))} Tm (`);
			out.textBytes(content);
			out.ascii(') Tj ET\n');
		}

		function multilineText(x, top, value, width, size, lineHeight, maxLines, options) {
			const lines = wrapText(value, size, width, maxLines);
			lines.forEach((lineValue, index) => {
				text(x, top + index * lineHeight, lineValue, Object.assign({ size }, options || {}));
			});
			return lines.length;
		}

		function labelValue(x, top, label, value, width, size) {
			const content = `${label}:  ${value || ''}`;
			multilineText(x, top, content, width, size || 9, 12, 2, { color: '#000000' });
		}

		const margin = 28.35;
		const right = W - margin;
		const subtotal = data.subtotalMensual || data.mrc;
		const printInstallCost = hasInstallationCost(data.costoInstalacion);
		const totalInstall = printInstallCost ? data.totalInstalacion || data.nrc : '';

		rect(0, 0, W, H, '#ffffff');
		rect(margin, 24, 168, 74, '#ffffff', '#d5deea');
		if (hasLogo) {
			image(38, 31, 150, 69);
		} else {
			text(41, 52, 'MEDIA', { font: 'F2', size: 25, color: '#164991' });
			text(42, 69, 'commerce', { font: 'F1', size: 11, color: '#0f346b' });
			rect(113, 26, 9, 9, '#ffd100');
		}
		text(right - 3, 43, `Orden de Servicio Nro  ${orderNumber}`, { font: 'F2', size: 11, align: 'right' });
		text(right - 3, 65, `Fecha  ${data.fecha || ''}`, { size: 10, align: 'right' });

		text(margin + 2.8, 101, data.direccion || 'Av. Enrique Canaval y Moreyra Nro 425', { size: 10 });
		text(margin + 2.8, 116, `Telefono: ${data.telefono || '(+51)748-4200'}  RUC: 20522259064`, { size: 10 });
		line(margin, 122, right, 122, '#000000', .65);

		text(W / 2, 137, 'Informacion general del cliente', { font: 'F2', size: 10, align: 'center' });
		line(margin, 146, right, 146, '#000000', .65);

		labelValue(31.18, 162, 'Razon social/Persona natural', data.razonSocial, 395, 9);
		labelValue(31.18, 179, 'RUC/DNI', data.documento, 240, 9);
		labelValue(31.18, 196, 'Nombre completo del Representante Legal', data.representante, 385, 9);
		labelValue(428, 196, 'Telefono', data.telefonoCliente, 130, 9);
		labelValue(31.18, 213, 'Domicilio', data.domicilio, 525, 9);
		labelValue(31.18, 230, 'Contacto Tecnico', data.contactoTecnico, 295, 9);
		labelValue(343, 230, 'Celular', data.celular, 180, 9);
		labelValue(31.18, 247, 'Contacto Administrativo', data.contactoAdministrativo, 295, 9);
		labelValue(343, 247, 'Telefono', data.telefonoCliente, 180, 9);
		line(margin, 258, right, 258, '#000000', .65);
		labelValue(31.18, 273, 'Moneda de negociacion', data.moneda, 250, 9);
		labelValue(300.47, 273, 'Tipo de servicio', data.tipoServicio, 250, 9);

		const tableTop = 294;
		const headerHeight = 24.5;
		const rowHeight = 91;
		const widths = [50, 86, 120, 90, 60, 45, 45, 43];
		const headers = ['Ciudad', 'Direccion Origen', 'Detalle', 'Direccion Destino', 'Servicio', 'Dias', 'MRC', 'NRC'];
		let x = margin;
		rect(margin, tableTop, right - margin, headerHeight + rowHeight, null, '#000000');
		widths.forEach((width, index) => {
			if (index > 0) {
				line(x, tableTop, x, tableTop + headerHeight + rowHeight, '#000000', .65);
			}
			multilineText(x + 2, tableTop + 13, headers[index], width - 4, 8.4, 9, 2, { color: '#000000' });
			x += width;
		});
		line(margin, tableTop + headerHeight, right, tableTop + headerHeight, '#000000', .65);

		const rowValues = [
			data.ciudad,
			data.direccionOrigen,
			data.detalle,
			data.direccionDestino,
			data.servicio,
			data.diasEntrega,
			formatAmount(data.mrc),
			printInstallCost ? formatAmount(data.nrc) : ''
		];
		x = margin;
		rowValues.forEach((value, index) => {
			const maxLines = index >= 6 ? 2 : 7;
			multilineText(x + 2, tableTop + headerHeight + 13, value, widths[index] - 4, 7, 8.7, maxLines, { color: '#000000' });
			x += widths[index];
		});

		text(357, 500, `Cargo Mensual sin IGV:   ${data.moneda || ''}   ${formatAmount(subtotal)}`, { size: 10 });
		if (printInstallCost) {
			text(360, 516, `Valor de la Instalacion:               ${formatAmount(totalInstall)}`, { size: 10 });
		}
		line(margin, 527, right, 527, '#000000', .65);

		text(31.18, 542, 'Importante: La facturacion de esta orden de servicios se realizara una vez activado el enlace.', { size: 9 });
		text(W / 2, 560, 'Observacion :', { size: 9, align: 'center' });
		multilineText(31.18, 578, data.observacion, 525, 8, 10, 8, { color: '#000000' });

		line(margin, 665, right, 665, '#000000', .65);
		text(31.18, 681, 'Facilidades de pago de instalacion :', { size: 9 });
		multilineText(31.18, 696, data.facilidadesPago, 525, 8, 10, 3, { color: '#000000' });
		line(margin, 727, right, 727, '#000000', .65);
		text(31.18, 742, 'Esta orden de servicios es parte integral del contrato por lo tanto prestara merito ejecutivo.', { size: 8.6 });
		text(31.18, 754, 'El plazo maximo para su legalizacion del contrato es de 19 dias habiles siguientes a la firma de esta orden de servicio:', { size: 8.6 });
		line(margin, 762, right, 762, '#000000', .65);

		text(172.9, 777, 'Cliente', { font: 'F2', size: 9, align: 'center' });
		text(385.5, 777, 'Comercial', { font: 'F2', size: 9, align: 'center' });
		text(59.5, 791, 'Representante Legal:', { size: 9 });
		text(130.4, 791, data.representante || '_____________________________', { size: 8 });
		text(314.6, 791, 'Nombre :', { size: 9 });
		text(357.1, 791, '_____________________________', { size: 9 });
		text(59.5, 807, 'Firma :', { size: 9 });
		text(130.4, 807, '_____________________________', { size: 9 });
		text(314.6, 807, 'Firma :', { size: 9 });
		text(357.1, 807, '_____________________________', { size: 9 });
		text(59.5, 823, 'Fecha de Firma :', { size: 9 });
		text(130.4, 823, '_____________________________', { size: 9 });
		text(314.6, 823, 'DNI :', { size: 9 });
		text(357.1, 823, '_____________________________', { size: 9 });
		text(59.5, 838, 'DNI/RUC :', { size: 9 });
		text(130.4, 838, data.documento || '_____________________________', { size: 8 });

		return out.bytes;
	}

	function concatBytes(parts) {
		const total = parts.reduce((sum, part) => sum + byteLength(part), 0);
		const bytes = new Uint8Array(total);
		let offset = 0;
		parts.forEach((part) => {
			bytes.set(part, offset);
			offset += part.length;
		});
		return bytes;
	}

	function buildPdf(contentBytes, logoImage) {
		const resources = logoImage
			? '/Resources << /Font << /F1 5 0 R /F2 6 0 R >> /XObject << /Im1 7 0 R >> >>'
			: '/Resources << /Font << /F1 5 0 R /F2 6 0 R >> >>';
		const objects = [
			asciiBytes('<< /Type /Catalog /Pages 2 0 R >>\n'),
			asciiBytes('<< /Type /Pages /Kids [3 0 R] /Count 1 >>\n'),
			asciiBytes(`<< /Type /Page /Parent 2 0 R /MediaBox [0 0 ${PAGE.width} ${PAGE.height}] ${resources} /Contents 4 0 R >>\n`),
			concatBytes([
				asciiBytes(`<< /Length ${contentBytes.length} >>\nstream\n`),
				new Uint8Array(contentBytes),
				asciiBytes('\nendstream\n')
			]),
			asciiBytes('<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica /Encoding /WinAnsiEncoding >>\n'),
			asciiBytes('<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica-Bold /Encoding /WinAnsiEncoding >>\n')
		];
		if (logoImage) {
			objects.push(concatBytes([
				asciiBytes(`<< /Type /XObject /Subtype /Image /Width ${logoImage.width} /Height ${logoImage.height} /ColorSpace /DeviceRGB /BitsPerComponent 8 /Filter /DCTDecode /Length ${logoImage.bytes.length} >>\nstream\n`),
				logoImage.bytes,
				asciiBytes('\nendstream\n')
			]));
		}
		const parts = [asciiBytes('%PDF-1.4\n%\xE2\xE3\xCF\xD3\n')];
		const offsets = [0];
		objects.forEach((objectBytes, index) => {
			const offset = parts.reduce((sum, part) => sum + part.length, 0);
			offsets.push(offset);
			parts.push(asciiBytes(`${index + 1} 0 obj\n`));
			parts.push(objectBytes);
			parts.push(asciiBytes('endobj\n'));
		});
		const xrefOffset = parts.reduce((sum, part) => sum + part.length, 0);
		parts.push(asciiBytes(`xref\n0 ${objects.length + 1}\n`));
		parts.push(asciiBytes('0000000000 65535 f \n'));
		offsets.slice(1).forEach((offset) => {
			parts.push(asciiBytes(`${String(offset).padStart(10, '0')} 00000 n \n`));
		});
		parts.push(asciiBytes(`trailer\n<< /Size ${objects.length + 1} /Root 1 0 R >>\nstartxref\n${xrefOffset}\n%%EOF\n`));
		return concatBytes(parts);
	}

	async function createPdfBlob(data, orderNumber) {
		const logoImage = await getPdfLogoImage();
		const content = buildServiceOrderContent(data, orderNumber, Boolean(logoImage));
		return new Blob([buildPdf(content, logoImage)], { type: 'application/pdf' });
	}

	document.addEventListener('DOMContentLoaded', init);
}());
