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

function getRaceEmoji(race) {
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
      chessOrbs += `<span class="valk-chess-orb" title="Quân cờ ${i+1}">⚫</span>`;
    }
    indicatorsHtml += `<div class="valk-special-indicators valk-wang-chess" title="Số quân cờ đang vây hãm">${chessOrbs}</div>`;
  }
  
  // 2. Lemuen (Sniper) Bullet Slots
  if (char.race === "Valkyrie" && char.char_class === "Sniper" && skills.bullet_count !== undefined) {
    let bullets = "";
    for (let i = 0; i < 5; i++) {
      if (i < skills.bullet_count) {
        bullets += `<span class="valk-bullet loaded" title="Đạn nạp sẵn: ${i+1}">⚡</span>`;
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

function getItemEmoji(itemType) {
  switch (itemType) {
    case "Weapon": return "🗡️";
    case "Armor": return "🛡️";
    case "Consume": return "🧪";
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
function getCharacterImageFilename(char) {
  if (!char) return null;
  const nameLower = char.name.toLowerCase();
  if (nameLower.includes("hoshiguma")) return "Hoshiguma_the_breacher.png";
  if (nameLower.includes("vina victoria") || nameLower.includes("vinavictoria") || nameLower.includes("vina_victoria")) return "VinaVictoria.png";
  if (nameLower.includes("wang")) return "Wang.png";
  if (nameLower.includes("lemuen") || nameLower.includes("lumuen")) return "Lemuen.png";
  
  if (char.character_id === "player") return "player_avatar.png";
  if (char.character_id === "monk") return "monk.png";
  if (char.character_id === "merchant") return "merchant.png";
  
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
  if (char.character_id === "player") {
    fallbackEmoji = char.gender === "Male" ? "🧔" : "👩";
  } else if (char.character_id === "monk") {
    fallbackEmoji = "🧘";
  } else if (char.character_id === "merchant") {
    fallbackEmoji = "🛒";
  } else if (char.race) {
    fallbackEmoji = getRaceEmoji(char.race);
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
  document.getElementById("rpgDetailsCharIcon").textContent = getRaceEmoji(char.race);
  document.getElementById("rpgDetailsCharRarity").textContent = getRarityLabel(char.rarity);
  document.getElementById("rpgDetailsCharRarity").className = `eyebrow rpg-text-${char.rarity}`;
  document.getElementById("rpgDetailsCharName").textContent = char.name;
  document.getElementById("rpgDetailsCharSub").textContent = `Lv.${char.level} - Tộc: ${char.race} - Lớp: ${char.char_class}`;

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
        <div class="party-avatar-circle" title="${c.race} ${c.char_class}">
          ${getRaceEmoji(c.race)}
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
        ${getItemEmoji(item.item_type)}
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
  }

  if (npc) {
    nameEl.textContent = npc.name;
    nameEl.className = `rpg-text-${npc.rarity}`;
    if (npcIconEl) npcIconEl.textContent = getRaceEmoji(npc.race);
    setupAvatarDisplay(npcImg, npcDefault, npc);

    rarityEl.textContent = getRarityLabel(npc.rarity);
    rarityEl.className = `rpg-badge rarity rpg-glow-${npc.rarity} rpg-text-${npc.rarity}`;

    raceEl.textContent = npc.race;
    classEl.textContent = npc.char_class;

    descEl.textContent = npc.condition === "Bình thường"
      ? `Một thực thể thuộc tộc ${npc.race}, đảm nhận vai trò ${npc.char_class}. Trạng thái chiến đấu tốt.`
      : `Thực thể này đang ${npc.condition}. Hãy cẩn trọng.`;

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
      setupAvatarDisplay(npcImg, npcDefault, { character_id: "merchant", name: "merchant" });
      rarityEl.textContent = "Thương Nhân";
      rarityEl.className = "rpg-badge rarity";
      raceEl.textContent = "-";
      classEl.textContent = "-";
      descEl.textContent = "Một thương nhân bí hiểm đang bày bán trang bị quý hiếm và chào mời lính đánh thuê gia nhập.";
    } else if (rpgState.current_event === "monk") {
      nameEl.textContent = "Tu Sĩ Đạo Nhân";
      nameEl.className = "";
      if (npcIconEl) npcIconEl.textContent = "🧘";
      setupAvatarDisplay(npcImg, npcDefault, { character_id: "monk", name: "monk" });
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
    "Thu thập vật phẩm cho vào túi"
  ];

  choices.forEach((choice, index) => {
    const btn = document.createElement("button");
    btn.type = "button";
    btn.className = "rpg-choice-btn";

    // Highlight Red border for special event trigger choices
    const isSpecial = index === 0 && triggers.includes(choice);
    if (isSpecial) {
      btn.classList.add("special-event-trigger");
    }

    btn.innerHTML = `
      <span class="choice-bullet">${isSpecial ? "⚡" : `${index + 1}.`}</span>
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
  } else if (item.item_type === "Consume") {
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
      <span>${getRaceEmoji(c.race)} ${c.name} (${c.char_class})</span>
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
      <h4 class="rpg-text-${item.rarity}">${getItemEmoji(item.item_type)} ${item.name} ${item.quantity > 1 ? `(x${item.quantity})` : ""}</h4>
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
  const mercPrices = { "Mythic": 800, "Legendary": 600, "Epic": 400, "Rare": 200, "Uncommon": 100, "Common": 50 };

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
        <h4 class="rpg-text-${item.rarity}">${getItemEmoji(item.item_type)} ${item.name}</h4>
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
      card.querySelector("button").addEventListener("click", () => buyMercenary(index, merc.name, price));
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
          <h4 class="rpg-text-${item.rarity}">${getItemEmoji(item.item_type)} ${item.name} ${item.quantity > 1 ? `(x${item.quantity})` : ""}</h4>
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

async function buyMercenary(index, mercName, price) {
  try {
    const res = await rpgFetch(`${getApiBase()}/game/rpg/shop/buy-merc`, {
      method: "POST",
      body: JSON.stringify({
        session_id: currentSessionId,
        merc_index: index
      })
    });
    appendLogEntry(`Đã tuyển mộ đồng hành mới: ${mercName} (-${price} Vàng)`);
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
          <h4 class="rpg-text-${c.rarity}" style="margin:0; font-size:0.85rem;">${getRaceEmoji(c.race)} ${c.name}</h4>
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
    const isAutoFiring = c.special_skills && c.special_skills.skill_1_activating;
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
    if (skillsObj.skill_1) {
      const opt = document.createElement("option");
      opt.value = "skill_1";
      const cooldown = skillsObj.skill_1_countdown || 0;
      if (cooldown > 0) {
        opt.textContent = `Chiêu 1: ${skillsObj.skill_1} [Hồi chiêu: ${cooldown}t]`;
        opt.disabled = true;
      } else {
        opt.textContent = `Chiêu 1: ${skillsObj.skill_1}`;
      }
      skillSelect.appendChild(opt);
    }
    if (skillsObj.skill_2) {
      const opt = document.createElement("option");
      opt.value = "skill_2";
      const cooldown = skillsObj.skill_2_countdown || 0;
      if (cooldown > 0) {
        opt.textContent = `Tuyệt Kỹ: ${skillsObj.skill_2} [Hồi chiêu: ${cooldown}t]`;
        opt.disabled = true;
      } else {
        opt.textContent = `Tuyệt Kỹ: ${skillsObj.skill_2}`;
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
      showCombatOverlay(res.combat_state);

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
          document.getElementById("rpgCombatEndOverlay").classList.remove("hidden");
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
  // Bind post-victory buttons
  const endActionBtns = document.querySelectorAll("#rpgCombatEndOverlay .end-action-btn");
  endActionBtns.forEach(btn => {
    btn.addEventListener("click", async () => {
      const action = btn.dataset.action; // "loot", "recruit", "leave"

      btn.disabled = true;
      try {
        const res = await rpgFetch(`${getApiBase()}/game/rpg/combat/end-action`, {
          method: "POST",
          body: JSON.stringify({
            session_id: currentSessionId,
            action: action
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
    seeWorldBtn.addEventListener("click", async () => {
      // Open modal
      worldImgModal.classList.remove("hidden");
      // Show spinner, hide image
      worldImgSpinner.style.display = "flex";
      worldImgView.style.display = "none";
      if (worldImgSpinnerText) {
        worldImgSpinnerText.textContent = "Đang kết nối backend sinh hình ảnh thế giới...";
      }

      try {
        const url = `${getApiBase()}/game/rpg/image/see-world?session_id=${encodeURIComponent(currentSessionId)}`;
        const res = await rpgFetch(url, { method: "POST" });
        if (res && res.success && res.image_url) {
          // Bypass browser cache by appending current timestamp
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
      return { character_id: "monk", name: "monk" };
    } else if (gameState.current_event === "merchant") {
      return { character_id: "merchant", name: "merchant" };
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

  // Saves tab navigation binding
  const savesBtn = document.getElementById("rpgSavesNavBtn");
  if (savesBtn) {
    savesBtn.addEventListener("click", () => {
      // Toggle global Saves view in main app
      const savesTabBtn = document.getElementById("savesTabBtn");
      if (savesTabBtn) savesTabBtn.click();
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
