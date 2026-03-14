from flask import Flask, jsonify

app = Flask(__name__)


def get_biotime():
    """
    Временная заглушка.
    Потом сюда подключим реальный расчет из core.biotime
    """
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
      --line:rgba(116,170,255,.18);
      --glow:rgba(88,170,255,.35);
      --text:#eef6ff;
      --muted:#9db2d1;
      --panel:rgba(5,14,30,.72);
      --panel2:rgba(6,18,40,.88);
      --blue1:#7fd6ff;
      --blue2:#5f9dff;
      --blue3:#1a5dff;
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
        radial-gradient(1200px 800px at 50% -10%, #0c2f70 0%, rgba(12,47,112,0) 45%),
        radial-gradient(700px 700px at 100% 10%, rgba(76,125,255,.16) 0%, rgba(76,125,255,0) 45%),
        linear-gradient(180deg, var(--bg2) 0%, var(--bg1) 58%, #01050d 100%);
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
      padding:18px 16px 130px;
      overflow:hidden;
    }

    .stars, .stars:before, .stars:after{
      position:absolute;
      inset:0;
      content:"";
      background-image:
        radial-gradient(circle at 12% 18%, rgba(255,255,255,.65) 0 1.2px, transparent 2px),
        radial-gradient(circle at 18% 32%, rgba(255,255,255,.4) 0 1px, transparent 2px),
        radial-gradient(circle at 84% 20%, rgba(255,255,255,.55) 0 1.2px, transparent 2px),
        radial-gradient(circle at 78% 42%, rgba(255,255,255,.35) 0 1px, transparent 2px),
        radial-gradient(circle at 88% 60%, rgba(255,255,255,.45) 0 1.1px, transparent 2px),
        radial-gradient(circle at 10% 72%, rgba(255,255,255,.3) 0 1px, transparent 2px);
      pointer-events:none;
    }

    .ring{
      position:absolute;
      right:-130px;
      top:60px;
      width:360px;
      height:360px;
      border-radius:50%;
      border:1px solid rgba(120,160,255,.12);
      box-shadow:
        0 0 0 34px rgba(120,160,255,.05),
        0 0 0 74px rgba(120,160,255,.025);
      pointer-events:none;
    }

    .topbar{
      display:flex;
      justify-content:space-between;
      align-items:center;
      margin-bottom:28px;
      position:relative;
      z-index:2;
    }

    .icon-btn{
      width:44px;
      height:44px;
      border-radius:50%;
      border:1px solid rgba(140,190,255,.16);
      background:rgba(8,18,34,.3);
      color:#fff;
      display:flex;
      align-items:center;
      justify-content:center;
      font-size:24px;
      box-shadow:
        0 0 18px rgba(90,150,255,.08) inset,
        0 0 24px rgba(30,80,180,.06);
    }

    .profile{
      font-size:22px;
      line-height:1;
    }

    .hero{
      text-align:center;
      position:relative;
      z-index:2;
    }

    .logo-wrap{
      margin:6px auto 10px;
      width:170px;
      height:210px;
      position:relative;
      filter:drop-shadow(0 0 24px rgba(120,190,255,.24));
    }

    .logo-main{
      position:absolute;
      inset:0;
      margin:auto;
      width:170px;
      height:210px;
      background:linear-gradient(180deg, #ddfbff 0%, #7bbaff 45%, #5b7dff 100%);
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
      background:radial-gradient(circle, #e9ffff 0%, #b2eeff 45%, #69b7ff 70%, rgba(105,183,255,.2) 100%);
      box-shadow:0 0 22px rgba(125,220,255,.85);
    }

    .brand{
      font-size:64px;
      letter-spacing:12px;
      font-weight:300;
      margin:0;
    }

    .sub{
      margin-top:8px;
      color:var(--muted);
      letter-spacing:8px;
      font-size:13px;
      text-transform:uppercase;
    }

    .enter{
      margin:28px auto 22px;
      width:100%;
      border-radius:999px;
      padding:20px 24px;
      border:1px solid rgba(96,170,255,.28);
      background:linear-gradient(180deg, rgba(22,54,120,.8), rgba(5,18,52,.96));
      box-shadow:
        inset 0 0 18px rgba(120,190,255,.14),
        0 0 18px rgba(25,80,200,.18);
      color:#eef8ff;
      font-size:22px;
      letter-spacing:1px;
      display:flex;
      align-items:center;
      justify-content:center;
      gap:12px;
      text-decoration:none;
    }

    .card{
      position:relative;
      width:100%;
      border-radius:30px;
      padding:24px 22px;
      background:linear-gradient(180deg, rgba(4,14,34,.94), rgba(1,8,22,.94));
      border:1px solid rgba(82,130,255,.16);
      box-shadow:
        inset 0 0 30px rgba(80,120,255,.05),
        0 10px 30px rgba(0,0,0,.26);
      overflow:hidden;
    }

    .card::after{
      content:"";
      position:absolute;
      left:10%;
      right:10%;
      bottom:28px;
      height:3px;
      border-radius:99px;
      background:linear-gradient(90deg, rgba(80,180,255,0), rgba(120,220,255,.95), rgba(80,180,255,0));
      box-shadow:0 0 20px rgba(120,220,255,.65);
    }

    .card-label{
      color:var(--muted);
      letter-spacing:10px;
      font-size:12px;
      text-transform:uppercase;
      margin-bottom:18px;
    }

    .card-value{
      font-size:96px;
      line-height:1;
      font-weight:300;
      margin:0 0 50px;
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
      background:linear-gradient(180deg, rgba(25,55,130,.92), rgba(9,22,68,.96));
      border:1px solid rgba(115,180,255,.2);
      box-shadow:inset 0 0 18px rgba(120,200,255,.16);
    }

    .nav-center{
      width:104px;
      height:104px;
      border-radius:50%;
      margin-top:-40px;
      background:
        radial-gradient(circle at 50% 42%, rgba(177,234,255,.9) 0%, rgba(112,194,255,.44) 18%, rgba(41,88,198,.36) 42%, rgba(8,20,56,.98) 74%);
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

    .hint{
      margin-top:18px;
      text-align:center;
      color:#88a7d0;
      font-size:12px;
      opacity:.7;
    }
  </style>
</head>
<body>
  <div class="app">
    <div class="stars"></div>
    <div class="ring"></div>

    <div class="topbar">
      <div class="icon-btn">☰</div>
      <div class="icon-btn profile">○</div>
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
      </div>

      <div class="hint">AION Premium Preview</div>
    </div>
  </div>

  <div class="bottom-nav">
    <a class="nav-link" href="/"><div class="nav-item active">⌂</div></a>
    <a class="nav-link" href="/modules"><div class="nav-item">◔</div></a>
    <a class="nav-link" href="/"><div class="nav-center"><div class="nav-a"></div></div></a>
    <a class="nav-link" href="/sleep"><div class="nav-item">∿</div></a>
    <a class="nav-link" href="/modules"><div class="nav-item">○</div></a>
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
        console.log('BioTime load error', err);
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
        radial-gradient(1000px 700px at 50% -10%, #0c2f70 0%, rgba(12,47,112,0) 42%),
        linear-gradient(180deg, var(--bg2) 0%, var(--bg1) 60%, #01050d 100%);
      color:var(--text);
      font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,Arial,sans-serif;
    }

    body{
      display:flex;
      justify-content:center;
    }

    .app{
      width:100%;
      max-width:430px;
      min-height:100vh;
      padding:18px 16px 130px;
      position:relative;
      overflow:hidden;
    }

    .topbar{
      display:flex;
      justify-content:space-between;
      align-items:center;
      margin-bottom:18px;
    }

    .icon-btn{
      width:44px;
      height:44px;
      border-radius:50%;
      border:1px solid rgba(140,190,255,.16);
      background:rgba(8,18,34,.3);
      color:#fff;
      display:flex;
      align-items:center;
      justify-content:center;
      font-size:24px;
      text-decoration:none;
    }

    .logo-wrap{
      margin:12px auto 8px;
      width:120px;
      height:150px;
      position:relative;
      filter:drop-shadow(0 0 20px rgba(120,190,255,.24));
    }

    .logo-main{
      position:absolute;
      inset:0;
      margin:auto;
      width:120px;
      height:150px;
      background:linear-gradient(180deg, #ddfbff 0%, #7bbaff 45%, #5b7dff 100%);
      clip-path:polygon(50% 0%, 90% 92%, 70% 92%, 50% 35%, 30% 92%, 10% 92%);
    }

    .logo-inner{
      position:absolute;
      left:50%;
      top:26%;
      transform:translateX(-50%);
      width:38px;
      height:62px;
      background:linear-gradient(180deg, #081932 0%, #0d2d66 100%);
      clip-path:polygon(50% 0%, 100% 100%, 0% 100%);
    }

    .logo-core{
      position:absolute;
      left:50%;
      top:42px;
      transform:translateX(-50%);
      width:14px;
      height:14px;
      border-radius:50%;
      background:radial-gradient(circle, #e9ffff 0%, #b2eeff 45%, #69b7ff 70%, rgba(105,183,255,.2) 100%);
      box-shadow:0 0 18px rgba(125,220,255,.85);
    }

    .brand{
      text-align:center;
      font-size:44px;
      letter-spacing:9px;
      font-weight:300;
      margin:0;
    }

    .sub{
      text-align:center;
      margin-top:6px;
      color:var(--muted);
      letter-spacing:5px;
      font-size:11px;
      text-transform:uppercase;
    }

    .section-title{
      margin:28px 0 18px;
      text-align:center;
      letter-spacing:6px;
      font-size:22px;
      color:#eef6ff;
    }

    .grid{
      display:grid;
      grid-template-columns:1fr 1fr;
      gap:16px;
    }

    .module{
      min-height:150px;
      border-radius:26px;
      border:1px solid rgba(82,130,255,.18);
      background:linear-gradient(180deg, rgba(4,14,34,.94), rgba(1,8,22,.94));
      box-shadow:
        inset 0 0 30px rgba(80,120,255,.05),
        0 10px 30px rgba(0,0,0,.22);
      display:flex;
      flex-direction:column;
      justify-content:center;
      align-items:center;
      text-decoration:none;
      color:#eef6ff;
    }

    .module-icon{
      font-size:42px;
      margin-bottom:14px;
      color:#bfe8ff;
      text-shadow:0 0 16px rgba(110,200,255,.45);
    }

    .module-name{
      font-size:28px;
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
      background:linear-gradient(180deg, rgba(25,55,130,.92), rgba(9,22,68,.96));
      border:1px solid rgba(115,180,255,.2);
      box-shadow:inset 0 0 18px rgba(120,200,255,.16);
    }

    .nav-center{
      width:104px;
      height:104px;
      border-radius:50%;
      margin-top:-40px;
      background:
        radial-gradient(circle at 50% 42%, rgba(177,234,255,.9) 0%, rgba(112,194,255,.44) 18%, rgba(41,88,198,.36) 42%, rgba(8,20,56,.98) 74%);
      border:1px solid rgba(120,190,255,.2);
      box-shadow:
        0 0 26px rgba(88,160,255,.28),
        inset 0 0 26px rgba(160,230,255,.14);
      display:flex;
      align-items:center;
      justify-content:center;
      position:relative;
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
    <div class="topbar">
      <a class="icon-btn" href="/">‹</a>
      <a class="icon-btn" href="/modules">○</a>
    </div>

    <div class="logo-wrap">
      <div class="logo-main"></div>
      <div class="logo-inner"></div>
      <div class="logo-core"></div>
    </div>

    <h1 class="brand">AION</h1>
    <div class="sub">Biological Upgrade System</div>

    <div class="section-title">MODULES</div>

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
  </div>

  <div class="bottom-nav">
    <a class="nav-link" href="/"><div class="nav-item">⌂</div></a>
    <a class="nav-link" href="/modules"><div class="nav-item active">◔</div></a>
    <a class="nav-link" href="/"><div class="nav-center"><div class="nav-a"></div></div></a>
    <a class="nav-link" href="/sleep"><div class="nav-item">∿</div></a>
    <a class="nav-link" href="/modules"><div class="nav-item">○</div></a>
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
        radial-gradient(1000px 700px at 50% -10%, #0c2f70 0%, rgba(12,47,112,0) 42%),
        linear-gradient(180deg, var(--bg2) 0%, var(--bg1) 60%, #01050d 100%);
      color:var(--text);
      font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,Arial,sans-serif;
    }

    body{
      display:flex;
      justify-content:center;
    }

    .app{
      width:100%;
      max-width:430px;
      min-height:100vh;
      padding:18px 16px 130px;
      position:relative;
      overflow:hidden;
    }

    .ring{
      position:absolute;
      right:-140px;
      top:80px;
      width:380px;
      height:380px;
      border-radius:50%;
      border:1px solid rgba(120,160,255,.1);
      box-shadow:
        0 0 0 32px rgba(120,160,255,.04),
        0 0 0 72px rgba(120,160,255,.02);
      pointer-events:none;
    }

    .topbar{
      display:flex;
      justify-content:space-between;
      align-items:center;
      margin-bottom:20px;
      position:relative;
      z-index:2;
    }

    .back{
      color:#eef6ff;
      text-decoration:none;
      font-size:22px;
    }

    .profile{
      width:44px;
      height:44px;
      border-radius:50%;
      border:1px solid rgba(140,190,255,.16);
      background:rgba(8,18,34,.3);
      color:#fff;
      display:flex;
      align-items:center;
      justify-content:center;
      font-size:20px;
      text-decoration:none;
    }

    .title{
      text-align:center;
      margin-top:6px;
      font-size:34px;
      letter-spacing:6px;
    }

    .subtitle{
      text-align:center;
      margin-top:6px;
      color:var(--muted);
      font-size:16px;
      letter-spacing:1px;
    }

    .score{
      text-align:center;
      margin-top:28px;
      font-size:90px;
      font-weight:300;
      line-height:1;
    }

    .score-text{
      text-align:center;
      color:#d9ecff;
      font-size:24px;
      margin-top:6px;
    }

    .chart-card{
      margin-top:26px;
      border-radius:28px;
      padding:22px 18px 20px;
      border:1px solid rgba(82,130,255,.18);
      background:linear-gradient(180deg, rgba(4,14,34,.94), rgba(1,8,22,.94));
      box-shadow:
        inset 0 0 30px rgba(80,120,255,.05),
        0 10px 30px rgba(0,0,0,.22);
    }

    .chart-title{
      text-align:center;
      color:#cfe2ff;
      letter-spacing:6px;
      font-size:14px;
      margin-bottom:16px;
    }

    .bars{
      display:flex;
      align-items:flex-end;
      gap:6px;
      height:120px;
      padding:0 8px;
    }

    .bar{
      flex:1;
      border-radius:8px 8px 0 0;
      background:linear-gradient(180deg, #8ee8ff 0%, #5ab3ff 60%, #2f6fff 100%);
      box-shadow:0 0 14px rgba(110,200,255,.25);
      opacity:.92;
    }

    .line{
      position:relative;
      margin-top:-40px;
      height:40px;
    }

    .line svg{
      width:100%;
      height:100%;
    }

    .metrics{
      margin-top:22px;
      display:flex;
      flex-direction:column;
      gap:14px;
    }

    .metric{
      border-radius:22px;
      padding:18px 18px;
      border:1px solid rgba(82,130,255,.14);
      background:rgba(6,15,34,.72);
      display:flex;
      justify-content:space-between;
      align-items:center;
    }

    .metric-left{
      display:flex;
      flex-direction:column;
      gap:6px;
    }

    .metric-title{
      font-size:22px;
      color:#eef6ff;
    }

    .metric-sub{
      font-size:14px;
      color:#97afd0;
    }

    .metric-right{
      text-align:right;
    }

    .metric-value{
      font-size:24px;
      color:#eef6ff;
    }

    .metric-state{
      font-size:14px;
      color:#97afd0;
      margin-top:6px;
    }

    .analysis-btn{
      display:flex;
      align-items:center;
      justify-content:center;
      margin-top:24px;
      width:100%;
      border-radius:999px;
      padding:19px 24px;
      border:1px solid rgba(96,170,255,.28);
      background:linear-gradient(180deg, rgba(22,54,120,.8), rgba(5,18,52,.96));
      box-shadow:
        inset 0 0 18px rgba(120,190,255,.14),
        0 0 18px rgba(25,80,200,.18);
      color:#eef8ff;
      font-size:20px;
      text-decoration:none;
      gap:10px;
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
      background:linear-gradient(180deg, rgba(25,55,130,.92), rgba(9,22,68,.96));
      border:1px solid rgba(115,180,255,.2);
      box-shadow:inset 0 0 18px rgba(120,200,255,.16);
    }

    .nav-center{
      width:104px;
      height:104px;
      border-radius:50%;
      margin-top:-40px;
      background:
        radial-gradient(circle at 50% 42%, rgba(177,234,255,.9) 0%, rgba(112,194,255,.44) 18%, rgba(41,88,198,.36) 42%, rgba(8,20,56,.98) 74%);
      border:1px solid rgba(120,190,255,.2);
      box-shadow:
        0 0 26px rgba(88,160,255,.28),
        inset 0 0 26px rgba(160,230,255,.14);
      display:flex;
      align-items:center;
      justify-content:center;
      position:relative;
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
    <div class="ring"></div>

    <div class="topbar">
      <a class="back" href="/modules">‹ Back</a>
      <a class="profile" href="/modules">○</a>
    </div>

    <div class="title">SLEEP</div>
    <div class="subtitle">Optimization Program</div>

    <div class="score">92</div>
    <div class="score-text">Excellent</div>

    <div class="chart-card">
      <div class="chart-title">SLEEP SCORE</div>

      <div class="bars">
        <div class="bar" style="height:62%"></div>
        <div class="bar" style="height:48%"></div>
        <div class="bar" style="height:54%"></div>
        <div class="bar" style="height:40%"></div>
        <div class="bar" style="height:46%"></div>
        <div class="bar" style="height:35%"></div>
        <div class="bar" style="height:57%"></div>
        <div class="bar" style="height:52%"></div>
        <div class="bar" style="height:49%"></div>
        <div class="bar" style="height:70%"></div>
        <div class="bar" style="height:78%"></div>
        <div class="bar" style="height:65%"></div>
        <div class="bar" style="height:58%"></div>
        <div class="bar" style="height:61%"></div>
        <div class="bar" style="height:46%"></div>
        <div class="bar" style="height:34%"></div>
        <div class="bar" style="height:30%"></div>
        <div class="bar" style="height:32%"></div>
      </div>

      <div class="line">
        <svg viewBox="0 0 100 30" preserveAspectRatio="none">
          <polyline
            fill="none"
            stroke="#7fd6ff"
            stroke-width="1.8"
            points="0,24 8,23 16,22 24,21 32,20 40,19 48,18 56,18 64,17 72,14 80,12 88,10 100,8"
          />
        </svg>
      </div>
    </div>

    <div class="metrics">
      <div class="metric">
        <div class="metric-left">
          <div class="metric-title">Sleep Duration</div>
          <div class="metric-sub">Past</div>
        </div>
        <div class="metric-right">
          <div class="metric-value">7h 25m</div>
        </div>
      </div>

      <div class="metric">
        <div class="metric-left">
          <div class="metric-title">Time to Fall Asleep</div>
          <div class="metric-sub">Normal</div>
        </div>
        <div class="metric-right">
          <div class="metric-value">5m</div>
        </div>
      </div>

      <div class="metric">
        <div class="metric-left">
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
    <a class="nav-link" href="/modules"><div class="nav-item">○</div></a>
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


@app.route("/api/status")
def status():
    return jsonify({
        "status": "ok",
        "system": "AION",
        "server": "running"
    })


@app.route("/api/biotime")
def api_biotime():
    return jsonify({
        "value": get_biotime()
    })


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)

Это правильно ?