import { initializeApp } from "https://www.gstatic.com/firebasejs/10.12.2/firebase-app.js";
import {
  browserPopupRedirectResolver,
  browserSessionPersistence,
  GoogleAuthProvider,
  initializeAuth,
  onAuthStateChanged,
  signInWithEmailAndPassword,
  signInWithPopup,
  signOut,
} from "https://www.gstatic.com/firebasejs/10.12.2/firebase-auth.js";

const firebaseConfig = {
  apiKey: "AIzaSyAltwdGZdj6RWKKKvc1cRIXTRA8IIs-5ZE",
  authDomain: "aistoryadventure-8796e.firebaseapp.com",
  projectId: "aistoryadventure-8796e",
  storageBucket: "aistoryadventure-8796e.firebasestorage.app",
  messagingSenderId: "587433707758",
  appId: "1:587433707758:web:2a1a36b90b9948fe7c8bff",
  measurementId: "G-EJW5P4ELFT",
};

const runtimeConfig = globalThis.AI_STORY_CONFIG || {};
const API_BASE = (runtimeConfig.API_BASE || "http://127.0.0.1:8000").replace(/\/+$/, "");

const app = initializeApp(firebaseConfig, "admin-console");
const auth = initializeAuth(app, {
  persistence: browserSessionPersistence,
  popupRedirectResolver: browserPopupRedirectResolver,
});
const provider = new GoogleAuthProvider();

const $ = (id) => document.getElementById(id);

const loginView = $("adminLoginView");
const deniedView = $("adminDeniedView");
const dashboardView = $("adminDashboardView");
const googleLoginBtn = $("adminGoogleLoginBtn");
const emailLoginBtn = $("adminEmailLoginBtn");
const emailInput = $("adminEmailInput");
const passwordInput = $("adminPasswordInput");
const loginStatus = $("adminLoginStatus");
const deniedText = $("adminDeniedText");
const retryAccessBtn = $("adminRetryAccessBtn");
const deniedLogoutBtn = $("adminDeniedLogoutBtn");
const logoutBtn = $("adminLogoutBtn");
const refreshBtn = $("adminRefreshBtn");
const statusText = $("adminStatus");
const identityText = $("adminIdentity");

const totalSessions = $("adminTotalSessions");
const usersCount = $("adminUsersCount");
const bannedCount = $("adminBannedCount");
const usageToday = $("adminUsageToday");
const usageErrorsToday = $("adminUsageErrorsToday");
const estimatedTokensToday = $("adminEstimatedTokensToday");
const pointsSpentToday = $("adminPointsSpentToday");
const rateLimitState = $("adminRateLimitState");

const systemFacts = $("adminSystemFacts");
const usageFacts = $("adminUsageFacts");
const readinessSummary = $("adminReadinessSummary");
const readinessList = $("adminReadinessList");
const usageTodayFacts = $("adminUsageTodayFacts");
const usageThirtyFacts = $("adminUsageThirtyFacts");
const recentErrorsList = $("adminRecentErrorsList");
const auditPreview = $("adminAuditPreview");
const usageUsersList = $("adminUsageUsersList");
const usageList = $("adminUsageList");
const usersList = $("adminUsersList");
const sessionsList = $("adminSessionsList");
const auditOutput = $("adminOutput");

const maintenanceToggle = $("adminMaintenanceToggle");
const maintenanceMessage = $("adminMaintenanceMessage");
const pointsToggle = $("adminPointsToggle");
const costAdventure = $("adminCostAdventure");
const costNovelWorld = $("adminCostNovelWorld");
const costNovelFoundation = $("adminCostNovelFoundation");
const costTurn = $("adminCostTurn");
const rateLimitToggle = $("adminRateLimitToggle");
const dailyTurnLimit = $("adminDailyTurnLimit");
const dailyCreateLimit = $("adminDailyCreateLimit");
const usageRetentionDays = $("adminUsageRetentionDays");
const saveSettingsBtn = $("adminSaveSettingsBtn");

const targetUidInput = $("adminTargetUid");
const pointDeltaInput = $("adminPointDelta");
const pointReasonInput = $("adminPointReason");
const adjustPointsBtn = $("adminAdjustPointsBtn");
const banReasonInput = $("adminBanReason");
const banUserBtn = $("adminBanUserBtn");
const unbanUserBtn = $("adminUnbanUserBtn");

let isAdmin = false;
let currentOverview = null;
let currentUsage = null;

function showOnly(view) {
  [loginView, deniedView, dashboardView].forEach((item) => {
    item?.classList.toggle("hidden", item !== view);
  });
}

function setStatus(message, tone = "muted") {
  if (!statusText) return;
  statusText.textContent = message;
  statusText.dataset.tone = tone;
}

function setLoginStatus(message, tone = "muted") {
  if (!loginStatus) return;
  loginStatus.textContent = message;
  loginStatus.dataset.tone = tone;
}

function setBusy(isBusy) {
  [
    googleLoginBtn,
    emailLoginBtn,
    retryAccessBtn,
    logoutBtn,
    deniedLogoutBtn,
    refreshBtn,
    saveSettingsBtn,
    adjustPointsBtn,
    banUserBtn,
    unbanUserBtn,
  ].forEach((button) => {
    if (button) button.disabled = isBusy;
  });
}

async function requestJson(url, options = {}) {
  const user = auth.currentUser;
  if (!user) throw new Error("Admin login is required.");

  const token = await user.getIdToken(true);
  const headers = {
    "Content-Type": "application/json",
    ...(options.headers || {}),
    Authorization: `Bearer ${token}`,
  };

  let response;
  try {
    response = await fetch(url, { ...options, headers });
  } catch (err) {
    throw new Error(err?.message || "Network request failed.");
  }

  const contentType = response.headers.get("content-type") || "";
  const data = contentType.includes("application/json")
    ? await response.json().catch(() => null)
    : await response.text().catch(() => "");

  if (!response.ok) {
    throw new Error(getApiErrorMessage(data, response.status));
  }

  return data;
}

function getApiErrorMessage(data, status) {
  if (data && typeof data === "object") {
    if (typeof data.detail === "string") return data.detail;
    if (Array.isArray(data.detail)) {
      return data.detail.map((item) => item.msg || JSON.stringify(item)).join("; ");
    }
    if (typeof data.message === "string") return data.message;
  }
  if (typeof data === "string" && data.trim()) return data;
  return `Request failed (${status})`;
}

async function checkAdminAccess() {
  try {
    const data = await requestJson(`${API_BASE}/admin/me`);
    isAdmin = data?.admin === true;

    if (!isAdmin) {
      showDenied("The backend did not confirm admin access.");
      return false;
    }

    if (identityText) {
      identityText.textContent = data.email || data.name || data.uid || "Admin";
    }

    showOnly(dashboardView);
    await loadDashboard();
    return true;
  } catch (err) {
    showDenied(err.message || "Admin access could not be confirmed.");
    return false;
  }
}

function showDenied(message) {
  isAdmin = false;
  if (deniedText) deniedText.textContent = message;
  showOnly(deniedView);
}

async function loadDashboard() {
  if (!isAdmin) return;

  setBusy(true);
  setStatus("Loading admin data...", "muted");

  const safeRequest = (promise, fallback) => promise.catch(err => {
    console.warn("Non-critical admin endpoint failed:", err);
    return fallback;
  });

  try {
    const [overview, users, sessions, audit, usage, usageUsers, errors, submissions] = await Promise.all([
      requestJson(`${API_BASE}/admin/overview`),
      safeRequest(requestJson(`${API_BASE}/admin/users?limit=100`), { items: [] }),
      safeRequest(requestJson(`${API_BASE}/admin/sessions?limit=40`), { items: [] }),
      safeRequest(requestJson(`${API_BASE}/admin/audit?limit=60`), { items: [] }),
      safeRequest(requestJson(`${API_BASE}/admin/usage?limit=80`), { today: {}, last_30d: {}, items: [] }),
      safeRequest(requestJson(`${API_BASE}/admin/usage/users?limit=100`), { items: [] }),
      safeRequest(requestJson(`${API_BASE}/admin/errors?limit=50`), { items: [] }),
      safeRequest(requestJson(`${API_BASE}/admin/submissions`), []),
    ]);

    currentOverview = overview;
    currentUsage = usage;

    renderOverview(overview);
    renderSettings(overview.settings || {});
    renderUsage(usage);
    renderUsageUsers(usageUsers.items || []);
    renderUsers(users.items || []);
    renderSessions(sessions.items || []);
    renderErrors(errors.items || []);
    renderAudit(audit.items || []);
    renderSubmissions(submissions || []);
    setStatus("Admin data is live.", "ok");
  } catch (err) {
    setStatus(err.message || "Could not load admin data.", "error");
  } finally {
    setBusy(false);
  }
}

function renderOverview(overview = {}) {
  const settings = overview.settings || {};

  setText(totalSessions, formatNumber(overview.sessions_total));
  setText(usersCount, formatNumber(overview.users_total));
  setText(bannedCount, formatNumber(overview.users_banned));
  setText(usageToday, formatNumber(overview.usage_today));
  setText(usageErrorsToday, formatNumber(overview.usage_errors_today));
  setText(estimatedTokensToday, formatNumber(overview.estimated_tokens_today));
  setText(pointsSpentToday, formatNumber(overview.points_spent_today));
  setText(rateLimitState, settings.rate_limit_enabled ? "On" : "Off");

  renderFacts(systemFacts, [
    ["Environment", overview.app_env || "local"],
    ["Provider", `${overview.text_provider || "-"} / ${overview.text_model || "-"}`],
    ["API key", overview.text_provider === "mock" ? "Mock provider" : "Server-side secret"],
    ["Embeddings", overview.embedding_provider || "-"],
    ["Storage", overview.storage_mode || "-"],
    ["Catalog", `${formatNumber(overview.catalog_count)} worlds`],
    ["Latest session", formatDate(overview.latest_updated_at)],
  ]);

  renderFacts(usageFacts, [
    ["Today", `${formatNumber(overview.usage_today)} AI events`],
    ["Errors", `${formatNumber(overview.usage_errors_today)} today`],
    ["Est. tokens", `${formatNumber(overview.estimated_tokens_today)} today`],
    ["30d est. tokens", formatNumber(overview.estimated_tokens_30d)],
    ["Points spent", `${formatNumber(overview.points_spent_today)} today`],
    ["Rate limit", settings.rate_limit_enabled ? `${settings.daily_turn_limit}/day turns` : "Disabled"],
  ]);

  renderReadiness(overview.readiness || {});
}

function renderReadiness(readiness = {}) {
  if (!readinessSummary || !readinessList) return;

  const status = readiness.overall_status || "unknown";
  const statusClass = status === "ok" ? "ok" : status === "warning" ? "warn" : "danger";
  const checks = Array.isArray(readiness.checks) ? readiness.checks : [];
  const errors = checks.filter((item) => item.status === "error").length;
  const warnings = checks.filter((item) => item.status === "warning").length;
  const readyText = readiness.production_ready ? "Ready for production" : "Not production-ready yet";

  readinessSummary.innerHTML = `
    <span class="admin-status-pill ${statusClass}">${escapeHtml(status)}</span>
    <strong>${escapeHtml(readyText)}</strong>
    <small>${formatNumber(errors)} errors / ${formatNumber(warnings)} warnings</small>
  `;

  if (!checks.length) {
    readinessList.innerHTML = `<div class="admin-empty">No readiness checks returned.</div>`;
    return;
  }

  readinessList.innerHTML = checks.map((item) => {
    const itemClass = item.status === "ok" ? "ok" : item.status === "warning" ? "warn" : "danger";
    return `
      <div class="admin-check-row ${itemClass}">
        <span class="admin-status-pill ${itemClass}">${escapeHtml(item.status || "-")}</span>
        <div>
          <strong>${escapeHtml(item.label || item.check_id || "Check")}</strong>
          <p>${escapeHtml(item.message || "")}</p>
          ${item.hint ? `<small>${escapeHtml(item.hint)}</small>` : ""}
        </div>
      </div>
    `;
  }).join("");
}

function renderSettings(settings = {}) {
  if (maintenanceToggle) maintenanceToggle.checked = Boolean(settings.maintenance_enabled);
  if (maintenanceMessage) {
    maintenanceMessage.value =
      settings.maintenance_message ||
      "AI Story Adventure is under maintenance. Please come back soon.";
  }
  if (pointsToggle) pointsToggle.checked = Boolean(settings.points_enabled);
  if (costAdventure) costAdventure.value = settings.cost_start_adventure ?? 10;
  if (costNovelWorld) costNovelWorld.value = settings.cost_novel_world ?? 5;
  if (costNovelFoundation) costNovelFoundation.value = settings.cost_novel_foundation ?? 15;
  if (costTurn) costTurn.value = settings.cost_turn ?? 3;
  if (rateLimitToggle) rateLimitToggle.checked = Boolean(settings.rate_limit_enabled);
  if (dailyTurnLimit) dailyTurnLimit.value = settings.daily_turn_limit ?? 20;
  if (dailyCreateLimit) dailyCreateLimit.value = settings.daily_create_limit ?? 5;
  if (usageRetentionDays) usageRetentionDays.value = settings.usage_log_retention_days ?? 30;
}

function renderUsage(usage = {}) {
  const today = usage.today || {};
  const thirty = usage.last_30d || {};

  renderFacts(usageTodayFacts, [
    ["Requests", formatNumber(today.requests)],
    ["Success", formatNumber(today.successes)],
    ["Errors", formatNumber(today.errors)],
    ["Blocked", formatNumber(today.blocked)],
    ["Est. input", formatNumber(today.estimated_input_tokens)],
    ["Est. output", formatNumber(today.estimated_output_tokens)],
    ["Actual tokens", actualTokenText(today)],
    ["Points spent", formatNumber(today.points_spent)],
  ]);

  renderFacts(usageThirtyFacts, [
    ["Requests", formatNumber(thirty.requests)],
    ["Success", formatNumber(thirty.successes)],
    ["Errors", formatNumber(thirty.errors)],
    ["Blocked", formatNumber(thirty.blocked)],
    ["Est. input", formatNumber(thirty.estimated_input_tokens)],
    ["Est. output", formatNumber(thirty.estimated_output_tokens)],
    ["Actual tokens", actualTokenText(thirty)],
    ["Points spent", formatNumber(thirty.points_spent)],
  ]);

  renderUsageList(usage.items || []);
}

function actualTokenText(totals = {}) {
  const value = Number(totals.actual_input_tokens || 0) + Number(totals.actual_output_tokens || 0);
  return value > 0 ? formatNumber(value) : "Estimate only";
}

function renderUsageUsers(items = []) {
  if (!usageUsersList) return;
  if (!items.length) {
    usageUsersList.innerHTML = `<div class="admin-empty">No usage data yet.</div>`;
    return;
  }

  usageUsersList.innerHTML = items.map((item) => `
    <button class="admin-list-row three" type="button" data-user-uid="${escapeHtml(item.uid)}">
      <span>
        <strong>${escapeHtml(item.email || item.name || "Unknown user")}</strong>
        <small>${escapeHtml(item.uid)}</small>
      </span>
      <span>
        <strong>${formatNumber(item.requests_today)} today</strong>
        <small>${formatNumber(item.requests_30d)} in 30d / ${formatNumber(item.errors_today)} errors</small>
      </span>
      <span>
        <strong>${formatNumber(item.estimated_tokens_today)} est. tokens</strong>
        <small>${formatNumber(item.points_spent_today)} points today</small>
      </span>
    </button>
  `).join("");
}

function renderUsageList(items = []) {
  if (!usageList) return;
  if (!items.length) {
    usageList.innerHTML = `<div class="admin-empty">No AI usage events yet.</div>`;
    return;
  }

  usageList.innerHTML = items.map((item) => usageRow(item)).join("");
}

function usageRow(item = {}) {
  const statusClass = item.status === "success" ? "ok" : item.status === "blocked" ? "warn" : "danger";
  const estimatedTokens = Number(item.estimated_input_tokens || 0) + Number(item.estimated_output_tokens || 0);
  const actualTokens = Number(item.actual_input_tokens || 0) + Number(item.actual_output_tokens || 0);

  return `
    <div class="admin-list-row three static">
      <span>
        <strong>${escapeHtml(item.action || "unknown")}</strong>
        <small>${escapeHtml(item.operation || "-")} / ${escapeHtml(item.provider || "-")}</small>
      </span>
      <span>
        <strong class="admin-status-pill ${statusClass}">${escapeHtml(item.status || "-")}</strong>
        <small>${escapeHtml(item.error_kind || "no error")}</small>
      </span>
      <span>
        <strong>${formatNumber(estimatedTokens)} est. tokens</strong>
        <small>${actualTokens ? `${formatNumber(actualTokens)} actual` : "estimate only"} / ${formatNumber(Math.abs(item.points_delta || 0))} pts</small>
      </span>
      <p>${escapeHtml(item.uid || "-")} ${item.session_id ? `- ${escapeHtml(item.session_id)}` : ""} - ${formatDate(item.created_at)} - ${formatNumber(item.latency_ms)}ms</p>
    </div>
  `;
}

function renderUsers(users = []) {
  if (!usersList) return;
  if (!users.length) {
    usersList.innerHTML = `<div class="admin-empty">No known users yet.</div>`;
    return;
  }

  usersList.innerHTML = users.map((user) => {
    const status = user.is_banned ? "Banned" : "Active";
    return `
      <button class="admin-list-row three" type="button" data-user-uid="${escapeHtml(user.uid)}">
        <span>
          <strong>${escapeHtml(user.email || user.name || "Unknown user")}</strong>
          <small>${escapeHtml(user.uid)}</small>
        </span>
        <span>
          <strong>${formatNumber(user.points_balance)} pts / ${escapeHtml(status)}</strong>
          <small>${formatNumber(user.saved_sessions)} saved / ${formatNumber(user.draft_sessions)} draft</small>
        </span>
        <span>
          <strong>${formatNumber(user.usage_today)} usage today</strong>
          <small>${formatNumber(user.estimated_tokens_today)} est. tokens / last seen ${formatDate(user.last_seen_at)}</small>
        </span>
      </button>
    `;
  }).join("");
}

function renderSessions(sessions = []) {
  if (!sessionsList) return;
  if (!sessions.length) {
    sessionsList.innerHTML = `<div class="admin-empty">No sessions found.</div>`;
    return;
  }

  sessionsList.innerHTML = sessions.map((session) => {
    const saveState = session.is_saved ? "Saved" : "Draft";
    return `
      <div class="admin-list-row three static">
        <span>
          <strong>${escapeHtml(session.title || "Untitled")}</strong>
          <small>${escapeHtml(session.session_id)}</small>
        </span>
        <span>
          <strong>${escapeHtml(session.mode || "unknown")} / ${saveState}</strong>
          <small>${formatNumber(session.target_words)} target words</small>
        </span>
        <span>
          <strong>${escapeHtml(session.summary_source || "preview")}</strong>
          <small>${formatDate(session.updated_at)}</small>
        </span>
        <p>${escapeHtml(session.preview || "No preview available.")}</p>
      </div>
    `;
  }).join("");
}

function renderErrors(items = []) {
  const targets = [recentErrorsList].filter(Boolean);
  targets.forEach((target) => {
    if (!items.length) {
      target.innerHTML = `<div class="admin-empty">No recent AI errors.</div>`;
      return;
    }
    target.innerHTML = items.slice(0, 8).map((item) => usageRow(item)).join("");
  });
}

function renderAudit(items = []) {
  const text = items.length
    ? items.map((item) => {
        const target = item.target_uid ? ` -> ${item.target_uid}` : "";
        return `[${item.created_at}] ${item.actor_email || item.actor_uid}: ${item.action}${target}`;
      }).join("\n")
    : "No audit log entries yet.";

  if (auditOutput) auditOutput.textContent = text;
  if (auditPreview) auditPreview.textContent = text;
}

function renderFacts(container, facts = []) {
  if (!container) return;
  container.innerHTML = facts.map(([label, value]) => `
    <div class="admin-kv-item">
      <span>${escapeHtml(label)}</span>
      <strong>${escapeHtml(value ?? "-")}</strong>
    </div>
  `).join("");
}

async function saveSettings() {
  const oldSettings = currentOverview?.settings || {};
  const newMaintenance = Boolean(maintenanceToggle?.checked);
  const newPoints = Boolean(pointsToggle?.checked);
  const newRateLimit = Boolean(rateLimitToggle?.checked);

  if (newMaintenance && !oldSettings.maintenance_enabled) {
    const confirmed = window.confirm("Turn on maintenance mode for normal players?");
    if (!confirmed) return;
  }

  if (newPoints !== Boolean(oldSettings.points_enabled)) {
    const confirmed = window.confirm("Change point spending mode?");
    if (!confirmed) return;
  }

  if (newRateLimit !== Boolean(oldSettings.rate_limit_enabled)) {
    const confirmed = window.confirm("Change daily rate limit mode?");
    if (!confirmed) return;
  }

  setBusy(true);
  setStatus("Saving settings...", "muted");

  try {
    await requestJson(`${API_BASE}/admin/settings`, {
      method: "PATCH",
      body: JSON.stringify({
        maintenance_enabled: newMaintenance,
        maintenance_message:
          maintenanceMessage?.value?.trim() ||
          "AI Story Adventure is under maintenance. Please come back soon.",
        points_enabled: newPoints,
        cost_start_adventure: numberValue(costAdventure, 10),
        cost_novel_world: numberValue(costNovelWorld, 5),
        cost_novel_foundation: numberValue(costNovelFoundation, 15),
        cost_turn: numberValue(costTurn, 3),
        rate_limit_enabled: newRateLimit,
        daily_turn_limit: numberValue(dailyTurnLimit, 20),
        daily_create_limit: numberValue(dailyCreateLimit, 5),
        usage_log_retention_days: Math.max(1, numberValue(usageRetentionDays, 30)),
      }),
    });
    await loadDashboard();
  } catch (err) {
    setStatus(err.message || "Could not save settings.", "error");
  } finally {
    setBusy(false);
  }
}

async function adjustPoints() {
  const uid = targetUidInput?.value?.trim() || "";
  const delta = Number(pointDeltaInput?.value);
  const reason = pointReasonInput?.value?.trim() || "Manual admin adjustment";

  if (!uid || !Number.isFinite(delta) || delta === 0) {
    setStatus("Enter a target UID and a non-zero point delta.", "error");
    return;
  }

  const confirmed = window.confirm(`${delta > 0 ? "Grant" : "Deduct"} ${Math.abs(delta)} points for this user?`);
  if (!confirmed) return;

  setBusy(true);
  setStatus("Applying point change...", "muted");

  try {
    await requestJson(`${API_BASE}/admin/users/${encodeURIComponent(uid)}/points`, {
      method: "POST",
      body: JSON.stringify({ delta: Math.trunc(delta), reason }),
    });
    await loadDashboard();
  } catch (err) {
    setStatus(err.message || "Could not adjust points.", "error");
  } finally {
    setBusy(false);
  }
}

async function setBanState(shouldBan) {
  const uid = targetUidInput?.value?.trim() || "";
  if (!uid) {
    setStatus("Enter a target UID first.", "error");
    return;
  }

  const confirmed = window.confirm(shouldBan ? "Ban this account?" : "Unban this account?");
  if (!confirmed) return;

  setBusy(true);
  setStatus(shouldBan ? "Banning user..." : "Unbanning user...", "muted");

  try {
    const endpoint = shouldBan ? "ban" : "unban";
    const options = shouldBan
      ? {
          method: "POST",
          body: JSON.stringify({ reason: banReasonInput?.value?.trim() || "" }),
        }
      : { method: "POST" };

    await requestJson(`${API_BASE}/admin/users/${encodeURIComponent(uid)}/${endpoint}`, options);
    await loadDashboard();
  } catch (err) {
    setStatus(err.message || "Could not update ban state.", "error");
  } finally {
    setBusy(false);
  }
}

function switchTab(name) {
  document.querySelectorAll("[data-admin-tab]").forEach((button) => {
    button.classList.toggle("active", button.dataset.adminTab === name);
  });
  document.querySelectorAll("[data-admin-panel]").forEach((panel) => {
    panel.classList.toggle("active", panel.dataset.adminPanel === name);
  });
}

function selectTargetUid(uid) {
  if (!uid || !targetUidInput) return;
  targetUidInput.value = uid;
  setStatus("Target UID selected.", "ok");
  switchTab("users");
}

function numberValue(input, fallback) {
  const value = Number(input?.value);
  return Number.isFinite(value) ? Math.max(0, Math.floor(value)) : fallback;
}

function setText(node, value) {
  if (node) node.textContent = value ?? "-";
}

function formatNumber(value) {
  const number = Number(value || 0);
  return Number.isFinite(number) ? number.toLocaleString() : "-";
}

function formatDate(value) {
  if (!value) return "Unknown";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return value;
  return date.toLocaleString();
}

function escapeHtml(value) {
  return String(value ?? "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}

googleLoginBtn?.addEventListener("click", async () => {
  setBusy(true);
  setLoginStatus("Opening Firebase login...", "muted");

  try {
    await signInWithPopup(auth, provider);
  } catch (err) {
    setLoginStatus(err.message || "Google login failed.", "error");
  } finally {
    setBusy(false);
  }
});

emailLoginBtn?.addEventListener("click", async () => {
  const email = emailInput?.value?.trim() || "";
  const password = passwordInput?.value || "";

  if (!email || !password) {
    setLoginStatus("Enter email and password.", "error");
    return;
  }

  setBusy(true);
  setLoginStatus("Signing in...", "muted");

  try {
    await signInWithEmailAndPassword(auth, email, password);
  } catch (err) {
    setLoginStatus(err.message || "Email login failed.", "error");
  } finally {
    setBusy(false);
  }
});

retryAccessBtn?.addEventListener("click", () => {
  checkAdminAccess();
});

deniedLogoutBtn?.addEventListener("click", () => {
  signOut(auth);
});

logoutBtn?.addEventListener("click", () => {
  signOut(auth);
});

refreshBtn?.addEventListener("click", () => {
  loadDashboard();
});

saveSettingsBtn?.addEventListener("click", () => {
  saveSettings();
});

adjustPointsBtn?.addEventListener("click", () => {
  adjustPoints();
});

banUserBtn?.addEventListener("click", () => {
  setBanState(true);
});

unbanUserBtn?.addEventListener("click", () => {
  setBanState(false);
});

document.querySelectorAll("[data-admin-tab]").forEach((button) => {
  button.addEventListener("click", () => switchTab(button.dataset.adminTab));
});

[usersList, usageUsersList].forEach((list) => {
  list?.addEventListener("click", (event) => {
    const row = event.target.closest("[data-user-uid]");
    if (!row) return;
    selectTargetUid(row.dataset.userUid || "");
  });
});

onAuthStateChanged(auth, async (user) => {
  setLoginStatus("", "muted");

  if (!user) {
    isAdmin = false;
    showOnly(loginView);
    return;
  }

  showOnly(deniedView);
  await checkAdminAccess();
});


/* =========================================================================
   COMMUNITY MODERATION TABS LOGIC
   ========================================================================= */

const submissionsList = $("adminSubmissionsList");

function renderSubmissions(items = []) {
  if (!submissionsList) return;
  if (!items.length) {
    submissionsList.innerHTML = `<div class="admin-empty">No pending submissions.</div>`;
    return;
  }

  submissionsList.innerHTML = items.map((item) => `
    <div class="submission-card glass-panel" data-sub-id="${escapeHtml(item.id)}">
      <div>
        <h3>${escapeHtml(item.title || "Untitled")}</h3>
        <p class="admin-muted" style="margin-bottom:10px;">${escapeHtml(item.description || "No description")}</p>
        <div class="submission-meta">
          <span>By: <strong>${escapeHtml(item.author_name)}</strong></span> |
          <span>Mode: <strong>${escapeHtml(item.mode)}</strong></span> |
          <span>Tags: <strong>${escapeHtml(item.tags?.join(", ") || "None")}</strong></span> |
          <span>Date: <strong>${formatDate(item.created_at)}</strong></span>
        </div>
      </div>
      <div class="submission-actions" style="margin-top:15px; display:flex; gap:10px;">
        <button class="primary-btn approve-btn" type="button">Approve</button>
        <button class="danger-btn reject-btn" type="button">Reject</button>
      </div>
    </div>
  `).join("");

  submissionsList.querySelectorAll(".submission-card").forEach((card) => {
    const subId = card.dataset.subId;
    card.querySelector(".approve-btn")?.addEventListener("click", async () => {
      await moderateSubmission(subId, "approve");
    });
    card.querySelector(".reject-btn")?.addEventListener("click", async () => {
      await moderateSubmission(subId, "reject");
    });
  });
}

async function moderateSubmission(subId, action) {
  const confirmed = window.confirm(`Are you sure you want to ${action} this submission?`);
  if (!confirmed) return;

  setBusy(true);
  setStatus(`${action === "approve" ? "Approving" : "Rejecting"} submission...`, "muted");

  try {
    await requestJson(`${API_BASE}/admin/submissions/${encodeURIComponent(subId)}/${action}`, {
      method: "POST"
    });
    await loadDashboard();
  } catch (err) {
    setStatus(err.message || `Could not ${action} submission.`, "error");
  } finally {
    setBusy(false);
  }
}

