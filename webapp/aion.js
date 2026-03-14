const screens = {
  home: document.getElementById("screen-home"),
  modules: document.getElementById("screen-modules"),
  sleep: document.getElementById("screen-sleep"),
};

const navItems = Array.from(document.querySelectorAll(".nav-item"));

function openScreen(name) {
  Object.values(screens).forEach((screen) => screen.classList.remove("active"));
  screens[name].classList.add("active");

  navItems.forEach((item) => item.classList.remove("active"));

  if (name === "home") {
    document.querySelector('[data-nav-home]')?.classList.add("active");
  }
  if (name === "modules") {
    document.querySelector('[data-nav-modules]')?.classList.add("active");
  }
  if (name === "sleep") {
    document.querySelector('[data-nav-sleep]')?.classList.add("active");
  }
}

async function loadBioTime() {
  try {
    const response = await fetch("/api/biotime");
    const data = await response.json();
    const target = document.getElementById("biotimeValue");
    if (target && data.value !== undefined) {
      target.textContent = data.value;
    }
  } catch (e) {
    console.log("BioTime load error", e);
  }
}

document.getElementById("enterSystemBtn")?.addEventListener("click", () => {
  openScreen("modules");
});

document.querySelectorAll("[data-open-sleep]").forEach((btn) => {
  btn.addEventListener("click", () => openScreen("sleep"));
});

document.querySelectorAll("[data-back-home]").forEach((btn) => {
  btn.addEventListener("click", () => openScreen("home"));
});

document.querySelectorAll("[data-back-modules]").forEach((btn) => {
  btn.addEventListener("click", () => openScreen("modules"));
});

document.querySelectorAll("[data-nav-home]").forEach((btn) => {
  btn.addEventListener("click", () => openScreen("home"));
});

document.querySelectorAll("[data-nav-modules]").forEach((btn) => {
  btn.addEventListener("click", () => openScreen("modules"));
});

document.querySelectorAll("[data-nav-sleep]").forEach((btn) => {
  btn.addEventListener("click", () => openScreen("sleep"));
});

loadBioTime();
openScreen("home");