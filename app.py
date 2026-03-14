from flask import Flask, jsonify

app = Flask(__name__)


def get_biotime():
    return 8.4


HOME_HTML = """
<!DOCTYPE html>
<html lang="ru">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no" />
  <title>AION</title>
  <style>
    :root{
      --bg1:#020814;
      --bg2:#04142c;
      --text:#eef6ff;
      --muted:#9db2d1;
      --panel:rgba(4,14,34,.94);
      --line:rgba(96,170,255,.22);
      --soft:rgba(82,130,255,.16);
      --glow:#7fd6ff;
      --glow2:#5b8fff;
    }

    *{
      box-sizing:border-box;
      -webkit-tap-highlight-color:transparent;
    }

    html,body{
      margin:0;
      width:100%;
      min-height:100%;
      background:
        radial-gradient(1200px 900px at 50% -10%, rgba(15,52,120,.85) 0%, rgba(15,52,120,0) 42%),
        radial-gradient(700px 700px at 100% 10%, rgba(76,125,255,.14) 0%, rgba(76,125,255,0) 45%),
        linear-gradient(180deg, #071325 0%, #030a14 58%, #01050d 100%);
      color:var(--text);
      font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,Arial,sans-serif;
      overflow-x:hidden;
    }

    body{
      display:flex;
      justify-content:center;
    }

    .app{
      position:relative;
      width:100%;
      max-width:430px;
      min-height:100vh;
      padding:18px 16px 138px;
      overflow:hidden;
    }

    .stars{
      position:absolute;
      inset:0;
      pointer-events:none;
      background-image:
        radial-gradient(circle at 12% 18%, rgba(255,255,255,.7) 0 1.2px, transparent 2px),
        radial-gradient(circle at 18% 32%, rgba(255,255,255,.35) 0 1px, transparent 2px),
        radial-gradient(circle at 84% 20%, rgba(255,255,255,.55) 0 1.2px, transparent 2px),
        radial-gradient(circle at 78% 42%, rgba(255,255,255,.28) 0 1px, transparent 2px),
        radial-gradient(circle at 88% 60%, rgba(255,255,255,.4) 0 1.1px, transparent 2px),
        radial-gradient(circle at 10% 72%, rgba(255,255,255,.2) 0 1px, transparent 2px);
    }

    .ring{
      position:absolute;
      right:-140px;
      top:48px;
      width:390px;
      height:390px;
      border-radius:50%;
      border:1px solid rgba(120,160,255,.1);
      box-shadow:
        0 0 0 36px rgba(120,160,255,.04),
        0 0 0 76px rgba(120,160,255,.02);
      pointer-events:none;
    }

    .topbar{
      display:flex;
      justify-content:space-between;
      align-items:center;
      position:relative;
      z-index:2;
      margin-bottom:10px;
    }

    .icon-btn{
      width:44px;
      height:44px;
      border-radius:50%;
      border:1px solid rgba(140,190,255,.16);
      background:rgba(8,18,34,.28);
      color:#fff;
      display:flex;
      align-items:center;
      justify-content:center;
      text-decoration:none;
      font-size:24px;
      box-shadow:
        inset 0 0 18px rgba(90,150,255,.08),
        0 0 24px rgba(30,80,180,.06);
    }

    .hero{
      position:relative;
      z-index:2;
      text-align:center;
      padding-top:8px;
    }

    .logo-wrap{
      margin:0 auto 6px;
      width:170px;
      height:210px;
      position:relative;
      filter:drop-shadow(0 0 26px rgba(120,190,255,.24));
    }

    .logo-main{
      position:absolute;
      inset:0;
      margin:auto;
      width:170px;
      height:210px;
      background:linear-gradient(180deg, #f0feff 0%, #95d8ff 36%, #6da6ff 68%, #6b7dff 100%);
      clip-path:polygon(50% 0%, 90% 92%, 70% 92%, 50% 35%, 30% 92%, 10% 92%);
    }

    .logo-inner{
      position:absolute;
      left:50%;
      top:26%;
      transform:translateX(-50%);
      width:54px;
      height:88px;
      background:linear-gradient(180deg, #081932 0%, #0d2d66 100%);
      clip-path:polygon(50% 0%, 100% 100%, 0% 100%);
      box-shadow:0 0 24px rgba(60,100,255,.25);
    }

    .logo-core{
      position:absolute;
      left:50%;
      top:58px;
      transform:translateX(-50%);
      width:18px;
      height:18px;
      border-radius:50%;
      background:radial-gradient(circle, #ffffff 0%, #b2eeff 42%, #69b7ff 70%, rgba(105,183,255,.18) 100%);
      box-shadow:0 0 22px rgba(125,220,255,.85);
    }

    .brand{
      font-size:64px;
      font-weight:300;
      letter-spacing:12px;
      margin:0;
    }

    .sub{
      margin-top:6px;
      color:var(--muted);
      letter-spacing:7px;
      font-size:13px;
      text-transform:uppercase;
    }

    .enter{
      margin:30px auto 24px;
      width:100%;
      border-radius:999px;
      padding:19px 24px;
      border:1px solid rgba(96,170,255,.26);
      background:linear-gradient(180deg, rgba(18,42,96,.66), rgba(5,18,52,.9));
      box-shadow:
        inset 0 0 18px rgba(120,190,255,.1),
        0 0 18px rgba(25,80,200,.12);
      color:#eef8ff;
      font-size:22px;
      letter-spacing:1px;
      display:flex;
      align-items:center;
      justify-content:center;
      gap:12px;
      text-decoration:none;
      position:relative;
      overflow:hidden;
    }

    .enter:before{
      content:"";
      position:absolute;
      left:16%;
      right:16%;
      bottom:0;
      height:2px;
      border-radius:99px;
      background:linear-gradient(90deg, rgba(80,180,255,0), rgba(120,220,255,.95), rgba(80,180,255,0));
      box-shadow:0 0 16px rgba(120,220,255,.5);
    }

    .card{
      position:relative;
      width:100%;
      border-radius:28px;
      padding:24px 22px 58px;
      background:linear-gradient(180deg, rgba(4,14,34,.92), rgba(1,8,22,.96));
      border:1px solid rgba(82,130,255,.16);
      box-shadow:
        inset 0 0 30px rgba(80,120,255,.05),
        0 10px 30px rgba(0,0,0,.26);
      overflow:hidden;
      text-align:center;
    }

    .card-label{
      color:#d7e8ff;
      letter-spacing:9px;
      font-size:13px;
      text-transform:uppercase;
      margin-bottom:16px;
    }

    .card-value{
      font-size:92px;
      line-height:1;
      font-weight:300;
      margin:0;
      color:#eef8ff;
    }

    .wave{
      position:absolute;
      left:0;
      right:0;
      bottom:6px;
      height:80px;
      opacity:.95;
    }

    .mini-nav{
      margin-top:18px;
      border-radius:22px;
      padding:12px 18px;
      border:1px solid rgba(96,150,255,.12);
      background:linear-gradient(180deg, rgba(3,12,28,.92), rgba(0,7,18,.96));
      box-shadow:0 8px 28px rgba(0,0,0,.32);
      display:flex;
      justify-content:space-between;
      align-items:center;
    }

    .mini-item{
      width:48px;
      height:48px;
      border-radius:16px;
      display:flex;
      align-items:center;
      justify-content:center;
      color:#dfeeff;
      font-size:24px;
    }

    .mini-item.active{
      color:#95daff;
      text-shadow:0 0 14px rgba(125,220,255,.6);
    }

    .bottom-nav{
      position:fixed;
      left:50%;
      transform:translateX(-50%);
      bottom:14px;
      width:calc(100% - 24px);
      max-width:406px;
      border-radius:34px;
      padding:14px 16px;
      background:linear-gradient(180deg, rgba(3,12,28,.98), rgba(0,7,18,.98));
      border:1px solid rgba(96,150,255,.14);
      box-shadow:
        0 0 0 1px rgba(24,44,86,.15) inset,
        0 12px 40px rgba(0,0,0,.46);
      display:flex;
      justify-content:space-between;
      align-items:center;
      z-index:5;
    }

    .nav-link{
      text-decoration:none;
    }

    .nav-item{
      width:62px;
      height:62px;
      border-radius:22px;
      display:flex;
      align-items:center;
      justify-content:center;
      color:#e8f3ff;
      font-size:28px;
      opacity:.92;
    }

    .nav-item.active{
      color:#9edcff;
      text-shadow:0 0 14px rgba(110,200,255,.65);
    }

    .nav-center{
      width:104px;
      height:104px;
      border-radius:50%;
      margin-top:-40px;
      background:
        radial-gradient(circle at 50% 42%, rgba(177,234,255,.95) 0%, rgba(112,194,255,.44) 18%, rgba(41,88,198,.36) 42%, rgba(8,20,56,.98) 74%);
      border:1px solid rgba(120,190,255,.2);
      box-shadow:
        0 0 26px rgba(88,160,255,.28),
        inset 0 0 26px rgba(160,230,255,.14);
      display:flex;
      align-items:center;
      justify-content:center;
      position:relative;
    }

    .nav-center::after{
      content:"";
      position:absolute;
      inset:22px;
      border-radius:50%;
      background:rgba(255,255,255,.02);
      filter:blur(1px);
    }

    .nav-a{
      position:relative;
      width:30px;
      height:36px;
      background:linear-gradient(180deg, #f0fbff 0%, #98caff 50%, #678fff 100%);
      clip-path:polygon(50% 0%, 100% 100%, 78% 100%, 50% 42%, 22% 100%, 0% 100%);
      z-index:1;
    }
  </style>
</head>
<body>
  <div class="app">
    <div class="stars"></div>
    <div class="ring"></div>

    <div class="topbar">
      <a class="icon-btn" href="/modules">☰</a>
      <a class="icon-btn" href="/modules">◌</a>
    </div>

    <div class="hero">
      <div class="logo-wrap">
        <div class="logo-main"></div>
        <div class="logo-inner"></div>
        <div class="logo-core"></div>
      </div>

      <h1 class="brand">AION</h1>
      <div class="sub">Biological Upgrade System</div>

      <a class="enter" href="/modules">ENTER SYSTEM <span>→</span></a>

      <div class="card">
        <div class="card-label">BIO TIME</div>
        <div class="card-value" id="biotime-value">8.4</div>

        <svg class="wave" viewBox="0 0 400 100" preserveAspectRatio="none">
          <defs>
            <linearGradient id="waveGlow" x1="0%" y1="0%" x2="100%" y2="0%">
              <stop offset="0%" stop-color="rgba(120,220,255,0)" />
              <stop offset="50%" stop-color="#7fd6ff" />
              <stop offset="100%" stop-color="rgba(120,220,255,0)" />
            </linearGradient>
          </defs>
          <path d="M0,70 C55,90 110,96 170,76 C220,58 255,40 304,50 C345,58 372,76 400,56"
                fill="none"
                stroke="#7fd6ff"
                stroke-width="2.4"
                stroke-linecap="round" />
          <path d="M0,71 C55,91 110,97 170,77 C220,59 255,41 304,51 C345,59 372,77 400,57"
                fill="none"
                stroke="rgba(127,214,255,.25)"
                stroke-width="7"
                stroke-linecap="round" />
        </svg>
      </div>

      <div class="mini-nav">
        <div class="mini-item active">⌂</div>
        <div class="mini-item">◔</div>
        <div class="mini-item">◉</div>
        <div class="mini-item">◌</div>
      </div>
    </div>
  </div>

  <div class="bottom-nav">
    <a class="nav-link" href="/"><div class="nav-item active">⌂</div></a>
    <a class="nav-link" href="/modules"><div class="nav-item">◔</div></a>
    <a class="nav-link" href="/"><div class="nav-center"><div class="nav-a"></div></div></a>
    <a class="nav-link" href="/sleep"><div class="nav-item">∿</div></a>
    <a class="nav-link" href="/modules"><div class="nav-item">◌</div></a>
  </div>

  <script>
    async function loadBioTime(){
      try{
        const response = await fetch('/api/biotime');
        const data = await response.json();
        const el = document.getElementById('biotime-value');
        if(el && data.value !== undefined){
          el.textContent = data.value;
        }
      }catch(err){
        console.log(err);
      }
    }
    loadBioTime();
  </script>
</body>
</html>
"""

MODULES_HTML = """
<!DOCTYPE html>
<html lang="ru">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no" />
  <title>AION Modules</title>
  <style>
    :root{
      --bg1:#020814;
      --bg2:#04142c;
      --text:#eef6ff;
      --muted:#9db2d1;
    }

    *{
      box-sizing:border-box;
      -webkit-tap-highlight-color:transparent;
    }

    html,body{
      margin:0;
      width:100%;
      min-height:100%;
      background:
        radial-gradient(1000px 700px at 50% -10%, rgba(15,52,120,.82) 0%, rgba(15,52,120,0) 42%),
        linear-gradient(180deg, #071325 0%, #030a14 58%, #01050d 100%);
      color:var(--text);
      font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,Arial,sans-serif;
      overflow-x:hidden;
    }

    body{
      display:flex;
      justify-content:center;
    }

    .app{
      width:100%;
      max-width:430px;
      min-height:100vh;
      padding:18px 16px 138px;
      position:relative;
      overflow:hidden;
    }

    .stars{
      position:absolute;
      inset:0;
      pointer-events:none;
      background-image:
        radial-gradient(circle at 12% 18%, rgba(255,255,255,.7) 0 1.2px, transparent 2px),
        radial-gradient(circle at 18% 32%, rgba(255,255,255,.35) 0 1px, transparent 2px),
        radial-gradient(circle at 84% 20%, rgba(255,255,255,.55) 0 1.2px, transparent 2px),
        radial-gradient(circle at 78% 42%, rgba(255,255,255,.28) 0 1px, transparent 2px);
    }

    .ring{
      position:absolute;
      right:-140px;
      top:40px;
      width:390px;
      height:390px;
      border-radius:50%;
      border:1px solid rgba(120,160,255,.1);
      box-shadow:
        0 0 0 36px rgba(120,160,255,.04),
        0 0 0 76px rgba(120,160,255,.02);
      pointer-events:none;
    }

    .topbar{
      display:flex;
      justify-content:space-between;
      align-items:center;
      position:relative;
      z-index:2;
      margin-bottom:4px;
    }

    .icon-btn{
      width:44px;
      height:44px;
      border-radius:50%;
      border:1px solid rgba(140,190,255,.16);
      background:rgba(8,18,34,.28);
      color:#fff;
      display:flex;
      align-items:center;
      justify-content:center;
      text-decoration:none;
      font-size:24px;
      box-shadow:
        inset 0 0 18px rgba(90,150,255,.08),
        0 0 24px rgba(30,80,180,.06);
    }

    .hero{
      text-align:center;
      position:relative;
      z-index:2;
    }

    .logo-wrap{
      margin:0 auto 8px;
      width:132px;
      height:165px;
      position:relative;
      filter:drop-shadow(0 0 24px rgba(120,190,255,.24));
    }

    .logo-main{
      position:absolute;
      inset:0;
      margin:auto;
      width:132px;
      height:165px;
      background:linear-gradient(180deg, #f0feff 0%, #95d8ff 36%, #6da6ff 68%, #6b7dff 100%);
      clip-path:polygon(50% 0%, 90% 92%, 70% 92%, 50% 35%, 30% 92%, 10% 92%);
    }

    .logo-inner{
      position:absolute;
      left:50%;
      top:26%;
      transform:translateX(-50%);
      width:42px;
      height:68px;
      background:linear-gradient(180deg, #081932 0%, #0d2d66 100%);
      clip-path:polygon(50% 0%, 100% 100%, 0% 100%);
    }

    .logo-core{
      position:absolute;
      left:50%;
      top:45px;
      transform:translateX(-50%);
      width:15px;
      height:15px;
      border-radius:50%;
      background:radial-gradient(circle, #ffffff 0%, #b2eeff 42%, #69b7ff 70%, rgba(105,183,255,.18) 100%);
      box-shadow:0 0 20px rgba(125,220,255,.85);
    }

    .brand{
      font-size:56px;
      font-weight:300;
      letter-spacing:11px;
      margin:0;
    }

    .sub{
      margin-top:6px;
      color:var(--muted);
      letter-spacing:6px;
      font-size:12px;
      text-transform:uppercase;
    }

    .title{
      margin:24px 0 20px;
      text-align:center;
      letter-spacing:7px;
      font-size:22px;
    }

    .grid{
      display:grid;
      grid-template-columns:1fr 1fr;
      gap:16px;
      position:relative;
      z-index:2;
    }

    .module{
      min-height:150px;
      border-radius:26px;
      border:1px solid rgba(82,130,255,.18);
      background:linear-gradient(180deg, rgba(4,14,34,.92), rgba(1,8,22,.96));
      box-shadow:
        inset 0 0 30px rgba(80,120,255,.05),
        0 10px 30px rgba(0,0,0,.22);
      display:flex;
      flex-direction:column;
      justify-content:center;
      align-items:center;
      text-decoration:none;
      color:#eef6ff;
      position:relative;
      overflow:hidden;
    }

    .module:after{
      content:"";
      position:absolute;
      inset:auto 14% 0 14%;
      height:2px;
      background:linear-gradient(90deg, rgba(80,180,255,0), rgba(120,220,255,.65), rgba(80,180,255,0));
      box-shadow:0 0 14px rgba(120,220,255,.4);
    }

    .module-icon{
      font-size:42px;
      margin-bottom:14px;
      color:#bfe8ff;
      text-shadow:0 0 16px rgba(110,200,255,.45);
    }

    .module-name{
      font-size:18px;
      letter-spacing:4px;
    }

    .mini-row{
      margin-top:22px;
      display:grid;
      grid-template-columns:repeat(3,1fr);
      gap:12px;
      position:relative;
      z-index:2;
    }

    .mini-box{
      min-height:96px;
      border-radius:22px;
      border:1px solid rgba(82,130,255,.16);
      background:linear-gradient(180deg, rgba(4,14,34,.92), rgba(1,8,22,.96));
      display:flex;
      flex-direction:column;
      justify-content:center;
      align-items:center;
      color:#eef6ff;
      text-decoration:none;
    }

    .mini-icon{
      font-size:28px;
      margin-bottom:8px;
      color:#bfe8ff;
    }

    .mini-name{
      font-size:15px;
      letter-spacing:2px;
    }

    .bottom-nav{
      position:fixed;
      left:50%;
      transform:translateX(-50%);
      bottom:14px;
      width:calc(100% - 24px);
      max-width:406px;
      border-radius:34px;
      padding:14px 16px;
      background:linear-gradient(180deg, rgba(3,12,28,.98), rgba(0,7,18,.98));
      border:1px solid rgba(96,150,255,.14);
      box-shadow:
        0 0 0 1px rgba(24,44,86,.15) inset,
        0 12px 40px rgba(0,0,0,.46);
      display:flex;
      justify-content:space-between;
      align-items:center;
      z-index:5;
    }

    .nav-link{
      text-decoration:none;
    }

    .nav-item{
      width:62px;
      height:62px;
      border-radius:22px;
      display:flex;
      align-items:center;
      justify-content:center;
      color:#e8f3ff;
      font-size:28px;
      opacity:.92;
    }

    .nav-item.active{
      color:#9edcff;
      text-shadow:0 0 14px rgba(110,200,255,.65);
    }

    .nav-center{
      width:104px;
      height:104px;
      border-radius:50%;
      margin-top:-40px;
      background:
        radial-gradient(circle at 50% 42%, rgba(177,234,255,.95) 0%, rgba(112,194,255,.44) 18%, rgba(41,88,198,.36) 42%, rgba(8,20,56,.98) 74%);
      border:1px solid rgba(120,190,255,.2);
      box-shadow:
        0 0 26px rgba(88,160,255,.28),
        inset 0 0 26px rgba(160,230,255,.14);
      display:flex;
      align-items:center;
      justify-content:center;
      position:relative;
    }

    .nav-center::after{
      content:"";
      position:absolute;
      inset:22px;
      border-radius:50%;
      background:rgba(255,255,255,.02);
      filter:blur(1px);
    }

    .nav-a{
      position:relative;
      width:30px;
      height:36px;
      background:linear-gradient(180deg, #f0fbff 0%, #98caff 50%, #678fff 100%);
      clip-path:polygon(50% 0%, 100% 100%, 78% 100%, 50% 42%, 22% 100%, 0% 100%);
      z-index:1;
    }
  </style>
</head>
<body>
  <div class="app">
    <div class="stars"></div>
    <div class="ring"></div>

    <div class="topbar">
      <a class="icon-btn" href="/">☰</a>
      <a class="icon-btn" href="/modules">◌</a>
    </div>

    <div class="hero">
      <div class="logo-wrap">
        <div class="logo-main"></div>
        <div class="logo-inner"></div>
        <div class="logo-core"></div>
      </div>

      <h1 class="brand">AION</h1>
      <div class="sub">Biological Upgrade System</div>
    </div>

    <div class="title">MODULES</div>

    <div class="grid">
      <a class="module" href="/sleep">
        <div class="module-icon">☾</div>
        <div class="module-name">SLEEP</div>
      </a>
      <a class="module" href="/modules">
        <div class="module-icon">✦</div>
        <div class="module-name">STRESS</div>
      </a>
      <a class="module" href="/modules">
        <div class="module-icon">♡</div>
        <div class="module-name">RECOVERY</div>
      </a>
      <a class="module" href="/modules">
        <div class="module-icon">＋</div>
        <div class="module-name">LONGEVITY</div>
      </a>
    </div>

    <div class="title" style="font-size:16px; letter-spacing:5px; margin-top:28px;">MODULES</div>

    <div class="mini-row">
      <a class="mini-box" href="/sleep">
        <div class="mini-icon">☾</div>
        <div class="mini-name">SLEEP</div>
      </a>
      <a class="mini-box" href="/modules">
        <div class="mini-icon">✦</div>
        <div class="mini-name">STRESS</div>
      </a>
      <a class="mini-box" href="/modules">
        <div class="mini-icon">＋</div>
        <div class="mini-name">RECOVERY</div>
      </a>
    </div>
  </div>

  <div class="bottom-nav">
    <a class="nav-link" href="/"><div class="nav-item">⌂</div></a>
    <a class="nav-link" href="/modules"><div class="nav-item active">◔</div></a>
    <a class="nav-link" href="/"><div class="nav-center"><div class="nav-a"></div></div></a>
    <a class="nav-link" href="/sleep"><div class="nav-item">∿</div></a>
    <a class="nav-link" href="/modules"><div class="nav-item">◌</div></a>
  </div>
</body>
</html>
"""

SLEEP_HTML = """
<!DOCTYPE html>
<html lang="ru">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no" />
  <title>AION Sleep</title>
  <style>
    :root{
      --bg1:#020814;
      --bg2:#04142c;
      --text:#eef6ff;
      --muted:#9db2d1;
    }

    *{
      box-sizing:border-box;
      -webkit-tap-highlight-color:transparent;
    }

    html,body{
      margin:0;
      width:100%;
      min-height:100%;
      background:
        radial-gradient(1000px 700px at 50% -10%, rgba(15,52,120,.82) 0%, rgba(15,52,120,0) 42%),
        linear-gradient(180deg, #071325 0%, #030a14 58%, #01050d 100%);
      color:var(--text);
      font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,Arial,sans-serif;
      overflow-x:hidden;
    }

    body{
      display:flex;
      justify-content:center;
    }

    .app{
      width:100%;
      max-width:430px;
      min-height:100vh;
      padding:18px 16px 138px;
      position:relative;
      overflow:hidden;
    }

    .stars{
      position:absolute;
      inset:0;
      pointer-events:none;
      background-image:
        radial-gradient(circle at 12% 18%, rgba(255,255,255,.7) 0 1.2px, transparent 2px),
        radial-gradient(circle at 18% 32%, rgba(255,255,255,.35) 0 1px, transparent 2px),
        radial-gradient(circle at 84% 20%, rgba(255,255,255,.55) 0 1.2px, transparent 2px),
        radial-gradient(circle at 78% 42%, rgba(255,255,255,.28) 0 1px, transparent 2px);
    }

    .ring{
      position:absolute;
      right:-140px;
      top:72px;
      width:390px;
      height:390px;
      border-radius:50%;
      border:1px solid rgba(120,160,255,.1);
      box-shadow:
        0 0 0 36px rgba(120,160,255,.04),
        0 0 0 76px rgba(120,160,255,.02);
      pointer-events:none;
    }

    .topbar{
      display:flex;
      justify-content:space-between;
      align-items:center;
      position:relative;
      z-index:2;
      margin-bottom:8px;
    }

    .back{
      color:#e8f3ff;
      text-decoration:none;
      font-size:22px;
    }

    .profile{
      width:44px;
      height:44px;
      border-radius:50%;
      border:1px solid rgba(140,190,255,.16);
      background:rgba(8,18,34,.28);
      color:#fff;
      display:flex;
      align-items:center;
      justify-content:center;
      text-decoration:none;
      font-size:22px;
      box-shadow:
        inset 0 0 18px rgba(90,150,255,.08),
        0 0 24px rgba(30,80,180,.06);
    }

    .title{
      text-align:center;
      font-size:26px;
      letter-spacing:6px;
      margin-top:8px;
    }

    .subtitle{
      text-align:center;
      color:#c8d9f1;
      font-size:16px;
      margin-top:8px;
    }

    .score{
      text-align:center;
      font-size:88px;
      line-height:1;
      font-weight:300;
      margin-top:24px;
    }

    .score-text{
      text-align:center;
      font-size:22px;
      color:#dbeaff;
      margin-top:6px;
    }

    .chart-card{
      margin-top:22px;
      border-radius:28px;
      padding:20px 16px 18px;
      border:1px solid rgba(82,130,255,.18);
      background:linear-gradient(180deg, rgba(4,14,34,.92), rgba(1,8,22,.96));
      box-shadow:
        inset 0 0 30px rgba(80,120,255,.05),
        0 10px 30px rgba(0,0,0,.22);
      overflow:hidden;
    }

    .chart-title{
      text-align:center;
      letter-spacing:6px;
      font-size:14px;
      color:#dbeaff;
      margin-bottom:14px;
    }

    .labels{
      display:flex;
      justify-content:space-between;
      color:#9fb6d8;
      font-size:11px;
      margin-bottom:8px;
      padding:0 4px;
    }

    .bars{
      height:124px;
      display:flex;
      align-items:flex-end;
      gap:5px;
      padding:0 4px;
      position:relative;
    }

    .bar{
      flex:1;
      border-radius:8px 8px 0 0;
      background:linear-gradient(180deg, #8ee8ff 0%, #5ab3ff 60%, #2f6fff 100%);
      box-shadow:0 0 14px rgba(110,200,255,.18);
      opacity:.95;
    }

    .trend{
      margin-top:-42px;
      position:relative;
      z-index:2;
    }

    .xlabels{
      display:flex;
      justify-content:space-between;
      color:#b2c8e6;
      font-size:12px;
      margin-top:-2px;
      padding:0 8px;
    }

    .metrics{
      margin-top:18px;
      display:flex;
      flex-direction:column;
      gap:12px;
    }

    .metric{
      border-top:1px solid rgba(110,150,220,.12);
      padding:18px 4px 6px;
      display:flex;
      justify-content:space-between;
      align-items:flex-start;
    }

    .metric-title{
      font-size:19px;
      color:#eef6ff;
      margin-bottom:4px;
    }

    .metric-sub{
      font-size:13px;
      color:#8ea8ca;
    }

    .metric-right{
      text-align:right;
    }

    .metric-value{
      font-size:18px;
      color:#eef6ff;
      margin-bottom:4px;
    }

    .metric-state{
      font-size:13px;
      color:#9bb3d3;
    }

    .analysis-btn{
      display:flex;
      align-items:center;
      justify-content:center;
      margin-top:18px;
      width:100%;
      border-radius:999px;
      padding:18px 24px;
      border:1px solid rgba(96,170,255,.26);
      background:linear-gradient(180deg, rgba(18,42,96,.66), rgba(5,18,52,.9));
      box-shadow:
        inset 0 0 18px rgba(120,190,255,.1),
        0 0 18px rgba(25,80,200,.12);
      color:#eef8ff;
      font-size:20px;
      letter-spacing:1px;
      gap:12px;
      text-decoration:none;
    }

    .bottom-nav{
      position:fixed;
      left:50%;
      transform:translateX(-50%);
      bottom:14px;
      width:calc(100% - 24px);
      max-width:406px;
      border-radius:34px;
      padding:14px 16px;
      background:linear-gradient(180deg, rgba(3,12,28,.98), rgba(0,7,18,.98));
      border:1px solid rgba(96,150,255,.14);
      box-shadow:
        0 0 0 1px rgba(24,44,86,.15) inset,
        0 12px 40px rgba(0,0,0,.46);
      display:flex;
      justify-content:space-between;
      align-items:center;
      z-index:5;
    }

    .nav-link{
      text-decoration:none;
    }

    .nav-item{
      width:62px;
      height:62px;
      border-radius:22px;
      display:flex;
      align-items:center;
      justify-content:center;
      color:#e8f3ff;
      font-size:28px;
      opacity:.92;
    }

    .nav-item.active{
      color:#9edcff;
      text-shadow:0 0 14px rgba(110,200,255,.65);
    }

    .nav-center{
      width:104px;
      height:104px;
      border-radius:50%;
      margin-top:-40px;
      background:
        radial-gradient(circle at 50% 42%, rgba(177,234,255,.95) 0%, rgba(112,194,255,.44) 18%, rgba(41,88,198,.36) 42%, rgba(8,20,56,.98) 74%);
      border:1px solid rgba(120,190,255,.2);
      box-shadow:
        0 0 26px rgba(88,160,255,.28),
        inset 0 0 26px rgba(160,230,255,.14);
      display:flex;
      align-items:center;
      justify-content:center;
      position:relative;
    }

    .nav-center::after{
      content:"";
      position:absolute;
      inset:22px;
      border-radius:50%;
      background:rgba(255,255,255,.02);
      filter:blur(1px);
    }

    .nav-a{
      position:relative;
      width:30px;
      height:36px;
      background:linear-gradient(180deg, #f0fbff 0%, #98caff 50%, #678fff 100%);
      clip-path:polygon(50% 0%, 100% 100%, 78% 100%, 50% 42%, 22% 100%, 0% 100%);
      z-index:1;
    }
  </style>
</head>
<body>
  <div class="app">
    <div class="stars"></div>
    <div class="ring"></div>

    <div class="topbar">
      <a class="back" href="/modules">‹ Back</a>
      <a class="profile" href="/modules">◌</a>
    </div>

    <div class="title">SLEEP</div>
    <div class="subtitle">Optimization Program</div>

    <div class="score">92</div>
    <div class="score-text">Excellent</div>

    <div class="chart-card">
      <div class="chart-title">SLEEP SCORE</div>

      <div class="labels">
        <span>90%</span>
        <span>80%</span>
        <span>97%</span>
        <span>110%</span>
        <span>110%</span>
      </div>

      <div class="bars">
        <div class="bar" style="height:64%"></div>
        <div class="bar" style="height:46%"></div>
        <div class="bar" style="height:52%"></div>
        <div class="bar" style="height:42%"></div>
        <div class="bar" style="height:46%"></div>
        <div class="bar" style="height:34%"></div>
        <div class="bar" style="height:58%"></div>
        <div class="bar" style="height:54%"></div>
        <div class="bar" style="height:48%"></div>
        <div class="bar" style="height:74%"></div>
        <div class="bar" style="height:81%"></div>
        <div class="bar" style="height:68%"></div>
        <div class="bar" style="height:62%"></div>
        <div class="bar" style="height:66%"></div>
        <div class="bar" style="height:46%"></div>
        <div class="bar" style="height:30%"></div>
        <div class="bar" style="height:28%"></div>
        <div class="bar" style="height:31%"></div>
      </div>

      <div class="trend">
        <svg viewBox="0 0 100 30" preserveAspectRatio="none" style="width:100%;height:40px;">
          <polyline
            fill="none"
            stroke="#7fd6ff"
            stroke-width="1.8"
            points="0,24 8,24 16,23 24,22 32,21 40,20 48,20 56,19 64,18 72,15 80,13 88,10 100,7"
          />
        </svg>
      </div>

      <div class="xlabels">
        <span>Avale</span>
        <span>REM</span>
        <span>Light</span>
        <span>Deep</span>
        <span>SLEEP</span>
      </div>
    </div>

    <div class="metrics">
      <div class="metric">
        <div>
          <div class="metric-title">Sleep Duration</div>
          <div class="metric-sub">Past</div>
        </div>
        <div class="metric-right">
          <div class="metric-value">7h 25m</div>
        </div>
      </div>

      <div class="metric">
        <div>
          <div class="metric-title">Time to Fall Asleep</div>
          <div class="metric-sub">Normal</div>
        </div>
        <div class="metric-right">
          <div class="metric-value">5m</div>
        </div>
      </div>

      <div class="metric">
        <div>
          <div class="metric-title">Sleep Stability</div>
          <div class="metric-sub">Optimal</div>
        </div>
        <div class="metric-right">
          <div class="metric-value">94%</div>
          <div class="metric-state">Optimal</div>
        </div>
      </div>
    </div>

    <a class="analysis-btn" href="/modules">START ANALYSIS <span>→</span></a>
  </div>

  <div class="bottom-nav">
    <a class="nav-link" href="/"><div class="nav-item">⌂</div></a>
    <a class="nav-link" href="/modules"><div class="nav-item">◔</div></a>
    <a class="nav-link" href="/"><div class="nav-center"><div class="nav-a"></div></div></a>
    <a class="nav-link" href="/sleep"><div class="nav-item active">∿</div></a>
    <a class="nav-link" href="/modules"><div class="nav-item">◌</div></a>
  </div>
</body>
</html>
"""


@app.route("/")
def home():
    return HOME_HTML


@app.route("/app")
def miniapp():
    return HOME_HTML


@app.route("/modules")
def modules():
    return MODULES_HTML


@app.route("/sleep")
def sleep():
    return SLEEP_HTML


@app.route("/api/biotime")
def api_biotime():
    return jsonify({"value": get_biotime()})


@app.route("/api/status")
def api_status():
    return jsonify({"status": "ok", "system": "AION"})


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)