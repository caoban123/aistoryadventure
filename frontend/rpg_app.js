/**
 * Chronicles of Destiny - RPG Mode Frontend Logic Orchestrator
 * Fully integrated with FastAPI Backend and Firebase Auth
 */

// Local state tracking
let currentSessionId = null;
let currentSessionIsSaved = false;
let gameState = null;
let selectedGender = "Male";
let swapSource = null; // Used for party swap click-to-select machine
let pendingAction = null; // Keeps track of action during target selection

// Global API Base
const getApiBase = () => window.API_BASE || "/api";

// ── UTILITIES & HELPER FUNCTIONS ────────────────────────────────────────────

function escapeHtml(text) {
  return String(text || "")
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#039;");
}

function formatRpgText(text) {
  let cleaned = String(text || "")
    .replace(/(?:^|[\r\n])\s*(?:>\s*)?(?:\*\*|<strong>|)?(?:Lựa chọn|Hành động|Quyết định|Choice|Action):\s*[^\r\n]*/gi, "")
    .trim();

  let html = escapeHtml(cleaned);
  // Support bold **text** -> <strong>text</strong>
  html = html.replace(/\*\*(.*?)\*\*/g, "<strong>$1</strong>");
  // Support italic *text* -> <em>$1</em>
  html = html.replace(/\*(.*?)\*/g, "<em>$1</em>");
  // Split into paragraphs
  return html
    .split(/\n\s*\n|\n/)
    .map(p => p.trim())
    .filter(Boolean)
    .map(p => `<p class="story-paragraph">${p}</p>`)
    .join("");
}

function getRaceEmoji(race, charName = "") {
  const bosses = ["medusa", "golem", "werewolf", "dracula", "vua goblin", "poseidon", "diablo", "thiên dực long vương", "ma vương xương cốt", "alpha"];
  if (race === "Bí ẩn" || race === "Mystery" || (charName && bosses.some(b => charName.toLowerCase().includes(b)))) {
    return "👿";
  }
  switch (race) {
    case "Valkyrie": return "⚔️";
    case "Angel": return "😇";
    case "Devil": return "😈";
    case "Elf": return "🧝";
    case "Royalty": return "👑";
    case "Orc": return "👹";
    case "Goblin": return "👺";
    case "Human": return "🧑";
    default: return "👤";
  }
}

function getClassEmoji(charClass) {
  switch (charClass) {
    case "Defender": return "🛡️";
    case "Guard": return "⚔️";
    case "Caster": return "🔮";
    case "Sniper": return "🏹";
    case "Supporter": return "💚";
    case "Specialist": return "✨";
    default: return "🌟";
  }
}

// Global RPG variables
let weatherEnabled = true;
let currentTextSpeed = 20; // 20ms per word by default

function getCubeRotation(rollValue) {
  switch (parseInt(rollValue)) {
    case 1: return "rotateX(0deg) rotateY(0deg)";
    case 2: return "rotateX(0deg) rotateY(-90deg)";
    case 3: return "rotateX(-90deg) rotateY(0deg)";
    case 4: return "rotateX(90deg) rotateY(0deg)";
    case 5: return "rotateX(0deg) rotateY(90deg)";
    case 6: return "rotateX(0deg) rotateY(180deg)";
    default: return "rotateX(0deg) rotateY(0deg)";
  }
}

function renderRadarChart(stats) {
  if (!stats) return "";

  const axes = [
    { label: "HP", val: stats.max_hp || stats.hp || 100, max: 200, color: "#2ecc71" },
    { label: "ATK", val: stats.atk || 10, max: 100, color: "#e74c3c" },
    { label: "DEF", val: parseFloat(stats.defense || 0), max: 50, color: "#3498db" },
    { label: "RES", val: stats.res || 0, max: 100, color: "#9b59b6" },
    { label: "M.DEF", val: parseFloat(stats.res_def || 0), max: 50, color: "#1abc9c" },
    { label: "SPD", val: stats.atk_spd || 100, max: 200, color: "#f1c40f" }
  ];

  const size = 160;
  const center = size / 2;
  const maxRadius = 45;
  const numAxes = axes.length;

  // Background grid polygons
  let gridPolys = "";
  const gridLevels = [0.33, 0.66, 1.0];
  gridLevels.forEach(level => {
    const points = [];
    for (let i = 0; i < numAxes; i++) {
      const angle = i * (2 * Math.PI / numAxes) - Math.PI / 2;
      const r = maxRadius * level;
      const x = center + Math.cos(angle) * r;
      const y = center + Math.sin(angle) * r;
      points.push(`${x},${y}`);
    }
    gridPolys += `<polygon points="${points.join(" ")}" fill="none" stroke="rgba(255,255,255,0.08)" stroke-width="1" />`;
  });

  // Radial lines and labels
  let radialLines = "";
  let labelText = "";
  for (let i = 0; i < numAxes; i++) {
    const angle = i * (2 * Math.PI / numAxes) - Math.PI / 2;
    const outerX = center + Math.cos(angle) * maxRadius;
    const outerY = center + Math.sin(angle) * maxRadius;

    radialLines += `<line x1="${center}" y1="${center}" x2="${outerX}" y2="${outerY}" stroke="rgba(255,255,255,0.12)" stroke-width="1" />`;

    const labelDist = maxRadius + 14;
    const labelX = center + Math.cos(angle) * labelDist;
    const labelY = center + Math.sin(angle) * labelDist + 3;
    let textAnchor = "middle";
    if (Math.cos(angle) > 0.1) textAnchor = "start";
    else if (Math.cos(angle) < -0.1) textAnchor = "end";

    labelText += `<text x="${labelX}" y="${labelY}" fill="rgba(255,255,255,0.5)" font-size="8" font-family="Outfit, sans-serif" text-anchor="${textAnchor}" font-weight="bold">${axes[i].label}</text>`;
  }

  // Data polygon
  const dataPoints = [];
  const vertexDots = [];
  for (let i = 0; i < numAxes; i++) {
    const angle = i * (2 * Math.PI / numAxes) - Math.PI / 2;
    const valPercent = Math.min(1.0, Math.max(0.1, axes[i].val / axes[i].max));
    const r = maxRadius * valPercent;
    const x = center + Math.cos(angle) * r;
    const y = center + Math.sin(angle) * r;
    dataPoints.push(`${x},${y}`);

    vertexDots.push(`<circle cx="${x}" cy="${y}" r="2" fill="${axes[i].color}" />`);
  }

  return `
    <svg width="${size}" height="${size}" viewBox="0 0 ${size} ${size}" style="display:block;margin:0 auto;overflow:visible;">
      ${gridPolys}
      ${radialLines}
      ${labelText}
      <polygon points="${dataPoints.join(" ")}" fill="rgba(162, 115, 255, 0.25)" stroke="#a273ff" stroke-width="2" style="filter: drop-shadow(0 0 4px rgba(162, 115, 255, 0.5));" />
      ${vertexDots.join("")}
    </svg>
  `;
}

function spawnDamageNumber(targetEl, amount, type) {
  if (!targetEl) return;
  const rect = targetEl.getBoundingClientRect();
  const docEl = document.documentElement;
  const x = rect.left + rect.width / 2 + (window.pageXOffset || docEl.scrollLeft) - (docEl.clientLeft || 0);
  const y = rect.top + (window.pageYOffset || docEl.scrollTop) - (docEl.clientTop || 0);

  const numEl = document.createElement("div");
  numEl.className = "floating-damage";
  numEl.style.left = `${x}px`;
  numEl.style.top = `${y}px`;

  if (type === "heal") {
    numEl.textContent = `+${amount}`;
    numEl.style.color = "#2ecc71";
  } else if (type === "critical") {
    numEl.textContent = `-${amount}!`;
    numEl.style.color = "#ffc837";
    numEl.style.fontSize = "2.4rem";
  } else if (type === "magic") {
    numEl.textContent = `-${amount}`;
    numEl.style.color = "#a273ff";
  } else {
    numEl.textContent = `-${amount}`;
    numEl.style.color = "#ff4d4d";
  }

  document.body.appendChild(numEl);
  setTimeout(() => {
    numEl.remove();
  }, 1000);
}

function typeTextWordByWord(element, htmlContent, speed) {
  if (speed <= 0) {
    element.innerHTML = htmlContent;
    return Promise.resolve();
  }

  return new Promise((resolve) => {
    const tokens = htmlContent.match(/<[^>]+>|[^<>\s]+|\s+/g) || [];
    let currentTokenIndex = 0;
    element.innerHTML = "";

    function showNextToken() {
      if (currentTokenIndex >= tokens.length) {
        resolve();
        return;
      }

      const token = tokens[currentTokenIndex++];
      element.innerHTML += token;

      const storyLog = document.getElementById("rpgStoryLog");
      if (storyLog) {
        storyLog.scrollTop = storyLog.scrollHeight;
      }

      if (token.startsWith("<") || token.trim() === "") {
        showNextToken();
      } else {
        setTimeout(showNextToken, speed);
      }
    }

    showNextToken();
  });
}

function renderSpecialSkillsIndicators(char) {
  const skills = char.special_skills;
  if (!skills) return "";

  let indicatorsHtml = "";

  // 1. Wang (Caster) Chess Pieces
  if (char.race === "Valkyrie" && char.char_class === "Caster" && skills.quan_co_count !== undefined && skills.quan_co_count > 0) {
    let chessOrbs = "";
    for (let i = 0; i < skills.quan_co_count; i++) {
      chessOrbs += `<span class="valk-chess-orb" title="Quân cờ ${i + 1}">⚫</span>`;
    }
    indicatorsHtml += `<div class="valk-special-indicators valk-wang-chess" title="Số quân cờ đang vây hãm">${chessOrbs}</div>`;
  }

  // 2. Lemuen (Sniper) Bullet Slots
  if (char.race === "Valkyrie" && char.char_class === "Sniper" && skills.bullet_count !== undefined) {
    let bullets = "";
    for (let i = 0; i < 5; i++) {
      if (i < skills.bullet_count) {
        bullets += `<span class="valk-bullet loaded" title="Đạn nạp sẵn: ${i + 1}">⚡</span>`;
      } else {
        bullets += `<span class="valk-bullet empty"></span>`;
      }
    }
    indicatorsHtml += `<div class="valk-special-indicators valk-lemuen-bullets" title="Đạn khóa mục tiêu (Lemuen)">${bullets}</div>`;
  }

  // 3. Hoshiguma (Defender) Revival countdown
  if (char.race === "Valkyrie" && char.char_class === "Defender" && skills.hoshi_passive_countdown !== undefined && skills.hoshi_passive_countdown > 0) {
    indicatorsHtml += `
      <div class="valk-special-indicators valk-hoshiguma-revive" title="Lượt hồi sinh Ma thần bất diệt">
        🌀 <span class="revive-count">${skills.hoshi_passive_countdown}t</span>
      </div>
    `;
  }

  return indicatorsHtml ? `<div class="special-skill-indicators-wrapper">${indicatorsHtml}</div>` : "";
}

function updateWeatherEffect(region) {
  const overlay = document.getElementById("rpgAmbientOverlay");
  if (!overlay) return;

  // Clear current classes
  overlay.className = "rpg-ambient-overlay";
  overlay.innerHTML = "";

  if (!region || !weatherEnabled) return;

  if (region === "Biên Cương Băng Giá") {
    overlay.classList.add("snow-weather");
    // Generate snow particles
    for (let i = 0; i < 40; i++) {
      const particle = document.createElement("div");
      particle.className = "snowflake";
      particle.style.left = `${Math.random() * 100}%`;
      particle.style.animationDelay = `${Math.random() * 5}s`;
      particle.style.animationDuration = `${Math.random() * 5 + 5}s`;
      particle.style.opacity = Math.random();
      particle.style.transform = `scale(${Math.random() * 0.5 + 0.5})`;
      overlay.appendChild(particle);
    }
  } else if (region === "Khu Rừng Đom Đóm") {
    overlay.classList.add("fireflies-weather");
    // Generate fireflies particles
    for (let i = 0; i < 25; i++) {
      const particle = document.createElement("div");
      particle.className = "firefly";
      particle.style.left = `${Math.random() * 100}%`;
      particle.style.top = `${Math.random() * 100}%`;
      particle.style.animationDelay = `${Math.random() * 8}s`;
      particle.style.animationDuration = `${Math.random() * 10 + 10}s`;
      overlay.appendChild(particle);
    }
  } else if (region === "Thung Lũng Hắc Ám") {
    overlay.classList.add("fog-weather");
    // Create fog layers
    const fog1 = document.createElement("div");
    fog1.className = "fog-layer fog-layer-1";
    const fog2 = document.createElement("div");
    fog2.className = "fog-layer fog-layer-2";
    overlay.appendChild(fog1);
    overlay.appendChild(fog2);
  } else if (region === "Vương Quốc VinaVictoria") {
    overlay.classList.add("sunrays-weather");
    const ray = document.createElement("div");
    ray.className = "sunray";
    overlay.appendChild(ray);
  }
}

function getItemEmoji(itemType, itemName = "") {
  const nameLower = itemName ? itemName.toLowerCase() : "";
  if (nameLower.includes("mảnh vỡ")) return "🧩";
  if (nameLower.includes("chìa khoá") || nameLower.includes("chìa khóa")) return "🔑";
  if (nameLower.includes("bản đồ")) return "🗺️";

  switch (itemType) {
    case "Weapon": return "🗡️";
    case "Armor": return "🛡️";
    case "Consume":
    case "Consumable": return "🧪";
    default: return "📦";
  }
}

function getRarityLabel(rarity) {
  switch (rarity) {
    case "Mythic": return "Thần Thoại";
    case "Legendary": return "Truyền Thuyết";
    case "Epic": return "Sử Thi";
    case "Rare": return "Hiếm";
    case "Uncommon": return "Thường";
    case "Common": return "Cơ Bản";
    default: return rarity;
  }
}

function showItemTooltip(item, event) {
  let tooltip = document.getElementById("rpgItemTooltip");
  if (!tooltip) {
    tooltip = document.createElement("div");
    tooltip.id = "rpgItemTooltip";
    tooltip.className = "rpg-item-tooltip glass-panel";
    document.body.appendChild(tooltip);
  }

  let statsHtml = "";
  if (item.stats_bonus) {
    for (const [stat, bonus] of Object.entries(item.stats_bonus)) {
      if (bonus !== 0) {
        let statLabel = stat.toUpperCase();
        if (stat === "max_hp") statLabel = "HP";
        if (stat === "atk") statLabel = "ATK";
        if (stat === "defense") statLabel = "DEF";
        if (stat === "res_def") statLabel = "M.DEF";
        if (stat === "res") statLabel = "RES";
        if (stat === "atk_spd") statLabel = "SPD";
        const sign = bonus > 0 ? "+" : "";
        statsHtml += `<div class="tooltip-stat-row"><span>${statLabel}:</span> <strong>${sign}${bonus}%</strong></div>`;
      }
    }
  }

  let typeLabel = "Vật phẩm";
  if (item.item_type === "Weapon") typeLabel = "Vũ khí";
  if (item.item_type === "Armor") typeLabel = "Giáp trụ";
  if (item.item_type === "Consume") typeLabel = "Tiêu dùng";

  tooltip.innerHTML = `
    <div class="tooltip-header">
      <h4 class="rpg-text-${item.rarity}" style="margin:0; font-size:0.9rem;">${item.name}</h4>
      <span class="rpg-badge rarity rpg-text-${item.rarity}" style="font-size:0.6rem; padding: 2px 6px;">${getRarityLabel(item.rarity)}</span>
    </div>
    <div class="tooltip-type">${typeLabel}</div>
    ${statsHtml ? `<div class="tooltip-stats">${statsHtml}</div>` : ""}
    <div class="tooltip-desc">${item.description || ""}</div>
  `;

  tooltip.style.display = "block";
  updateItemTooltipPosition(event);
}

function updateItemTooltipPosition(event) {
  const tooltip = document.getElementById("rpgItemTooltip");
  if (!tooltip) return;
  const padding = 15;
  let left = event.pageX + padding;
  let top = event.pageY + padding;

  if (left + tooltip.offsetWidth > window.innerWidth) {
    left = event.pageX - tooltip.offsetWidth - padding;
  }
  if (top + tooltip.offsetHeight > window.innerHeight) {
    top = event.pageY - tooltip.offsetHeight - padding;
  }

  tooltip.style.left = `${left}px`;
  tooltip.style.top = `${top}px`;
}

function hideItemTooltip() {
  const tooltip = document.getElementById("rpgItemTooltip");
  if (tooltip) {
    tooltip.style.display = "none";
  }
}

function sleep(ms) {
  return new Promise(resolve => setTimeout(resolve, ms));
}

// ── BACKEND API COMMUNICATION ────────────────────────────────────────────────

async function rpgFetch(url, options = {}) {
  const headers = {
    "Content-Type": "application/json",
    ...(options.headers || {}),
  };

  const auth = window.auth;
  let token = "guest";
  if (auth && auth.currentUser) {
    token = await auth.currentUser.getIdToken(true);
  } else if (window.AI_STORY_CONFIG?.BYPASS_FIREBASE) {
    token = "guest";
  }
  headers.Authorization = `Bearer ${token}`;

  const response = await fetch(url, {
    ...options,
    headers,
  });

  if (!response.ok) {
    let errMsg = "Đã xảy ra lỗi hệ thống.";
    try {
      const errData = await response.json();
      errMsg = errData.detail || errData.message || errMsg;
    } catch (_) {
      try {
        const text = await response.text();
        if (text) errMsg = text;
      } catch (_) { }
    }
    throw new Error(errMsg);
  }

  const contentType = response.headers.get("content-type") || "";
  if (contentType.includes("application/json")) {
    return await response.json();
  }
  return await response.text();
}

async function updatePointsDisplay() {
  try {
    const auth = window.auth;
    if (!auth || !auth.currentUser) return;
    const data = await rpgFetch(`${getApiBase()}/game/me`);
    const points = data.points_balance || 0;
    const pointsValue = document.getElementById("pointsValue");
    if (pointsValue) pointsValue.textContent = points.toLocaleString();
    const pointsBadge = document.getElementById("pointsBadge");
    if (pointsBadge) pointsBadge.classList.remove("hidden");
  } catch (err) {
    console.warn("Lỗi khi tải thông tin điểm:", err);
  }
}

// ── SETUP SCREEN WIZARD & DICE ROLLING ───────────────────────────────────────

function initRpgSetupWizard() {
  let currentStep = 1;
  let rolledGold = null;
  let rolledEquipment = null;
  let selectedRegion = "Vương Quốc VinaVictoria";
  let selectedObjective = "Tiêu diệt Ma Vương cứu thế giới";
  let selectedAppearance = "";

  function updateWizardProgress(step) {
    currentStep = step;

    // Hide all step views
    for (let i = 1; i <= 8; i++) {
      const el = document.getElementById(`rpgStep${i}`);
      if (el) el.classList.remove("active");
    }
    // Show current step view
    const currentEl = document.getElementById(`rpgStep${step}`);
    if (currentEl) currentEl.classList.add("active");

    // Update SVG Mystic Path fill and glowing token
    const pathFill = document.getElementById("rpgMysticPathFill");
    const token = document.getElementById("rpgMysticToken");
    if (pathFill && token) {
      const totalLength = 800; // standard SVG path length
      const fillPercent = (step - 1) / 7;
      const drawLength = totalLength * fillPercent;
      pathFill.style.strokeDashoffset = totalLength - drawLength;

      try {
        const point = pathFill.getPointAtLength(drawLength);
        token.setAttribute("cx", point.x);
        token.setAttribute("cy", point.y);
      } catch (e) {
        // Safe math fallback
        const x = 10 + fillPercent * 780;
        const y = 30 - Math.sin(fillPercent * Math.PI * 3) * 10;
        token.setAttribute("cx", x);
        token.setAttribute("cy", y);
      }
    }

    // Update step indicators active/completed state
    const stepIndicators = document.querySelectorAll("#rpgWizardStepsContainer .progress-step");
    stepIndicators.forEach(ind => {
      const indStep = parseInt(ind.dataset.step);
      ind.classList.remove("active", "completed");
      if (indStep === step) {
        ind.classList.add("active");
      } else if (indStep < step) {
        ind.classList.add("completed");
      }
    });
  }

  window.resetRpgSetupWizard = () => {
    currentStep = 1;
    rolledGold = null;
    rolledEquipment = null;
    selectedRegion = "Vương Quốc VinaVictoria";
    selectedObjective = "Tiêu diệt Ma Vương cứu thế giới";
    selectedGender = "Female";
    selectedAppearance = "";

    const appInput = document.getElementById("rpgAppearanceInput");
    if (appInput) appInput.value = "";

    const genderBtns = document.querySelectorAll(".rpg-gender-btn");
    genderBtns.forEach(b => {
      if (b.dataset.gender === "Female") b.classList.add("active");
      else b.classList.remove("active");
    });

    const regionChips = document.querySelectorAll("#rpgRegionPresets .rpg-preset-chip");
    regionChips.forEach(c => {
      if (c.dataset.value === "Vương Quốc VinaVictoria") c.classList.add("active");
      else c.classList.remove("active");
    });
    const regionInput = document.getElementById("rpgRegionInput");
    if (regionInput) regionInput.value = "Vương Quốc VinaVictoria";

    const objectiveChips = document.querySelectorAll("#rpgObjectivePresets .rpg-preset-chip");
    objectiveChips.forEach(c => {
      if (c.dataset.value === "Tiêu diệt Ma Vương cứu thế giới") c.classList.add("active");
      else c.classList.remove("active");
    });
    const objectiveInput = document.getElementById("rpgObjectiveInput");
    if (objectiveInput) objectiveInput.value = "Tiêu diệt Ma Vương cứu thế giới";

    const nameInput = document.getElementById("rpgPlayerName");
    if (nameInput) nameInput.value = "";

    const nameSuggestionsContainer = document.getElementById("rpgNameSuggestions");
    if (nameSuggestionsContainer) {
      nameSuggestionsContainer.classList.add("hidden");
      nameSuggestionsContainer.innerHTML = "";
    }
    const objectiveSuggestionsContainer = document.getElementById("rpgObjectiveSuggestions");
    if (objectiveSuggestionsContainer) {
      objectiveSuggestionsContainer.classList.add("hidden");
      objectiveSuggestionsContainer.innerHTML = "";
    }

    const goldDiceCube = document.getElementById("goldDiceCube");
    if (goldDiceCube) {
      goldDiceCube.style.transform = "rotateX(0deg) rotateY(0deg)";
      goldDiceCube.classList.remove("rolling");
    }
    const goldResult = document.getElementById("goldRollResult");
    if (goldResult) goldResult.innerHTML = "";

    const equipDiceCube = document.getElementById("equipDiceCube");
    if (equipDiceCube) {
      equipDiceCube.style.transform = "rotateX(0deg) rotateY(0deg)";
      equipDiceCube.classList.remove("rolling");
    }
    const equipResult = document.getElementById("equipRollResult");
    if (equipResult) equipResult.innerHTML = "";

    const rollGoldBtn = document.getElementById("rpgRollGoldBtn");
    if (rollGoldBtn) rollGoldBtn.disabled = false;
    const rollEquipBtn = document.getElementById("rpgRollEquipBtn");
    if (rollEquipBtn) rollEquipBtn.disabled = true;

    const step4NextBtn = document.getElementById("rpgStep4Next");
    if (step4NextBtn) {
      step4NextBtn.disabled = true;
      step4NextBtn.classList.add("disabled");
    }
    const step5NextBtn = document.getElementById("rpgStep5Next");
    if (step5NextBtn) {
      step5NextBtn.disabled = true;
      step5NextBtn.classList.add("disabled");
    }

    updateWizardProgress(1);
  };

  // Gender buttons
  const genderBtns = document.querySelectorAll(".rpg-gender-btn");
  genderBtns.forEach(btn => {
    btn.addEventListener("click", () => {
      genderBtns.forEach(b => b.classList.remove("active"));
      btn.classList.add("active");
      selectedGender = btn.dataset.gender;

      // Hide name suggestions when gender changes, so they have to suggest again
      const nameSuggestionsContainer = document.getElementById("rpgNameSuggestions");
      if (nameSuggestionsContainer) {
        nameSuggestionsContainer.classList.add("hidden");
        nameSuggestionsContainer.innerHTML = "";
      }
    });
  });

  // Region Presets Chips
  const regionChips = document.querySelectorAll("#rpgRegionPresets .rpg-preset-chip");
  const regionInput = document.getElementById("rpgRegionInput");
  regionChips.forEach(chip => {
    chip.addEventListener("click", () => {
      regionChips.forEach(c => c.classList.remove("active"));
      chip.classList.add("active");
      if (regionInput) {
        regionInput.value = chip.dataset.value;
        selectedRegion = chip.dataset.value;
      }
    });
  });
  if (regionInput) {
    regionInput.addEventListener("input", (e) => {
      selectedRegion = e.target.value.trim();
      regionChips.forEach(c => {
        if (c.dataset.value === selectedRegion) {
          c.classList.add("active");
        } else {
          c.classList.remove("active");
        }
      });
    });
  }

  // Step 3: Random Region Suggestion
  const suggestRegionBtn = document.getElementById("rpgSuggestRegionBtn");
  if (suggestRegionBtn) {
    suggestRegionBtn.addEventListener("click", () => {
      const regionsList = [
        "Vương đô Victoria",
        "Long kinh thành",
        "Vương đô Londinium",
        "Tòa Thành Chúa Quỷ",
        "Thành Phố Tự Do",
        "Pháo Đài Mùa Đông",
        "Thánh Đường Tối Cao"
      ];
      const randomRegion = regionsList[Math.floor(Math.random() * regionsList.length)];
      if (regionInput) {
        regionInput.value = randomRegion;
        selectedRegion = randomRegion;

        regionChips.forEach(c => {
          if (c.dataset.value === randomRegion) {
            c.classList.add("active");
          } else {
            c.classList.remove("active");
          }
        });
      }
    });
  }

  // Objective Presets Chips
  const objectiveChips = document.querySelectorAll("#rpgObjectivePresets .rpg-preset-chip");
  const objectiveInput = document.getElementById("rpgObjectiveInput");
  objectiveChips.forEach(chip => {
    chip.addEventListener("click", () => {
      objectiveChips.forEach(c => c.classList.remove("active"));
      chip.classList.add("active");
      if (objectiveInput) {
        objectiveInput.value = chip.dataset.value;
        selectedObjective = chip.dataset.value;
      }
    });
  });
  if (objectiveInput) {
    objectiveInput.addEventListener("input", (e) => {
      selectedObjective = e.target.value.trim();
      objectiveChips.forEach(c => {
        if (c.dataset.value === selectedObjective) {
          c.classList.add("active");
        } else {
          c.classList.remove("active");
        }
      });
    });
  }

  // Back to landing page
  const backBtn = document.getElementById("backToLandingFromRpgSetup");
  if (backBtn) {
    backBtn.addEventListener("click", async () => {
      if (window.guardUnsavedDraftNavigation) {
        await window.guardUnsavedDraftNavigation(() => {
          if (window.showPage) {
            window.showPage(document.getElementById("landingPage"));
          }
        });
      } else {
        if (window.showPage) {
          window.showPage(document.getElementById("landingPage"));
        }
      }
    });
  }

  // Step 1: AI Name Suggestion
  const suggestNameBtn = document.getElementById("rpgSuggestNameBtn");
  if (suggestNameBtn) {
    suggestNameBtn.addEventListener("click", async () => {
      suggestNameBtn.disabled = true;
      const originalText = suggestNameBtn.textContent;
      suggestNameBtn.textContent = "🪄 Đang tìm...";

      try {
        const res = await rpgFetch(`${getApiBase()}/game/rpg/suggest-names?gender=${selectedGender}`);
        const container = document.getElementById("rpgNameSuggestions");
        if (container && res && res.names) {
          container.innerHTML = "";
          container.classList.remove("hidden");
          res.names.forEach(name => {
            const chip = document.createElement("button");
            chip.type = "button";
            chip.className = "suggestion-chip";
            chip.textContent = name;
            chip.addEventListener("click", () => {
              const nameInput = document.getElementById("rpgPlayerName");
              if (nameInput) nameInput.value = name;
            });
            container.appendChild(chip);
          });
        }
      } catch (err) {
        console.error("Name suggest failed:", err);
        alert("Gợi ý tên lỗi: " + err.message);
      } finally {
        suggestNameBtn.disabled = false;
        suggestNameBtn.textContent = originalText;
      }
    });
  }

  // Step 6: AI Objective Suggestion
  const suggestObjectiveBtn = document.getElementById("rpgSuggestObjectiveBtn");
  if (suggestObjectiveBtn) {
    suggestObjectiveBtn.addEventListener("click", async () => {
      suggestObjectiveBtn.disabled = true;
      const originalText = suggestObjectiveBtn.textContent;
      suggestObjectiveBtn.textContent = "🪄 Đang tìm...";

      try {
        const res = await rpgFetch(`${getApiBase()}/game/rpg/suggest-objectives`);
        const container = document.getElementById("rpgObjectiveSuggestions");
        if (container && res && res.objectives) {
          container.innerHTML = "";
          container.classList.remove("hidden");
          res.objectives.forEach(obj => {
            const chip = document.createElement("button");
            chip.type = "button";
            chip.className = "suggestion-chip";
            chip.textContent = obj;
            chip.addEventListener("click", () => {
              if (objectiveInput) {
                objectiveInput.value = obj;
                selectedObjective = obj;
              }
              objectiveChips.forEach(c => c.classList.remove("active"));
            });
            container.appendChild(chip);
          });
        }
      } catch (err) {
        console.error("Objective suggest failed:", err);
        alert("Gợi ý mục tiêu lỗi: " + err.message);
      } finally {
        suggestObjectiveBtn.disabled = false;
        suggestObjectiveBtn.textContent = originalText;
      }
    });
  }

  // Step 1 -> Step 2
  const step1Next = document.getElementById("rpgStep1Next");
  if (step1Next) {
    step1Next.addEventListener("click", () => {
      const nameInput = document.getElementById("rpgPlayerName");
      if (!nameInput.value.trim()) {
        alert("Vui lòng nhập tên hoặc chọn từ gợi ý!");
        return;
      }
      updateWizardProgress(2);
    });
  }

  // Step 2 -> Step 3
  const step2Next = document.getElementById("rpgStep2Next");
  if (step2Next) {
    step2Next.addEventListener("click", () => {
      updateWizardProgress(3);
    });
  }
  const step2Back = document.getElementById("rpgStep2Back");
  if (step2Back) {
    step2Back.addEventListener("click", () => {
      updateWizardProgress(1);
    });
  }

  // Step 3 -> Step 4 (Calls session start on backend)
  const step3Next = document.getElementById("rpgStep3Next");
  if (step3Next) {
    step3Next.addEventListener("click", async () => {
      const nameInput = document.getElementById("rpgPlayerName");
      const playerName = nameInput.value.trim() || "Người lữ hành";
      if (regionInput) {
        selectedRegion = regionInput.value.trim() || "Vương Quốc VinaVictoria";
      }

      step3Next.disabled = true;
      step3Next.textContent = "Đang khởi tạo...";

      try {
        const res = await rpgFetch(`${getApiBase()}/game/rpg/start`, {
          method: "POST",
          body: JSON.stringify({
            player_name: playerName,
            gender: selectedGender,
            region: selectedRegion
          })
        });

        currentSessionId = res.session_id;
        currentSessionIsSaved = false;
        gameState = res.rpg_state;

        // Reset dice rolled indicators for Step 4/5
        rolledGold = null;
        rolledEquipment = null;

        const goldDiceCube = document.getElementById("goldDiceCube");
        if (goldDiceCube) {
          goldDiceCube.style.transform = "rotateX(0deg) rotateY(0deg)";
          goldDiceCube.classList.remove("rolling");
        }
        document.getElementById("goldRollResult").innerHTML = "";

        const equipDiceCube = document.getElementById("equipDiceCube");
        if (equipDiceCube) {
          equipDiceCube.style.transform = "rotateX(0deg) rotateY(0deg)";
          equipDiceCube.classList.remove("rolling");
        }
        document.getElementById("equipRollResult").innerHTML = "";

        // Reset navigation buttons for rolling steps
        document.getElementById("rpgRollGoldBtn").disabled = false;
        document.getElementById("rpgRollEquipBtn").disabled = true;

        const step4NextBtn = document.getElementById("rpgStep4Next");
        step4NextBtn.disabled = true;
        step4NextBtn.classList.add("disabled");

        const step5NextBtn = document.getElementById("rpgStep5Next");
        step5NextBtn.disabled = true;
        step5NextBtn.classList.add("disabled");

        updateWizardProgress(4);

      } catch (err) {
        alert("Khởi tạo nhân vật thất bại: " + err.message);
      } finally {
        step3Next.disabled = false;
        step3Next.textContent = "Tạo Nhân Vật ⚔";
      }
    });
  }
  const step3Back = document.getElementById("rpgStep3Back");
  if (step3Back) {
    step3Back.addEventListener("click", () => {
      updateWizardProgress(2);
    });
  }

  // Step 4: Roll Gold
  const rollGoldBtn = document.getElementById("rpgRollGoldBtn");
  if (rollGoldBtn) {
    rollGoldBtn.addEventListener("click", async () => {
      rollGoldBtn.disabled = true;
      const goldDiceCube = document.getElementById("goldDiceCube");
      if (goldDiceCube) {
        goldDiceCube.classList.add("rolling");
        goldDiceCube.style.transform = "";
      }

      try {
        const [res] = await Promise.all([
          rpgFetch(`${getApiBase()}/game/rpg/roll-gold?session_id=${encodeURIComponent(currentSessionId)}`, { method: "POST" }),
          sleep(1200)
        ]);

        if (goldDiceCube) {
          goldDiceCube.classList.remove("rolling");
          goldDiceCube.style.transform = getCubeRotation(res.dice_roll);
        }

        rolledGold = res.gold_gained;
        document.getElementById("goldRollResult").innerHTML = `💰 <strong>+${res.gold_gained} Vàng</strong> ban đầu!`;
        gameState = res.rpg_state;

        // Enable Step 4 Next
        const step4NextBtn = document.getElementById("rpgStep4Next");
        step4NextBtn.disabled = false;
        step4NextBtn.classList.remove("disabled");

        // Enable Equipment Roll on Step 5
        document.getElementById("rpgRollEquipBtn").disabled = false;

      } catch (err) {
        if (goldDiceCube) {
          goldDiceCube.classList.remove("rolling");
          goldDiceCube.style.transform = "rotateX(0deg) rotateY(0deg)";
        }
        alert("Tung xúc xắc vàng lỗi: " + err.message);
        rollGoldBtn.disabled = false;
      }
    });
  }
  const step4Back = document.getElementById("rpgStep4Back");
  if (step4Back) {
    step4Back.disabled = false;
    step4Back.addEventListener("click", () => {
      updateWizardProgress(3);
    });
  }
  const step4NextBtn = document.getElementById("rpgStep4Next");
  if (step4NextBtn) {
    step4NextBtn.addEventListener("click", () => {
      updateWizardProgress(5);
    });
  }

  // Step 5: Roll Equipment
  const rollEquipBtn = document.getElementById("rpgRollEquipBtn");
  if (rollEquipBtn) {
    rollEquipBtn.addEventListener("click", async () => {
      rollEquipBtn.disabled = true;
      const equipDiceCube = document.getElementById("equipDiceCube");
      if (equipDiceCube) {
        equipDiceCube.classList.add("rolling");
        equipDiceCube.style.transform = "";
      }

      try {
        const [res] = await Promise.all([
          rpgFetch(`${getApiBase()}/game/rpg/roll-equipment?session_id=${encodeURIComponent(currentSessionId)}`, { method: "POST" }),
          sleep(1200)
        ]);

        if (equipDiceCube) {
          equipDiceCube.classList.remove("rolling");
          equipDiceCube.style.transform = getCubeRotation(res.dice_roll);
        }

        rolledEquipment = res.item;
        const rarity = res.item.rarity;
        document.getElementById("equipRollResult").innerHTML = `Nhận được: <strong class="rpg-text-${rarity}">${res.item.name}</strong> (${getRarityLabel(rarity)})!`;
        gameState = res.rpg_state;

        // Enable Step 5 Next
        const step5NextBtn = document.getElementById("rpgStep5Next");
        step5NextBtn.disabled = false;
        step5NextBtn.classList.remove("disabled");

      } catch (err) {
        if (equipDiceCube) {
          equipDiceCube.classList.remove("rolling");
          equipDiceCube.style.transform = "rotateX(0deg) rotateY(0deg)";
        }
        alert("Tung xúc xắc trang bị lỗi: " + err.message);
        rollEquipBtn.disabled = false;
      }
    });
  }
  const step5Back = document.getElementById("rpgStep5Back");
  if (step5Back) {
    step5Back.disabled = false;
    step5Back.addEventListener("click", () => {
      updateWizardProgress(4);
    });
  }
  const step5NextBtn = document.getElementById("rpgStep5Next");
  if (step5NextBtn) {
    step5NextBtn.addEventListener("click", () => {
      updateWizardProgress(6);
    });
  }

  // Step 6: Objective Next
  const step6Next = document.getElementById("rpgStep6Next");
  if (step6Next) {
    step6Next.addEventListener("click", () => {
      if (objectiveInput) {
        selectedObjective = objectiveInput.value.trim() || "Tiêu diệt Ma Vương cứu thế giới";
      }
      updateWizardProgress(7);
    });
  }
  const step6Back = document.getElementById("rpgStep6Back");
  if (step6Back) {
    step6Back.disabled = false;
    step6Back.addEventListener("click", () => {
      updateWizardProgress(5);
    });
  }

  // Step 7: Appearance AI Suggestion
  const suggestAppearanceBtn = document.getElementById("rpgSuggestAppearanceBtn");
  if (suggestAppearanceBtn) {
    suggestAppearanceBtn.addEventListener("click", async () => {
      suggestAppearanceBtn.disabled = true;
      const originalText = suggestAppearanceBtn.textContent;
      suggestAppearanceBtn.textContent = "🪄 Đang gợi ý...";

      try {
        const nameInput = document.getElementById("rpgPlayerName");
        const playerName = nameInput ? nameInput.value.trim() : "Người lữ hành";
        const equipName = rolledEquipment ? rolledEquipment.name : "Không";
        const goldVal = rolledGold || 0;

        const url = `${getApiBase()}/game/rpg/suggest-appearance?player_name=${encodeURIComponent(playerName)}&gender=${encodeURIComponent(selectedGender)}&region=${encodeURIComponent(selectedRegion)}&objective=${encodeURIComponent(selectedObjective)}&gold=${goldVal}&equipment_name=${encodeURIComponent(equipName)}`;
        const res = await rpgFetch(url, { method: "POST" });

        const appInput = document.getElementById("rpgAppearanceInput");
        if (appInput && res && res.appearance) {
          appInput.value = res.appearance;
        }
      } catch (err) {
        console.error("Appearance suggest failed:", err);
        alert("Gợi ý ngoại hình lỗi: " + err.message);
      } finally {
        suggestAppearanceBtn.disabled = false;
        suggestAppearanceBtn.textContent = originalText;
      }
    });
  }

  // Step 7: Next to Step 8 (Summary)
  const step7Next = document.getElementById("rpgStep7Next");
  if (step7Next) {
    step7Next.addEventListener("click", () => {
      const appInput = document.getElementById("rpgAppearanceInput");
      selectedAppearance = appInput ? appInput.value.trim() : "";
      if (!selectedAppearance) {
        selectedAppearance = "Một người lữ hành bí ẩn.";
      }

      // Populate Step 8 Summary
      const nameInput = document.getElementById("rpgPlayerName");
      document.getElementById("rpgSummaryPlayerName").textContent = nameInput.value.trim() || "Người lữ hành";
      document.getElementById("summaryPlayerGender").textContent =
        selectedGender === "Female" ? "Nữ (Female)" : (selectedGender === "Male" ? "Nam (Male)" : "Ẩn danh (No mention)");
      document.getElementById("summaryPlayerRegion").textContent = selectedRegion;
      document.getElementById("summaryPlayerObjective").textContent = selectedObjective;
      document.getElementById("summaryPlayerAppearance").textContent = selectedAppearance;
      document.getElementById("summaryPlayerGold").textContent = rolledGold ? `${rolledGold} Vàng` : "-";
      document.getElementById("summaryPlayerEquip").innerHTML = rolledEquipment
        ? `<span class="rpg-text-${rolledEquipment.rarity}">${rolledEquipment.name}</span> (${getRarityLabel(rolledEquipment.rarity)})`
        : "-";

      // Populate starting stats preview dynamically from gameState
      if (gameState && gameState.player_character && gameState.player_character.stats) {
        const stats = gameState.player_character.stats;
        document.getElementById("summaryStatHp").textContent = `${stats.hp}/${stats.max_hp}`;
        document.getElementById("summaryStatAtk").textContent = stats.atk;
        document.getElementById("summaryStatDef").textContent = `${stats.defense}%`;
        document.getElementById("summaryStatRes").textContent = stats.res;
        document.getElementById("summaryStatResDef").textContent = `${stats.res_def}%`;
        document.getElementById("summaryStatSpd").textContent = stats.atk_spd;

        // Render Radar Chart SVG
        const radarContainer = document.getElementById("rpgSummaryRadarContainer");
        if (radarContainer) {
          radarContainer.innerHTML = renderRadarChart(stats);
        }
      }

      // Enable Start Adventure Button
      const startAdventureBtn = document.getElementById("rpgStartAdventureBtn");
      if (startAdventureBtn) {
        startAdventureBtn.disabled = false;
        startAdventureBtn.classList.remove("disabled");
      }

      updateWizardProgress(8);
    });
  }

  // Step 7: Back
  const step7Back = document.getElementById("rpgStep7Back");
  if (step7Back) {
    step7Back.addEventListener("click", () => {
      updateWizardProgress(6);
    });
  }

  // Step 8: Back to 7
  const step8Back = document.getElementById("rpgStep8Back");
  if (step8Back) {
    step8Back.addEventListener("click", () => {
      updateWizardProgress(7);
    });
  }

  // Step 8: Start Adventure Button click (triggers story narrative)
  const startAdventureBtn = document.getElementById("rpgStartAdventureBtn");
  if (startAdventureBtn) {
    startAdventureBtn.addEventListener("click", async () => {
      startAdventureBtn.disabled = true;
      startAdventureBtn.textContent = "Đang tạo thế giới...";

      try {
        const url = `${getApiBase()}/game/rpg/start-story?session_id=${encodeURIComponent(currentSessionId)}&region=${encodeURIComponent(selectedRegion)}&objective=${encodeURIComponent(selectedObjective)}&appearance_desc=${encodeURIComponent(selectedAppearance)}`;
        const res = await rpgFetch(url, { method: "POST" });

        // Redirect to RPG Play Screen
        if (window.showPage) {
          window.showPage(document.getElementById("rpgPage"));
        }

        currentSessionId = res.session_id;
        currentSessionIsSaved = false;
        gameState = res.rpg_state;

        // Reset and show initial story
        const storyLog = document.getElementById("rpgStoryLog");
        storyLog.innerHTML = "";
        appendStoryBlock(res.story);

        renderChoices(res.choices, res.event_type);
        renderState(res.rpg_state);
        updatePointsDisplay();

      } catch (err) {
        alert("Bắt đầu lỗi: " + err.message);
        startAdventureBtn.disabled = false;
        startAdventureBtn.textContent = "Bắt Đầu Hành Trình ▷";
      }
    });
  }
}

// Avatar Image Helpers
function isRecruitedCompanion(char) {
  if (!char || !char.character_id) return false;
  if (char.character_id === "player" || char.character_id === "monk" || char.character_id === "merchant") return false;

  if (gameState && gameState.party) {
    const active = gameState.party.active || [];
    const reserve = gameState.party.reserve || [];
    const inActive = active.some(c => c.character_id === char.character_id);
    const inReserve = reserve.some(c => c.character_id === char.character_id);
    if (inActive || inReserve) return true;
  }
  return false;
}

function isBossCharacter(char) {
  if (!char || !char.name) return false;
  const bosses = ["medusa", "golem", "werewolf", "dracula", "vua goblin", "poseidon", "diablo", "thiên dực long vương", "ma vương xương cốt", "alpha"];
  const nameLower = char.name.toLowerCase();
  return bosses.some(b => nameLower.includes(b)) || char.char_class === "Boss" || char.race === "Bí ẩn" || char.char_class === "Bí ẩn";
}

function getCharacterImageFilename(char) {
  if (!char) return null;
  const nameLower = char.name.toLowerCase();
  if (nameLower.includes("hoshiguma")) return "Hoshiguma_the_breacher.png";
  if (nameLower.includes("vina victoria") || nameLower.includes("vinavictoria") || nameLower.includes("vina_victoria")) return "VinaVictoria.png";
  if (nameLower.includes("wang")) return "Wang.png";
  if (nameLower.includes("lemuen") || nameLower.includes("lumuen")) return "Lemuen.png";
  if (nameLower.includes("silverash")) return "SilverAsh_the_Reignfrost.png";

  if (nameLower.includes("medusa")) return "Medusa.png";
  if (nameLower.includes("vua goblin") || nameLower.includes("goblin king")) return "Goblin_King.png";
  if (nameLower.includes("werewolf")) return "Werewolf.png";
  if (nameLower.includes("dracula")) return "Dracula.png";
  if (nameLower.includes("golem")) return "Golem.png";
  if (nameLower.includes("poseidon")) return "Poseidon.png";
  if (nameLower.includes("diablo")) return "Diablo.png";
  if (nameLower.includes("thiên dực long vương") || nameLower.includes("dragon king")) return "Dragon_King.png";
  if (nameLower.includes("ma vương xương cốt") || nameLower.includes("bone king")) return "Bone_King.png";
  if (nameLower.includes("alpha")) return "Alpha.png";

  if (char.character_id === "player") return "player_avatar.png";
  if (char.character_id && (char.character_id === "monk" || char.character_id.startsWith("monk_"))) return `${char.character_id}.png`;
  if (char.character_id && (char.character_id === "merchant" || char.character_id.startsWith("merchant_"))) return `${char.character_id}.png`;

  if (isRecruitedCompanion(char)) {
    return `${char.character_id}.png`;
  }

  return `${char.race}_${char.char_class}.png`;
}

function setupAvatarDisplay(imgElement, defaultSpan, char) {
  if (!char) {
    imgElement.style.display = "none";
    defaultSpan.style.display = "block";
    defaultSpan.textContent = "❔";
    return;
  }

  // Set fallback emoji
  let fallbackEmoji = "❔";
  if (isBossCharacter(char)) {
    fallbackEmoji = "👿";
  } else if (char.character_id === "player") {
    fallbackEmoji = char.gender === "Male" ? "🧔" : "👩";
  } else if (char.character_id === "monk") {
    fallbackEmoji = "🧘";
  } else if (char.character_id === "merchant") {
    fallbackEmoji = "🛒";
  } else if (char.race) {
    fallbackEmoji = getRaceEmoji(char.race, char.name);
  }
  defaultSpan.textContent = fallbackEmoji;

  const filename = getCharacterImageFilename(char);
  if (!filename) {
    imgElement.style.display = "none";
    defaultSpan.style.display = "block";
    return;
  }

  const prefKey = `show_img_${char.character_id || char.name}`;
  const showImg = localStorage.getItem(prefKey) !== "false";

  if (!showImg) {
    imgElement.style.display = "none";
    defaultSpan.style.display = "block";
    return;
  }

  // Hide image first while loading new src
  imgElement.style.display = "none";
  defaultSpan.style.display = "block";

  const apiBase = getApiBase();
  const baseUrl = apiBase.startsWith("http") ? apiBase : (apiBase === "/api" ? "/api" : "");
  const cleanBaseUrl = baseUrl.replace(/\/+$/, "");
  const srcPath = `${cleanBaseUrl}/assets/generated/${currentSessionId}_${filename}`;
  const version = char._img_version || 0;
  imgElement.src = srcPath + "?t=" + version;

  imgElement.onload = () => {
    imgElement.style.display = "block";
    defaultSpan.style.display = "none";
  };

  imgElement.onerror = () => {
    imgElement.style.display = "none";
    defaultSpan.style.display = "block";

    // Auto-generate avatar if loading fails and not already tried in this run
    if (!window.autoGeneratedAvatars) {
      window.autoGeneratedAvatars = new Set();
    }
    const charId = char.character_id || char.name;
    if (charId && !window.autoGeneratedAvatars.has(charId)) {
      window.autoGeneratedAvatars.add(charId);
      console.log(`Auto-generating avatar in background for character: ${charId}`);
      (async () => {
        try {
          const url = `${getApiBase()}/game/rpg/image/refresh-character?session_id=${encodeURIComponent(currentSessionId)}&character_id=${encodeURIComponent(charId)}`;
          const res = await rpgFetch(url, { method: "POST" });
          if (res && res.success) {
            char._img_version = Date.now();
            setupAvatarDisplay(imgElement, defaultSpan, char);
          }
        } catch (err) {
          console.error("Failed to auto-generate character avatar:", err);
        }
      })();
    }
  };
}

// ── PLAY STATE RENDERING ─────────────────────────────────────────────────────

const skillDescriptions = {
  // Hoshiguma
  "Ma thần bất diệt": "Khi gục ngã lần đầu, tự động kích hoạt hồi sinh sau 8 lượt. Bị hủy nếu nhận sát thương trong lúc chờ.",
  "Võ sĩ đạo": "Kích hoạt 1 lần duy nhất: Chuyển toàn bộ chỉ số phòng thủ (DEF) thành lượng máu tối đa (Max HP) tương đương.",
  "Hoả liên trảm quỷ": "Chém 6 nhát kiếm lửa cuồng bạo lên kẻ địch, đồng thời kích hoạt trạng thái Bất Tử trong lượt này.",

  // VinaVictoria
  "Hoàng đế": "Tăng +5% chỉ số cơ bản cho bản thân với mỗi đồng hành còn sống trong đội hình chính (tối đa +15%).",
  "Sư tử hống": "Phát ra tiếng gầm uy nghiêm gây sát thương vật lý và có tỷ lệ làm choáng kẻ địch.",
  "Phán quyết cuối cùng": "Tấn công phép bùng nổ gây sát thương lớn và áp dụng trạng thái Yếu Đuối lên kẻ địch.",

  // Royalty
  "Chiến tích hoàng gia": "Khi tử trận, Royalty lập tức giảm 2 lượt thời gian hồi chiêu cho toàn bộ đồng đội còn sống.",
  "Phong tước": "Chỉ dùng 1 lần duy nhất: Hiến tế 50% HP của bản thân để làm mới hoàn toàn thời gian hồi chiêu của 1 đồng minh chỉ định.",

  // Lemuen
  "Truy nã": "Khi không thực hiện tấn công và không chịu sát thương trong lượt, tự động tích lũy thêm 1 viên đạn truy nã (tối đa 5).",
  "Khóa mục tiêu": "Khởi động và bắn ngay 1 viên đạn truy nã. Mỗi lượt kế tiếp tự động bắn 1 viên vào đầu lượt mà không cần điều kiện (đến khi hết đạn).",
  "Khai hoả toàn diện": "Tiêu hao toàn bộ đạn tích lũy để dội bão tên lửa gồm nhiều viên đạn liên tiếp vào kẻ địch.",

  // Devil
  "Ngạ Quỷ": "Nếu không hành động hoặc không chịu đòn trong lượt, hồi phục 5% HP đã mất.",
  "Hấp thụ": "Hút 15% HP của mục tiêu (đồng minh hoặc kẻ địch) để hồi phục cho bản thân.",
  "Huyết quỷ thuật": "Rút 20% HP hiện tại của đồng đội và 30% HP của bản thân để tạo ra quả cầu máu gây sát thương cực lớn lên kẻ địch.",

  // Elf
  "Uyển chuyển": "Tăng khả năng né tránh, có 20% cơ hội né hoàn toàn các đòn tấn công cơ bản từ kẻ địch.",
  "Mưa tên": "Tăng 20% tốc độ (SPD) và bắn liên hoàn từ 2-5 mũi tên chuẩn vào kẻ địch. Nhận trạng thái Sơ Hở (+20% sát thương nhận vào) trong lượt.",

  // Angel
  "Hộ vệ thiên sứ": "Hồi sinh một đồng đội (trừ Hoshiguma) khi họ lần đầu tiên về 0 HP trong trận chiến, phục hồi 5% HP tối đa. Kích hoạt 1 lần duy nhất.",
  "Lá chắn": "Tạo Lá Chắn bảo vệ Angel và 1 đồng minh chỉ định trong 2 lượt (lượt này và lượt sau), chặn hoàn toàn sát thương 1 lần.",
  "Thiên lôi": "Triệu hồi sấm sét giáng xuống gây sát thương chuẩn và có 30% cơ hội làm Tê Liệt kẻ địch."
};

function showCharacterDetails(char, isCombat) {
  const modal = document.getElementById("rpgCharDetailsModal");
  if (!modal) return;

  // 1. Details header & Avatar setup
  document.getElementById("rpgDetailsCharIcon").textContent = getRaceEmoji(char.race, char.name);
  document.getElementById("rpgDetailsCharRarity").textContent = getRarityLabel(char.rarity);
  document.getElementById("rpgDetailsCharRarity").className = `eyebrow rpg-text-${char.rarity}`;
  document.getElementById("rpgDetailsCharName").textContent = char.name;

  if (isBossCharacter(char)) {
    document.getElementById("rpgDetailsCharSub").textContent = `Lv.${char.level} - Tộc: Bí ẩn - Lớp: Bí ẩn`;
  } else {
    document.getElementById("rpgDetailsCharSub").textContent = `Lv.${char.level} - Tộc: ${char.race} - Lớp: ${char.char_class}`;
  }

  const specEl = document.getElementById("rpgDetailsSpecialIndicators");
  if (specEl) {
    specEl.innerHTML = renderSpecialSkillsIndicators(char);
  }

  const imgElement = document.getElementById("rpgDetailsCharAvatarImg");
  const defaultSpan = document.getElementById("rpgDetailsCharAvatarDefault");
  const toggleBtn = document.getElementById("rpgDetailsCharToggleBtn");
  const refreshBtn = document.getElementById("rpgDetailsCharRefreshBtn");
  const avatarLoading = document.getElementById("rpgDetailsCharAvatarLoading");

  setupAvatarDisplay(imgElement, defaultSpan, char);

  const prefKey = `show_img_${char.character_id || char.name}`;
  const showImg = localStorage.getItem(prefKey) !== "false";
  toggleBtn.textContent = showImg ? "👁️ Tắt ảnh" : "👁️ Hiện ảnh";

  if (avatarLoading) avatarLoading.classList.add("hidden");

  toggleBtn.onclick = (e) => {
    e.stopPropagation();
    const currentlyShown = localStorage.getItem(prefKey) !== "false";
    localStorage.setItem(prefKey, currentlyShown ? "false" : "true");
    toggleBtn.textContent = !currentlyShown ? "👁️ Tắt ảnh" : "👁️ Hiện ảnh";
    setupAvatarDisplay(imgElement, defaultSpan, char);
  };

  refreshBtn.onclick = async (e) => {
    e.stopPropagation();
    if (avatarLoading) avatarLoading.classList.remove("hidden");
    try {
      const url = `${getApiBase()}/game/rpg/image/refresh-character?session_id=${encodeURIComponent(currentSessionId)}&character_id=${encodeURIComponent(char.character_id || char.name)}`;
      const res = await rpgFetch(url, { method: "POST" });
      if (res && res.success) {
        char._img_version = Date.now();
        localStorage.setItem(prefKey, "true");
        toggleBtn.textContent = "👁️ Tắt ảnh";
        setupAvatarDisplay(imgElement, defaultSpan, char);
      } else {
        alert("Làm mới ảnh thất bại từ backend.");
      }
    } catch (err) {
      console.error(err);
      alert("Lỗi kết nối sinh ảnh: " + err.message);
    } finally {
      if (avatarLoading) avatarLoading.classList.add("hidden");
    }
  };

  // 2. Stats
  let conditionText = "Bình thường";
  let conditionStyle = "color:#2ecc71;";
  if (char.stats.hp <= 0) {
    conditionText = "Tử trận";
    conditionStyle = "color:#e74c3c;";
  } else {
    const activeDebuffs = char.debuffs || [];
    if (activeDebuffs.length > 0) {
      conditionText = activeDebuffs.map(d => d.name).join(", ");
      conditionStyle = "color:#e67e22;";
    }
  }
  document.getElementById("rpgDetailsStatCondition").textContent = conditionText;
  document.getElementById("rpgDetailsStatCondition").setAttribute("style", `text-align: right; font-weight: bold; ${conditionStyle}`);

  document.getElementById("rpgDetailsStatHp").textContent = `${char.stats.hp}/${char.stats.max_hp}`;
  document.getElementById("rpgDetailsStatAtk").textContent = char.stats.atk;
  document.getElementById("rpgDetailsStatDef").textContent = `${char.stats.defense}%`;
  document.getElementById("rpgDetailsStatRes").textContent = char.stats.res;
  document.getElementById("rpgDetailsStatResDef").textContent = `${char.stats.res_def}%`;
  document.getElementById("rpgDetailsStatAtkSpd").textContent = char.stats.atk_spd;

  const envDisplay = document.getElementById("rpgDetailsEnv");
  const regDisplay = document.getElementById("rpgDetailsRegion");
  if (envDisplay) {
    envDisplay.textContent = (gameState && gameState.environment) ? gameState.environment : "Chưa xác định";
  }
  if (regDisplay) {
    regDisplay.textContent = (gameState && gameState.current_region) ? gameState.current_region : "Hoang dã";
  }

  // 3. Equipment
  const weapon = char.equipment ? char.equipment.weapon : null;
  const armor = char.equipment ? char.equipment.armor : null;

  const weaponEl = document.getElementById("rpgDetailsEquipWeapon");
  if (weapon) {
    weaponEl.textContent = weapon.name;
    weaponEl.className = `rpg-text-${weapon.rarity}`;
  } else {
    weaponEl.textContent = "Trống";
    weaponEl.className = "rpg-text-Common";
  }

  const armorEl = document.getElementById("rpgDetailsEquipArmor");
  if (armor) {
    armorEl.textContent = armor.name;
    armorEl.className = `rpg-text-${armor.rarity}`;
  } else {
    armorEl.textContent = "Trống";
    armorEl.className = "rpg-text-Common";
  }

  // 4. Skills & Cooldowns/Durations
  const skills = char.special_skills || {};

  const renderSkillInfo = (elementId, label, name, descKey, cd, cdMax, isActive, activeDuration) => {
    const container = document.getElementById(elementId);
    if (!container) return;

    const nameEl = container.querySelector(".skill-name");
    const descEl = container.querySelector(".skill-desc");

    if (name) {
      let statusStr = "";
      if (isCombat) {
        if (cd > 0) {
          statusStr = ` (Đang hồi: ${cd} lượt)`;
        } else if (isActive) {
          statusStr = activeDuration !== null && activeDuration !== undefined ? ` (Đang kích hoạt: còn ${activeDuration} lượt)` : ` (Đang kích hoạt)`;
        } else {
          statusStr = ` (Sẵn sàng)`;
        }
      } else {
        statusStr = ` (Sẵn sàng)`;
      }
      nameEl.textContent = name + statusStr;
      descEl.textContent = skillDescriptions[name] || "Không có mô tả.";
      container.style.display = "block";
    } else {
      nameEl.textContent = "Chưa mở";
      descEl.textContent = "";
      container.style.display = "none";
    }
  };

  // Passive
  const passiveName = skills.passive_skill;
  let passiveIsActive = isCombat && skills.passive_activated;
  let passiveDurationText = null;
  if (passiveName === "Ma thần bất diệt" && isCombat && skills.hoshi_passive_countdown > 0) {
    passiveDurationText = `${skills.hoshi_passive_countdown} lượt để hồi sinh`;
  }
  renderSkillInfo(
    "rpgDetailsSkillPassive",
    "Nội Tại",
    passiveName,
    passiveName,
    0,
    0,
    passiveIsActive,
    passiveDurationText
  );

  // Skill 1
  const skill1Name = skills.skill_1;
  const s1cd = skills.skill_1_countdown || 0;
  const s1Active = skills.skill_1_activating || skills.skill_1_activated || false;
  let s1Duration = null;
  if (skill1Name === "Khóa mục tiêu" && isCombat && skills.skill_1_activating) {
    s1Duration = char.special_skills.bullet_count;
  }
  renderSkillInfo(
    "rpgDetailsSkill1",
    "Kỹ Năng 1",
    skill1Name,
    skill1Name,
    s1cd,
    5,
    s1Active,
    s1Duration
  );

  // Skill 2
  const skill2Name = skills.skill_2;
  const s2cd = skills.skill_2_countdown || 0;
  const s2Active = false;
  renderSkillInfo(
    "rpgDetailsSkill2",
    "Tuyệt Kỹ",
    skill2Name,
    skill2Name,
    s2cd,
    10,
    s2Active,
    null
  );

  // 5. Buffs / Debuffs
  const activeEffectsContainer = document.getElementById("rpgDetailsActiveEffects");
  activeEffectsContainer.innerHTML = "";

  const buffs = char.buffs || [];
  const debuffs = char.debuffs || [];

  if (buffs.length === 0 && debuffs.length === 0) {
    activeEffectsContainer.innerHTML = `<span style="font-size:0.75rem; color:rgba(255,255,255,0.3)">Không có hiệu ứng kích hoạt.</span>`;
  } else {
    buffs.forEach(b => {
      const span = document.createElement("span");
      span.className = "rpg-badge";
      const durationStr = b.duration === null || b.duration === undefined ? "Vĩnh viễn" : `${b.duration} lượt`;
      span.setAttribute("style", "background:#2ecc71; color:#fff; font-size:0.7rem; border-radius:3px; padding:2px 6px;");
      span.textContent = `🛡️ ${b.name} (${durationStr})`;
      activeEffectsContainer.appendChild(span);
    });
    debuffs.forEach(d => {
      const span = document.createElement("span");
      span.className = "rpg-badge";
      const durationStr = d.duration === null || d.duration === undefined ? "Vĩnh viễn" : `${d.duration} lượt`;
      span.setAttribute("style", "background:#e74c3c; color:#fff; font-size:0.7rem; border-radius:3px; padding:2px 6px;");
      span.textContent = `🤢 ${d.name} (${durationStr})`;
      activeEffectsContainer.appendChild(span);
    });
  }

  // Bind close events
  const closeBtn = document.getElementById("rpgCloseCharDetailsBtn");
  const backdrop = document.getElementById("rpgCharDetailsBackdrop");

  const hideDetails = () => {
    modal.classList.add("hidden");
  };

  closeBtn.onclick = hideDetails;
  backdrop.onclick = hideDetails;

  // Show modal
  modal.classList.remove("hidden");
}

function renderState(rpgState) {
  if (!rpgState) return;
  gameState = rpgState;

  // 1. Sidebar - Player Stats Card
  const player = rpgState.player_character;
  if (player) {
    document.getElementById("rpgPlayerNameDisplay").textContent = player.name;
    document.getElementById("rpgPlayerLevel").textContent = `Cấp ${player.level}`;

    // HP Bar
    const hpText = `${player.stats.hp}/${player.stats.max_hp}`;
    document.getElementById("rpgPlayerHpText").textContent = hpText;
    const hpPercent = Math.max(0, Math.min(100, (player.stats.hp / player.stats.max_hp) * 100));
    document.getElementById("rpgPlayerHpBar").style.width = `${hpPercent}%`;

    // Stats Grid
    document.getElementById("rpgPlayerAtk").textContent = player.stats.atk;
    document.getElementById("rpgPlayerDef").textContent = `${player.stats.defense}%`;
    document.getElementById("rpgPlayerRes").textContent = player.stats.res;
    document.getElementById("rpgPlayerMdef").textContent = `${player.stats.res_def}%`;
    document.getElementById("rpgPlayerSpd").textContent = player.stats.atk_spd;
    document.getElementById("rpgPlayerExp").textContent = `${player.exp}/${player.level}`;

    // Equipment Slots
    renderEquipSlot("rpgEquipWeapon", player.equipment.weapon, "Weapon", player.character_id);
    renderEquipSlot("rpgEquipArmor", player.equipment.armor, "Armor", player.character_id);

    // Bind details click
    const playerDetailsBtn = document.getElementById("rpgPlayerDetailsBtn");
    if (playerDetailsBtn) {
      playerDetailsBtn.onclick = () => {
        showCharacterDetails(player, false);
      };
    }
  }

  // Update Location Info in Sidebar
  const envDisplay = document.getElementById("rpgCurrentEnvironmentDisplay");
  const regDisplay = document.getElementById("rpgCurrentRegionDisplay");
  if (envDisplay) {
    envDisplay.textContent = rpgState.environment || "Chưa xác định";
  }
  if (regDisplay) {
    regDisplay.textContent = rpgState.current_region || "Hoang dã";
  }

  const leaveRegionBtn = document.getElementById("rpgLeaveRegionBtn");
  if (leaveRegionBtn) {
    const isInRegion = !!rpgState.current_region;
    const isInDungeon = !!(rpgState.dungeon_state && rpgState.dungeon_state.active);
    const isInCombat = !!(rpgState.combat && rpgState.combat.is_active);
    if (isInRegion && !isInDungeon && !isInCombat) {
      leaveRegionBtn.style.display = "inline-block";
    } else {
      leaveRegionBtn.style.display = "none";
    }
  }

  // 2. Sidebar - Party List (Active companions other than player)
  const partyList = document.getElementById("rpgPartyList");
  partyList.innerHTML = "";
  const companions = rpgState.party.active.filter(c => c.character_id !== player.character_id);

  if (companions.length === 0) {
    partyList.innerHTML = `<p style="font-size:0.8rem;color:rgba(255,255,255,0.3);text-align:center;padding:10px 0;margin:0;">Chưa tuyển mộ đồng hành</p>`;
  } else {
    companions.forEach(c => {
      const hpPercent = Math.max(0, Math.min(100, (c.stats.hp / c.stats.max_hp) * 100));
      const card = document.createElement("div");
      card.className = "party-card-compact";
      card.innerHTML = `
        <div class="party-avatar-circle" title="${c.race} ${c.char_class}" style="position: relative; overflow: hidden; width: 32px; height: 32px; display: flex; align-items: center; justify-content: center; border-radius: 50%;">
          <span class="companion-avatar-default" style="font-size: 1.2rem;">${getRaceEmoji(c.race, c.name)}</span>
          <img class="companion-avatar-img" src="" alt="${c.name}" style="width: 100%; height: 100%; object-fit: cover; display: none; border-radius: 50%;" />
        </div>
        <div class="party-info-compact" style="flex:1;">
          <div style="display:flex; align-items:center; gap:5px;">
            <h4 class="rpg-text-${c.rarity}" style="margin:0; font-size:0.85rem;">${c.name}</h4>
            <button class="ghost-btn rpg-companion-details-btn" data-id="${c.character_id}" type="button" style="padding:0; font-size:0.65rem; border-radius:50%; width:16px; height:16px; display:inline-flex; align-items:center; justify-content:center; border-color:rgba(255,255,255,0.15); color:rgba(255,255,255,0.5); cursor:pointer; flex-shrink:0;" title="Xem chi tiết chỉ số">?</button>
          </div>
          <p style="margin:2px 0 0 0;">Lv.${c.level} - ${c.char_class}</p>
          ${renderSpecialSkillsIndicators(c)}
        </div>
        <div class="party-hp-compact">
          <div class="rpg-hp-label" style="font-size: 0.65rem; margin-bottom: 2px;">
            <span>HP</span>
            <span>${c.stats.hp}/${c.stats.max_hp}</span>
          </div>
          <div class="hp-bar-container" style="height: 4px;">
            <div class="hp-bar" style="width: ${hpPercent}%;"></div>
          </div>
        </div>
      `;

      const defaultSpan = card.querySelector(".companion-avatar-default");
      const imgElement = card.querySelector(".companion-avatar-img");
      setupAvatarDisplay(imgElement, defaultSpan, c);

      card.addEventListener("click", () => showPartyManagementModal());

      const detailsBtn = card.querySelector(".rpg-companion-details-btn");
      if (detailsBtn) {
        detailsBtn.addEventListener("click", (e) => {
          e.stopPropagation(); // Avoid triggering card's click event (which opens party management modal)
          showCharacterDetails(c, false);
        });
      }
      partyList.appendChild(card);
    });
  }

  // 3. Sidebar - Inventory Grid (16 slots)
  const inventoryGrid = document.getElementById("rpgInventoryGrid");
  inventoryGrid.innerHTML = "";
  document.getElementById("rpgGoldText").textContent = rpgState.inventory.gold.toLocaleString();

  const items = rpgState.inventory.items || [];
  for (let i = 0; i < 16; i++) {
    const item = items[i];
    const slot = document.createElement("div");

    if (item) {
      slot.className = `inventory-slot-box has-item rpg-glow-${item.rarity}`;
      slot.innerHTML = `
        ${getItemEmoji(item.item_type, item.name)}
        ${item.quantity > 1 ? `<span class="item-qty">${item.quantity}</span>` : ""}
      `;
      // Interactive Item Hover & Clicks
      slot.addEventListener("mouseenter", (e) => showItemTooltip(item, e));
      slot.addEventListener("mousemove", (e) => updateItemTooltipPosition(e));
      slot.addEventListener("mouseleave", () => hideItemTooltip());
      slot.addEventListener("click", () => {
        hideItemTooltip();
        handleInventoryItemClick(item, i);
      });
    } else {
      slot.className = "inventory-slot-box";
      slot.innerHTML = "";
    }
    inventoryGrid.appendChild(slot);
  }

  // 4. Left Sidebar - NPC Info Panel
  updateLeftNpcPanel(rpgState);

  // 5. Check if Combat is Active
  if (rpgState.combat && rpgState.combat.is_active) {
    showCombatOverlay(rpgState.combat);
  } else {
    hideCombatOverlay();
  }

  // 6. Check if main character is dead (Game Over)
  if (player && player.stats.hp <= 0) {
    triggerGameOver();
  }

  // 7. Update ambient weather overlay
  updateWeatherEffect(rpgState.region);

  // 8. Update Day/Night Cycle and Ambient Shader
  const turn = rpgState.turn_count || 0;
  const timeBadge = document.getElementById("rpgTimeBadge");
  const rpgPage = document.getElementById("rpgPage");

  if (rpgPage) {
    rpgPage.classList.remove("morning", "day", "sunset", "night");
    let timeLabel = "☀️ Trưa";
    if (turn % 4 === 0) {
      rpgPage.classList.add("morning");
      timeLabel = "🌅 Sáng";
    } else if (turn % 4 === 1) {
      rpgPage.classList.add("day");
      timeLabel = "☀️ Trưa";
    } else if (turn % 4 === 2) {
      rpgPage.classList.add("sunset");
      timeLabel = "🌇 Chiều";
    } else {
      rpgPage.classList.add("night");
      timeLabel = "🌙 Tối";
    }
    if (timeBadge) {
      timeBadge.textContent = timeLabel;
    }
  }
}

function renderEquipSlot(elementId, item, slotType, characterId) {
  let oldContainer = document.getElementById(elementId);
  if (!oldContainer) return;

  // Clone to clean previous listeners
  const container = oldContainer.cloneNode(true);
  oldContainer.parentNode.replaceChild(container, oldContainer);

  const titleNode = container.querySelector("span");
  const nameNode = container.querySelector(".equip-name");

  if (item) {
    nameNode.textContent = item.name;
    nameNode.className = `equip-name rpg-text-${item.rarity}`;

    // Add custom tooltip hover listeners
    container.addEventListener("mouseenter", (e) => showItemTooltip(item, e));
    container.addEventListener("mousemove", (e) => updateItemTooltipPosition(e));
    container.addEventListener("mouseleave", () => hideItemTooltip());

    // Unequip on click with confirmation prompt
    container.onclick = async (e) => {
      e.preventDefault();
      hideItemTooltip();
      if (confirm(`Bạn có muốn cởi trang bị ${item.name} không?`)) {
        try {
          const url = `${getApiBase()}/game/rpg/party/unequip?session_id=${encodeURIComponent(currentSessionId)}&character_id=${encodeURIComponent(characterId)}&slot=${slotType}`;
          const res = await rpgFetch(url, { method: "POST" });
          appendLogEntry(`Đã tháo trang bị: ${item.name}`);
          renderState(res.rpg_state);
        } catch (err) {
          alert("Tháo trang bị lỗi: " + err.message);
        }
      }
    };
  } else {
    nameNode.textContent = "Trống";
    nameNode.className = "equip-name";
    container.title = "Trống - Nhấp vào vũ khí/giáp trong hành trang để trang bị";
    container.onclick = null;
  }
}

function updateLeftNpcPanel(rpgState) {
  const panel = document.getElementById("rpgNpcPanel");
  const nameEl = document.getElementById("rpgNpcName");
  const npcIconEl = document.getElementById("rpgNpcIcon");
  const npcImg = document.getElementById("rpgNpcAvatarImg");
  const npcDefault = document.getElementById("rpgNpcAvatarDefault");
  const rarityEl = document.getElementById("rpgNpcRarity");
  const raceEl = document.getElementById("rpgNpcRace");
  const classEl = document.getElementById("rpgNpcClass");
  const descEl = document.getElementById("rpgNpcDescription");

  // Stats rows elements
  const hpEl = document.getElementById("rpgNpcStatHp");
  const atkEl = document.getElementById("rpgNpcStatAtk");
  const resEl = document.getElementById("rpgNpcStatRes");
  const defEl = document.getElementById("rpgNpcStatDef");
  const mdefEl = document.getElementById("rpgNpcStatMdef");
  const spdEl = document.getElementById("rpgNpcStatSpd");

  let npc = null;

  if (rpgState.combat && rpgState.combat.is_active && rpgState.combat.enemy) {
    npc = rpgState.combat.enemy;
  } else if (rpgState.current_event === "stranger" && rpgState.current_stranger) {
    npc = rpgState.current_stranger;
  } else if (rpgState.current_event === "merchant" && rpgState.current_merchant) {
    npc = rpgState.current_merchant;
  } else if (rpgState.current_event === "monk" && rpgState.current_monk) {
    npc = rpgState.current_monk;
  }

  const container = document.querySelector(".rpg-grid-container");
  if (container && (rpgState.combat?.is_active || rpgState.current_event === "stranger")) {
    container.classList.remove("npc-hidden");
  }

  if (npc) {
    nameEl.textContent = npc.name;
    nameEl.className = `rpg-text-${npc.rarity}`;
    if (npcIconEl) npcIconEl.textContent = getRaceEmoji(npc.race);
    setupAvatarDisplay(npcImg, npcDefault, npc);

    if (npc.character_id && npc.character_id.startsWith("merchant")) {
      rarityEl.textContent = "Thương Nhân";
      rarityEl.className = "rpg-badge rarity";
    } else if (npc.character_id && npc.character_id.startsWith("monk")) {
      rarityEl.textContent = "Tu Sĩ";
      rarityEl.className = "rpg-badge rarity";
    } else {
      rarityEl.textContent = getRarityLabel(npc.rarity);
      rarityEl.className = `rpg-badge rarity rpg-glow-${npc.rarity} rpg-text-${npc.rarity}`;
    }

    raceEl.textContent = npc.race;
    classEl.textContent = npc.char_class;

    if (npc.character_id && npc.character_id.startsWith("merchant")) {
      descEl.textContent = "Một thương nhân bí hiểm đang bày bán trang bị quý hiếm và chào mời lính đánh thuê gia nhập.";
    } else if (npc.character_id && npc.character_id.startsWith("monk")) {
      descEl.textContent = "Vị ẩn giả mang trong mình thánh lực, sẵn sàng ban phước phục hồi cho lữ khách.";
    } else {
      descEl.textContent = npc.condition === "Bình thường"
        ? `Một thực thể thuộc tộc ${npc.race}, đảm nhận vai trò ${npc.char_class}. Trạng thái chiến đấu tốt.`
        : `Thực thể này đang ${npc.condition}. Hãy cẩn trọng.`;
    }

    hpEl.textContent = `${npc.stats.hp}/${npc.stats.max_hp}`;
    atkEl.textContent = npc.stats.atk;
    resEl.textContent = npc.stats.res;
    defEl.textContent = `${npc.stats.defense}%`;
    mdefEl.textContent = `${npc.stats.res_def}%`;
    spdEl.textContent = npc.stats.atk_spd;
  } else {
    // Standard Merchant event details
    if (rpgState.current_event === "merchant") {
      nameEl.textContent = "Thương Nhân Lang Thang";
      nameEl.className = "";
      if (npcIconEl) npcIconEl.textContent = "🛒";
      setupAvatarDisplay(npcImg, npcDefault, rpgState.current_merchant);
      rarityEl.textContent = "Thương Nhân";
      rarityEl.className = "rpg-badge rarity";
      raceEl.textContent = "-";
      classEl.textContent = "-";
      descEl.textContent = "Một thương nhân bí hiểm đang bày bán trang bị quý hiếm và chào mời lính đánh thuê gia nhập.";
    } else if (rpgState.current_event === "monk") {
      nameEl.textContent = "Tu Sĩ Đạo Nhân";
      nameEl.className = "";
      if (npcIconEl) npcIconEl.textContent = "🧘";
      setupAvatarDisplay(npcImg, npcDefault, rpgState.current_monk);
      rarityEl.textContent = "Tu Sĩ";
      rarityEl.className = "rpg-badge rarity";
      raceEl.textContent = "-";
      classEl.textContent = "-";
      descEl.textContent = "Vị ẩn giả mang trong mình thánh lực, sẵn sàng ban phước phục hồi cho lữ khách.";
    } else {
      nameEl.textContent = "Chưa Gặp Gỡ";
      nameEl.className = "";
      if (npcIconEl) npcIconEl.textContent = "❔";
      setupAvatarDisplay(npcImg, npcDefault, null);
      rarityEl.textContent = "-";
      rarityEl.className = "rpg-badge rarity";
      raceEl.textContent = "-";
      classEl.textContent = "-";
      descEl.textContent = "Không có thông tin thực thể hiện tại.";
    }

    hpEl.textContent = "-/-";
    atkEl.textContent = "-";
    resEl.textContent = "-";
    defEl.textContent = "-";
    mdefEl.textContent = "-";
    spdEl.textContent = "-";
  }

  // Cập nhật Quest/Achievement/Dungeon/World Map và triggerBackgroundSeeWorld
  updateQuestAchievementUI(rpgState);
  updateDungeonUI(rpgState);
  updateWorldMapUI(rpgState);

  if (rpgState.environment !== window.lastRpgEnvironment || rpgState.current_region !== window.lastRpgRegion) {
    window.lastRpgEnvironment = rpgState.environment;
    window.lastRpgRegion = rpgState.current_region;
    triggerBackgroundSeeWorld();
  }
}

// ── STORY LOG & CHOICES PANEL ────────────────────────────────────────────────

async function appendStoryBlock(storyText) {
  const storyLog = document.getElementById("rpgStoryLog");
  if (!storyLog) return;

  const div = document.createElement("div");
  div.className = "story-block-entry";
  div.style.marginBottom = "20px";
  storyLog.appendChild(div);

  const formattedHtml = formatRpgText(storyText);
  await typeTextWordByWord(div, formattedHtml, currentTextSpeed);

  // Smooth scroll final correction
  setTimeout(() => {
    storyLog.scrollTop = storyLog.scrollHeight;
  }, 50);
}

function appendLogEntry(logMsg) {
  const storyLog = document.getElementById("rpgStoryLog");
  if (!storyLog) return;

  const div = document.createElement("div");
  div.className = "event-log-entry";
  div.innerHTML = `📜 <i>${escapeHtml(logMsg)}</i>`;

  storyLog.appendChild(div);

  setTimeout(() => {
    storyLog.scrollTop = storyLog.scrollHeight;
  }, 100);
}

function renderChoices(choices = [], eventType = null) {
  const choicesBox = document.getElementById("rpgChoicesBox");
  const composerPanel = document.getElementById("rpgComposerPanel");

  if (!choicesBox) return;
  choicesBox.innerHTML = "";

  // If there's an event active, hide composer text prompt box to avoid breaking deterministic flow
  if (eventType && eventType !== "normal") {
    if (composerPanel) composerPanel.classList.add("hidden");
  } else {
    if (composerPanel) composerPanel.classList.remove("hidden");
  }

  if (choices.length === 0) {
    choicesBox.innerHTML = `<p style="font-size:0.86rem;color:rgba(255,255,255,0.3);padding:8px 0;">Không có lựa chọn nào tiếp theo.</p>`;
    return;
  }

  const triggers = [
    "Đi đến gặp tu sĩ",
    "Đi đến gặp thương nhân",
    "Đi đến gặp kẻ lạ mặt",
    "Đi đến gặp kẻ lạ mặt từ xa",
    "Thu thập vật phẩm cho vào túi",
    "Tiến vào sâu bên trong để khám phá Dungeon"
  ];

  choices.forEach((choice, index) => {
    const btn = document.createElement("button");
    btn.type = "button";
    btn.className = "rpg-choice-btn";

    // Highlight Red border for special event trigger choices
    const isSpecial = index === 0 && triggers.includes(choice);
    // Highlight Green border for region exploration choices
    let isRegion = false;
    if (index === 0 && gameState && gameState.offered_event) {
      if (gameState.offered_event.startsWith("region:")) {
        const regName = gameState.offered_event.substring(7);
        if (choice === `Khám phá ${regName}`) {
          isRegion = true;
        }
      } else if (gameState.offered_event.startsWith("dungeon:")) {
        const dunName = gameState.offered_event.substring(8);
        if (choice === `Tiến vào hầm ngục ${dunName}`) {
          isRegion = true;
        }
      }
    }

    if (isSpecial) {
      btn.classList.add("special-event-trigger");
    } else if (isRegion) {
      btn.classList.add("region-event-trigger");
    }

    btn.innerHTML = `
      <span class="choice-bullet">${isSpecial ? "⚡" : (isRegion ? "🗺️" : `${index + 1}.`)}</span>
      <span class="choice-text">${escapeHtml(choice)}</span>
    `;

    btn.addEventListener("click", () => handleChoiceClick(index, choice, eventType));
    choicesBox.appendChild(btn);
  });
}

async function handleChoiceClick(choiceIndex, choiceText, eventType) {
  disableChoiceButtons(true);

  // Print user's decision into the story log
  appendStoryBlock(`Lựa chọn: ${choiceText}`);

  try {
    let res;

    // If inside a special event, trigger specialized API route
    if (eventType && eventType !== "normal") {
      let endpoint = "";
      if (eventType === "monk") endpoint = "/game/rpg/event/monk/action";
      else if (eventType === "merchant") endpoint = "/game/rpg/event/merchant/action";
      else if (eventType === "stranger") endpoint = "/game/rpg/event/stranger/action";
      else if (eventType === "item") endpoint = "/game/rpg/event/item/action";

      res = await rpgFetch(`${getApiBase()}${endpoint}`, {
        method: "POST",
        body: JSON.stringify({
          session_id: currentSessionId,
          action: choiceText
        })
      });

      // Auto open Merchant shop popup if choice is viewing shop
      if (eventType === "merchant" && choiceIndex === 1) {
        showShopModal();
      }
    } else {
      // Normal turn choice routing
      res = await rpgFetch(`${getApiBase()}/game/rpg/turn`, {
        method: "POST",
        body: JSON.stringify({
          session_id: currentSessionId,
          choice_index: choiceIndex
        })
      });
    }

    // Process narrative results
    appendStoryBlock(res.story);
    checkEndingConditions(res.story);
    renderChoices(res.choices, res.event_type);
    renderState(res.rpg_state);
    updatePointsDisplay();

  } catch (err) {
    alert("Thực thi lựa chọn lỗi: " + err.message);
    disableChoiceButtons(false);
  }
}

function disableChoiceButtons(disabled) {
  const buttons = document.querySelectorAll(".rpg-choice-btn");
  buttons.forEach(btn => btn.disabled = disabled);
}

// ── CUSTOM TEXT PROMPT INPUT ────────────────────────────────────────────────

function initRpgComposer() {
  const submitBtn = document.getElementById("rpgSubmitBtn");
  const textarea = document.getElementById("rpgCustomAction");

  if (submitBtn && textarea) {
    submitBtn.addEventListener("click", async () => {
      const text = textarea.value.trim();
      if (!text) return;

      const wordsTargetInput = document.getElementById("rpgTurnTargetWords");
      const targetWordsValue = wordsTargetInput ? parseInt(wordsTargetInput.value) : 600;

      textarea.value = "";
      submitBtn.disabled = true;
      disableChoiceButtons(true);

      appendStoryBlock(`Hành động: ${text}`);

      try {
        const res = await rpgFetch(`${getApiBase()}/game/rpg/turn/prompt`, {
          method: "POST",
          body: JSON.stringify({
            session_id: currentSessionId,
            player_input: text,
            target_words: targetWordsValue
          })
        });

        appendStoryBlock(res.story);
        checkEndingConditions(res.story);
        renderChoices(res.choices, res.event_type);
        renderState(res.rpg_state);
        updatePointsDisplay();

      } catch (err) {
        alert("Gửi hành động thất bại: " + err.message);
      } finally {
        submitBtn.disabled = false;
      }
    });
  }
}

// ── INVENTORY ITEM CLICKS & EQUIPPING ────────────────────────────────────────

function handleInventoryItemClick(item, itemIndex) {
  // If merchant shop is open, sell item immediately
  const shopModal = document.getElementById("rpgShopModal");
  if (shopModal && !shopModal.classList.contains("hidden")) {
    sellItemPrompt(item);
    return;
  }

  if (item.name && item.name.startsWith("Mảnh vỡ chìa khoá vĩ đại ")) {
    const confirmUse = confirm("Bạn có muốn kết hợp 7 mảnh vỡ để rèn thành [Chìa khoá Hư Không vĩ đại]?");
    if (!confirmUse) return;

    (async () => {
      try {
        const res = await rpgFetch(`${getApiBase()}/game/rpg/inventory/use`, {
          method: "POST",
          body: JSON.stringify({
            session_id: currentSessionId,
            character_id: "",
            item_id: item.item_id
          })
        });
        alert(res.message);
        renderState(res.rpg_state);
        if (res.rpg_state && res.rpg_state.combat && res.rpg_state.combat.is_active) {
          showCombatOverlay(res.rpg_state.combat);
        }
      } catch (err) {
        alert("Lỗi rèn chìa khóa: " + err.message);
      }
    })();
    return;
  }

  if (item.name === "Chìa khoá Hư Không vĩ đại") {
    const confirmUse = confirm("Bạn có muốn sử dụng [Chìa khoá Hư Không vĩ đại] mở Cánh Cổng Hư Không tiến vào khiêu chiến Final BOSS ALPHA?");
    if (!confirmUse) return;

    (async () => {
      try {
        const res = await rpgFetch(`${getApiBase()}/game/rpg/inventory/use`, {
          method: "POST",
          body: JSON.stringify({
            session_id: currentSessionId,
            character_id: "",
            item_id: item.item_id
          })
        });
        alert(res.message);
        renderState(res.rpg_state);
        if (res.rpg_state && res.rpg_state.combat && res.rpg_state.combat.is_active) {
          showCombatOverlay(res.rpg_state.combat);
        }
      } catch (err) {
        alert("Lỗi mở cổng hư không: " + err.message);
      }
    })();
    return;
  }

  // Open item action popup depending on weapon/armor or consume
  const targetChars = gameState.party.active;

  if (item.item_type === "Weapon" || item.item_type === "Armor") {
    // Show quick target modal selector to equip item
    showTargetSelector(item.name, "Trang bị vật phẩm", targetChars, async (charId) => {
      try {
        const res = await rpgFetch(`${getApiBase()}/game/rpg/party/equip`, {
          method: "POST",
          body: JSON.stringify({
            session_id: currentSessionId,
            character_id: charId,
            item_id: item.item_id
          })
        });
        const targetName = targetChars.find(c => c.character_id === charId)?.name || "Đồng minh";
        appendLogEntry(`Đã trang bị ${item.name} cho ${targetName}`);
        renderState(res.rpg_state);
      } catch (err) {
        alert("Trang bị lỗi: " + err.message);
      }
    });
  } else if (item.item_type === "Consume" || item.item_type === "Consumable") {
    // Show quick target selector to use consumable item
    showTargetSelector(item.name, "Sử dụng vật phẩm", targetChars, async (charId) => {
      try {
        const res = await rpgFetch(`${getApiBase()}/game/rpg/inventory/use`, {
          method: "POST",
          body: JSON.stringify({
            session_id: currentSessionId,
            character_id: charId,
            item_id: item.item_id
          })
        });
        const targetName = targetChars.find(c => c.character_id === charId)?.name || "Đồng minh";
        appendLogEntry(`Đã sử dụng ${item.name} cho ${targetName}`);
        renderState(res.rpg_state);
      } catch (err) {
        alert("Sử dụng vật phẩm lỗi: " + err.message);
      }
    });
  }
}

// Quick modal utility to select target character (built dynamically)
function showTargetSelector(itemName, headerText, characters, onSelect) {
  // Check if selector overlay already exists, delete it first
  const existing = document.getElementById("rpgTargetSelectorOverlay");
  if (existing) existing.remove();

  const overlay = document.createElement("div");
  overlay.id = "rpgTargetSelectorOverlay";
  overlay.className = "rpg-modal";
  overlay.innerHTML = `
    <div class="rpg-modal-backdrop" id="rpgTargetSelectorBackdrop"></div>
    <div class="rpg-modal-panel glass-panel" style="max-width: 400px; text-align: center;">
      <button class="rpg-modal-close" id="rpgCloseTargetSelector">×</button>
      <p class="eyebrow">${headerText}</p>
      <h3 style="margin: 5px 0 15px 0;">Vật phẩm: ${itemName}</h3>
      <p class="rpg-modal-subtitle" style="margin-bottom: 20px;">Chọn một thành viên đội hình:</p>
      <div id="targetCharsList" style="display: flex; flex-direction: column; gap: 10px;"></div>
    </div>
  `;

  document.body.appendChild(overlay);

  const listContainer = overlay.querySelector("#targetCharsList");
  characters.forEach(c => {
    const btn = document.createElement("button");
    btn.type = "button";
    btn.className = "primary-btn";
    btn.style.width = "100%";
    btn.style.textAlign = "left";
    btn.style.display = "flex";
    btn.style.justifyContent = "space-between";
    btn.innerHTML = `
      <span>${getRaceEmoji(c.race, c.name)} ${c.name} (${c.char_class})</span>
      <strong>HP: ${c.stats.hp}/${c.stats.max_hp}</strong>
    `;
    btn.addEventListener("click", () => {
      onSelect(c.character_id);
      overlay.remove();
    });
    listContainer.appendChild(btn);
  });

  // Closers
  overlay.querySelector("#rpgCloseTargetSelector").addEventListener("click", () => overlay.remove());
  overlay.querySelector("#rpgTargetSelectorBackdrop").addEventListener("click", () => overlay.remove());
}

// ── SHOP MODAL CONTROLLERS ───────────────────────────────────────────────────

function initShopController() {
  document.getElementById("rpgCloseShopBtn").addEventListener("click", hideShopModal);
  document.getElementById("rpgShopBackdrop").addEventListener("click", hideShopModal);

  // Open sell modal
  document.getElementById("rpgSellDropArea").addEventListener("click", () => {
    showSellModal();
  });

  // Sell modal closing handlers
  document.getElementById("rpgCloseSellBtn").addEventListener("click", hideSellModal);
  document.getElementById("rpgSellBackdrop").addEventListener("click", hideSellModal);
  document.getElementById("rpgSellModalCloseBtn").addEventListener("click", hideSellModal);

  // Shop Upgrade
  document.getElementById("rpgUpgradeShopBtn").addEventListener("click", async () => {
    try {
      const res = await rpgFetch(`${getApiBase()}/game/rpg/shop/upgrade?session_id=${encodeURIComponent(currentSessionId)}`, {
        method: "POST"
      });
      appendLogEntry("Đã nâng cấp Quầy Hàng lên cấp tiếp theo!");
      renderState(res.rpg_state);
      renderShopGrids(res.shop, res.inventory);
    } catch (err) {
      alert("Nâng cấp quầy hàng lỗi: " + err.message);
    }
  });

  // Shop Refresh
  document.getElementById("rpgRefreshShopBtn").addEventListener("click", async () => {
    try {
      const res = await rpgFetch(`${getApiBase()}/game/rpg/shop/refresh?session_id=${encodeURIComponent(currentSessionId)}`, {
        method: "POST"
      });
      appendLogEntry("Đã làm mới danh mục hàng hoá của Shop (Tốn 5 Vàng)");
      renderState(res.rpg_state);
      renderShopGrids(res.shop, res.inventory);
    } catch (err) {
      alert("Làm mới quầy hàng lỗi: " + err.message);
    }
  });
}

function showShopModal() {
  const shopModal = document.getElementById("rpgShopModal");
  if (!shopModal) return;

  shopModal.classList.remove("hidden");
  document.body.classList.add("rpg-shop-open");

  if (gameState && gameState.shop) {
    renderShopGrids(gameState.shop, gameState.inventory);
  }
}

function hideShopModal() {
  const shopModal = document.getElementById("rpgShopModal");
  if (shopModal) {
    shopModal.classList.add("hidden");
  }
  document.body.classList.remove("rpg-shop-open");
  // Also hide the sell modal if it was open
  hideSellModal();
}

function showSellModal() {
  const sellModal = document.getElementById("rpgSellModal");
  if (!sellModal) return;

  sellModal.classList.remove("hidden");
  renderSellModalGrid();
}

function hideSellModal() {
  const sellModal = document.getElementById("rpgSellModal");
  if (sellModal) {
    sellModal.classList.add("hidden");
  }
}

function renderSellModalGrid() {
  const sellListGrid = document.getElementById("rpgSellListGrid");
  if (!sellListGrid) return;
  sellListGrid.innerHTML = "";

  const inventory = gameState ? gameState.inventory : null;
  const items = inventory ? (inventory.items || []) : [];

  if (items.length === 0) {
    sellListGrid.innerHTML = `<p style="font-size:0.86rem;color:rgba(255,255,255,0.3);grid-column: 1 / -1;text-align:center;padding:20px;">Hành lý của bạn trống rỗng.</p>`;
    return;
  }

  items.forEach((item, index) => {
    const sellPrices = { "Mythic": 400, "Legendary": 300, "Epic": 200, "Rare": 90, "Uncommon": 50, "Common": 10 };
    const price = sellPrices[item.rarity] || 5;
    const card = document.createElement("div");
    card.className = "shop-card";
    card.innerHTML = `
      <h4 class="rpg-text-${item.rarity}">${getItemEmoji(item.item_type, item.name)} ${item.name} ${item.quantity > 1 ? `(x${item.quantity})` : ""}</h4>
      <p style="margin: 4px 0;">${item.description || "Bán vật phẩm này."}</p>
      <div class="shop-card-price" style="margin-bottom: 8px;">💰 Giá bán: ${price} Vàng</div>
      <button class="primary-btn shop-card-sell-btn" style="background:#e74c3c; border:none; box-shadow:0 4px 10px rgba(231,76,60,0.2); width:100%;">Bán</button>
    `;
    card.querySelector("button").addEventListener("click", () => sellItemPrompt(item));
    sellListGrid.appendChild(card);
  });
}

function renderShopGrids(shop, inventory) {
  // Update badges
  document.getElementById("rpgShopLevel").textContent = shop.level;

  // Calculate costs based on level
  const upgradeCosts = { 1: 25, 2: 60, 3: 90, 4: 100, 5: 120 };
  const cost = upgradeCosts[shop.level];
  const upgradeBtn = document.getElementById("rpgUpgradeShopBtn");

  if (cost) {
    document.getElementById("rpgUpgradeCost").textContent = cost;
    upgradeBtn.disabled = inventory.gold < cost;
    upgradeBtn.style.display = "block";
  } else {
    upgradeBtn.style.display = "none"; // Max level 6
  }

  // Disable refresh if not enough gold
  document.getElementById("rpgRefreshShopBtn").disabled = inventory.gold < 5;

  // Grid populators
  const itemsGrid = document.getElementById("rpgShopItemsGrid");
  const mercsGrid = document.getElementById("rpgShopMercsGrid");
  itemsGrid.innerHTML = "";
  mercsGrid.innerHTML = "";

  const buyPrices = { "Mythic": 500, "Legendary": 400, "Epic": 300, "Rare": 150, "Uncommon": 80, "Common": 30 };
  const mercPrices = { "Mythic": 3999, "Legendary": 600, "Epic": 400, "Rare": 200, "Uncommon": 100, "Common": 50 };

  // Populating Items
  const items = shop.items_for_sale || [];
  if (items.length === 0) {
    itemsGrid.innerHTML = `<p style="font-size:0.86rem;color:rgba(255,255,255,0.3)">Các kệ hàng vật phẩm đã trống.</p>`;
  } else {
    items.forEach((item, index) => {
      const price = buyPrices[item.rarity] || 50;
      const card = document.createElement("div");
      card.className = "shop-card";
      card.innerHTML = `
        <h4 class="rpg-text-${item.rarity}">${getItemEmoji(item.item_type, item.name)} ${item.name}</h4>
        <p>${item.description || "Tăng chỉ số nhân vật khi trang bị."}</p>
        <div class="shop-card-price">💰 ${price} Vàng</div>
        <button class="primary-btn shop-card-buy-btn" ${inventory.gold < price ? "disabled" : ""}>Mua</button>
      `;
      card.querySelector("button").addEventListener("click", () => buyItem(index, item.name, price));
      itemsGrid.appendChild(card);
    });
  }

  // Populating Mercenaries
  const mercs = shop.mercenaries_for_sale || [];
  if (mercs.length === 0) {
    mercsGrid.innerHTML = `<p style="font-size:0.86rem;color:rgba(255,255,255,0.3)">Không còn lính đánh thuê nào đăng ký.</p>`;
  } else {
    mercs.forEach((merc, index) => {
      const price = mercPrices[merc.rarity] || 100;
      const card = document.createElement("div");
      card.className = "shop-card";
      card.innerHTML = `
        <h4 class="rpg-text-${merc.rarity}">${getRaceEmoji(merc.race)} ${merc.name}</h4>
        <p>Tộc: ${merc.race} | Class: ${merc.char_class}<br>ATK: ${merc.stats.atk} | HP: ${merc.stats.max_hp}</p>
        <div class="shop-card-price">💰 ${price} Vàng</div>
        <button class="primary-btn shop-card-buy-btn" ${inventory.gold < price ? "disabled" : ""}>Thuê</button>
      `;
      card.querySelector("button").addEventListener("click", () => {
        let customName = null;
        if (merc.rarity !== "Mythic") {
          const inputName = prompt(`Nhập tên tùy chọn cho đồng hành ${merc.name} (hoặc để trống để dùng tên mặc định):`, "");
          if (inputName !== null) {
            customName = inputName.trim() || null;
          } else {
            return;
          }
        }
        buyMercenary(index, merc.name, price, customName);
      });
      mercsGrid.appendChild(card);
    });
  }

  // Populating Player Inventory to Sell
  const sellGrid = document.getElementById("rpgShopSellGrid");
  if (sellGrid) {
    sellGrid.innerHTML = "";
    const items = inventory.items || [];
    if (items.length === 0) {
      sellGrid.innerHTML = `<p style="font-size:0.86rem;color:rgba(255,255,255,0.3)">Hành lý của bạn trống rỗng.</p>`;
    } else {
      items.forEach((item, index) => {
        const sellPrices = { "Mythic": 400, "Legendary": 300, "Epic": 200, "Rare": 90, "Uncommon": 50, "Common": 10 };
        const price = sellPrices[item.rarity] || 5;
        const card = document.createElement("div");
        card.className = "shop-card";
        card.innerHTML = `
          <h4 class="rpg-text-${item.rarity}">${getItemEmoji(item.item_type, item.name)} ${item.name} ${item.quantity > 1 ? `(x${item.quantity})` : ""}</h4>
          <p>${item.description || "Nhấp để bán vật phẩm này."}</p>
          <div class="shop-card-price">💰 Giá bán: ${price} Vàng</div>
          <button class="primary-btn shop-card-sell-btn" style="background:#e74c3c; border:none; box-shadow:0 4px 10px rgba(231,76,60,0.2);">Bán</button>
        `;
        card.querySelector("button").addEventListener("click", () => sellItemPrompt(item));
        sellGrid.appendChild(card);
      });
    }
  }
}

async function buyItem(index, itemName, price) {
  try {
    const res = await rpgFetch(`${getApiBase()}/game/rpg/shop/buy-item`, {
      method: "POST",
      body: JSON.stringify({
        session_id: currentSessionId,
        item_index: index
      })
    });
    appendLogEntry(`Đã mua vật phẩm: ${itemName} (-${price} Vàng)`);
    renderState(res.rpg_state);
    renderShopGrids(res.shop, res.inventory);
  } catch (err) {
    alert("Mua vật phẩm thất bại: " + err.message);
  }
}

async function buyMercenary(index, mercName, price, customName = null) {
  try {
    const res = await rpgFetch(`${getApiBase()}/game/rpg/shop/buy-merc`, {
      method: "POST",
      body: JSON.stringify({
        session_id: currentSessionId,
        merc_index: index,
        custom_name: customName
      })
    });
    const displayName = customName ? `${customName} (${mercName})` : mercName;
    appendLogEntry(`Đã tuyển mộ đồng hành mới: ${displayName} (-${price} Vàng)`);
    renderState(res.rpg_state);
    renderShopGrids(res.shop, res.inventory);
  } catch (err) {
    alert("Tuyển đồng hành lỗi: " + err.message);
  }
}

async function sellItemPrompt(item) {
  const sellPrices = { "Mythic": 400, "Legendary": 300, "Epic": 200, "Rare": 90, "Uncommon": 50, "Common": 10 };
  const price = sellPrices[item.rarity] || 5;

  const confirmed = confirm(`Bạn có chắc chắn muốn bán [${item.name}] với giá ${price} Vàng?`);
  if (!confirmed) return;

  try {
    const res = await rpgFetch(`${getApiBase()}/game/rpg/shop/sell-item`, {
      method: "POST",
      body: JSON.stringify({
        session_id: currentSessionId,
        item_id: item.item_id
      })
    });
    appendLogEntry(`Đã bán vật phẩm: ${item.name} (+${price} Vàng)`);
    renderState(res.rpg_state);
    renderShopGrids(res.shop, res.inventory);
    renderSellModalGrid();
  } catch (err) {
    alert("Bán vật phẩm lỗi: " + err.message);
  }
}

// ── PARTY MANAGEMENT MODAL CONTROLLERS ───────────────────────────────────────

function initPartyController() {
  document.getElementById("rpgClosePartyBtn").addEventListener("click", hidePartyManagementModal);
  document.getElementById("rpgPartyBackdrop").addEventListener("click", hidePartyManagementModal);
  document.getElementById("rpgManagePartyBtn").addEventListener("click", showPartyManagementModal);
}

function showPartyManagementModal() {
  const partyModal = document.getElementById("rpgPartyModal");
  if (!partyModal) return;

  partyModal.classList.remove("hidden");
  swapSource = null; // Clear selections
  renderPartyModalGrids();
}

function hidePartyManagementModal() {
  const partyModal = document.getElementById("rpgPartyModal");
  if (partyModal) partyModal.classList.add("hidden");
}

function renderPartyModalGrids() {
  const activeContainer = document.getElementById("rpgActiveSlotsModal");
  const reserveContainer = document.getElementById("rpgReserveSlotsModal");

  activeContainer.innerHTML = "";
  reserveContainer.innerHTML = "";

  if (!gameState) return;

  // Render Active slots (fixed size: 4)
  const activeMembers = gameState.party.active || [];
  for (let i = 0; i < 4; i++) {
    const char = activeMembers[i];
    const slotId = `active_${i}`;
    const box = document.createElement("div");

    if (char) {
      const isPlayer = char.is_player_character;
      box.className = `party-modal-card ${swapSource === slotId ? "active" : ""}`;
      box.innerHTML = `
        <h4 class="rpg-text-${char.rarity}">${getRaceEmoji(char.race)} ${char.name} ${isPlayer ? "(Bạn)" : ""}</h4>
        <p>Cấp ${char.level} - Tộc: ${char.race} - Lớp: ${char.char_class}</p>
        <div style="font-size:0.75rem;opacity:0.8;">ATK: ${char.stats.atk} | HP: ${char.stats.hp}/${char.stats.max_hp}</div>
      `;
      box.addEventListener("click", () => handlePartySlotClick(slotId));
    } else {
      box.className = `party-modal-card empty-slot ${swapSource === slotId ? "active" : ""}`;
      box.innerHTML = `<p style="margin:auto;font-size:0.8rem;color:rgba(255,255,255,0.25);">Khu vực trống</p>`;
      box.addEventListener("click", () => handlePartySlotClick(slotId));
    }
    activeContainer.appendChild(box);
  }

  // Render Reserve slots (fixed size: 5)
  const reserveMembers = gameState.party.reserve || [];
  for (let i = 0; i < 5; i++) {
    const char = reserveMembers[i];
    const slotId = `reserve_${i}`;
    const box = document.createElement("div");

    if (char) {
      box.className = `party-modal-card ${swapSource === slotId ? "active" : ""}`;
      box.innerHTML = `
        <h4 class="rpg-text-${char.rarity}">${getRaceEmoji(char.race)} ${char.name}</h4>
        <p>Cấp ${char.level} - Tộc: ${char.race} - Lớp: ${char.char_class}</p>
        <div style="font-size:0.75rem;opacity:0.8;">ATK: ${char.stats.atk} | HP: ${char.stats.hp}/${char.stats.max_hp}</div>
      `;
      box.addEventListener("click", () => handlePartySlotClick(slotId));
    } else {
      box.className = `party-modal-card empty-slot ${swapSource === slotId ? "active" : ""}`;
      box.innerHTML = `<p style="margin:auto;font-size:0.8rem;color:rgba(255,255,255,0.25);">Dự bị trống</p>`;
      box.addEventListener("click", () => handlePartySlotClick(slotId));
    }
    reserveContainer.appendChild(box);
  }
}

async function handlePartySlotClick(slotId) {
  if (swapSource === null) {
    // Determine if the clicked slot actually has a member to move
    const [section, indexStr] = slotId.split("_");
    const index = parseInt(indexStr);
    const char = section === "active" ? gameState.party.active[index] : gameState.party.reserve[index];

    if (!char) {
      return; // Can't select empty slot as source
    }

    swapSource = slotId;
    renderPartyModalGrids();
  } else {
    // If double clicking the same slot, cancel swap selection
    if (swapSource === slotId) {
      swapSource = null;
      renderPartyModalGrids();
      return;
    }

    // Call swap API
    const fromVal = swapSource;
    const toVal = slotId;
    swapSource = null;

    try {
      const res = await rpgFetch(`${getApiBase()}/game/rpg/party/swap`, {
        method: "POST",
        body: JSON.stringify({
          session_id: currentSessionId,
          from_position: fromVal,
          to_position: toVal
        })
      });
      gameState = res; // Returns updated party object on backend or full state? Wait, let's verify in route.
      // Wait, let's refresh the session state to make sure
      const fullRes = await rpgFetch(`${getApiBase()}/game/rpg/state?session_id=${encodeURIComponent(currentSessionId)}`);
      renderState(fullRes);
      renderPartyModalGrids();
      appendLogEntry("Đã thay đổi sơ đồ đội hình chiến đấu!");
    } catch (err) {
      alert("Hoán đổi đội hình lỗi: " + err.message);
      renderPartyModalGrids();
    }
  }
}

// ── COMBAT OVERLAY CONTROLLERS ───────────────────────────────────────────────

function showCombatOverlay(combatState) {
  if (!combatState) return;
  const overlay = document.getElementById("rpgCombatOverlay");
  if (!overlay) return;

  overlay.classList.remove("hidden");
  overlay.combatState = combatState;

  // Render Combat Initiative Timeline Sequence based on speeds
  const timelineSequence = document.getElementById("rpgTimelineSequence");
  if (timelineSequence && combatState) {
    timelineSequence.innerHTML = "";
    const participants = [];

    if (combatState.combat_party) {
      combatState.combat_party.forEach(c => {
        if (c.stats.hp > 0) {
          participants.push({
            name: c.name,
            spd: c.stats.atk_spd || 100,
            race: c.race,
            class: c.char_class,
            isEnemy: false,
            id: c.character_id
          });
        }
      });
    }

    if (combatState.enemy && combatState.enemy.stats.hp > 0) {
      participants.push({
        name: combatState.enemy.name,
        spd: combatState.enemy.stats.atk_spd || 90,
        race: "Demon",
        class: "Boss",
        isEnemy: true,
        id: "enemy"
      });
    }

    // Sort descending by speed (SPD)
    participants.sort((a, b) => b.spd - a.spd);

    // Render timeline units
    participants.forEach((p, idx) => {
      const unit = document.createElement("div");
      unit.className = `timeline-unit ${p.isEnemy ? "enemy" : ""} ${idx === 0 ? "active" : ""}`;
      unit.innerHTML = `
        <span class="timeline-emoji">${p.isEnemy ? "👿" : getRaceEmoji(p.race)}</span>
        <span class="timeline-name">${p.name}</span>
        <span class="timeline-spd" style="opacity:0.6;font-size:0.65rem;">(${p.spd})</span>
      `;
      timelineSequence.appendChild(unit);
    });
  }

  // 1. Enemy Card Details
  const enemy = combatState.enemy;
  if (enemy) {
    document.getElementById("rpgCombatEnemyName").textContent = enemy.name;
    document.getElementById("rpgCombatEnemyName").className = `rpg-text-${enemy.rarity}`;

    const rarityEl = document.getElementById("rpgCombatEnemyRarity");
    rarityEl.textContent = getRarityLabel(enemy.rarity);
    rarityEl.className = `rpg-badge rarity rpg-text-${enemy.rarity} rpg-glow-${enemy.rarity}`;

    // HP Bar
    document.getElementById("rpgCombatEnemyHpText").textContent = `${enemy.stats.hp}/${enemy.stats.max_hp}`;
    const percent = Math.max(0, Math.min(100, (enemy.stats.hp / enemy.stats.max_hp) * 100));
    document.getElementById("rpgCombatEnemyHpBar").style.width = `${percent}%`;

    // Debuffs
    const debuffs = enemy.debuffs || [];
    const debuffText = document.getElementById("rpgCombatEnemyDebuffs");
    if (debuffs.length > 0) {
      debuffText.innerHTML = "Trạng thái phụ: " + debuffs.map(d => {
        const dur = (d.duration === null || d.duration === undefined || d.duration === "None" || d.duration === "null") ? "∞" : `${d.duration}t`;
        return `<span class="rpg-badge" style="background:#e74c3c;color:#fff;">${d.name} (${dur})</span>`;
      }).join(" ");
    } else {
      debuffText.innerHTML = "";
    }
  }

  // 2. Combat logs
  const logContainer = document.getElementById("rpgCombatLog");
  logContainer.innerHTML = "";
  combatState.combat_log.forEach(log => {
    const div = document.createElement("div");
    if (log.includes("LƯỢT ĐẤU THỨ")) {
      div.className = "combat-log-turn-header";
      div.innerHTML = `<span>${escapeHtml(log)}</span>`;
    } else {
      div.className = "combat-log-line";
      div.innerHTML = escapeHtml(log);
    }
    logContainer.appendChild(div);
  });
  logContainer.scrollTop = logContainer.scrollHeight;

  // 3. Combat Party Containers (active party visual list)
  const partyContainer = document.getElementById("rpgCombatPartyContainer");
  partyContainer.innerHTML = "";

  const combatParty = combatState.combat_party || [];
  combatParty.forEach(c => {
    const isDead = c.stats.hp <= 0;
    const hpPercent = Math.max(0, Math.min(100, (c.stats.hp / c.stats.max_hp) * 100));

    const buffs = c.buffs || [];
    const debuffs = c.debuffs || [];

    const card = document.createElement("div");
    card.className = `combat-party-card ${isDead ? "dead" : ""}`;
    card.innerHTML = `
      <div style="display:flex; justify-content:space-between; align-items:center;">
        <div style="display:flex; align-items:center; gap:5px;">
          <h4 class="rpg-text-${c.rarity}" style="margin:0; font-size:0.85rem;">${getRaceEmoji(c.race, c.name)} ${c.name}</h4>
          <button class="ghost-btn rpg-combat-char-details-btn" data-id="${c.character_id}" type="button" style="padding:0; font-size:0.65rem; border-radius:50%; width:16px; height:16px; display:inline-flex; align-items:center; justify-content:center; border-color:rgba(255,255,255,0.15); color:rgba(255,255,255,0.5); cursor:pointer; flex-shrink:0;" title="Xem chi tiết chỉ số">?</button>
        </div>
        <span style="font-size:0.75rem;opacity:0.75;">Lv.${c.level}</span>
      </div>
      <div class="rpg-hp-container" style="margin: 4px 0;">
        <div class="rpg-hp-label" style="font-size:0.7rem; margin-bottom: 2px;">
          <span>HP</span>
          <span>${c.stats.hp}/${c.stats.max_hp}</span>
        </div>
        <div class="hp-bar-container" style="height: 5px;">
          <div class="hp-bar" style="width: ${hpPercent}%;"></div>
        </div>
      </div>
      <div class="buffs-indicators" style="display:flex;flex-wrap:wrap;gap:4px;font-size:0.65rem;margin-bottom:4px;">
        ${buffs.map(b => `<span style="background:#2ecc71;color:#fff;padding:1px 4px;border-radius:3px;">${b.name}</span>`).join("")}
        ${debuffs.map(d => `<span style="background:#e74c3c;color:#fff;padding:1px 4px;border-radius:3px;">${d.name}</span>`).join("")}
      </div>
      ${renderSpecialSkillsIndicators(c)}
    `;
    const detailsBtn = card.querySelector(".rpg-combat-char-details-btn");
    if (detailsBtn) {
      detailsBtn.addEventListener("click", (e) => {
        e.stopPropagation();
        showCharacterDetails(c, true);
      });
    }
    partyContainer.appendChild(card);
  });

  // 4. Populate drop-downs for targeting
  const aliveMembers = combatParty.filter(c => c.stats.hp > 0);

  const attackerSelect = document.getElementById("rpgAttackerSelect");
  attackerSelect.innerHTML = "";
  let firstEnabledAttacker = null;
  aliveMembers.forEach(c => {
    const hasStunOrFear = c.debuffs && c.debuffs.some(d => (d.name === "Choáng" || d.name === "Sợ hãi") && d.duration > 0);
    const isAutoFiring = c.special_skills && c.special_skills.skill_1_activating &&
      c.char_class === "Sniper" && c.special_skills.skill_1 === "Khóa mục tiêu";
    const opt = document.createElement("option");
    opt.value = c.character_id;
    if (hasStunOrFear) {
      opt.textContent = `❌ ${c.name} (${c.char_class}) [Bị khống chế]`;
      opt.disabled = true;
    } else if (isAutoFiring) {
      opt.textContent = `❌ ${c.name} (${c.char_class}) [Đang Tự Động Bắn]`;
      opt.disabled = true;
    } else {
      opt.textContent = `${c.name} (${c.char_class})`;
      if (!firstEnabledAttacker) {
        firstEnabledAttacker = c.character_id;
      }
    }
    attackerSelect.appendChild(opt);
  });
  if (firstEnabledAttacker) {
    attackerSelect.value = firstEnabledAttacker;
  }

  const defenderSelect = document.getElementById("rpgDefenderSelect");
  defenderSelect.innerHTML = '<option value="">Không cử ai (Nhận sát thương ngẫu nhiên)</option>';
  aliveMembers.forEach(c => {
    const hasStunOrFear = c.debuffs && c.debuffs.some(d => (d.name === "Choáng" || d.name === "Sợ hãi") && d.duration > 0);
    const opt = document.createElement("option");
    opt.value = c.character_id;
    if (hasStunOrFear) {
      opt.textContent = `❌ ${c.name} [Bị khống chế]`;
      opt.disabled = true;
    } else {
      opt.textContent = c.name;
    }
    defenderSelect.appendChild(opt);
  });
  defenderSelect.value = "";

  // Skill Bindings
  const skillSelect = document.getElementById("rpgSkillSelect");
  const targetSelect = document.getElementById("rpgTargetSelect");

  const syncTargetDropdown = () => {
    const selectedAttackerId = attackerSelect.value;
    const selectedAttacker = combatParty.find(c => c.character_id === selectedAttackerId);
    if (!selectedAttacker) return;

    const selectedSkill = skillSelect.value;
    targetSelect.innerHTML = "";

    // Determine target type
    const isSupporterHeal = (selectedAttacker.char_class === "Supporter" && selectedSkill === "basic_attack");
    const isAngelShield = (selectedSkill === "skill_1" && selectedAttacker.special_skills?.skill_1 === "Lá chắn");
    const isRoyaltyBless = (selectedSkill === "skill_1" && selectedAttacker.special_skills?.skill_1 === "Phong tước");

    if (isSupporterHeal) {
      // Can target anyone in the party, including self
      aliveMembers.forEach(c => {
        const opt = document.createElement("option");
        opt.value = c.character_id;
        opt.textContent = `${c.name} (Ta)`;
        targetSelect.appendChild(opt);
      });
    } else if (isAngelShield || isRoyaltyBless) {
      // Must target another alive ally (excluding the attacker themselves)
      const otherAllies = aliveMembers.filter(c => c.character_id !== selectedAttackerId);
      if (otherAllies.length === 0) {
        const opt = document.createElement("option");
        opt.value = "";
        opt.textContent = "Không có đồng đội hợp lệ";
        targetSelect.appendChild(opt);
      } else {
        otherAllies.forEach(c => {
          const opt = document.createElement("option");
          opt.value = c.character_id;
          opt.textContent = `${c.name} (Ta)`;
          targetSelect.appendChild(opt);
        });
      }
    } else {
      // Offensive targets enemy
      const opt = document.createElement("option");
      opt.value = enemy.character_id;
      opt.textContent = `${enemy.name} (Địch)`;
      targetSelect.appendChild(opt);
    }
  };

  const syncSkillsDropdown = () => {
    const selectedAttackerId = attackerSelect.value;
    const selectedAttacker = combatParty.find(c => c.character_id === selectedAttackerId);
    if (!selectedAttacker) return;

    skillSelect.innerHTML = "";

    // Basic attack option
    const basicOpt = document.createElement("option");
    basicOpt.value = "basic_attack";
    basicOpt.textContent = selectedAttacker.char_class === "Supporter"
      ? "Trị Thương Đội Hình"
      : "Tấn Công Cơ Bản";
    skillSelect.appendChild(basicOpt);

    // Active skills if exists
    const skillsObj = selectedAttacker.special_skills || {};

    // Fallback: if special_skills is missing/null but we know the race's skills, reconstruct them
    const raceSkillMap = {
      "Elf": { skill_1: "Mưa tên" },
      "Angel": { skill_1: "Lá chắn", skill_2: "Thiên lôi" },
      "Devil": { skill_1: "Hấp thụ", skill_2: "Huyết quỷ thuật" },
      "Royalty": { skill_1: "Phong tước" },
    };
    const fallbackSkills = !skillsObj.skill_1 && raceSkillMap[selectedAttacker.race]
      ? raceSkillMap[selectedAttacker.race]
      : {};
    const effectiveSkills = Object.assign({}, fallbackSkills, skillsObj);

    if (effectiveSkills.skill_1) {
      const opt = document.createElement("option");
      opt.value = "skill_1";
      const cooldown = effectiveSkills.skill_1_countdown || 0;
      const isOneTimeUsed = effectiveSkills.skill_1_activated === true;
      if (isOneTimeUsed) {
        opt.textContent = `Chiêu 1: ${effectiveSkills.skill_1} [Đã dùng]`;
        opt.disabled = true;
      } else if (cooldown > 0) {
        opt.textContent = `Chiêu 1: ${effectiveSkills.skill_1} [Hồi chiêu: ${cooldown}t]`;
        opt.disabled = true;
      } else {
        opt.textContent = `Chiêu 1: ${effectiveSkills.skill_1}`;
      }
      skillSelect.appendChild(opt);
    }
    if (effectiveSkills.skill_2) {
      const opt = document.createElement("option");
      opt.value = "skill_2";
      const cooldown = effectiveSkills.skill_2_countdown || 0;
      if (cooldown > 0) {
        opt.textContent = `Tuyệt Kỹ: ${effectiveSkills.skill_2} [Hồi chiêu: ${cooldown}t]`;
        opt.disabled = true;
      } else {
        opt.textContent = `Tuyệt Kỹ: ${effectiveSkills.skill_2}`;
      }
      skillSelect.appendChild(opt);
    }
  };

  attackerSelect.onchange = () => {
    syncSkillsDropdown();
    syncTargetDropdown();
  };

  skillSelect.onchange = () => {
    syncTargetDropdown();
  };

  // Initial Sync
  if (aliveMembers.length > 0) {
    syncSkillsDropdown();
    syncTargetDropdown();
  }

  // Bind execute
  const executeBtn = document.getElementById("rpgCombatExecuteBtn");
  executeBtn.onclick = async () => {
    executeBtn.disabled = true;
    executeBtn.textContent = "Đang giao đấu...";

    const overlay = document.getElementById("rpgCombatOverlay");
    const lastCombatState = overlay ? overlay.combatState : null;
    const oldEnemyHp = lastCombatState?.enemy?.stats?.hp || 0;
    const oldPartyHps = {};
    if (lastCombatState?.combat_party) {
      lastCombatState.combat_party.forEach(c => {
        oldPartyHps[c.character_id] = c.stats.hp;
      });
    }

    try {
      const res = await rpgFetch(`${getApiBase()}/game/rpg/combat/action`, {
        method: "POST",
        body: JSON.stringify({
          session_id: currentSessionId,
          attacker_id: attackerSelect.value,
          skill_name: skillSelect.value,
          target_id: targetSelect.value,
          defender_id: defenderSelect.value || null
        })
      });

      // Update Combat details
      if (res.combat_state) {
        showCombatOverlay(res.combat_state);
      }

      // Trigger hit animations based on HP decrease
      if (res.combat_state) {
        const newEnemyHp = res.combat_state.enemy?.stats?.hp || 0;
        if (newEnemyHp < oldEnemyHp) {
          const enemyCard = document.getElementById("rpgCombatEnemyCard");
          if (enemyCard) {
            enemyCard.classList.add("damage-shake", "damage-flash");
            spawnDamageNumber(enemyCard, oldEnemyHp - newEnemyHp, "normal");
            setTimeout(() => {
              enemyCard.classList.remove("damage-shake", "damage-flash");
            }, 500);
          }
        }

        let partyTookDamage = false;
        if (res.combat_state.combat_party) {
          res.combat_state.combat_party.forEach(c => {
            const oldHp = oldPartyHps[c.character_id] || 0;
            if (c.stats.hp < oldHp) {
              const card = document.querySelector(`.combat-party-card button[data-id="${c.character_id}"]`)?.closest('.combat-party-card');
              if (card) {
                spawnDamageNumber(card, oldHp - c.stats.hp, "normal");
              }
              partyTookDamage = true;
            } else if (c.stats.hp > oldHp && oldHp > 0) {
              const card = document.querySelector(`.combat-party-card button[data-id="${c.character_id}"]`)?.closest('.combat-party-card');
              if (card) {
                spawnDamageNumber(card, c.stats.hp - oldHp, "heal");
              }
            }
          });
        }

        if (partyTookDamage && overlay) {
          overlay.classList.add("party-damage-shake", "screen-flash-red");
          setTimeout(() => {
            overlay.classList.remove("party-damage-shake", "screen-flash-red");
          }, 500);
        }
      }

      // If combat has concluded, show post victory selection or death
      if (res.is_combat_over) {
        if (res.result === "win") {
          if (!res.combat_state) {
            // Special victory (Alpha or Dummy) - clean up and return to normal flow
            hideCombatOverlay();
            appendStoryBlock(res.story);
            renderChoices(res.choices || [], res.rpg_state ? res.rpg_state.current_event : null);
            renderState(res.rpg_state);
            updatePointsDisplay();
          } else if (res.rpg_state && res.rpg_state.dungeon_state && res.rpg_state.dungeon_state.active) {
            try {
              const endActionRes = await rpgFetch(`${getApiBase()}/game/rpg/combat/end-action`, {
                method: "POST",
                body: JSON.stringify({
                  session_id: currentSessionId,
                  action: "loot"
                })
              });
              hideCombatOverlay();
              appendStoryBlock(endActionRes.story);
              renderChoices(endActionRes.choices, endActionRes.event_type);
              renderState(endActionRes.rpg_state);
              updatePointsDisplay();
            } catch (err) {
              alert("Lỗi thám hiểm tự động loot: " + err.message);
            }
          } else {
            document.getElementById("rpgCombatEndOverlay").classList.remove("hidden");
          }
        } else if (res.result === "lose") {
          alert("THẤT BẠI: Đội ngũ của bạn đã gục ngã trước sức mạnh kẻ địch!");
          triggerGameOver();
        }
      }

    } catch (err) {
      alert("Lỗi thực thi lượt đấu: " + err.message);
    } finally {
      executeBtn.disabled = false;
      executeBtn.textContent = "Thực Thi Hành Động ⚔";
    }
  };
}

function hideCombatOverlay() {
  const overlay = document.getElementById("rpgCombatOverlay");
  if (overlay) overlay.classList.add("hidden");
  document.getElementById("rpgCombatEndOverlay").classList.add("hidden");
}

function initCombatOverlayController() {
  // Bind enemy info button
  const enemyInfoBtn = document.getElementById("rpgCombatEnemyInfoBtn");
  if (enemyInfoBtn) {
    enemyInfoBtn.addEventListener("click", (e) => {
      e.stopPropagation();
      if (gameState && gameState.combat && gameState.combat.enemy) {
        showCharacterDetails(gameState.combat.enemy, true);
      }
    });
  }

  // Bind post-victory buttons
  const endActionBtns = document.querySelectorAll("#rpgCombatEndOverlay .end-action-btn");
  endActionBtns.forEach(btn => {
    btn.addEventListener("click", async () => {
      const action = btn.dataset.action; // "loot", "recruit", "leave"
      let customName = null;
      if (action === "recruit") {
        const enemy = (gameState && gameState.combat && gameState.combat.enemy) || (gameState && gameState.current_stranger);
        if (enemy && enemy.rarity !== "Mythic") {
          customName = prompt(`Nhập tên mới cho đồng hành của bạn (${enemy.race} ${enemy.char_class}):`, enemy.name);
          if (customName === null) {
            btn.disabled = false;
            return;
          }
          customName = customName.trim();
        }
      }

      btn.disabled = true;
      try {
        const res = await rpgFetch(`${getApiBase()}/game/rpg/combat/end-action`, {
          method: "POST",
          body: JSON.stringify({
            session_id: currentSessionId,
            action: action,
            custom_name: customName
          })
        });

        // Hide overlay, resume normal adventure flow
        hideCombatOverlay();
        appendStoryBlock(res.story);
        renderChoices(res.choices, res.event_type);
        renderState(res.rpg_state);
        updatePointsDisplay();

      } catch (err) {
        alert("Thực thi kết thúc lỗi: " + err.message);
      } finally {
        btn.disabled = false;
      }
    });
  });
}

// ── SAVES & GAME OVER ────────────────────────────────────────────────────────

function triggerGameOver() {
  // Hide active gameplay interfaces, force GameOver display
  hideCombatOverlay();
  hidePartyManagementModal();
  hideShopModal();

  const existingOverlay = document.getElementById("rpgGameOverOverlay");
  if (existingOverlay) existingOverlay.remove();

  const overlay = document.createElement("div");
  overlay.id = "rpgGameOverOverlay";
  overlay.className = "rpg-combat-overlay";
  overlay.style.zIndex = "1005";
  overlay.innerHTML = `
    <div class="combat-end-overlay glass-panel" style="display:flex !important; flex-direction:column; align-items:center; max-width:500px; padding:40px;">
      <h1 style="color:#ff2a2a; font-family:var(--rpg-font-cinzel); font-size:3rem; margin-bottom:15px; text-shadow:0 0 15px rgba(255,42,42,0.6)">HÀNH TRÌNH TỬ NẠN</h1>
      <p style="text-align:center; line-height:1.6; margin-bottom:30px;">
        Đội ngũ thám hiểm đã hoàn toàn kiệt sức và gục ngã giữa chặng đường khám phá. Tên của bạn sẽ được lưu truyền trong sử sách Chronicles of Destiny, nhưng cuộc hành trình này đã kết thúc...
      </p>
      <button class="primary-btn big-btn" id="rpgGameOverReturnBtn" style="width:100%;">
        Quay Lại Sảnh Chính 🏛
      </button>
    </div>
  `;

  document.body.appendChild(overlay);

  overlay.querySelector("#rpgGameOverReturnBtn").addEventListener("click", () => {
    overlay.remove();
    if (typeof window.resetRpgSetupWizard === "function") {
      window.resetRpgSetupWizard();
    }
    if (window.showPage) {
      window.showPage(document.getElementById("landingPage"));
    }
  });
}

function triggerGameCompleted(endingType, storyText) {
  hideCombatOverlay();
  hidePartyManagementModal();
  hideShopModal();

  const existingOverlay = document.getElementById("rpgGameCompletedOverlay");
  if (existingOverlay) existingOverlay.remove();

  const overlay = document.createElement("div");
  overlay.id = "rpgGameCompletedOverlay";
  overlay.className = "rpg-combat-overlay";
  overlay.style.zIndex = "1006";

  const isGood = endingType === "good";
  const title = isGood ? "KHẢI HOÀN KHÚC ✨" : "HƯ VÔ VĨNH HẰNG 💀";
  const titleColor = isGood ? "#a273ff" : "#ff2a2a";
  const textShadow = isGood ? "rgba(162, 115, 255, 0.6)" : "rgba(255, 42, 42, 0.6)";

  overlay.innerHTML = `
    <div class="combat-end-overlay glass-panel" style="display:flex !important; flex-direction:column; align-items:center; max-width:600px; padding:40px; text-align:center;">
      <h1 style="color:${titleColor}; font-family:var(--rpg-font-cinzel); font-size:2.8rem; margin-bottom:15px; text-shadow:0 0 15px ${textShadow}">${title}</h1>
      <div style="font-size:0.95rem; line-height:1.6; margin-bottom:30px; max-height: 250px; overflow-y: auto; padding: 15px; background: rgba(0,0,0,0.2); border-radius: 8px; border: 1px dashed rgba(255,255,255,0.1); width: 100%; box-sizing: border-box; text-align: left;">
        ${storyText.replace(/\n/g, "<br>")}
      </div>
      <button class="primary-btn big-btn" id="rpgGameCompletedReturnBtn" style="width:100%;">
        Quay Lại Sảnh Chính 🏛
      </button>
    </div>
  `;

  document.body.appendChild(overlay);

  overlay.querySelector("#rpgGameCompletedReturnBtn").addEventListener("click", () => {
    overlay.remove();
    if (typeof window.resetRpgSetupWizard === "function") {
      window.resetRpgSetupWizard();
    }
    if (window.showPage) {
      window.showPage(document.getElementById("landingPage"));
    }
  });
}

function checkEndingConditions(storyText) {
  if (!storyText) return;
  if (storyText.includes("GOOD ENDING:") || storyText.includes("✨ GOOD ENDING")) {
    triggerGameCompleted("good", storyText);
  } else if (storyText.includes("BAD ENDING:") || storyText.includes("💀 BAD ENDING")) {
    triggerGameCompleted("bad", storyText);
  }
}

// ── INITIALIZATION & GLOBAL EXPOSURE ─────────────────────────────────────────

async function resumeSession(sessionId, sessionData) {
  currentSessionId = sessionId;
  currentSessionIsSaved = true;

  // Clear story log and composer
  const storyLog = document.getElementById("rpgStoryLog");
  storyLog.innerHTML = "";
  document.getElementById("rpgCustomAction").value = "";

  // 1. Fetch active state from backend
  try {
    const stateRes = await rpgFetch(`${getApiBase()}/game/rpg/state?session_id=${encodeURIComponent(sessionId)}`);
    gameState = stateRes;
  } catch (err) {
    console.warn("Could not retrieve state from backend, fallback to session data:", err);
    gameState = sessionData.session?.rpg_state || null;
  }

  // 2. Populate historical message logs
  const messages = sessionData.messages || [];
  messages.forEach(msg => {
    if (msg.role === "system") return;
    if (msg.role === "user") {
      appendStoryBlock(`Lựa chọn: ${msg.content}`);
    } else {
      appendStoryBlock(msg.content);
    }
  });

  // 3. Render latest choices
  const lastAiMessage = [...messages]
    .reverse()
    .find(m => m.role === "ai" && m.choices?.length);

  const eventType = gameState ? gameState.current_event : null;

  if (lastAiMessage) {
    renderChoices(lastAiMessage.choices, eventType);
  } else {
    // If no message choices exist yet, trigger opening story
    try {
      const res = await rpgFetch(`${getApiBase()}/game/rpg/start-story?session_id=${encodeURIComponent(sessionId)}`, {
        method: "POST"
      });
      appendStoryBlock(res.story);
      renderChoices(res.choices, res.event_type);
      gameState = res.rpg_state;
    } catch (err) {
      console.error(err);
    }
  }

  renderState(gameState);
  updatePointsDisplay();
}

function initRpgImagesController() {
  // See World Feature
  const seeWorldBtn = document.getElementById("rpgSeeWorldBtn");
  const worldImgModal = document.getElementById("rpgWorldImgModal");
  const closeWorldImgBtn = document.getElementById("rpgCloseWorldImgBtn");
  const worldImgBackdrop = document.getElementById("rpgWorldImgBackdrop");
  const worldImgView = document.getElementById("rpgWorldImgView");
  const worldImgSpinner = document.getElementById("rpgWorldImgSpinner");
  const worldImgSpinnerText = document.getElementById("rpgWorldImgSpinnerText");

  if (seeWorldBtn && worldImgModal) {
    seeWorldBtn.addEventListener("click", () => {
      // Open modal
      worldImgModal.classList.remove("hidden");

      const apiBase = getApiBase();
      const baseUrl = apiBase.startsWith("http") ? apiBase : (apiBase === "/api" ? "/api" : "");
      const cleanBaseUrl = baseUrl.replace(/\/+$/, "");
      const fallbackUrl = `${cleanBaseUrl}/assets/generated/${currentSessionId}_see_the_world.png`;
      const targetUrl = window.lastSeeWorldImageUrl || fallbackUrl;

      // Show spinner, hide image
      worldImgSpinner.style.display = "flex";
      worldImgView.style.display = "none";
      if (worldImgSpinnerText) {
        worldImgSpinnerText.textContent = "Đang tải ảnh từ bộ nhớ tạm...";
      }

      const loadFromApi = async () => {
        if (worldImgSpinnerText) {
          worldImgSpinnerText.textContent = "Đang kết nối backend sinh hình ảnh thế giới...";
        }
        try {
          const url = `${getApiBase()}/game/rpg/image/see-world?session_id=${encodeURIComponent(currentSessionId)}`;
          const res = await rpgFetch(url, { method: "POST" });
          if (res && res.success && res.image_url) {
            let imgUrl = res.image_url;
            if (!imgUrl.startsWith("http")) {
              if (imgUrl.startsWith("/")) {
                imgUrl = imgUrl.substring(1);
              }
              imgUrl = `${cleanBaseUrl}/${imgUrl}`;
            }
            window.lastSeeWorldImageUrl = imgUrl;
            worldImgView.src = `${imgUrl}?t=${Date.now()}`;
            worldImgView.onload = () => {
              worldImgSpinner.style.display = "none";
              worldImgView.style.display = "block";
            };
            worldImgView.onerror = () => {
              worldImgSpinner.style.display = "flex";
              if (worldImgSpinnerText) {
                worldImgSpinnerText.textContent = "Lỗi khi hiển thị hình ảnh tải về.";
              }
            };
          } else {
            throw new Error("Không nhận được đường dẫn ảnh từ server.");
          }
        } catch (err) {
          if (worldImgSpinnerText) {
            worldImgSpinnerText.textContent = "Lỗi sinh ảnh: " + err.message;
          }
          console.error("Lỗi xem thế giới:", err);
        }
      };

      worldImgView.src = `${targetUrl}?t=${Date.now()}`;
      worldImgView.onload = () => {
        worldImgSpinner.style.display = "none";
        worldImgView.style.display = "block";
      };
      worldImgView.onerror = () => {
        // Cached/fallback image failed to load, call API
        console.log("Cached/fallback image failed to load, requesting from API...");
        loadFromApi();
      };
    });

    const hideWorldModal = () => {
      worldImgModal.classList.add("hidden");
    };

    if (closeWorldImgBtn) closeWorldImgBtn.addEventListener("click", hideWorldModal);
    if (worldImgBackdrop) worldImgBackdrop.addEventListener("click", hideWorldModal);
  }

  // NPC Avatar Panel Controls
  const npcRefreshBtn = document.getElementById("rpgNpcRefreshBtn");
  const npcToggleBtn = document.getElementById("rpgNpcToggleBtn");
  const npcImg = document.getElementById("rpgNpcAvatarImg");
  const npcDefault = document.getElementById("rpgNpcAvatarDefault");
  const npcLoading = document.getElementById("rpgNpcAvatarLoading");

  const getActiveNpc = () => {
    if (!gameState) return null;
    if (gameState.combat && gameState.combat.is_active && gameState.combat.enemy) {
      return gameState.combat.enemy;
    } else if (gameState.current_event === "stranger" && gameState.current_stranger) {
      return gameState.current_stranger;
    } else if (gameState.current_event === "monk") {
      return gameState.current_monk;
    } else if (gameState.current_event === "merchant") {
      return gameState.current_merchant;
    }
    return null;
  };

  if (npcToggleBtn) {
    npcToggleBtn.addEventListener("click", (e) => {
      e.stopPropagation();
      const char = getActiveNpc();
      if (!char) return;
      const prefKey = `show_img_${char.character_id || char.name}`;
      const currentlyShown = localStorage.getItem(prefKey) !== "false";
      localStorage.setItem(prefKey, currentlyShown ? "false" : "true");
      setupAvatarDisplay(npcImg, npcDefault, char);
    });
  }

  if (npcRefreshBtn) {
    npcRefreshBtn.addEventListener("click", async (e) => {
      e.stopPropagation();
      const char = getActiveNpc();
      if (!char) return;

      const charId = char.character_id || char.name;
      if (npcLoading) npcLoading.classList.remove("hidden");
      try {
        const url = `${getApiBase()}/game/rpg/image/refresh-character?session_id=${encodeURIComponent(currentSessionId)}&character_id=${encodeURIComponent(charId)}`;
        const res = await rpgFetch(url, { method: "POST" });
        if (res && res.success) {
          char._img_version = Date.now();
          localStorage.setItem(`show_img_${charId}`, "true");
          setupAvatarDisplay(npcImg, npcDefault, char);
        } else {
          alert("Làm mới ảnh thất bại.");
        }
      } catch (err) {
        console.error(err);
        alert("Lỗi kết nối sinh ảnh: " + err.message);
      } finally {
        if (npcLoading) npcLoading.classList.add("hidden");
      }
    });
  }
}

function initRpgSettingsDrawer() {
  const settingsBtn = document.getElementById("rpgSettingsBtn");
  const settingsDrawer = document.getElementById("rpgSettingsDrawer");
  const closeSettingsBtn = document.getElementById("rpgCloseSettingsBtn");
  const backdrop = document.getElementById("rpgSettingsDrawerBackdrop");

  if (settingsBtn && settingsDrawer) {
    // Open drawer
    settingsBtn.addEventListener("click", () => {
      settingsDrawer.classList.add("active");
    });

    // Close drawer handlers
    const closeDrawer = () => settingsDrawer.classList.remove("active");
    if (closeSettingsBtn) closeSettingsBtn.addEventListener("click", closeDrawer);
    if (backdrop) backdrop.addEventListener("click", closeDrawer);

    // 1. Text Speed Setting
    const textSpeedSelect = document.getElementById("settingsTextSpeed");
    if (textSpeedSelect) {
      textSpeedSelect.value = currentTextSpeed;
      textSpeedSelect.addEventListener("change", (e) => {
        currentTextSpeed = parseInt(e.target.value);
        console.log("RPG Text Speed updated to:", currentTextSpeed);
      });
    }

    // 2. Weather Toggle Setting
    const toggleWeatherCheckbox = document.getElementById("settingsToggleWeather");
    if (toggleWeatherCheckbox) {
      toggleWeatherCheckbox.checked = weatherEnabled;
      toggleWeatherCheckbox.addEventListener("change", (e) => {
        weatherEnabled = e.target.checked;
        console.log("RPG Weather Particle System enabled:", weatherEnabled);
        if (gameState && gameState.region) {
          updateWeatherEffect(gameState.region);
        } else {
          updateWeatherEffect(null);
        }
      });
    }

    // 3. Export Save Button
    const exportBtn = document.getElementById("settingsExportSaveBtn");
    if (exportBtn) {
      exportBtn.addEventListener("click", () => {
        if (!gameState) {
          alert("Không tìm thấy dữ liệu game hiện tại để tải về.");
          return;
        }

        const exportData = {
          session_id: currentSessionId,
          game_state: gameState,
          saved_at: new Date().toISOString(),
          app: "AI Story Adventure RPG Mode"
        };

        const dataStr = "data:text/json;charset=utf-8," + encodeURIComponent(JSON.stringify(exportData, null, 2));
        const downloadAnchor = document.createElement("a");
        downloadAnchor.setAttribute("href", dataStr);
        downloadAnchor.setAttribute("download", `aistory_rpg_save_${currentSessionId || "session"}.json`);
        document.body.appendChild(downloadAnchor);
        downloadAnchor.click();
        downloadAnchor.remove();
        console.log("RPG Save exported successfully.");
      });
    }

    // 4. Import Save Button & File Input trigger
    const importTrigger = document.getElementById("settingsImportSaveTrigger");
    const importInput = document.getElementById("settingsImportSaveInput");

    if (importTrigger && importInput) {
      importTrigger.addEventListener("click", () => {
        importInput.click();
      });

      importInput.addEventListener("change", (e) => {
        const file = e.target.files[0];
        if (!file) return;

        const reader = new FileReader();
        reader.onload = async (evt) => {
          try {
            const importedData = JSON.parse(evt.target.result);
            if (!importedData.game_state || !importedData.session_id) {
              throw new Error("Tệp JSON không chứa session_id hoặc game_state hợp lệ.");
            }

            const apiBase = getApiBase();
            const response = await fetch(`${apiBase}/game/rpg/session/restore`, {
              method: "POST",
              headers: { "Content-Type": "application/json" },
              body: JSON.stringify({
                session_id: importedData.session_id,
                game_state: importedData.game_state
              })
            });
            const res = await response.json();
            if (response.ok && res.success) {
              alert("Khôi phục save game thành công! Đang tải lại phiên chơi...");
              currentSessionId = importedData.session_id;
              gameState = importedData.game_state;

              // Load view
              const setupPage = document.getElementById("rpgSetupPage");
              const rpgPage = document.getElementById("rpgPage");
              if (setupPage) setupPage.classList.remove("active");
              if (rpgPage) {
                rpgPage.classList.add("active");
                if (typeof window.showPage === "function") {
                  window.showPage("rpgPage");
                }
              }

              renderState(gameState);
              appendStoryBlock("♻️ *Đã khôi phục thành công phiên chơi từ file save JSON của bạn! Hãy tiếp tục cuộc hành trình.*");
              closeDrawer();
            } else {
              throw new Error(res.detail || "Không thể đồng bộ dữ liệu save lên máy chủ.");
            }
          } catch (err) {
            alert("Nạp file save thất bại: " + err.message);
          } finally {
            importInput.value = "";
          }
        };
        reader.readAsText(file);
      });
    }
  }
}

function initRPGApp() {
  initRpgSetupWizard();
  initRpgComposer();
  initShopController();
  initPartyController();
  initCombatOverlayController();
  initRpgImagesController();
  initRpgSettingsDrawer();

  initRpgQuestController();
  initRpgMapController();
  initRpgDungeonController();
  initRpgHelpController();
  initRpgDebugConsoleController();
  initRpgKeyboardShortcuts();

  // Saves tab navigation binding
  const savesBtn = document.getElementById("rpgSavesNavBtn");
  if (savesBtn) {
    savesBtn.addEventListener("click", () => {
      // Toggle global Saves view in main app
      const savesTabBtn = document.getElementById("savesTabBtn");
      if (savesTabBtn) savesTabBtn.click();
    });
  }

  // Leave region button binding
  const leaveRegionBtn = document.getElementById("rpgLeaveRegionBtn");
  if (leaveRegionBtn) {
    leaveRegionBtn.addEventListener("click", async () => {
      if (!currentSessionId) return;
      if (confirm("Bạn có chắc chắn muốn rời khỏi địa điểm này và quay lại bản đồ hoang dã?")) {
        try {
          const res = await rpgFetch(`${getApiBase()}/game/rpg/leave-region`, {
            method: "POST",
            body: JSON.stringify({
              session_id: currentSessionId
            })
          });

          appendStoryBlock(res.story);
          renderChoices(res.choices, res.event_type);
          renderState(res.rpg_state);
          updatePointsDisplay();

          if (res.notifications) {
            res.notifications.forEach((notif) => appendLogEntry(notif));
          }
        } catch (err) {
          alert("Lỗi khi rời khu vực: " + err.message);
        }
      }
    });
  }
}

// Register page structures in the navigation system
const rpgSetupPage = document.getElementById("rpgSetupPage");
const rpgPage = document.getElementById("rpgPage");
if (rpgSetupPage && window.ALL_PAGES && !window.ALL_PAGES.includes(rpgSetupPage)) {
  window.ALL_PAGES.push(rpgSetupPage);
}
if (rpgPage && window.ALL_PAGES && !window.ALL_PAGES.includes(rpgPage)) {
  window.ALL_PAGES.push(rpgPage);
}

// Initialise on script load (module)
initRPGApp();

function clearSession() {
  currentSessionId = null;
  currentSessionIsSaved = false;
  gameState = null;
  const storyLog = document.getElementById("rpgStoryLog");
  if (storyLog) storyLog.innerHTML = "";
  const choicesBox = document.getElementById("rpgChoicesBox");
  if (choicesBox) choicesBox.innerHTML = "";
  const customAction = document.getElementById("rpgCustomAction");
  if (customAction) customAction.value = "";
  if (typeof window.resetRpgSetupWizard === "function") {
    window.resetRpgSetupWizard();
  }
}

let isRpgMapEditMode = false;

// ── NEW FEATURE CONTROLLERS ──────────────────────────────────────────────────

function updateQuestAchievementUI(rpgState) {
  // 1. Quests UI
  const questsList = document.getElementById("rpgQuestsList");
  if (questsList) {
    questsList.innerHTML = "";
    const quests = rpgState.active_quests || [];
    quests.forEach((q) => {
      const qDiv = document.createElement("div");
      qDiv.className = `quest-card ${q.completed ? "completed" : ""}`;
      qDiv.style.background = "rgba(255, 255, 255, 0.03)";
      qDiv.style.border = "1px solid rgba(255, 255, 255, 0.08)";
      qDiv.style.padding = "10px";
      qDiv.style.borderRadius = "8px";
      qDiv.style.display = "flex";
      qDiv.style.justifyContent = "space-between";
      qDiv.style.alignItems = "center";

      const infoDiv = document.createElement("div");
      infoDiv.style.flex = "1";
      infoDiv.innerHTML = `
        <div style="font-weight: bold; font-size: 0.9rem; color: ${q.completed ? "#2ecc71" : "#fff"};">
          ${q.completed ? "✅ " : "⏳ "}${q.description}
        </div>
        <div style="font-size: 0.8rem; color: rgba(255, 255, 255, 0.6); margin-top: 4px;">
          Tiến độ: ${q.current}/${q.target} | Thưởng: 💰 ${q.gold_reward} vàng, ✨ ${q.exp_reward} EXP
        </div>
      `;
      qDiv.appendChild(infoDiv);

      if (!q.completed) {
        const refreshBtn = document.createElement("button");
        refreshBtn.type = "button";
        refreshBtn.className = "ghost-btn small-btn";
        refreshBtn.textContent = "Đổi (2💰)";
        refreshBtn.style.padding = "4px 8px";
        refreshBtn.style.fontSize = "0.75rem";
        refreshBtn.addEventListener("click", () => refreshQuest(q.quest_id));
        qDiv.appendChild(refreshBtn);
      }

      questsList.appendChild(qDiv);
    });
  }

  // 2. Achievements UI
  const achievementsList = document.getElementById("rpgAchievementsList");
  if (achievementsList) {
    achievementsList.innerHTML = "";
    const progress = rpgState.achievements_progress || {};
    const unlocked = progress.unlocked || [];

    const achievementsConfig = [
      { id: "billionaire", name: "Tỷ phú lục địa", desc: "Tích lũy đạt 10,000 vàng.", field: "gold_accumulated", target: 10000 },
      { id: "bounty_hunter", name: "Thợ săn tiền thưởng", desc: "Hoàn thành 300 nhiệm vụ.", field: "quests_completed", target: 300 },
      { id: "butcher", name: "Kẻ đồ tể", desc: "Kết liễu 500 Kẻ lạ mặt.", field: "strangers_killed", target: 500 },
      { id: "silver_warrior", name: "Dũng sĩ giáp bạc", desc: "Tiêu diệt 50 BOSS Elite 1.", field: "elite1_defeated", target: 50 },
      { id: "gold_knight", name: "Hiệp sĩ giáp vàng", desc: "Tiêu diệt 20 BOSS Elite 2.", field: "elite2_defeated", target: 20 },
      { id: "epic_hero", name: "Anh hùng sử thi", desc: "Tiêu diệt 1 Final BOSS Alpha.", field: "final_boss_defeated", target: 1 },
      { id: "chatterbox", name: "Kẻ nhiều chuyện", desc: "Nói chuyện 1000 lần với NPC.", field: "conversations", target: 1000 },
      { id: "nomad", name: "Kẻ du mục", desc: "Di chuyển 300 lần giữa các khu vực.", field: "travels", target: 300 },
      { id: "savior", name: "Thánh nhân cứu rỗi", desc: "Tha bổng cho Kẻ lạ mặt 500 lần.", field: "strangers_spared", target: 500 }
    ];

    achievementsConfig.forEach((ach) => {
      const isUnlocked = unlocked.includes(ach.id);
      const current = progress[ach.field] || 0;
      const percent = Math.min(100, (current / ach.target) * 100);

      const achCard = document.createElement("div");
      achCard.className = `achievement-card ${isUnlocked ? "unlocked" : "locked"}`;
      achCard.style.background = isUnlocked ? "rgba(162, 115, 255, 0.1)" : "rgba(255, 255, 255, 0.02)";
      achCard.style.border = `1px solid ${isUnlocked ? "rgba(162, 115, 255, 0.3)" : "rgba(255, 255, 255, 0.05)"}`;
      achCard.style.padding = "10px";
      achCard.style.borderRadius = "8px";
      achCard.style.boxShadow = isUnlocked ? "0 0 10px rgba(162, 115, 255, 0.1)" : "none";

      achCard.innerHTML = `
        <div style="font-weight: bold; font-size: 0.85rem; color: ${isUnlocked ? "#a273ff" : "#888"};">
          ${isUnlocked ? "🏆 " : "🔒 "}${ach.name}
        </div>
        <div style="font-size: 0.75rem; color: rgba(255,255,255,0.5); margin-top: 3px; min-height: 28px;">
          ${ach.desc}
        </div>
        <div style="margin-top: 6px;">
          <div style="display:flex; justify-content:space-between; font-size:0.7rem; color:rgba(255,255,255,0.4); margin-bottom:2px;">
            <span>Tiến độ</span>
            <span>${current}/${ach.target}</span>
          </div>
          <div style="width: 100%; height: 4px; background: rgba(255,255,255,0.08); border-radius: 2px; overflow:hidden;">
            <div style="width: ${percent}%; height: 100%; background: ${isUnlocked ? "#a273ff" : "#888"};"></div>
          </div>
        </div>
      `;
      achievementsList.appendChild(achCard);
    });
  }
}

async function refreshQuest(questId) {
  if (confirm("Bạn có chắc chắn muốn dùng 2 Vàng để làm mới nhiệm vụ này?")) {
    try {
      const res = await rpgFetch(`${getApiBase()}/game/rpg/quest/refresh`, {
        method: "POST",
        body: JSON.stringify({
          session_id: currentSessionId,
          quest_id: questId
        })
      });
      appendLogEntry(res.message);
      renderState(res.rpg_state);
    } catch (err) {
      alert("Làm mới nhiệm vụ thất bại: " + err.message);
    }
  }
}

function updateDungeonUI(rpgState) {
  const dState = rpgState.dungeon_state;
  if (dState && dState.active && dState.in_safe_zone) {
    const dungeonModal = document.getElementById("rpgDungeonModal");
    if (dungeonModal && dungeonModal.classList.contains("hidden")) {
      dungeonModal.classList.remove("hidden");
    }

    // Update texts
    document.getElementById("rpgDungeonFloorText").textContent = `Ải ${dState.floor}/3`;
    document.getElementById("rpgDungeonGoldText").textContent = `${dState.accumulated_gold} vàng`;
    document.getElementById("rpgDungeonExpText").textContent = `${dState.accumulated_exp} EXP`;

    // Update items
    const itemsList = document.getElementById("rpgDungeonItemsList");
    if (itemsList) {
      itemsList.innerHTML = "";
      const items = dState.accumulated_items || [];
      if (items.length === 0) {
        itemsList.innerHTML = `<span style="font-size:0.8rem; font-style:italic; color:rgba(255,255,255,0.4);">Chưa có vật phẩm nào</span>`;
      } else {
        items.forEach((it) => {
          const chip = document.createElement("span");
          chip.className = `rpg-badge rarity rpg-glow-${it.rarity} rpg-text-${it.rarity}`;
          chip.style.fontSize = "0.75rem";
          chip.style.padding = "2px 6px";
          chip.style.margin = "2px";
          chip.textContent = it.name;
          itemsList.appendChild(chip);
        });
      }
    }
  } else {
    hideDungeonModal();
  }
}

function hideDungeonModal() {
  const dungeonModal = document.getElementById("rpgDungeonModal");
  if (dungeonModal && !dungeonModal.classList.contains("hidden")) {
    dungeonModal.classList.add("hidden");
  }
}

const MAP_ENVIRONMENTS = [
  { name: "Đồng bằng", major: "Vương đô Victoria", defaultPos: { top: 60, left: 20 }, icon: "🌾" },
  { name: "Đồi núi", major: "Long kinh thành", defaultPos: { top: 40, left: 35 }, icon: "🏔️" },
  { name: "Rừng rậm", major: "Vương đô Londinium", defaultPos: { top: 70, left: 45 }, icon: "🌳" },
  { name: "Núi lửa", major: "Tòa Thành Chúa Quỷ", defaultPos: { top: 25, left: 65 }, icon: "🌋" },
  { name: "Hoang mạc", major: "Thành Phố Tự Do", defaultPos: { top: 80, left: 75 }, icon: "🏜️" },
  { name: "Núi tuyết", major: "Pháo Đài Mùa Đông", defaultPos: { top: 15, left: 80 }, icon: "❄️" },
  { name: "Thiên giới", major: "Thánh Đường Tối Cao The Light Heavens", defaultPos: { top: 50, left: 85 }, icon: "👼" }
];

const MAP_GRAPH = {
  "Đồng bằng": ["Hoang mạc", "Rừng rậm", "Đồi núi"],
  "Hoang mạc": ["Đồng bằng", "Núi lửa", "Rừng rậm", "Núi tuyết"],
  "Núi lửa": ["Hoang mạc"],
  "Núi tuyết": ["Hoang mạc", "Đồi núi"],
  "Đồi núi": ["Đồng bằng", "Núi tuyết", "Thiên giới"],
  "Rừng rậm": ["Đồng bằng", "Hoang mạc", "Thiên giới"],
  "Thiên giới": ["Đồi núi", "Rừng rậm"]
};

function getMapDistance(start, end) {
  if (start === end) return 0;
  const queue = [[start, 0]];
  const visited = new Set([start]);
  while (queue.length > 0) {
    const [curr, dist] = queue.shift();
    if (curr === end) return dist;
    const neighbors = MAP_GRAPH[curr] || [];
    for (const neighbor of neighbors) {
      if (!visited.has(neighbor)) {
        visited.add(neighbor);
        queue.push([neighbor, dist + 1]);
      }
    }
  }
  return 1; // Fallback
}

function updateWorldMapUI(rpgState) {
  const mapArea = document.getElementById("rpgMapArea");
  if (!mapArea) return;
  mapArea.innerHTML = "";

  MAP_ENVIRONMENTS.forEach((env) => {
    let pos = env.defaultPos;
    const saved = localStorage.getItem(`rpg_map_pin_${env.name}`);
    if (saved) {
      try {
        pos = JSON.parse(saved);
      } catch (e) { }
    }

    const pin = document.createElement("div");
    pin.className = "map-pin";

    const isCurrent = (rpgState.environment === env.name) || (rpgState.environment === env.major);
    const isUnlocked = rpgState.unlocked_fast_travel && rpgState.unlocked_fast_travel.includes(env.major);

    pin.style.position = "absolute";
    pin.style.top = `${pos.top}%`;
    pin.style.left = `${pos.left}%`;
    pin.style.transform = "translate(-50%, -50%)";

    // Circle Pin styling
    pin.style.width = "38px";
    pin.style.height = "38px";
    pin.style.borderRadius = "50%";
    pin.style.display = "flex";
    pin.style.alignItems = "center";
    pin.style.justifyContent = "center";
    pin.style.fontSize = "1.25rem";
    pin.style.transition = "transform 0.2s ease, box-shadow 0.2s ease";
    pin.style.zIndex = isCurrent ? "100" : "10";
    pin.style.cursor = isRpgMapEditMode ? "grab" : "pointer";

    const distance = getMapDistance(rpgState.environment, env.name);
    const cost = distance * 100;

    if (isCurrent) {
      pin.className = "map-pin current-env-pin";
      pin.style.background = "rgba(46, 204, 113, 0.35)";
      pin.style.border = "2px solid #2ecc71";
      pin.style.color = "#fff";
      pin.style.boxShadow = "0 0 15px rgba(46, 204, 113, 0.8), inset 0 0 5px rgba(255,255,255,0.3)";
    } else {
      if (isUnlocked) {
        pin.className = "map-pin unlocked-env-pin";
        pin.style.background = "rgba(162, 115, 255, 0.35)";
        pin.style.border = "2px solid #a273ff";
        pin.style.color = "#fff";
        pin.style.boxShadow = "0 0 10px rgba(162, 115, 255, 0.6)";
      } else {
        pin.className = "map-pin locked-env-pin";
        pin.style.background = "rgba(15, 10, 25, 0.85)";
        pin.style.border = "2px solid rgba(255,255,255,0.25)";
        pin.style.color = "rgba(255,255,255,0.5)";
        pin.style.boxShadow = "0 4px 8px rgba(0,0,0,0.5)";
      }
    }

    pin.addEventListener("mouseenter", () => {
      pin.style.transform = "translate(-50%, -50%) scale(1.15)";
      if (isCurrent) {
        pin.style.boxShadow = "0 0 20px rgba(46, 204, 113, 1), inset 0 0 8px rgba(255,255,255,0.5)";
      } else if (isUnlocked) {
        pin.style.boxShadow = "0 0 15px rgba(162, 115, 255, 0.9)";
      } else {
        pin.style.boxShadow = "0 0 12px rgba(255,255,255,0.4)";
      }
    });
    pin.addEventListener("mouseleave", () => {
      pin.style.transform = "translate(-50%, -50%) scale(1)";
      if (isCurrent) {
        pin.style.boxShadow = "0 0 15px rgba(46, 204, 113, 0.8), inset 0 0 5px rgba(255,255,255,0.3)";
      } else if (isUnlocked) {
        pin.style.boxShadow = "0 0 10px rgba(162, 115, 255, 0.6)";
      } else {
        pin.style.boxShadow = "0 4px 8px rgba(0,0,0,0.5)";
      }
    });

    pin.innerHTML = `<span>${env.icon}</span>`;

    // Create detailed tooltip
    const tooltip = document.createElement("div");
    tooltip.className = "rpg-map-pin-tooltip";

    tooltip.style.position = "absolute";
    tooltip.style.display = "none";
    tooltip.style.width = "220px";
    tooltip.style.background = "rgba(10, 8, 20, 0.95)";
    tooltip.style.border = "1px solid rgba(162, 115, 255, 0.35)";
    tooltip.style.borderRadius = "8px";
    tooltip.style.padding = "10px 12px";
    tooltip.style.boxShadow = "0 8px 32px rgba(0,0,0,0.8)";
    tooltip.style.backdropFilter = "blur(12px)";
    tooltip.style.zIndex = "2000";
    tooltip.style.color = "#fff";
    tooltip.style.fontFamily = "var(--rpg-font-outfit)";
    tooltip.style.pointerEvents = "auto";
    tooltip.style.opacity = "1";
    tooltip.style.textAlign = "left";
    tooltip.style.whiteSpace = "normal";

    // Smart position helper to prevent overflow/clipping
    if (pos.top < 35) {
      tooltip.style.top = "44px";
      tooltip.style.bottom = "auto";
    } else {
      tooltip.style.bottom = "44px";
      tooltip.style.top = "auto";
    }

    if (pos.left < 25) {
      tooltip.style.left = "0";
      tooltip.style.transform = "none";
    } else if (pos.left > 75) {
      tooltip.style.right = "0";
      tooltip.style.left = "auto";
      tooltip.style.transform = "none";
    } else {
      tooltip.style.left = "50%";
      tooltip.style.transform = "translateX(-50%)";
    }

    let statusText = "";
    let actionBtnHtml = "";
    if (isCurrent) {
      statusText = `<span style="color:#2ecc71; font-weight:bold; font-size:0.75rem;">📍 Bạn đang ở đây</span>`;
    } else if (isUnlocked) {
      statusText = `<span style="color:#ffc837; font-size:0.75rem;">✨ Đã mở khóa dịch chuyển</span>`;
      actionBtnHtml = `<button class="fast-travel-btn" style="margin-top:8px; padding:6px; font-size:0.75rem; width:100%; border:none; background: linear-gradient(135deg, #a273ff 0%, #ff4fa8 100%); color:white; font-weight:bold; border-radius:4px; cursor:pointer; box-shadow: 0 4px 10px rgba(162, 115, 255, 0.4); transition: filter 0.2s;" type="button">Dịch chuyển (${cost} vàng)</button>`;
    } else {
      statusText = `<span style="color:rgba(255,255,255,0.45); font-size:0.75rem;">🔒 Chưa mở khóa</span><div style="font-size:0.65rem; color:rgba(255,255,255,0.35); margin-top:2px;">Khám phá khu vực này để mở khóa dịch chuyển</div>`;
    }

    tooltip.innerHTML = `
      <div style="font-weight:bold; font-size:0.9rem; color:#fff; display:flex; align-items:center; gap:6px; margin-bottom:4px;">
        <span>${env.icon}</span> <span>${env.name}</span>
      </div>
      <div style="font-size:0.78rem; color:rgba(255,255,255,0.6); margin-bottom:6px; font-style:italic;">🏰 ${env.major}</div>
      <div style="border-top:1px solid rgba(255,255,255,0.1); padding-top:6px; margin-top:4px;">
        ${statusText}
      </div>
      ${actionBtnHtml}
    `;

    pin.appendChild(tooltip);

    if (actionBtnHtml) {
      const travelBtn = tooltip.querySelector(".fast-travel-btn");
      if (travelBtn) {
        travelBtn.addEventListener("click", (e) => {
          e.stopPropagation();
          triggerFastTravel(env.major, cost, env.name);
        });
      }
    }

    pin.addEventListener("click", (e) => {
      if (isRpgMapEditMode) return;
      e.stopPropagation();

      const isVisible = tooltip.style.display === "block";

      // Close all other tooltips first
      const allTooltips = mapArea.querySelectorAll(".rpg-map-pin-tooltip");
      allTooltips.forEach(t => t.style.display = "none");

      if (!isVisible) {
        tooltip.style.display = "block";
      }
    });

    setupDragAndDrop(pin, env.name);
    mapArea.appendChild(pin);
  });

  // Close tooltips when clicking outside
  document.addEventListener("click", (e) => {
    if (!e.target.closest(".map-pin")) {
      const allTooltips = mapArea.querySelectorAll(".rpg-map-pin-tooltip");
      allTooltips.forEach(t => t.style.display = "none");
    }
  });
}

function setupDragAndDrop(pinEl, envName) {
  let isDragging = false;
  let startX, startY, startLeft, startTop;

  pinEl.addEventListener("mousedown", (e) => {
    if (!isRpgMapEditMode) return;
    isDragging = true;
    startX = e.clientX;
    startY = e.clientY;

    const rect = pinEl.getBoundingClientRect();
    const parentRect = document.getElementById("rpgMapArea").getBoundingClientRect();
    startLeft = rect.left - parentRect.left;
    startTop = rect.top - parentRect.top;

    pinEl.style.cursor = "grabbing";
    e.preventDefault();
  });

  document.addEventListener("mousemove", (e) => {
    if (!isDragging) return;
    const parent = document.getElementById("rpgMapArea");
    const parentRect = parent.getBoundingClientRect();

    let left = startLeft + (e.clientX - startX);
    let top = startTop + (e.clientY - startY);

    left = Math.max(0, Math.min(parentRect.width - pinEl.offsetWidth, left));
    top = Math.max(0, Math.min(parentRect.height - pinEl.offsetHeight, top));

    const leftPercent = (left / parentRect.width) * 100;
    const topPercent = (top / parentRect.height) * 100;

    pinEl.style.left = `${leftPercent}%`;
    pinEl.style.top = `${topPercent}%`;
  });

  document.addEventListener("mouseup", () => {
    if (!isDragging) return;
    isDragging = false;
    pinEl.style.cursor = isRpgMapEditMode ? "grab" : "pointer";

    const leftPercent = parseFloat(pinEl.style.left);
    const topPercent = parseFloat(pinEl.style.top);
    localStorage.setItem(`rpg_map_pin_${envName}`, JSON.stringify({ left: leftPercent, top: topPercent }));
  });
}

async function triggerFastTravel(targetRegion, cost, targetEnv) {
  if (gameState && gameState.combat && gameState.combat.is_active) {
    alert("Không thể dịch chuyển nhanh khi đang trong chiến đấu!");
    return;
  }
  if (gameState && gameState.dungeon_state && gameState.dungeon_state.active) {
    alert("Không thể dịch chuyển nhanh khi đang thám hiểm hầm ngục!");
    return;
  }

  const currentGold = (gameState && gameState.inventory && gameState.inventory.gold) || 0;
  if (currentGold < cost) {
    alert(`Không đủ vàng! Dịch chuyển đến [${targetRegion}] yêu cầu ${cost} vàng, nhưng bạn chỉ có ${currentGold} vàng.`);
    return;
  }

  if (confirm(`Bạn muốn dịch chuyển nhanh đến vương đô [${targetRegion}] của vùng đất [${targetEnv}]?\nChi phí: ${cost} vàng.`)) {
    try {
      const res = await rpgFetch(`${getApiBase()}/game/rpg/fast-travel`, {
        method: "POST",
        body: JSON.stringify({
          session_id: currentSessionId,
          target_region: targetRegion
        })
      });

      const mapModal = document.getElementById("rpgMapModal");
      if (mapModal) mapModal.classList.add("hidden");

      appendStoryBlock(res.story);
      renderChoices(res.choices, res.event_type);
      renderState(res.rpg_state);
      updatePointsDisplay();

      if (res.notifications) {
        res.notifications.forEach((notif) => appendLogEntry(notif));
      }
    } catch (err) {
      alert("Dịch chuyển nhanh thất bại: " + err.message);
    }
  }
}

async function triggerBackgroundSeeWorld() {
  if (!currentSessionId) return;
  try {
    const url = `${getApiBase()}/game/rpg/image/see-world?session_id=${encodeURIComponent(currentSessionId)}`;
    const res = await rpgFetch(url, { method: "POST" });
    if (res && res.success && res.image_url) {
      const apiBase = getApiBase();
      const baseUrl = apiBase.startsWith("http") ? apiBase : (apiBase === "/api" ? "/api" : "");
      const cleanBaseUrl = baseUrl.replace(/\/+$/, "");
      let imgUrl = res.image_url;
      if (!imgUrl.startsWith("http")) {
        if (imgUrl.startsWith("/")) {
          imgUrl = imgUrl.substring(1);
        }
        imgUrl = `${cleanBaseUrl}/${imgUrl}`;
      }

      window.lastSeeWorldImageUrl = imgUrl;

      const ambient = document.getElementById("rpgAmbientOverlay");
      if (ambient) {
        ambient.style.backgroundImage = `url('${imgUrl}?t=${Date.now()}')`;
        ambient.style.backgroundSize = "cover";
        ambient.style.backgroundPosition = "center";
        ambient.style.opacity = "0.15";
      }
    }
  } catch (err) {
    console.error("Background see-world error:", err);
  }
}

function initRpgQuestController() {
  const questModal = document.getElementById("rpgQuestModal");
  const closeQuestBtn = document.getElementById("rpgCloseQuestBtn");
  const questBackdrop = document.getElementById("rpgQuestBackdrop");
  const questNavBtn = document.getElementById("rpgQuestBtn"); // Topbar button

  if (closeQuestBtn && questModal) {
    closeQuestBtn.addEventListener("click", () => questModal.classList.add("hidden"));
  }
  if (questBackdrop && questModal) {
    questBackdrop.addEventListener("click", () => questModal.classList.add("hidden"));
  }
  if (questNavBtn && questModal) {
    questNavBtn.addEventListener("click", () => {
      questModal.classList.toggle("hidden");
      if (!questModal.classList.contains("hidden") && gameState) {
        updateQuestAchievementUI(gameState);
      }
    });
  }

  const tabQuestsBtn = document.getElementById("rpgTabQuestsBtn");
  const tabAchievementsBtn = document.getElementById("rpgTabAchievementsBtn");
  const tabQuestsContent = document.getElementById("rpgTabQuestsContent");
  const tabAchievementsContent = document.getElementById("rpgTabAchievementsContent");

  if (tabQuestsBtn && tabAchievementsBtn && tabQuestsContent && tabAchievementsContent) {
    tabQuestsBtn.addEventListener("click", () => {
      tabQuestsBtn.classList.add("active-tab-btn");
      tabQuestsBtn.style.color = "white";
      tabQuestsBtn.style.fontWeight = "bold";

      tabAchievementsBtn.classList.remove("active-tab-btn");
      tabAchievementsBtn.style.color = "rgba(255,255,255,0.5)";
      tabAchievementsBtn.style.fontWeight = "normal";

      tabQuestsContent.classList.remove("hidden");
      tabAchievementsContent.classList.add("hidden");
    });

    tabAchievementsBtn.addEventListener("click", () => {
      tabAchievementsBtn.classList.add("active-tab-btn");
      tabAchievementsBtn.style.color = "white";
      tabAchievementsBtn.style.fontWeight = "bold";

      tabQuestsBtn.classList.remove("active-tab-btn");
      tabQuestsBtn.style.color = "rgba(255,255,255,0.5)";
      tabQuestsBtn.style.fontWeight = "normal";

      tabAchievementsContent.classList.remove("hidden");
      tabQuestsContent.classList.add("hidden");
    });
  }
}

function initRpgMapController() {
  const mapModal = document.getElementById("rpgMapModal");
  const closeMapBtn = document.getElementById("rpgCloseMapBtn");
  const mapBackdrop = document.getElementById("rpgMapBackdrop");
  const mapNavBtn = document.getElementById("rpgMapBtn"); // Topbar button

  if (closeMapBtn && mapModal) {
    closeMapBtn.addEventListener("click", () => mapModal.classList.add("hidden"));
  }
  if (mapBackdrop && mapModal) {
    mapBackdrop.addEventListener("click", () => mapModal.classList.add("hidden"));
  }
  if (mapNavBtn && mapModal) {
    mapNavBtn.addEventListener("click", () => {
      if (gameState && gameState.combat && gameState.combat.is_active) return;
      mapModal.classList.toggle("hidden");
      if (!mapModal.classList.contains("hidden")) {
        if (document.activeElement) document.activeElement.blur();
        if (gameState) {
          updateWorldMapUI(gameState);
        }
      }
    });
  }
}

function toggleRpgMapMode() {
  isRpgMapEditMode = !isRpgMapEditMode;
  const badge = document.getElementById("rpgMapModeBadge");
  const subtitle = document.getElementById("rpgMapSubtitle");
  if (isRpgMapEditMode) {
    if (badge) {
      badge.textContent = "Chỉnh sửa 🛠️";
      badge.style.background = "rgba(231, 76, 60, 0.12)";
      badge.style.borderColor = "rgba(231, 76, 60, 0.3)";
      badge.style.color = "#e74c3c";
    }
    if (subtitle) {
      subtitle.textContent = "🛠️ CHẾ ĐỘ CHỈNH SỬA: Kéo thả các vùng đất để tùy biến vị trí bản đồ thế giới của riêng bạn.";
    }
  } else {
    if (badge) {
      badge.textContent = "Xem 👁️";
      badge.style.background = "rgba(162, 115, 255, 0.12)";
      badge.style.borderColor = "rgba(162, 115, 255, 0.3)";
      badge.style.color = "#b862ff";
    }
    if (subtitle) {
      subtitle.textContent = "Khám phá các vùng đất. Dịch chuyển nhanh đến kiến trúc lớn đã mở khóa.";
    }
  }
  if (gameState) updateWorldMapUI(gameState);
}

function initRpgDungeonController() {
  const dungeonModal = document.getElementById("rpgDungeonModal");
  const closeDungeonBtn = document.getElementById("rpgCloseDungeonBtn");
  const dungeonBackdrop = document.getElementById("rpgDungeonBackdrop");

  if (closeDungeonBtn && dungeonModal) {
    closeDungeonBtn.addEventListener("click", () => dungeonModal.classList.add("hidden"));
  }
  if (dungeonBackdrop && dungeonModal) {
    dungeonBackdrop.addEventListener("click", () => dungeonModal.classList.add("hidden"));
  }

  const continueBtn = document.getElementById("rpgDungeonContinueBtn");
  const leaveBtn = document.getElementById("rpgDungeonLeaveBtn");

  if (continueBtn && leaveBtn) {
    continueBtn.addEventListener("click", () => {
      dungeonModal.classList.add("hidden");
      handleChoiceClick(0, "Tiếp tục thám hiểm hầm ngục", null);
    });

    leaveBtn.addEventListener("click", () => {
      dungeonModal.classList.add("hidden");
      handleChoiceClick(1, "Rút lui khỏi hầm ngục", null);
    });
  }
}

function initRpgHelpController() {
  const helpModal = document.getElementById("rpgHelpModal");
  const closeHelpBtn = document.getElementById("rpgCloseHelpBtn");
  const helpBackdrop = document.getElementById("rpgHelpBackdrop");
  const helpNavBtn = document.getElementById("rpgHelpNavBtn");

  if (closeHelpBtn && helpModal) {
    closeHelpBtn.addEventListener("click", () => helpModal.classList.add("hidden"));
  }
  if (helpBackdrop && helpModal) {
    helpBackdrop.addEventListener("click", () => helpModal.classList.add("hidden"));
  }
  if (helpNavBtn && helpModal) {
    helpNavBtn.addEventListener("click", () => helpModal.classList.remove("hidden"));
  }
}

function validateDebugCommand(cmd) {
  const c = cmd.trim();
  if (!c) {
    return "Vui lòng nhập câu lệnh.";
  }

  // 1. game_over
  if (c === "game_over") return null;

  // 2. gain_gold_{n}
  let match = c.match(/^gain_gold_(\d+)$/);
  if (match) {
    const val = parseInt(match[1], 10);
    if (isNaN(val) || val < 0) return "Số vàng n phải lớn hơn hoặc bằng 0.";
    return null;
  }
  if (c.startsWith("gain_gold_")) {
    return "Sai cú pháp lệnh gain_gold_{n}. Ví dụ: gain_gold_500";
  }

  // 3. gain_exp_{n}
  match = c.match(/^gain_exp_(\d+)$/);
  if (match) {
    const val = parseInt(match[1], 10);
    if (isNaN(val) || val < 0) return "Số exp n phải lớn hơn hoặc bằng 0.";
    return null;
  }
  if (c.startsWith("gain_exp_")) {
    return "Sai cú pháp lệnh gain_exp_{n}. Ví dụ: gain_exp_1000";
  }

  // 4. gain_maxlvl
  if (c === "gain_maxlvl") return null;

  // 5. revive
  if (c === "revive") return null;

  // 6. gain_{type}_{rarity}_{n}
  match = c.match(/^gain_(weapon|armor|consume)_(mythic|legendary|epic|rare|uncommon|common)_(\d+)$/i);
  if (match) {
    const val = parseInt(match[3], 10);
    if (isNaN(val) || val <= 0) return "Số lượng vật phẩm n phải lớn hơn 0.";
    return null;
  }
  if (c.startsWith("gain_") && c.split("_").length >= 4) {
    const parts = c.split("_");
    if (["weapon", "armor", "consume"].includes(parts[1].toLowerCase())) {
      return "Sai cú pháp lệnh gain_{type}_{rarity}_{n}. type phải là weapon/armor/consume, rarity phải là mythic/legendary/epic/rare/uncommon/common, n phải là số nguyên dương.";
    }
  }

  // 7. go_to_{direct}_{region}
  match = c.match(/^go_to_(M|W|E|NE|SW|SE|NW)_(main|sub|dungeon|none)$/i);
  if (match) return null;
  if (c.startsWith("go_to_")) {
    return "Sai cú pháp lệnh go_to_{direct}_{region}. Hướng direct phải là M/W/E/NE/SW/SE/NW, region phải là main/sub/dungeon/none.";
  }

  // 8. meet_{character}
  match = c.match(/^meet_(merchant|monk|npc|mythic|legendary|epic|rare|uncommon|common)$/i);
  if (match) {
    const target = match[1].toLowerCase();
    if (gameState) {
      const currentLoc = gameState.current_region;
      if (target === "mythic") {
        const allowedVươngĐô = [
          "Vương đô Victoria", "Long kinh thành", "Tòa Thành Chúa Quỷ",
          "Pháo Đài Mùa Đông", "Thánh Đường Tối Cao The Light Heavens"
        ];
        if (!allowedVươngĐô.includes(currentLoc)) {
          return `Không thể gặp Mythic tại vị trí này. Mythic chỉ xuất hiện tại các vương đô lớn.`;
        }
      }

      if (currentLoc === "Hang tối") {
        if (["merchant", "monk", "npc", "epic", "rare", "mythic"].includes(target)) {
          return `Vị trí Hang tối không hỗ trợ gặp ${target}. (Chỉ cho phép Legendary, Uncommon, Common)`;
        }
      }
    }
    return null;
  }
  if (c.startsWith("meet_")) {
    return "Sai cú pháp lệnh meet_{character}. Nhân vật/độ hiếm phải là merchant/monk/npc hoặc mythic/legendary/epic/rare/uncommon/common.";
  }

  // 9. recruit_{race}_{class}_{gender}
  match = c.match(/^recruit_(valkyrie|angel|devil|elf|royalty|orc|goblin|human)_(defender|guard|caster|sniper|supporter)_(male|female)$/i);
  if (match) {
    const race = match[1].toLowerCase();
    const cls = match[2].toLowerCase();

    const raceClasses = {
      valkyrie: ["defender", "guard", "caster", "sniper"],
      angel: ["caster", "supporter"],
      devil: ["defender", "caster"],
      elf: ["sniper", "supporter"],
      royalty: ["guard", "supporter"],
      orc: ["defender", "guard"],
      goblin: ["guard", "sniper"],
      human: ["defender", "guard", "caster", "sniper", "supporter"]
    };

    const allowed = raceClasses[race] || [];
    if (!allowed.includes(cls)) {
      return `Chủng tộc ${race.toUpperCase()} không thể có lớp nhân vật ${cls.toUpperCase()}. Lớp hợp lệ: ${allowed.map(x => x.toUpperCase()).join(", ")}.`;
    }
    return null;
  }
  if (c.startsWith("recruit_")) {
    return "Sai cú pháp lệnh recruit_{race}_{class}_{gender}. race phải là valkyrie/angel/devil/elf/royalty/orc/goblin/human, class phải là defender/guard/caster/sniper/supporter, gender phải là male/female.";
  }

  // 10. found_item
  if (c === "found_item") return null;

  // 11. gain_keys
  if (c === "gain_keys") return null;

  // 12. good_ending
  if (c === "good_ending") return null;

  // 13. bad_ending
  if (c === "bad_ending") return null;

  // 14. continue_ending
  if (c === "continue_ending") return null;

  // 15. combat_{type}
  match = c.match(/^combat_(kill|recruit|forgive)$/i);
  if (match) {
    if (!gameState || !gameState.combat || !gameState.combat.is_active) {
      return "Lệnh này chỉ có thể sử dụng khi đang chiến đấu.";
    }
    const type = match[1].toLowerCase();
    if ((type === "recruit" || type === "forgive") && gameState.dungeon_state && gameState.dungeon_state.active) {
      return "Lệnh combat_recruit và combat_forgive không áp dụng trong Hầm ngục.";
    }
    return null;
  }

  // 16. dummy_combat and dummy_*
  if (c === "dummy_combat") return null;
  if (c === "dummy_kill" || c === "dummy_reset" || c === "dummy_recharge" || c === "dummy_revive" || c === "dummy_restore") {
    if (!gameState || !gameState.combat || !gameState.combat.is_active || gameState.combat.enemy.character_id !== "dummy") {
      return "Lệnh này chỉ có thể sử dụng khi đang đấu tập với Dummy.";
    }
    return null;
  }

  match = c.match(/^dummy_drain_(\d+)$/);
  if (match) {
    if (!gameState || !gameState.combat || !gameState.combat.is_active || gameState.combat.enemy.character_id !== "dummy") {
      return "Lệnh này chỉ có thể sử dụng khi đang đấu tập với Dummy.";
    }
    const n = parseInt(match[1], 10);
    if (isNaN(n) || n < 1 || n >= 100) return "Tỷ lệ n phải nằm trong khoảng từ 1 đến 99.";
    return null;
  }

  match = c.match(/^dummy_drain_party_(\d+)$/);
  if (match) {
    if (!gameState || !gameState.combat || !gameState.combat.is_active || gameState.combat.enemy.character_id !== "dummy") {
      return "Lệnh này chỉ có thể sử dụng khi đang đấu tập với Dummy.";
    }
    const n = parseInt(match[1], 10);
    if (isNaN(n) || n < 1 || n >= 100) return "Tỷ lệ n phải nằm trong khoảng từ 1 đến 99.";
    return null;
  }

  // 17. boss_e1_{character}_combat
  match = c.match(/^boss_e1_(medusa|goblin|werewolf|dracula|golem)_combat$/i);
  if (match) return null;

  // 18. boss_e2_{character}_combat
  match = c.match(/^boss_e2_(fishman|devil|dragon|undead)_combat$/i);
  if (match) return null;

  // 19. final_boss_combat
  if (c === "final_boss_combat") return null;

  return "Không nhận diện được lệnh debug. Vui lòng kiểm tra lại cú pháp.";
}

function initRpgDebugConsoleController() {
  const debugModal = document.getElementById("rpgDebugConsoleModal");
  const closeBtn = document.getElementById("rpgCloseDebugConsoleBtn");
  const backdrop = document.getElementById("rpgDebugConsoleBackdrop");
  const submitBtn = document.getElementById("rpgSubmitDebugBtn");
  const inputEl = document.getElementById("rpgDebugInput");
  const errorEl = document.getElementById("rpgDebugError");
  const successEl = document.getElementById("rpgDebugSuccess");

  if (closeBtn && debugModal) {
    closeBtn.addEventListener("click", () => debugModal.classList.add("hidden"));
  }
  if (backdrop && debugModal) {
    backdrop.addEventListener("click", () => debugModal.classList.add("hidden"));
  }

  async function handleSubmit() {
    if (!currentSessionId) {
      if (errorEl) {
        errorEl.textContent = "Không tìm thấy session game đang chạy.";
        errorEl.style.display = "block";
      }
      return;
    }
    const cmd = inputEl.value.trim();
    if (errorEl) errorEl.style.display = "none";
    if (successEl) successEl.style.display = "none";

    const validationError = validateDebugCommand(cmd);
    if (validationError) {
      if (errorEl) {
        errorEl.textContent = validationError;
        errorEl.style.display = "block";
      }
      return;
    }

    try {
      submitBtn.disabled = true;
      submitBtn.textContent = "Đang thực thi...";

      const res = await rpgFetch(`${getApiBase()}/game/rpg/debug/command`, {
        method: "POST",
        body: JSON.stringify({
          session_id: currentSessionId,
          command: cmd
        })
      });

      if (successEl) {
        successEl.textContent = "Thực thi lệnh debug thành công!";
        successEl.style.display = "block";
      }

      // Sync state and render
      if (res.rpg_state) {
        renderState(res.rpg_state);
        if (!res.rpg_state.combat || !res.rpg_state.combat.is_active) {
          hideCombatOverlay();
        }
      }

      // Append narrative log
      if (res.story) {
        appendStoryBlock(res.story);
      }

      // If narrative choices are returned, render them
      if (res.choices && res.choices.length > 0) {
        renderChoices(res.choices, res.rpg_state ? res.rpg_state.current_event : null);
      }

      // Clear input
      inputEl.value = "";

      // Close modal after brief delay to show success
      setTimeout(() => {
        debugModal.classList.add("hidden");
      }, 800);

    } catch (err) {
      if (errorEl) {
        errorEl.textContent = "Lỗi thực thi: " + err.message;
        errorEl.style.display = "block";
      }
    } finally {
      submitBtn.disabled = false;
      submitBtn.textContent = "Thực thi lệnh";
    }
  }

  if (submitBtn && inputEl) {
    submitBtn.addEventListener("click", handleSubmit);
    inputEl.addEventListener("keydown", (e) => {
      if (e.key === "Enter") {
        handleSubmit();
        e.preventDefault();
      }
    });
  }
}

function initRpgKeyboardShortcuts() {
  document.addEventListener("keydown", (e) => {
    const rpgPage = document.getElementById("rpgPage");
    if (!rpgPage || !rpgPage.classList.contains("active")) {
      return;
    }

    const key = e.key.toUpperCase();
    const mapModal = document.getElementById("rpgMapModal");
    const isMapOpen = mapModal && !mapModal.classList.contains("hidden");

    // If map modal is open, prioritize map hotkeys even if input is focused
    if (isMapOpen) {
      if (key === "E") {
        toggleRpgMapMode();
        e.preventDefault();
        return;
      }
      if (key === "M" || e.key === "Escape") {
        mapModal.classList.add("hidden");
        e.preventDefault();
        return;
      }
    }

    const activeEl = document.activeElement;
    if (activeEl && (
      activeEl.tagName === "INPUT" ||
      activeEl.tagName === "TEXTAREA" ||
      activeEl.isContentEditable
    )) {
      return;
    }

    if (key === "T") {
      const debugModal = document.getElementById("rpgDebugConsoleModal");
      if (debugModal) {
        debugModal.classList.toggle("hidden");
        if (!debugModal.classList.contains("hidden")) {
          const input = document.getElementById("rpgDebugInput");
          if (input) {
            input.value = "";
            setTimeout(() => input.focus(), 50);
          }
          const errDiv = document.getElementById("rpgDebugError");
          const succDiv = document.getElementById("rpgDebugSuccess");
          if (errDiv) errDiv.style.display = "none";
          if (succDiv) succDiv.style.display = "none";
        }
      }
      e.preventDefault();
    }

    if (key === "Q") {
      const questModal = document.getElementById("rpgQuestModal");
      if (questModal) {
        questModal.classList.toggle("hidden");
        if (!questModal.classList.contains("hidden") && gameState) {
          updateQuestAchievementUI(gameState);
        }
      }
      e.preventDefault();
    }

    if (key === "M") {
      if (gameState && gameState.combat && gameState.combat.is_active) {
        return;
      }
      if (mapModal) {
        mapModal.classList.toggle("hidden");
        if (!mapModal.classList.contains("hidden")) {
          if (document.activeElement) document.activeElement.blur();
          if (gameState) {
            updateWorldMapUI(gameState);
          }
        }
      }
      e.preventDefault();
    }

    if (key === "E") {
      if (mapModal && !mapModal.classList.contains("hidden")) {
        toggleRpgMapMode();
      }
      e.preventDefault();
    }

    if (key === "I") {
      const container = document.querySelector(".rpg-grid-container");
      if (container) {
        container.classList.toggle("player-hidden");
      }
      e.preventDefault();
    }

    if (key === "N") {
      const container = document.querySelector(".rpg-grid-container");
      if (container) {
        container.classList.toggle("npc-hidden");
      }
      e.preventDefault();
    }

    if (key === "S") {
      const seeWorldBtn = document.getElementById("rpgSeeWorldBtn");
      if (seeWorldBtn) {
        seeWorldBtn.click();
      }
      e.preventDefault();
    }

    if (e.key === "?") {
      const helpModal = document.getElementById("rpgHelpModal");
      if (helpModal) {
        helpModal.classList.toggle("hidden");
      }
      e.preventDefault();
    }
  });
}

// Expose to window namespace for main app integration
window.RPGApp = {
  resumeSession,
  renderState,
  initRPGApp,
  getCurrentSessionId: () => currentSessionId,
  isSessionSaved: () => currentSessionIsSaved,
  setSessionSaved: (val) => { currentSessionIsSaved = val; },
  clearSession
};
console.log("Chronicles of Destiny RPG Engine loaded successfully.");
