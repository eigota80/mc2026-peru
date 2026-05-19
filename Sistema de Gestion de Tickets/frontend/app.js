const API_URL = window.location.protocol === "file:" ? "http://127.0.0.1:8001" : window.location.origin;

const state = {
  tickets: [],
  users: [],
  clientGraphs: [],
  cactiImageUrls: new Map(),
  attachmentUrls: new Map(),
  selectedTicketId: null,
  token: localStorage.getItem("accessToken"),
  currentUser: null,
};

const labels = {
  open: "Abierto",
  in_progress: "En proceso",
  waiting_customer: "Esperando cliente",
  resolved: "Resuelto",
  escalated: "Escalado",
  closed: "Cerrado",
  low: "Baja",
  medium: "Media",
  high: "Alta",
  urgent: "Urgente",
  admin: "Administrador",
  agent: "Agente",
  customer: "Cliente",
  network: "Red / equipo",
  bar: "Barras",
  line: "Línea",
  pie: "Distribución",
  cacti: "Cacti",
  gestion_tickets: "Gestión de tickets",
  crm: "CRM / clientes",
  facturacion: "Facturación",
  portal_cliente: "Portal cliente",
  correo: "Correo corporativo",
  infraestructura: "Infraestructura",
  general: "General",
};

const qs = (selector) => document.querySelector(selector);
const ticketStatuses = ["open", "in_progress", "waiting_customer", "resolved", "escalated", "closed"];

function showToast(message) {
  const toast = qs("#toast");
  toast.textContent = message;
  toast.classList.add("show");
  window.setTimeout(() => toast.classList.remove("show"), 2800);
}

async function request(path, options = {}) {
  const isFormData = options.body instanceof FormData;
  const headers = { ...(isFormData ? {} : { "Content-Type": "application/json" }), ...(options.headers || {}) };
  if (state.token) headers.Authorization = `Bearer ${state.token}`;

  const response = await fetch(`${API_URL}${path}`, { ...options, headers });
  if (!response.ok) {
    const error = await response.json().catch(() => ({}));
    if (response.status === 401 && !path.startsWith("/auth/login") && !path.startsWith("/auth/register")) {
      logout();
    }
    throw new Error(error.detail || "No se pudo completar la acción");
  }

  if (response.status === 204) return null;
  return response.json();
}

async function fetchCactiImageUrl(graphId) {
  if (state.cactiImageUrls.has(graphId)) {
    return state.cactiImageUrls.get(graphId);
  }

  const headers = {};
  if (state.token) headers.Authorization = `Bearer ${state.token}`;

  const response = await fetch(`${API_URL}/client-graphs/${graphId}/image`, { headers });
  if (!response.ok) {
    if (response.status === 401) logout();
    const error = await response.json().catch(() => ({}));
    throw new Error(error.detail || "No se pudo cargar la gráfica de Cacti");
  }

  const blob = await response.blob();
  const imageUrl = URL.createObjectURL(blob);
  state.cactiImageUrls.set(graphId, imageUrl);
  return imageUrl;
}

function clearCactiImageUrls() {
  state.cactiImageUrls.forEach((imageUrl) => URL.revokeObjectURL(imageUrl));
  state.cactiImageUrls.clear();
}

async function fetchAuthenticatedFileUrl(fileUrl) {
  if (state.attachmentUrls.has(fileUrl)) {
    return state.attachmentUrls.get(fileUrl);
  }

  const headers = {};
  if (state.token) headers.Authorization = `Bearer ${state.token}`;

  const response = await fetch(fileUrl, { headers });
  if (!response.ok) {
    if (response.status === 401) logout();
    throw new Error("No se pudo cargar el adjunto");
  }

  const blobUrl = URL.createObjectURL(await response.blob());
  state.attachmentUrls.set(fileUrl, blobUrl);
  return blobUrl;
}

function clearAttachmentUrls() {
  state.attachmentUrls.forEach((imageUrl) => URL.revokeObjectURL(imageUrl));
  state.attachmentUrls.clear();
}

async function hydrateAttachmentImages(container = document) {
  const links = [...container.querySelectorAll("[data-attachment-url]")];
  await Promise.all(links.map(async (link) => {
    const image = link.querySelector("img");
    try {
      const blobUrl = await fetchAuthenticatedFileUrl(link.dataset.attachmentUrl);
      link.href = blobUrl;
      if (image) {
        image.src = blobUrl;
        image.hidden = false;
      }
    } catch (error) {
      console.error("Attachment failed:", error);
      link.classList.add("has-error");
    }
  }));
}

function openGraphFullscreen(src, title) {
  const fullscreen = qs("#graph-fullscreen");
  const image = qs("#graph-fullscreen-image");
  qs("#graph-fullscreen-title").textContent = title || "Gráfica";
  image.src = src;
  image.alt = title || "Gráfica";
  fullscreen.hidden = false;
  document.body.classList.add("fullscreen-open");
}

function closeGraphFullscreen() {
  const fullscreen = qs("#graph-fullscreen");
  const image = qs("#graph-fullscreen-image");
  fullscreen.hidden = true;
  image.removeAttribute("src");
  document.body.classList.remove("fullscreen-open");
}

async function hydrateCactiImages(container = document) {
  const images = [...container.querySelectorAll("[data-cacti-image-id]")];
  await Promise.all(images.map(async (image) => {
    const graphId = Number(image.dataset.cactiImageId);
    try {
      image.src = await fetchCactiImageUrl(graphId);
      image.hidden = false;
      image.addEventListener("click", () => openGraphFullscreen(image.src, image.alt));
      image.closest(".graph-cacti")?.classList.remove("is-loading", "has-error");
    } catch (error) {
      console.error("Cacti image failed:", error);
      const preview = image.closest(".graph-cacti");
      if (preview) {
        preview.classList.remove("is-loading");
        preview.classList.add("has-error");
        preview.innerHTML = `<strong>No se pudo cargar Cacti</strong><span>${escapeHtml(error.message)}</span>`;
      }
    }
  }));
}

function formatDate(value) {
  return new Intl.DateTimeFormat("es-CO", {
    dateStyle: "medium",
    timeStyle: "short",
  }).format(new Date(value));
}

function normalizeFormNumber(value) {
  return value ? Number(value) : null;
}

function formatFileSize(bytes) {
  if (bytes < 1024 * 1024) return `${Math.max(1, Math.round(bytes / 1024))} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

function formatDuration(milliseconds) {
  if (!Number.isFinite(milliseconds) || milliseconds < 0) return "Sin datos";
  const minutes = Math.max(1, Math.round(milliseconds / 60000));
  const days = Math.floor(minutes / 1440);
  const hours = Math.floor((minutes % 1440) / 60);
  const remainingMinutes = minutes % 60;
  const parts = [];
  if (days) parts.push(`${days} d`);
  if (hours) parts.push(`${hours} h`);
  if (!days && remainingMinutes) parts.push(`${remainingMinutes} min`);
  return parts.join(" ") || "Menos de 1 min";
}

function isCurrentAdmin() {
  return state.currentUser?.role === "admin";
}

function canManageGraphs() {
  return ["admin", "agent"].includes(state.currentUser?.role);
}

function canManageTickets() {
  return ["admin", "agent"].includes(state.currentUser?.role);
}

function updateRoleVisibility() {
  document.querySelectorAll("[data-admin-view]").forEach((element) => {
    element.hidden = state.currentUser?.role === "customer";
  });
}

function escapeHtml(value) {
  return String(value)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}

function labelFor(value) {
  return labels[value] || value;
}

function userNameById(userId) {
  const user = state.users.find((item) => item.id === Number(userId));
  return user?.name || (userId ? `Usuario #${userId}` : "Sin asignar");
}

function formatEventValue(event, value) {
  if (value === null || value === undefined || value === "None" || value === "") return "Sin asignar";
  if (["status", "priority", "category"].includes(event.field_name)) return labelFor(value);
  if (["requester_id", "assigned_to_id"].includes(event.field_name)) return userNameById(value);
  return value;
}

function renderTicketTimeline(ticket) {
  const events = [...(ticket.events || [])].sort((a, b) => new Date(a.created_at) - new Date(b.created_at));
  if (!events.length) {
    return `<p>No hay historial registrado todavía.</p>`;
  }

  const statusEvents = events
    .filter((event) => event.field_name === "status" && event.new_value)
    .map((event) => ({ ...event, status: event.new_value }));

  if (!statusEvents.length) {
    statusEvents.push({
      id: `current-${ticket.id}`,
      event_type: "status_changed",
      message: "Estado actual",
      field_name: "status",
      old_value: null,
      new_value: ticket.status,
      status: ticket.status,
      created_at: ticket.created_at,
      actor: ticket.requester,
    });
  }

  const now = new Date();
  const enrichedStatusEvents = statusEvents.map((event, index) => {
    const start = new Date(event.created_at);
    const next = statusEvents[index + 1] ? new Date(statusEvents[index + 1].created_at) : now;
    return {
      ...event,
      durationLabel: formatDuration(next - start),
    };
  });

  return `
    <div class="timeline-toolbar" data-timeline-filter>
      <button class="timeline-filter active" type="button" data-status-filter="all">Todos</button>
      ${ticketStatuses.map((status) => `
        <button class="timeline-filter" type="button" data-status-filter="${status}">${labels[status]}</button>
      `).join("")}
    </div>
    <div class="status-lifecycle">
      ${enrichedStatusEvents.map((event) => `
        <article class="status-step status-${event.status}" data-status-item="${event.status}">
          <span>${escapeHtml(labelFor(event.status))}</span>
          <strong>${event.durationLabel}</strong>
          <small>${event.actor ? escapeHtml(event.actor.name) : "Sistema"} · ${formatDate(event.created_at)}</small>
        </article>
      `).join("")}
    </div>
    <ol class="timeline-list">
      ${events.map((event) => {
        const hasValues = event.field_name && (event.old_value !== null || event.new_value !== null);
        const statusValue = event.field_name === "status" ? event.new_value : "";
        return `
          <li class="timeline-item event-${event.event_type}" ${statusValue ? `data-status-item="${escapeHtml(statusValue)}"` : ""}>
            <div>
              <strong>${escapeHtml(event.message)}</strong>
              <small>${event.actor ? escapeHtml(event.actor.name) : "Sistema"} · ${formatDate(event.created_at)}</small>
              ${hasValues ? `
                <span>${escapeHtml(formatEventValue(event, event.old_value))} &rarr; ${escapeHtml(formatEventValue(event, event.new_value))}</span>
              ` : ""}
            </div>
          </li>
        `;
      }).join("")}
    </ol>
  `;
}

function bindTimelineFilters(container) {
  const toolbar = container.querySelector("[data-timeline-filter]");
  if (!toolbar) return;
  toolbar.querySelectorAll("[data-status-filter]").forEach((button) => {
    button.addEventListener("click", () => {
      const selected = button.dataset.statusFilter;
      toolbar.querySelectorAll("[data-status-filter]").forEach((item) => {
        item.classList.toggle("active", item === button);
      });
      container.querySelectorAll("[data-status-item]").forEach((item) => {
        item.hidden = selected !== "all" && item.dataset.statusItem !== selected;
      });
    });
  });
}

function showApp() {
  qs("#auth-screen").hidden = true;
  qs("#sidebar").hidden = false;
  qs("#app-shell").hidden = false;
  updateRoleVisibility();

  // Mostrar vista por defecto (dashboard)
  qs("#dashboard-view").hidden = false;
  qs("#tickets-view").hidden = false;
  qs("#ticket-detail").hidden = false;
  qs("#graphs-view").hidden = true;
  qs("#users-view").hidden = true;
}

function showAuth() {
  qs("#auth-screen").hidden = false;
  qs("#sidebar").hidden = true;
  qs("#app-shell").hidden = true;
}

function showAuthForm(formId) {
  ["#login-form", "#register-form", "#password-reset-request-form", "#password-reset-confirm-form"].forEach((selector) => {
    qs(selector).hidden = selector !== formId;
  });

  const showTabs = formId === "#login-form" || formId === "#register-form";
  qs(".auth-tabs").hidden = !showTabs;
  if (showTabs) {
    document.querySelectorAll(".auth-tab").forEach((tab) => {
      tab.classList.toggle("active", tab.dataset.authTab === (formId === "#login-form" ? "login" : "register"));
    });
  }
}

function logout() {
  clearCactiImageUrls();
  clearAttachmentUrls();
  state.token = null;
  state.currentUser = null;
  state.tickets = [];
  state.users = [];
  state.selectedTicketId = null;
  localStorage.removeItem("accessToken");
  showAuth();
  showAuthForm("#login-form");
}

async function login(event) {
  event.preventDefault();
  const form = event.currentTarget;
  try {
    const formData = new FormData(form);
    const data = await request("/auth/login", {
      method: "POST",
      body: JSON.stringify({
        email: formData.get("email"),
        password: formData.get("password"),
      }),
    });

    state.token = data.access_token;
    state.currentUser = data.user;
    localStorage.setItem("accessToken", state.token);
    
    qs("#session-pill").textContent = `${state.currentUser.name} · ${labels[state.currentUser.role]}`;
    
    form.reset();
    showApp();
    
    await loadHealth().catch(e => console.error("Health check failed:", e));
    await loadUsers().catch(e => {
      console.error("Load users failed:", e);
      showToast("Error al cargar usuarios");
    });
    await loadTickets().catch(e => {
      console.error("Load tickets failed:", e);
      showToast("Error al cargar tickets");
    });
    await loadGraphs().catch(e => {
      console.error("Load graphs failed:", e);
      showToast("Error al cargar gráficas");
    });
  } catch (error) {
    console.error("Login error:", error);
    showToast(error.message);
  }
}

async function register(event) {
  event.preventDefault();
  const form = event.currentTarget;
  try {
    const formData = new FormData(form);
    const data = await request("/auth/register", {
      method: "POST",
      body: JSON.stringify({
        name: formData.get("name"),
        email: formData.get("email"),
        password: formData.get("password"),
      }),
    });

    state.token = data.access_token;
    state.currentUser = data.user;
    localStorage.setItem("accessToken", state.token);
    
    qs("#session-pill").textContent = `${state.currentUser.name} · ${labels[state.currentUser.role]}`;
    
    form.reset();
    showApp();
    
    await loadHealth().catch(e => console.error("Health check failed:", e));
    await loadUsers().catch(e => {
      console.error("Load users failed:", e);
      showToast("Error al cargar usuarios");
    });
    await loadTickets().catch(e => {
      console.error("Load tickets failed:", e);
      showToast("Error al cargar tickets");
    });
    await loadGraphs().catch(e => {
      console.error("Load graphs failed:", e);
      showToast("Error al cargar gráficas");
    });
  } catch (error) {
    console.error("Register error:", error);
    showToast(error.message);
  }
}

async function requestPasswordReset(event) {
  event.preventDefault();
  const form = event.currentTarget;
  const formData = new FormData(form);

  try {
    const data = await request("/auth/password-reset/request", {
      method: "POST",
      body: JSON.stringify({
        email: formData.get("email"),
      }),
    });

    form.reset();
    showAuthForm("#login-form");
    showToast(data.message);
  } catch (error) {
    showToast(error.message);
  }
}

async function confirmPasswordReset(event) {
  event.preventDefault();
  const form = event.currentTarget;
  const formData = new FormData(form);
  const password = formData.get("password");
  const passwordConfirm = formData.get("password_confirm");

  if (password !== passwordConfirm) {
    showToast("Las contraseñas no coinciden");
    return;
  }

  try {
    const data = await request("/auth/password-reset/confirm", {
      method: "POST",
      body: JSON.stringify({
        token: formData.get("token"),
        password,
      }),
    });

    form.reset();
    window.history.replaceState({}, document.title, window.location.pathname);
    showAuthForm("#login-form");
    showToast(data.message);
  } catch (error) {
    showToast(error.message);
  }
}

function getFilters() {
  return {
    search: qs("#search-input").value.trim(),
    status: qs("#status-filter").value,
    priority: qs("#priority-filter").value,
  };
}

function buildTicketQuery() {
  const params = new URLSearchParams();
  Object.entries(getFilters()).forEach(([key, value]) => {
    if (value) params.set(key, value);
  });
  const query = params.toString();
  return query ? `/tickets?${query}` : "/tickets";
}

async function loadHealth() {
  try {
    await request("/health");
    qs("#api-status").textContent = "Conectada";
  } catch (error) {
    qs("#api-status").textContent = "Sin conexión";
  }
}

async function loadMe() {
  state.currentUser = await request("/auth/me");
  qs("#session-pill").textContent = `${state.currentUser.name} · ${labels[state.currentUser.role]}`;
  updateRoleVisibility();
}

async function loadUsers() {
  state.users = await request("/users");
  renderUsers();
  fillUserSelects();
  fillGraphCustomerSelect();
}

async function loadTickets() {
  state.tickets = await request(buildTicketQuery());
  renderTickets();
  renderMetrics();

  if (state.selectedTicketId) {
    const exists = state.tickets.some((ticket) => ticket.id === state.selectedTicketId);
    if (exists) await selectTicket(state.selectedTicketId);
  }
}

async function loadGraphs() {
  state.clientGraphs = await request("/client-graphs");
  renderGraphs();
}

function renderMetrics() {
  qs("#metric-total").textContent = state.tickets.length;
  qs("#metric-open").textContent = state.tickets.filter((ticket) => ticket.status === "open").length;
  qs("#metric-progress").textContent = state.tickets.filter((ticket) => ticket.status === "in_progress").length;
  qs("#metric-urgent").textContent = state.tickets.filter((ticket) => ticket.priority === "urgent").length;
}

function renderTickets() {
  const list = qs("#ticket-list");

  if (!state.tickets.length) {
    list.innerHTML = `<div class="empty-state"><strong>No hay tickets</strong><span>Crea un ticket o cambia los filtros.</span></div>`;
    return;
  }

  list.innerHTML = state.tickets.map((ticket) => `
    <button class="ticket-card priority-${ticket.priority} ${ticket.id === state.selectedTicketId ? "active" : ""}" data-ticket-id="${ticket.id}" type="button">
      <div class="ticket-title">
        <strong>#${ticket.id} ${escapeHtml(ticket.title)}</strong>
        <span class="pill priority-${ticket.priority}">${labels[ticket.priority]}</span>
      </div>
      <div class="ticket-meta">
        <span class="pill status-${ticket.status}">${labels[ticket.status]}</span>
        <span class="pill">${escapeHtml(labelFor(ticket.category))}</span>
        <span class="pill">${ticket.assignee ? ticket.assignee.name : "Sin asignar"}</span>
        ${ticket.attachments?.length ? `<span class="pill">${ticket.attachments.length} captura${ticket.attachments.length === 1 ? "" : "s"}</span>` : ""}
      </div>
    </button>
  `).join("");

  list.querySelectorAll("[data-ticket-id]").forEach((button) => {
    button.addEventListener("click", () => selectTicket(Number(button.dataset.ticketId)));
  });
}

function renderUsers() {
  const list = qs("#user-list");
  const canManage = isCurrentAdmin();
  const form = qs("#user-form");

  if (!state.users.length) {
    list.innerHTML = `<div class="empty-state"><strong>No hay usuarios</strong><span>Registra el primer administrador desde la pantalla de acceso.</span></div>`;
  } else {
    list.innerHTML = state.users.map((user) => `
      <article class="user-card">
        <form class="user-edit-form" data-user-id="${user.id}">
          <input name="name" type="text" value="${escapeHtml(user.name)}" ${canManage ? "" : "disabled"}>
          <input name="email" type="email" value="${escapeHtml(user.email)}" ${canManage ? "" : "disabled"}>
          <input name="password" type="password" placeholder="Nueva contraseña opcional" minlength="8" ${canManage ? "" : "disabled"}>
          <select name="role" ${canManage ? "" : "disabled"}>
            ${["admin", "agent", "customer"].map((role) => `
              <option value="${role}" ${user.role === role ? "selected" : ""}>${labels[role]}</option>
            `).join("")}
          </select>
          <div class="user-actions">
            <button class="ghost-button" type="submit" ${canManage ? "" : "disabled"}>Guardar</button>
            <button class="danger-button" type="button" data-delete-user="${user.id}" ${canManage && user.id !== state.currentUser?.id ? "" : "disabled"}>Eliminar</button>
          </div>
        </form>
      </article>
    `).join("");
  }

  form.querySelectorAll("input, select, button").forEach((element) => {
    element.disabled = !canManage;
  });
  qs("#admin-note").textContent = canManage
    ? "Puedes crear, editar y borrar usuarios."
    : "Solo los administradores pueden crear, editar o borrar usuarios.";

  list.querySelectorAll(".user-edit-form").forEach((formElement) => {
    formElement.addEventListener("submit", updateUser);
  });
  list.querySelectorAll("[data-delete-user]").forEach((button) => {
    button.addEventListener("click", () => deleteUser(Number(button.dataset.deleteUser)));
  });
}

function fillUserSelects() {
  const requesterSelect = qs("#requester-select");
  const assigneeSelect = qs("#assignee-select");
  if (!requesterSelect || !assigneeSelect) return;

  const options = [
    `<option value="">Sin seleccionar</option>`,
    ...state.users.map((user) => `<option value="${user.id}">${user.name} · ${labels[user.role]}</option>`),
  ].join("");

  requesterSelect.innerHTML = options;
  assigneeSelect.innerHTML = options;
}

function fillGraphCustomerSelect() {
  const select = qs("#graph-customer-select");
  if (!select) return;

  const customers = state.users.filter((user) => user.role === "customer");
  select.innerHTML = customers.length
    ? customers.map((user) => `<option value="${user.id}">${escapeHtml(user.name)} · ${escapeHtml(user.email)}</option>`).join("")
    : `<option value="">No hay clientes disponibles</option>`;
}

function parseGraphItems(chartData) {
  return String(chartData)
    .split(/[\n,;]+/)
    .map((item) => item.trim())
    .filter(Boolean);
}

function parseGraphValue(item, index) {
  const match = item.match(/(\d+(?:[.,]\d+)?)/);
  if (!match) return 45 + ((index * 17) % 46);
  return Math.max(8, Math.min(100, Number(match[1].replace(",", "."))));
}

function renderGraphPreview(graph) {
  const items = parseGraphItems(graph.chart_data);
  if (!items.length) return `<div class="graph-preview empty-state"><strong>Sin datos</strong></div>`;

  if (graph.graph_type === "cacti") {
    return `
      <div class="graph-preview graph-cacti is-loading">
        <img data-cacti-image-id="${graph.id}" alt="${escapeHtml(graph.title)}" loading="lazy" hidden>
        <span>Cargando gráfica de Cacti...</span>
      </div>
    `;
  }

  if (graph.graph_type === "bar") {
    const bars = items.map((item, index) => {
      const value = parseGraphValue(item, index);
      return `<span class="graph-bar" style="height:${value}%"><small>${escapeHtml(item)}</small></span>`;
    }).join("");
    return `<div class="graph-preview graph-bars">${bars}</div>`;
  }

  if (graph.graph_type === "line") {
    const points = items.map((item, index) => {
      const x = items.length === 1 ? 50 : (index / (items.length - 1)) * 100;
      const y = 100 - parseGraphValue(item, index);
      return `${x},${y}`;
    }).join(" ");
    return `
      <div class="graph-preview graph-line">
        <svg viewBox="0 0 100 100" preserveAspectRatio="none" aria-hidden="true">
          <polyline points="${points}" />
        </svg>
        <div>${items.map((item) => `<span>${escapeHtml(item)}</span>`).join("")}</div>
      </div>
    `;
  }

  if (graph.graph_type === "pie") {
    return `
      <div class="graph-preview graph-pie">
        <span></span>
        <div>${items.map((item) => `<small>${escapeHtml(item)}</small>`).join("")}</div>
      </div>
    `;
  }

  return `
    <div class="graph-preview graph-network">
      <strong>${escapeHtml(graph.customer?.name || "Cliente")}</strong>
      <div>
        ${items.map((item) => `<span>${escapeHtml(item)}</span>`).join("")}
      </div>
    </div>
  `;
}

let chartInstances = {
  status: null,
  priority: null,
  category: null,
  assignee: null,
};

async function loadCharts() {
  try {
    const stats = await request("/tickets/statistics");
    renderCharts(stats);
  } catch (error) {
    console.error("Error loading charts:", error);
    showToast("No se pudieron cargar los gráficos");
  }
}

function renderCharts(stats) {
  const commonOptions = {
    responsive: true,
    maintainAspectRatio: true,
    plugins: {
      legend: {
        labels: {
          color: "#a9b9d7",
          font: { family: "'Eina MC', sans-serif" },
          padding: 15,
        },
      },
    },
  };

  // Status Chart (Bar)
  const statusCtx = qs("#chart-status");
  if (statusCtx) {
    if (chartInstances.status) chartInstances.status.destroy();
    chartInstances.status = new Chart(statusCtx, {
      type: "bar",
      data: {
        labels: Object.keys(stats.by_status).map((s) => labels[s] || s),
        datasets: [{
          label: "Cantidad",
          data: Object.values(stats.by_status),
          backgroundColor: ["#00d620", "#0047ab", "#ffbf00", "#f76b1c", "#be1e24", "#7c8798"],
          borderRadius: 4,
          borderSkipped: false,
        }],
      },
      options: {
        ...commonOptions,
        scales: {
          y: {
            beginAtZero: true,
            ticks: { color: "#a9b9d7" },
            grid: { color: "rgba(0, 71, 171, 0.1)" },
          },
          x: {
            ticks: { color: "#a9b9d7" },
            grid: { color: "rgba(0, 71, 171, 0.1)" },
          },
        },
      },
    });
  }

  // Priority Chart (Doughnut)
  const priorityCtx = qs("#chart-priority");
  if (priorityCtx) {
    if (chartInstances.priority) chartInstances.priority.destroy();
    chartInstances.priority = new Chart(priorityCtx, {
      type: "doughnut",
      data: {
        labels: Object.keys(stats.by_priority).map((p) => labels[p] || p),
        datasets: [{
          data: Object.values(stats.by_priority),
          backgroundColor: ["#00d620", "#ffbf00", "#f76b1c", "#be1e24"],
          borderColor: "#08080d",
          borderWidth: 2,
        }],
      },
      options: commonOptions,
    });
  }

  // Category Chart (Pie)
  const categoryCtx = qs("#chart-category");
  if (categoryCtx) {
    if (chartInstances.category) chartInstances.category.destroy();
    chartInstances.category = new Chart(categoryCtx, {
      type: "pie",
      data: {
        labels: Object.keys(stats.by_category).map((c) => labels[c] || c),
        datasets: [{
          data: Object.values(stats.by_category),
          backgroundColor: ["#0047ab", "#990ef1", "#00d620", "#ffbf00", "#f76b1c", "#be1e24"],
          borderColor: "#08080d",
          borderWidth: 2,
        }],
      },
      options: commonOptions,
    });
  }

  // Assignee Chart (Horizontal Bar)
  const assigneeCtx = qs("#chart-assignee");
  if (assigneeCtx) {
    if (chartInstances.assignee) chartInstances.assignee.destroy();
    chartInstances.assignee = new Chart(assigneeCtx, {
      type: "bar",
      data: {
        labels: Object.keys(stats.by_assignee).length > 0 ? Object.keys(stats.by_assignee) : ["Sin asignación"],
        datasets: [{
          label: "Tickets asignados",
          data: Object.keys(stats.by_assignee).length > 0 ? Object.values(stats.by_assignee) : [0],
          backgroundColor: "#0047ab",
          borderRadius: 4,
          borderSkipped: false,
        }],
      },
      options: {
        ...commonOptions,
        indexAxis: "y",
        scales: {
          x: {
            beginAtZero: true,
            ticks: { color: "#a9b9d7" },
            grid: { color: "rgba(0, 71, 171, 0.1)" },
          },
          y: {
            ticks: { color: "#a9b9d7" },
            grid: { color: "rgba(0, 71, 171, 0.1)" },
          },
        },
      },
    });
  }
}

function renderGraphs() {
  const list = qs("#graph-list");
  const form = qs("#graph-form");
  const canManage = canManageGraphs();

  form.hidden = !canManage;
  fillGraphCustomerSelect();

  if (!state.clientGraphs.length) {
    list.innerHTML = `<div class="empty-state"><strong>No hay gráficas asignadas</strong><span>Las gráficas aparecerán aquí cuando un agente o administrador las asigne.</span></div>`;
    return;
  }

  list.innerHTML = state.clientGraphs.map((graph) => `
    <article class="graph-card">
      <div class="graph-card-heading">
        <div>
          <p class="eyebrow">${labels[graph.graph_type] || "Gráfica"}</p>
          <h3>${escapeHtml(graph.title)}</h3>
        </div>
        ${canManage ? `<button class="danger-button" data-delete-graph="${graph.id}" type="button">Eliminar</button>` : ""}
      </div>
      ${renderGraphPreview(graph)}
      <p>${escapeHtml(graph.description || "Equipo asignado al cliente.")}</p>
      <div class="ticket-meta">
        <span class="pill">Cliente: ${escapeHtml(graph.customer?.name || "Sin cliente")}</span>
        <span class="pill">Asignado por: ${escapeHtml(graph.assigned_by?.name || "Sistema")}</span>
        <span class="pill">${formatDate(graph.updated_at)}</span>
      </div>
    </article>
  `).join("");

  list.querySelectorAll("[data-delete-graph]").forEach((button) => {
    button.addEventListener("click", () => deleteGraph(Number(button.dataset.deleteGraph)));
  });

  hydrateCactiImages(list);
}

function renderTicketGraphs(ticket) {
  const graphs = state.clientGraphs.filter((graph) => graph.customer?.id === ticket.requester_id);
  if (!graphs.length) {
    return `
      <section class="ticket-graphs">
        <p class="eyebrow">Gráficas del cliente</p>
        <div class="empty-state"><strong>No hay gráficas asignadas</strong><span>Asigna una gráfica al cliente desde la vista Gráficas para que aparezca aquí.</span></div>
      </section>
    `;
  }

  return `
    <section class="ticket-graphs">
      <p class="eyebrow">Gráficas del cliente</p>
      <div class="graph-grid">
        ${graphs.map((graph) => `
          <article class="graph-card">
            <div class="graph-card-heading">
              <div>
                <p class="eyebrow">${labels[graph.graph_type] || "Gráfica"}</p>
                <h3>${escapeHtml(graph.title)}</h3>
              </div>
            </div>
            ${renderGraphPreview(graph)}
            <p>${escapeHtml(graph.description || "Gráfica asociada al cliente.")}</p>
          </article>
        `).join("")}
      </div>
    </section>
  `;
}

async function selectTicket(ticketId) {
  state.selectedTicketId = ticketId;
  const ticket = await request(`/tickets/${ticketId}`);
  renderTicketDetail(ticket);
  renderTickets();
}

function renderTicketDetail(ticket) {
  const canManage = canManageTickets();
  qs("#ticket-detail").innerHTML = `
    <section class="ticket-detail">
      <p class="eyebrow">Ticket #${ticket.id}</p>
      <h3>${escapeHtml(ticket.title)}</h3>
      <div class="detail-meta">
        <span class="pill status-${ticket.status}">${labels[ticket.status]}</span>
        <span class="pill priority-${ticket.priority}">${labels[ticket.priority]}</span>
        <span class="pill">${escapeHtml(labelFor(ticket.category))}</span>
      </div>
      <p>${escapeHtml(ticket.description)}</p>
      <div class="detail-meta">
        <span class="pill">Creado: ${formatDate(ticket.created_at)}</span>
        <span class="pill">Asignado: ${ticket.assignee ? ticket.assignee.name : "Sin asignar"}</span>
      </div>
      ${canManage ? `
      <div class="detail-actions">
        <select id="detail-status">
          ${ticketStatuses.map((status) => `
            <option value="${status}" ${ticket.status === status ? "selected" : ""}>${labels[status]}</option>
          `).join("")}
        </select>
        <select id="detail-assignee">
          <option value="">Sin asignar</option>
          ${state.users.map((user) => `
            <option value="${user.id}" ${ticket.assigned_to_id === user.id ? "selected" : ""}>${user.name}</option>
          `).join("")}
        </select>
        <button class="ghost-button" id="save-ticket-button" type="button">Guardar cambios</button>
        <button class="ghost-button" id="delete-ticket-button" type="button">Eliminar</button>
      </div>
      ` : ""}
      ${renderTicketGraphs(ticket)}
      <section class="attachments">
        <p class="eyebrow">Capturas</p>
        <div class="attachment-grid">
          ${ticket.attachments?.length ? ticket.attachments.map((attachment) => `
            <a class="attachment-card" href="#" data-attachment-url="${API_URL}${attachment.url}" target="_blank" rel="noopener">
              <img alt="${escapeHtml(attachment.original_filename)}" hidden>
              <span>${escapeHtml(attachment.original_filename)}</span>
              <small>${formatFileSize(attachment.size_bytes)} · ${attachment.uploader ? escapeHtml(attachment.uploader.name) : "Sin usuario"}</small>
            </a>
          `).join("") : `<p>No hay capturas adjuntas.</p>`}
        </div>
        <form class="attachment-form" id="attachment-form">
          <input name="attachments" type="file" accept="image/png,image/jpeg,image/gif,image/webp,image/*" multiple>
          <button class="ghost-button" type="submit">Agregar capturas</button>
        </form>
      </section>
      <section class="history">
        <p class="eyebrow">Historial y trazabilidad</p>
        ${renderTicketTimeline(ticket)}
      </section>
      <section class="comments">
        <p class="eyebrow">Comentarios</p>
        <div id="comment-list">
          ${ticket.comments.length ? ticket.comments.map((comment) => `
            <article class="comment">
              <small>${comment.author ? comment.author.name : "Sin autor"} · ${formatDate(comment.created_at)}</small>
              <p>${escapeHtml(comment.body)}</p>
            </article>
          `).join("") : `<p>No hay comentarios todavía.</p>`}
        </div>
        <form class="comment-form" id="comment-form">
          <textarea name="body" rows="3" placeholder="Agregar comentario" required></textarea>
          <button class="primary-button" type="submit">Comentar</button>
        </form>
      </section>
    </section>
  `;

  if (canManage) {
    qs("#save-ticket-button").addEventListener("click", () => saveTicketChanges(ticket.id));
    qs("#delete-ticket-button").addEventListener("click", () => deleteTicket(ticket.id));
  }
  qs("#attachment-form").addEventListener("submit", (event) => uploadAttachmentFromDetail(event, ticket.id));
  qs("#comment-form").addEventListener("submit", (event) => createComment(event, ticket.id));
  bindTimelineFilters(qs("#ticket-detail"));
  hydrateCactiImages(qs("#ticket-detail"));
  hydrateAttachmentImages(qs("#ticket-detail"));
}

async function saveTicketChanges(ticketId) {
  if (!canManageTickets()) {
    showToast("No tienes permisos para modificar tickets");
    return;
  }

  await request(`/tickets/${ticketId}`, {
    method: "PATCH",
    body: JSON.stringify({
      status: qs("#detail-status").value,
      assigned_to_id: normalizeFormNumber(qs("#detail-assignee").value),
    }),
  });

  showToast("Ticket actualizado");
  await loadTickets();
}

async function deleteTicket(ticketId) {
  if (!canManageTickets()) {
    showToast("No tienes permisos para eliminar tickets");
    return;
  }

  const confirmed = window.confirm("¿Eliminar este ticket?");
  if (!confirmed) return;

  await request(`/tickets/${ticketId}`, { method: "DELETE" });
  state.selectedTicketId = null;
  qs("#ticket-detail").innerHTML = `<div class="empty-state"><strong>Ticket eliminado</strong><span>Selecciona otro ticket para continuar.</span></div>`;
  showToast("Ticket eliminado");
  await loadTickets();
}

async function createComment(event, ticketId) {
  event.preventDefault();
  const form = event.currentTarget;
  const formData = new FormData(form);

  await request(`/tickets/${ticketId}/comments`, {
    method: "POST",
    body: JSON.stringify({
      body: formData.get("body"),
    }),
  });

  form.reset();
  showToast("Comentario agregado");
  await selectTicket(ticketId);
}

async function uploadTicketAttachments(ticketId, files) {
  for (const file of files) {
    const formData = new FormData();
    formData.append("file", file);
    await request(`/tickets/${ticketId}/attachments`, {
      method: "POST",
      body: formData,
    });
  }
}

async function uploadAttachmentFromDetail(event, ticketId) {
  event.preventDefault();
  const form = event.currentTarget;
  const files = Array.from(form.elements.attachments.files || []);
  if (!files.length) {
    showToast("Selecciona una captura");
    return;
  }

  await uploadTicketAttachments(ticketId, files);
  form.reset();
  showToast(files.length === 1 ? "Captura agregada" : "Capturas agregadas");
  await selectTicket(ticketId);
}

async function createTicket(event) {
  event.preventDefault();
  const form = event.currentTarget;
  const formData = new FormData(form);
  const attachments = Array.from(formData.getAll("attachments")).filter((file) => file.size > 0);

  const ticket = await request("/tickets", {
    method: "POST",
    body: JSON.stringify({
      title: formData.get("title"),
      description: formData.get("description"),
      priority: formData.get("priority"),
      category: formData.get("category") || "general",
    }),
  });

  if (attachments.length) {
    await uploadTicketAttachments(ticket.id, attachments);
  }

  form.reset();
  qs("#ticket-modal").close();
  showToast(attachments.length ? "Ticket creado con capturas" : "Ticket creado");
  await loadTickets();
}

async function createUser(event) {
  event.preventDefault();
  const form = event.currentTarget;
  const formData = new FormData(form);

  await request("/users", {
    method: "POST",
    body: JSON.stringify({
      name: formData.get("name"),
      email: formData.get("email"),
      password: formData.get("password"),
      role: formData.get("role"),
    }),
  });

  form.reset();
  showToast("Usuario creado");
  await loadUsers();
}

async function updateUser(event) {
  event.preventDefault();
  const form = event.currentTarget;
  const formData = new FormData(form);
  const userId = Number(form.dataset.userId);
  const password = formData.get("password");
  const payload = {
    name: formData.get("name"),
    email: formData.get("email"),
    role: formData.get("role"),
  };
  if (password) payload.password = password;

  await request(`/users/${userId}`, {
    method: "PATCH",
    body: JSON.stringify(payload),
  });

  showToast("Usuario actualizado");
  await loadUsers();
}

async function deleteUser(userId) {
  const confirmed = window.confirm("¿Eliminar este usuario? Se quitará de tickets y comentarios asociados.");
  if (!confirmed) return;

  await request(`/users/${userId}`, { method: "DELETE" });
  showToast("Usuario eliminado");
  await loadUsers();
  await loadTickets();
}

async function createGraph(event) {
  event.preventDefault();
  const form = event.currentTarget;
  const formData = new FormData(form);
  const customerId = normalizeFormNumber(formData.get("customer_id"));

  if (!customerId) {
    showToast("Selecciona un cliente");
    return;
  }

  await request("/client-graphs", {
    method: "POST",
    body: JSON.stringify({
      title: formData.get("title"),
      description: formData.get("description") || null,
      graph_type: formData.get("graph_type"),
      chart_data: formData.get("chart_data"),
      customer_id: customerId,
    }),
  });

  form.reset();
  fillGraphCustomerSelect();
  showToast("Gráfica asignada");
  await loadGraphs();
}

async function deleteGraph(graphId) {
  const confirmed = window.confirm("¿Eliminar esta gráfica asignada?");
  if (!confirmed) return;

  await request(`/client-graphs/${graphId}`, { method: "DELETE" });
  showToast("Gráfica eliminada");
  await loadGraphs();
}

function bindEvents() {
  qs("#login-form").addEventListener("submit", login);
  qs("#register-form").addEventListener("submit", register);
  qs("#password-reset-request-form").addEventListener("submit", requestPasswordReset);
  qs("#password-reset-confirm-form").addEventListener("submit", confirmPasswordReset);
  qs("#forgot-password-button").addEventListener("click", () => showAuthForm("#password-reset-request-form"));
  document.querySelectorAll("[data-auth-back]").forEach((button) => {
    button.addEventListener("click", () => showAuthForm("#login-form"));
  });
  qs("#logout-button").addEventListener("click", logout);
  qs("#refresh-button").addEventListener("click", bootstrap);
  qs("#new-ticket-button").addEventListener("click", () => qs("#ticket-modal").showModal());
  qs("#close-ticket-modal").addEventListener("click", () => qs("#ticket-modal").close());
  qs("#cancel-ticket-button").addEventListener("click", () => qs("#ticket-modal").close());
  qs("#ticket-form").addEventListener("submit", createTicket);
  qs("#user-form").addEventListener("submit", createUser);
  qs("#graph-form").addEventListener("submit", createGraph);
  qs("#close-graph-fullscreen").addEventListener("click", closeGraphFullscreen);
  qs("#graph-fullscreen").addEventListener("click", (event) => {
    if (event.target.id === "graph-fullscreen") closeGraphFullscreen();
  });
  document.addEventListener("keydown", (event) => {
    if (event.key === "Escape" && !qs("#graph-fullscreen").hidden) {
      closeGraphFullscreen();
    }
  });

  document.querySelectorAll(".auth-tab").forEach((button) => {
    button.addEventListener("click", () => {
      document.querySelectorAll(".auth-tab").forEach((tab) => tab.classList.remove("active"));
      button.classList.add("active");
      const isLogin = button.dataset.authTab === "login";
      showAuthForm(isLogin ? "#login-form" : "#register-form");
    });
  });

  ["#search-input", "#status-filter", "#priority-filter"].forEach((selector) => {
    qs(selector).addEventListener("input", loadTickets);
  });

  document.querySelectorAll(".side-link").forEach((button) => {
    button.addEventListener("click", () => {
      const view = button.dataset.view;
      if (view === "users" && state.currentUser?.role === "customer") return;

      document.querySelectorAll(".side-link").forEach((item) => item.classList.remove("active"));
      button.classList.add("active");

      qs("#dashboard-view").hidden = view !== "dashboard";
      qs("#tickets-view").hidden = view !== "dashboard" && view !== "tickets";
      qs("#ticket-detail").hidden = view !== "dashboard" && view !== "tickets";
      qs("#dashboard-charts-view").hidden = view !== "charts";
      qs("#graphs-view").hidden = view !== "graphs";
      qs("#users-view").hidden = view !== "users";

      if (view === "charts") {
        loadCharts();
      }
    });
  });
}

async function bootstrap() {
  try {
    const resetToken = new URLSearchParams(window.location.search).get("reset_token");
    if (resetToken) {
      state.token = null;
      localStorage.removeItem("accessToken");
      qs("#password-reset-confirm-form [name='token']").value = resetToken;
      showAuth();
      showAuthForm("#password-reset-confirm-form");
      return;
    }

    if (!state.token) {
      showAuth();
      showAuthForm("#login-form");
      return;
    }

    showApp();
    await loadHealth();
    await loadMe();
    await loadUsers();
    await loadTickets();
    await loadGraphs();
  } catch (error) {
    if (String(error.message).toLowerCase().includes("sesión") || String(error.message).toLowerCase().includes("iniciar sesión")) {
      logout();
    }
    showToast(error.message);
  }
}

bindEvents();
bootstrap();
