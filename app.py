from flask import Flask

app = Flask(__name__)

HTML = """
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

      <div class="enter">ENTER SYSTEM <span>→</span></div>

      <div class="card">
        <div class="card-label">BIO TIME</div>
        <div class="card-value">8.4</div>
      </div>

      <div class="hint">AION Premium Preview</div>
    </div>
  </div>

  <div class="bottom-nav">
    <div class="nav-item active">⌂</div>
    <div class="nav-item">◔</div>
    <div class="nav-center"><div class="nav-a"></div></div>
    <div class="nav-item">∿</div>
    <div class="nav-item">○</div>
  </div>
</body>
</html>
"""

@app.route("/")
def home():
    return HTML

@app.route("/app")
def miniapp():
    return HTML

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)