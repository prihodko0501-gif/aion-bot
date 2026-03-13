const tg = window.Telegram && window.Telegram.WebApp ? window.Telegram.WebApp : null;
if (tg) {
  tg.ready();
  tg.expand();
}

const API = window.location.origin;
let currentDays = 7;

function qs(id) {
  return document.getElementById(id);
}

function setText(id, value) {
  const el = qs(id);
  if (el) el.textContent = value ?? "—";
}

function showScreen(id) {
  document.querySelectorAll(".screen").forEach(el => el.classList.remove("active"));
  const target = qs(id);
  if (target) target.classList.add("active");

  if (id === "screen-history") loadHistory(currentDays);
  if (id === "screen-home" || id === "screen-dashboard" || id === "screen-sleep") loadDashboard();
}

qs("enterBtn")?.addEventListener("click", () => showScreen("screen-dashboard"));

document.querySelectorAll("[data-open]").forEach(btn => {
  btn.addEventListener("click", () => showScreen(btn.dataset.open));
});

async function loadDashboard() {
  try {
    const res = await fetch(API + "/api/dashboard", { cache: "no-store" });
    const json = await res.json();
    const d = json.data || json || {};

    const biotime = d.biotime != null ? d.biotime : "—";
    setText("homeBiotime", biotime);

    if (d.sleep != null) {
      setText("sleepScoreValue", Math.round(Number(d.sleep)));
    }
  } catch (e) {
    console.error("dashboard error", e);
  }
}

async function loadHistory(days = 7) {
  currentDays = Number(days);
  const list = qs("historyList");
  if (!list) return;

  list.innerHTML = '<div class="history-empty">Загрузка...</div>';

  try {
    const res = await fetch(API + "/api/history?days=" + currentDays, { cache: "no-store" });
    const json = await res.json();
    const rows = Array.isArray(json.data) ? json.data : [];

    if (!rows.length) {
      list.innerHTML = '<div class="history-empty">Нет данных за ' + currentDays + ' дней</div>';
      return;
    }

    list.innerHTML = "";

    rows.slice().reverse().forEach(row => {
      const item = document.createElement("div");
      item.className = "history-item";
      item.innerHTML = `
        <div class="history-top">
          <div>
            <div style="font-size:20px;">BioTime ${row.biotime ?? "—"}</div>
            <div class="history-date">${row.date ?? "—"}</div>
          </div>
          <div class="history-date">${row.pressure ?? "—"}</div>
        </div>
        <div class="history-grid">
          <div>Sleep<br><strong>${row.sleep ?? "—"}</strong></div>
          <div>Stress<br><strong>${row.stress ?? "—"}</strong></div>
          <div>Recovery<br><strong>${row.recovery ?? "—"}</strong></div>
        </div>
      `;
      list.appendChild(item);
    });
  } catch (e) {
    console.error("history error", e);
    list.innerHTML = '<div class="history-empty">Ошибка загрузки истории</div>';
  }
}

document.querySelectorAll(".historyBtn").forEach(btn => {
  btn.addEventListener("click", () => {
    document.querySelectorAll(".historyBtn").forEach(b => b.classList.remove("active"));
    btn.classList.add("active");
    loadHistory(btn.dataset.days);
  });
});

qs("saveBtn")?.addEventListener("click", async () => {
  const saveStatus = qs("saveStatus");
  if (saveStatus) {
    saveStatus.className = "save-status";
    saveStatus.textContent = "Сохранение...";
  }

  const sleep = qs("sleepInput")?.value.trim();
  const stress = qs("stressInput")?.value.trim();
  const recovery = qs("recoveryInput")?.value.trim();
  const systolic = qs("systolicInput")?.value.trim();
  const diastolic = qs("diastolicInput")?.value.trim();

  const payload = { sleep, stress, recovery };
  if (systolic && diastolic) {
    payload.systolic = systolic;
    payload.diastolic = diastolic;
  }

  try {
    const res = await fetch(API + "/api/entry", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload)
    });

    const json = await res.json();

    if (!res.ok || !json.ok) {
      throw new Error(json.error || "Ошибка сохранения");
    }

    const d = json.data || {};
    setText("resultBiotime", d.biotime ?? "—");
    setText("resultDate", "Данные сохранены");

    if (saveStatus) {
      saveStatus.className = "save-status ok";
      saveStatus.textContent = "Сохранено в PostgreSQL";
    }

    await loadDashboard();
    await loadHistory(currentDays);
  } catch (e) {
    console.error("save error", e);
    if (saveStatus) {
      saveStatus.className = "save-status err";
      saveStatus.textContent = e.message || "Ошибка";
    }
  }
});

loadDashboard();
loadHistory(7);
