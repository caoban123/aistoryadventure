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
const costToday = $("adminCostToday");
const costThirty = $("adminCostThirty");
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
  if (!user) throw new Error("Yêu cầu đăng nhập tài khoản quản trị.");

  let token = await user.getIdToken(true);
  const headers = {
    "Content-Type": "application/json",
    ...(options.headers || {}),
    Authorization: `Bearer ${token}`,
  };

  let response;
  let retries = 1;

  while (true) {
    try {
      response = await fetch(url, { ...options, headers });
    } catch (err) {
      throw new Error(err?.message || "Không thể gửi yêu cầu mạng.");
    }

    const contentType = response.headers.get("content-type") || "";
    const data = contentType.includes("application/json")
      ? await response.json().catch(() => null)
      : await response.text().catch(() => "");

    if (!response.ok) {
      const errMsg = getApiErrorMessage(data, response.status);
      if (retries > 0 && errMsg && errMsg.includes("Token used too early")) {
        console.warn("Token used too early (clock skew). Retrying in 2s...");
        await new Promise(resolve => setTimeout(resolve, 2000));
        if (auth.currentUser) {
          const newToken = await auth.currentUser.getIdToken(true);
          headers.Authorization = `Bearer ${newToken}`;
        }
        retries--;
        continue;
      }
      throw new Error(errMsg);
    }

    return data;
  }
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
  return `Yêu cầu thất bại (Mã lỗi: ${status})`;
}

async function checkAdminAccess() {
  try {
    const data = await requestJson(`${API_BASE}/admin/me`);
    isAdmin = data?.admin === true;

    if (!isAdmin) {
      showDenied("Hệ thống backend không xác thực được quyền Admin của tài khoản này.");
      return false;
    }

    if (identityText) {
      identityText.textContent = data.email || data.name || data.uid || "Quản trị viên";
    }

    showOnly(dashboardView);
    await loadDashboard();
    return true;
  } catch (err) {
    showDenied(err.message || "Không thể xác nhận quyền truy cập Admin.");
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
  setStatus("Đang tải dữ liệu quản trị...", "muted");

  const safeRequest = (promise, fallback) => promise.catch(err => {
    console.warn("Yêu cầu tới endpoint không bắt buộc thất bại:", err);
    return fallback;
  });

  try {
    const [overview, users, sessions, audit, usage, usageUsers, errors, submissions, announcements] = await Promise.all([
      requestJson(`${API_BASE}/admin/overview`),
      safeRequest(requestJson(`${API_BASE}/admin/users?limit=100`), { items: [] }),
      safeRequest(requestJson(`${API_BASE}/admin/sessions?limit=40`), { items: [] }),
      safeRequest(requestJson(`${API_BASE}/admin/audit?limit=60`), { items: [] }),
      safeRequest(requestJson(`${API_BASE}/admin/usage?limit=80`), { today: {}, last_30d: {}, items: [] }),
      safeRequest(requestJson(`${API_BASE}/admin/usage/users?limit=100`), { items: [] }),
      safeRequest(requestJson(`${API_BASE}/admin/errors?limit=50`), { items: [] }),
      safeRequest(requestJson(`${API_BASE}/admin/submissions`), []),
      safeRequest(requestJson(`${API_BASE}/admin/announcements`), []),
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
    renderAnnouncements(announcements || []);
    setStatus("Dữ liệu hệ thống đã được đồng bộ trực tiếp.", "ok");
  } catch (err) {
    setStatus(err.message || "Không thể tải dữ liệu quản trị.", "error");
  } finally {
    setBusy(false);
  }
}

/* Logic quy đổi Token sang chi phí API */
function estimateCost(inputTokens, outputTokens, provider, model) {
  const p = (provider || "google").toLowerCase();
  const m = (model || "gemini-1.5-flash").toLowerCase();

  // Giá mặc định: Gemini 1.5 Flash ($0.075 / 1M input, $0.30 / 1M output)
  let inputRate = 0.075;
  let outputRate = 0.30;

  if (p.includes("openai") || m.includes("gpt")) {
    if (m.includes("gpt-4o-mini")) {
      inputRate = 0.15;
      outputRate = 0.60;
    } else if (m.includes("gpt-4")) {
      inputRate = 2.50;
      outputRate = 10.00;
    }
  } else if (p.includes("google") || p.includes("gemini")) {
    if (m.includes("pro")) {
      inputRate = 1.25;
      outputRate = 5.00;
    } else {
      inputRate = 0.075;
      outputRate = 0.30;
    }
  } else if (p.includes("mock")) {
    inputRate = 0.0;
    outputRate = 0.0;
  }

  const costUsd = (inputTokens * inputRate / 1000000) + (outputTokens * outputRate / 1000000);
  const costVnd = costUsd * 25400; // Tỷ giá quy đổi mặc định sang VND
  return { usd: costUsd, vnd: costVnd };
}

function formatCost(costObj) {
  const usdStr = costObj.usd.toLocaleString("en-US", { minimumFractionDigits: 4, maximumFractionDigits: 4 });
  const vndStr = Math.round(costObj.vnd).toLocaleString("vi-VN");
  return `$${usdStr} (~ ${vndStr} ₫)`;
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
  setText(rateLimitState, settings.rate_limit_enabled ? "Bật" : "Tắt");

  // Quy đổi chi phí cho Today và 30 ngày qua
  const todayUsage = currentUsage?.today || {};
  const thirtyUsage = currentUsage?.last_30d || {};
  const provider = overview.text_provider;
  const model = overview.text_model;

  const inToday = todayUsage.actual_input_tokens || todayUsage.estimated_input_tokens || 0;
  const outToday = todayUsage.actual_output_tokens || todayUsage.estimated_output_tokens || 0;
  const costTodayVal = estimateCost(inToday, outToday, provider, model);
  setText(costToday, formatCost(costTodayVal));

  const inThirty = thirtyUsage.actual_input_tokens || thirtyUsage.estimated_input_tokens || 0;
  const outThirty = thirtyUsage.actual_output_tokens || thirtyUsage.estimated_output_tokens || 0;
  const costThirtyVal = estimateCost(inThirty, outThirty, provider, model);
  setText(costThirty, formatCost(costThirtyVal));

  renderFacts(systemFacts, [
    ["Môi trường", overview.app_env || "local"],
    ["Nhà cung cấp", `${overview.text_provider || "-"} / ${overview.text_model || "-"}`],
    ["Khóa API", overview.text_provider === "mock" ? "Sử dụng mô phỏng (Mock)" : "Cấu hình phía máy chủ"],
    ["Mô hình nhúng", overview.embedding_provider || "-"],
    ["Cơ chế lưu trữ", overview.storage_mode || "-"],
    ["Thư viện thế giới", `${formatNumber(overview.catalog_count)} thế giới`],
    ["Cập nhật mới nhất", formatDate(overview.latest_updated_at)],
  ]);

  renderFacts(usageFacts, [
    ["Hôm nay", `${formatNumber(overview.usage_today)} yêu cầu`],
    ["Sự cố hôm nay", `${formatNumber(overview.usage_errors_today)} lỗi`],
    ["Token hôm nay", `${formatNumber(overview.estimated_tokens_today)} tokens`],
    ["Token 30 ngày", formatNumber(overview.estimated_tokens_30d)],
    ["Chi phí hôm nay", formatCost(costTodayVal)],
    ["Giới hạn tần suất", settings.rate_limit_enabled ? `${settings.daily_turn_limit} lượt/ngày` : "Vô hiệu hóa"],
  ]);

  renderReadiness(overview.readiness || {});
}

function renderReadiness(readiness = {}) {
  if (!readinessSummary || !readinessList) return;

  const status = readiness.overall_status || "unknown";
  const statusClass = status === "ok" ? "ok" : status === "warning" ? "warn" : "danger";
  const statusVi = status === "ok" ? "Hoạt động" : status === "warning" ? "Cảnh báo" : "Lỗi";
  const checks = Array.isArray(readiness.checks) ? readiness.checks : [];
  const errors = checks.filter((item) => item.status === "error").length;
  const warnings = checks.filter((item) => item.status === "warning").length;
  const readyText = readiness.production_ready ? "Sẵn sàng chạy Production" : "Chưa đủ điều kiện Production";

  readinessSummary.innerHTML = `
    <span class="admin-status-pill ${statusClass}">${escapeHtml(statusVi)}</span>
    <strong>${escapeHtml(readyText)}</strong>
    <small>${formatNumber(errors)} lỗi / ${formatNumber(warnings)} cảnh báo</small>
  `;

  if (!checks.length) {
    readinessList.innerHTML = `<div class="admin-empty">Không có nhật ký kiểm tra trạng thái nào.</div>`;
    return;
  }

  readinessList.innerHTML = checks.map((item) => {
    const itemClass = item.status === "ok" ? "ok" : item.status === "warning" ? "warn" : "danger";
    const checkStatusVi = item.status === "ok" ? "Đạt" : item.status === "warning" ? "Cảnh báo" : "Lỗi";
    return `
      <div class="admin-check-row ${itemClass}">
        <span class="admin-status-pill ${itemClass}">${escapeHtml(checkStatusVi)}</span>
        <div>
          <strong>${escapeHtml(item.label || item.check_id || "Kiểm tra")}</strong>
          <p>${escapeHtml(item.message || "")}</p>
          ${item.hint ? `<small>Gợi ý: ${escapeHtml(item.hint)}</small>` : ""}
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
      "Hệ thống AI Story Adventure đang được bảo trì. Vui lòng quay lại sau.";
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
    ["Tổng yêu cầu", formatNumber(today.requests)],
    ["Thành công", formatNumber(today.successes)],
    ["Thất bại (Lỗi)", formatNumber(today.errors)],
    ["Bị chặn giới hạn", formatNumber(today.blocked)],
    ["Token đầu vào (Input)", formatNumber(today.estimated_input_tokens)],
    ["Token đầu ra (Output)", formatNumber(today.estimated_output_tokens)],
    ["Tổng token tiêu hao", actualTokenText(today)],
    ["Chi phí ước tính", formatCost(estimateCost(today.estimated_input_tokens, today.estimated_output_tokens, currentOverview?.text_provider, currentOverview?.text_model))],
  ]);

  renderFacts(usageThirtyFacts, [
    ["Tổng yêu cầu", formatNumber(thirty.requests)],
    ["Thành công", formatNumber(thirty.successes)],
    ["Thất bại (Lỗi)", formatNumber(thirty.errors)],
    ["Bị chặn giới hạn", formatNumber(thirty.blocked)],
    ["Token đầu vào (Input)", formatNumber(thirty.estimated_input_tokens)],
    ["Token đầu ra (Output)", formatNumber(thirty.estimated_output_tokens)],
    ["Tổng token tiêu hao", actualTokenText(thirty)],
    ["Chi phí ước tính", formatCost(estimateCost(thirty.estimated_input_tokens, thirty.estimated_output_tokens, currentOverview?.text_provider, currentOverview?.text_model))],
  ]);

  renderUsageList(usage.items || []);
}

function actualTokenText(totals = {}) {
  const value = Number(totals.actual_input_tokens || 0) + Number(totals.actual_output_tokens || 0);
  return value > 0 ? formatNumber(value) : "Dựa theo ước tính";
}

function renderUsageUsers(items = []) {
  if (!usageUsersList) return;
  if (!items.length) {
    usageUsersList.innerHTML = `<div class="admin-empty">Chưa có dữ liệu tiêu thụ.</div>`;
    return;
  }

  usageUsersList.innerHTML = items.map((item) => `
    <button class="admin-list-row static" type="button" data-user-uid="${escapeHtml(item.uid)}">
      <span>
        <strong>${escapeHtml(item.email || item.name || "Người chơi ẩn danh")}</strong>
        <small>${escapeHtml(item.uid)}</small>
      </span>
      <span>
        <strong>${formatNumber(item.requests_today)} lượt hôm nay</strong>
        <small>${formatNumber(item.requests_30d)} lượt / 30 ngày</small>
      </span>
      <span>
        <strong>${formatNumber(item.estimated_tokens_today)} tokens</strong>
        <small>Chi phí ngày: ${formatCost(estimateCost(item.estimated_tokens_today * 0.7, item.estimated_tokens_today * 0.3, currentOverview?.text_provider, currentOverview?.text_model))}</small>
      </span>
    </button>
  `).join("");
}

function renderUsageList(items = []) {
  if (!usageList) return;
  if (!items.length) {
    usageList.innerHTML = `<div class="admin-empty">Chưa có nhật ký API nào được tạo.</div>`;
    return;
  }

  usageList.innerHTML = items.map((item) => usageRow(item)).join("");
}

function usageRow(item = {}) {
  const statusClass = item.status === "success" ? "ok" : item.status === "blocked" ? "warn" : "danger";
  const statusVi = item.status === "success" ? "Thành công" : item.status === "blocked" ? "Bị chặn" : "Lỗi";
  const estimatedTokens = Number(item.estimated_input_tokens || 0) + Number(item.estimated_output_tokens || 0);
  const actualTokens = Number(item.actual_input_tokens || 0) + Number(item.actual_output_tokens || 0);

  const calculatedCost = estimateCost(item.estimated_input_tokens, item.estimated_output_tokens, item.provider, item.model);

  return `
    <div class="admin-list-row static">
      <span>
        <strong>Tác vụ: ${escapeHtml(item.action || "Không rõ")}</strong>
        <small>Provider: ${escapeHtml(item.provider || "-")} (${escapeHtml(item.model || "-")})</small>
      </span>
      <span>
        <strong class="admin-status-pill ${statusClass}">${escapeHtml(statusVi)}</strong>
        <small>Lỗi: ${escapeHtml(item.error_kind || "Không có")}</small>
      </span>
      <span>
        <strong>${formatNumber(estimatedTokens)} tokens</strong>
        <small>Chi phí: ${formatCost(calculatedCost)} / -${formatNumber(Math.abs(item.points_delta || 0))} điểm</small>
      </span>
      <p>ID: ${escapeHtml(item.uid || "-")} ${item.session_id ? `| Phiên: ${escapeHtml(item.session_id)}` : ""} | Thời gian: ${formatDate(item.created_at)} | Độ trễ: ${formatNumber(item.latency_ms)}ms</p>
    </div>
  `;
}

function renderUsers(users = []) {
  if (!usersList) return;
  if (!users.length) {
    usersList.innerHTML = `<div class="admin-empty">Không tìm thấy người chơi nào.</div>`;
    return;
  }

  usersList.innerHTML = users.map((user) => {
    const status = user.is_banned ? "Đã cấm" : "Hoạt động";
    const statusClass = user.is_banned ? "danger" : "ok";
    return `
      <button class="admin-list-row" type="button" data-user-uid="${escapeHtml(user.uid)}">
        <span>
          <strong>${escapeHtml(user.email || user.name || "Người chơi ẩn danh")}</strong>
          <small>${escapeHtml(user.uid)}</small>
        </span>
        <span>
          <strong class="admin-status-pill ${statusClass}">${status} | ${formatNumber(user.points_balance)} điểm</strong>
          <small>Phiên chơi: ${formatNumber(user.saved_sessions)} đã lưu / ${formatNumber(user.draft_sessions)} nháp</small>
        </span>
        <span>
          <strong>${formatNumber(user.usage_today)} lượt dùng hôm nay</strong>
          <small>Hoạt động cuối: ${formatDate(user.last_seen_at)}</small>
        </span>
      </button>
    `;
  }).join("");
}

function renderSessions(sessions = []) {
  if (!sessionsList) return;
  if (!sessions.length) {
    sessionsList.innerHTML = `<div class="admin-empty">Không có phiên chơi nào hoạt động.</div>`;
    return;
  }

  sessionsList.innerHTML = sessions.map((session) => {
    const saveState = session.is_saved ? "Đã lưu" : "Nháp";
    const modeVi = session.mode === "adventure" ? "Nhập Vai (Adventure)" : "Tiểu Thuyết (Novel)";
    return `
      <div class="admin-list-row static">
        <span>
          <strong>Tiêu đề: ${escapeHtml(session.title || "Chưa đặt tên")}</strong>
          <small>Mã phiên: ${escapeHtml(session.session_id)}</small>
        </span>
        <span>
          <strong>Chế độ: ${modeVi} | Trạng thái: ${saveState}</strong>
          <small>Độ dài tối thiểu: ${formatNumber(session.target_words)} từ</small>
        </span>
        <span>
          <strong>Nguồn tóm tắt: ${escapeHtml(session.summary_source || "preview")}</strong>
          <small>Cập nhật lúc: ${formatDate(session.updated_at)}</small>
        </span>
        <p>Bản xem trước nội dung: ${escapeHtml(session.preview || "Không có bản xem trước nào.")}</p>
      </div>
    `;
  }).join("");
}

function renderErrors(items = []) {
  const targets = [recentErrorsList].filter(Boolean);
  targets.forEach((target) => {
    if (!items.length) {
      target.innerHTML = `<div class="admin-empty">Không ghi nhận lỗi hệ thống nào gần đây.</div>`;
      return;
    }
    target.innerHTML = items.slice(0, 8).map((item) => usageRow(item)).join("");
  });
}

function renderAudit(items = []) {
  const text = items.length
    ? items.map((item) => {
        const target = item.target_uid ? ` -> đối tượng: ${item.target_uid}` : "";
        return `[${formatDate(item.created_at)}] Admin ${item.actor_email || item.actor_uid}: ${item.action}${target}`;
      }).join("\n")
    : "Chưa ghi nhận nhật ký tác vụ admin nào.";

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
    const confirmed = window.confirm("Bạn có chắc chắn muốn BẬT chế độ bảo trì toàn hệ thống không? Người chơi bình thường sẽ không thể trải nghiệm game.");
    if (!confirmed) return;
  }

  if (newPoints !== Boolean(oldSettings.points_enabled)) {
    const confirmed = window.confirm("Bạn có chắc chắn muốn thay đổi trạng thái tiêu hao điểm số không?");
    if (!confirmed) return;
  }

  if (newRateLimit !== Boolean(oldSettings.rate_limit_enabled)) {
    const confirmed = window.confirm("Bạn có chắc chắn muốn thay đổi giới hạn tần suất API hàng ngày không?");
    if (!confirmed) return;
  }

  setBusy(true);
  setStatus("Đang lưu cấu hình hệ thống...", "muted");

  try {
    await requestJson(`${API_BASE}/admin/settings`, {
      method: "PATCH",
      body: JSON.stringify({
        maintenance_enabled: newMaintenance,
        maintenance_message:
          maintenanceMessage?.value?.trim() ||
          "Hệ thống AI Story Adventure đang được bảo trì. Vui lòng quay lại sau.",
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
    setStatus(err.message || "Không thể lưu cấu hình hệ thống.", "error");
  } finally {
    setBusy(false);
  }
}

async function adjustPoints() {
  const uid = targetUidInput?.value?.trim() || "";
  const delta = Number(pointDeltaInput?.value);
  const reason = pointReasonInput?.value?.trim() || "Thay đổi điểm thủ công bởi Admin";

  if (!uid || !Number.isFinite(delta) || delta === 0) {
    setStatus("Vui lòng nhập UID người chơi và số điểm muốn thay đổi (khác 0).", "error");
    return;
  }

  const confirmed = window.confirm(`Bạn có chắc chắn muốn ${delta > 0 ? "cộng" : "trừ"} ${Math.abs(delta)} điểm đối với người chơi này không?`);
  if (!confirmed) return;

  setBusy(true);
  setStatus("Đang thực hiện cộng/trừ điểm...", "muted");

  try {
    await requestJson(`${API_BASE}/admin/users/${encodeURIComponent(uid)}/points`, {
      method: "POST",
      body: JSON.stringify({ delta: Math.trunc(delta), reason }),
    });
    await loadDashboard();
  } catch (err) {
    setStatus(err.message || "Không thể điều chỉnh điểm người chơi.", "error");
  } finally {
    setBusy(false);
  }
}

async function setBanState(shouldBan) {
  const uid = targetUidInput?.value?.trim() || "";
  if (!uid) {
    setStatus("Vui lòng điền UID người chơi mục tiêu.", "error");
    return;
  }

  const confirmed = window.confirm(shouldBan ? "Bạn có chắc chắn muốn CẤM người chơi này không?" : "Bạn có chắc chắn muốn MỞ KHÓA cho người chơi này không?");
  if (!confirmed) return;

  setBusy(true);
  setStatus(shouldBan ? "Đang tiến hành cấm người chơi..." : "Đang tiến hành mở khóa...", "muted");

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
    setStatus(err.message || "Không thể cập nhật trạng thái hoạt động.", "error");
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
  setStatus("Đã chọn UID người chơi mục tiêu.", "ok");
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
  if (!value) return "Không rõ";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return value;
  return date.toLocaleString("vi-VN");
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
  setLoginStatus("Đang mở trang đăng nhập Google...", "muted");

  try {
    await signInWithPopup(auth, provider);
  } catch (err) {
    setLoginStatus(err.message || "Đăng nhập Google thất bại.", "error");
  } finally {
    setBusy(false);
  }
});

emailLoginBtn?.addEventListener("click", async () => {
  const email = emailInput?.value?.trim() || "";
  const password = passwordInput?.value || "";

  if (!email || !password) {
    setLoginStatus("Vui lòng nhập đầy đủ Email và Mật khẩu.", "error");
    return;
  }

  setBusy(true);
  setLoginStatus("Đang đăng nhập hệ thống...", "muted");

  try {
    await signInWithEmailAndPassword(auth, email, password);
  } catch (err) {
    setLoginStatus(err.message || "Đăng nhập thất bại. Kiểm tra lại thông tin.", "error");
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
    submissionsList.innerHTML = `<div class="admin-empty">Không có thế giới nào đang chờ duyệt.</div>`;
    return;
  }

  submissionsList.innerHTML = items.map((item) => `
    <div class="submission-card" data-sub-id="${escapeHtml(item.id)}">
      <div>
        <h3>${escapeHtml(item.title || "Chưa đặt tên")}</h3>
        <p class="admin-muted" style="margin-bottom:10px;">${escapeHtml(item.description || "Không có mô tả")}</p>
        <div class="submission-meta">
          <span>Người tạo: <strong>${escapeHtml(item.author_name)}</strong></span> |
          <span>Chế độ: <strong>${escapeHtml(item.mode)}</strong></span> |
          <span>Thẻ: <strong>${escapeHtml(item.tags?.join(", ") || "Không có")}</strong></span> |
          <span>Ngày gửi: <strong>${formatDate(item.created_at)}</strong></span>
        </div>
      </div>
      <div class="submission-actions" style="margin-top:15px; display:flex; gap:10px;">
        <button class="primary-btn approve-btn" type="button">Phê Duyệt</button>
        <button class="danger-btn reject-btn" type="button">Từ Chối</button>
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
  const actionVi = action === "approve" ? "phê duyệt" : "từ chối và xóa";
  const confirmed = window.confirm(`Bạn có chắc chắn muốn ${actionVi} thế giới cộng đồng này không?`);
  if (!confirmed) return;

  setBusy(true);
  setStatus(`Đang tiến hành ${action === "approve" ? "phê duyệt" : "từ chối"} bài đăng...`, "muted");

  try {
    await requestJson(`${API_BASE}/admin/submissions/${encodeURIComponent(subId)}/${action}`, {
      method: "POST"
    });
    await loadDashboard();
  } catch (err) {
    setStatus(err.message || `Không thể hoàn thành hành động ${actionVi}.`, "error");
  } finally {
    setBusy(false);
  }
}

/* =========================================================================
   ANNOUNCEMENT SYSTEM LOGIC
   ========================================================================= */

const announcementsList = $("adminAnnouncementsList");
const announcementForm = $("announcementForm");

function renderAnnouncements(items = []) {
  if (!announcementsList) return;
  if (!items.length) {
    announcementsList.innerHTML = `<div class="admin-empty">Không có thông báo nào được đăng.</div>`;
    return;
  }

  announcementsList.innerHTML = items.map((item) => `
    <div class="admin-item" data-announcement-id="${escapeHtml(item.id)}" style="display:flex; justify-content:space-between; align-items:center; padding:12px; margin-bottom:8px; border:1px solid #444; border-radius:4px; background:#222;">
      <div style="flex:1; margin-right:15px;">
        <div style="display:flex; align-items:center; gap:8px;">
          <strong style="color:#fff;">${escapeHtml(item.title)}</strong>
          <span style="font-size:0.75rem; padding:2px 6px; border-radius:3px; font-weight:bold; background:${item.type === 'fixed' ? 'rgba(255,215,0,0.15)' : 'rgba(255,255,255,0.08)'}; color:${item.type === 'fixed' ? '#ffd700' : '#bbb'}; border:1px solid ${item.type === 'fixed' ? 'rgba(255,215,0,0.3)' : 'rgba(255,255,255,0.15)'};">
            ${item.type === 'fixed' ? 'Cố định' : 'Hiện tại'}
          </span>
        </div>
        <p style="margin:6px 0 0 0; font-size:0.9rem; color:#aaa; line-height:1.4; word-break:break-word;">${escapeHtml(item.content)}</p>
        <div style="margin-top:6px; font-size:0.75rem; color:#666;">
          Đăng bởi: <strong>${escapeHtml(item.created_by)}</strong> | Ngày: <strong>${formatDate(item.created_at)}</strong>
        </div>
      </div>
      <button class="danger-btn delete-announcement-btn" type="button" style="padding:6px 12px; font-size:0.85rem;">Xóa</button>
    </div>
  `).join("");

  announcementsList.querySelectorAll(".delete-announcement-btn").forEach((btn) => {
    const parent = btn.closest("[data-announcement-id]");
    const announcementId = parent.dataset.announcementId;
    btn.addEventListener("click", async () => {
      if (confirm("Bạn có chắc chắn muốn xóa thông báo này?")) {
        setBusy(true);
        setStatus("Đang xóa thông báo...", "muted");
        try {
          await requestJson(`${API_BASE}/admin/announcements/${encodeURIComponent(announcementId)}`, {
            method: "DELETE",
          });
          await loadDashboard();
        } catch (err) {
          setStatus(err.message || "Không thể xóa thông báo.", "error");
        } finally {
          setBusy(false);
        }
      }
    });
  });
}

announcementForm?.addEventListener("submit", async (event) => {
  event.preventDefault();
  const title = $("announcementTitle")?.value?.trim() || "";
  const content = $("announcementContent")?.value?.trim() || "";
  const type = $("announcementType")?.value || "temporary";

  if (!title || !content) {
    alert("Vui lòng điền đầy đủ tiêu đề và nội dung.");
    return;
  }

  setBusy(true);
  setStatus("Đang phát sóng thông báo mới...", "muted");

  try {
    await requestJson(`${API_BASE}/admin/announcements`, {
      method: "POST",
      body: JSON.stringify({ title, content, type }),
    });
    
    // Clear form
    if ($("announcementTitle")) $("announcementTitle").value = "";
    if ($("announcementContent")) $("announcementContent").value = "";
    if ($("announcementType")) $("announcementType").value = "temporary";
    
    await loadDashboard();
    setStatus("Phát sóng thông báo thành công!", "ok");
  } catch (err) {
    setStatus(err.message || "Không thể phát sóng thông báo.", "error");
  } finally {
    setBusy(false);
  }
});
