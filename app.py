<!DOCTYPE html>
<html lang="ru">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0, viewport-fit=cover" />
  <title>AION</title>

  <style>
    * {
      box-sizing: border-box;
      margin: 0;
      padding: 0;
      -webkit-tap-highlight-color: transparent;
    }

    html, body {
      width: 100%;
      height: 100%;
      background: #020814;
      font-family: Arial, sans-serif;
      overflow: hidden;
      color: #fff;
    }

    body {
      display: flex;
      justify-content: center;
      align-items: stretch;
    }

    .screen {
      position: relative;
      width: 100%;
      max-width: 430px;
      height: 100vh;
      margin: 0 auto;
      overflow: hidden;
      background-color: #020814;
      background-repeat: no-repeat;
      background-position: center center;
      background-size: cover;
    }

    .tap {
      position: absolute;
      background: transparent;
      border: none;
      outline: none;
      cursor: pointer;
      z-index: 10;
      transition: transform 0.08s ease, opacity 0.08s ease;
    }

    .tap:active {
      transform: scale(0.97);
      opacity: 0.9;
    }

    .hidden {
      display: none;
    }

    /* SCREEN 1 = ENTRY */
    #screen1 {
      background-image: url("/screen-1");
    }

    .s1-enter {
      left: 18%;
      top: 39%;
      width: 64%;
      height: 7%;
      border-radius: 999px;
    }

    .s1-biotime {
      left: 19%;
      top: 52%;
      width: 62%;
      height: 18%;
      border-radius: 28px;
    }

    .s1-top-profile {
      right: 4%;
      top: 4%;
      width: 14%;
      height: 8%;
      border-radius: 50%;
    }

    /* BOTTOM NAV */
    .nav-home  { left: 13%; bottom: 3.2%; width: 9%; height: 5%; border-radius: 50%; }
    .nav-clock { left: 31%; bottom: 3.2%; width: 9%; height: 5%; border-radius: 50%; }
    .nav-aion  { left: 45%; bottom: 1%;   width: 16%; height: 8%; border-radius: 50%; }
    .nav-wave  { left: 63%; bottom: 3.2%; width: 9%; height: 5%; border-radius: 50%; }
    .nav-user  { left: 81%; bottom: 3.2%; width: 9%; height: 5%; border-radius: 50%; }

    /* SCREEN 2 = SLEEP */
    #screen2 {
      background-image: url("/screen-2");
    }

    .s2-start-analysis {
      left: 18%;
      bottom: 11%;
      width: 64%;
      height: 6.5%;
      border-radius: 999px;
    }

    /* SCREEN 3 = RESULT */
    #screen3 {
      background-image: url("/screen-3");
    }

    .s3-back {
      left: 9%;
      top: 11%;
      width: 18%;
      height: 5%;
    }

    .s3-repeat {
      left: 18%;
      bottom: 11%;
      width: 64%;
      height: 6.5%;
      border-radius: 999px;
    }
  </style>
</head>
<body>
  <!-- SCREEN 1 -->
  <div class="screen" id="screen1">
    <button class="tap s1-enter" id="goScreen2" aria-label="Enter System"></button>
    <button class="tap s1-biotime" id="bioTimeInfo" aria-label="BioTime"></button>
    <button class="tap s1-top-profile" id="topProfile" aria-label="Top Profile"></button>

    <button class="tap nav-home" id="s1Home"></button>
    <button class="tap nav-clock" id="s1Clock"></button>
    <button class="tap nav-aion" id="s1Aion"></button>
    <button class="tap nav-wave" id="s1Wave"></button>
    <button class="tap nav-user" id="s1User"></button>
  </div>

  <!-- SCREEN 2 -->
  <div class="screen hidden" id="screen2">
    <button class="tap s2-start-analysis" id="goScreen3" aria-label="Start Analysis"></button>

    <button class="tap nav-home" id="s2Home"></button>
    <button class="tap nav-clock" id="s2Clock"></button>
    <button class="tap nav-aion" id="s2Aion"></button>
    <button class="tap nav-wave" id="s2Wave"></button>
    <button class="tap nav-user" id="s2User"></button>
  </div>

  <!-- SCREEN 3 -->
  <div class="screen hidden" id="screen3">
    <button class="tap s3-back" id="backToScreen2"></button>
    <button class="tap s3-repeat" id="repeatAnalysis"></button>

    <button class="tap nav-home" id="s3Home"></button>
    <button class="tap nav-clock" id="s3Clock"></button>
    <button class="tap nav-aion" id="s3Aion"></button>
    <button class="tap nav-wave" id="s3Wave"></button>
    <button class="tap nav-user" id="s3User"></button>
  </div>

  <script>
    (function () {
      try {
        if (window.Telegram && window.Telegram.WebApp) {
          const tg = window.Telegram.WebApp;
          tg.ready();
          tg.expand();
          try { tg.setHeaderColor("#020814"); } catch (e) {}
          try { tg.setBackgroundColor("#020814"); } catch (e) {}
        }
      } catch (e) {}

      ["/screen-1", "/screen-2", "/screen-3"].forEach(function (src) {
        const img = new Image();
        img.src = src;
      });

      const screen1 = document.getElementById("screen1");
      const screen2 = document.getElementById("screen2");
      const screen3 = document.getElementById("screen3");

      function showScreen(n) {
        screen1.classList.add("hidden");
        screen2.classList.add("hidden");
        screen3.classList.add("hidden");

        if (n === 1) screen1.classList.remove("hidden");
        if (n === 2) screen2.classList.remove("hidden");
        if (n === 3) screen3.classList.remove("hidden");
      }

      function bindClick(id, fn) {
        const el = document.getElementById(id);
        if (!el) return;
        el.addEventListener("click", fn);
      }

      /* ОСНОВНОЙ ЦИКЛ */
      bindClick("goScreen2", function () { showScreen(2); });
      bindClick("goScreen3", function () { showScreen(3); });
      bindClick("backToScreen2", function () { showScreen(2); });
      bindClick("repeatAnalysis", function () { showScreen(3); });

      /* HOME */
      bindClick("s1Home", function () { showScreen(1); });
      bindClick("s2Home", function () { showScreen(1); });
      bindClick("s3Home", function () { showScreen(1); });

      /* AION */
      bindClick("s1Aion", function () { showScreen(2); });
      bindClick("s2Aion", function () { showScreen(2); });
      bindClick("s3Aion", function () { showScreen(2); });

      /* BIO TIME = ПОКА ЗАГЛУШКА */
      bindClick("bioTimeInfo", function () {
        alert("BioTime details: пока заглушка");
      });

      /* PROFILE = ПОКА ЗАГЛУШКА */
      bindClick("topProfile", function () {
        alert("Profile: пока заглушка");
      });
      bindClick("s1User", function () { alert("Profile: пока заглушка"); });
      bindClick("s2User", function () { alert("Profile: пока заглушка"); });
      bindClick("s3User", function () { alert("Profile: пока заглушка"); });

      /* HISTORY = ПОКА ЗАГЛУШКА */
      bindClick("s1Clock", function () { alert("History: пока заглушка"); });
      bindClick("s2Clock", function () { alert("History: пока заглушка"); });
      bindClick("s3Clock", function () { alert("History: пока заглушка"); });

      /* ANALYTICS = ПОКА ЗАГЛУШКА */
      bindClick("s1Wave", function () { alert("Analytics: пока заглушка"); });
      bindClick("s2Wave", function () { alert("Analytics: пока заглушка"); });
      bindClick("s3Wave", function () { alert("Analytics: пока заглушка"); });
    })();
  </script>
</body>
</html>