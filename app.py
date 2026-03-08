@app.route("/app")
def mini_app():

    return """
<html>

<head>

<meta name="viewport" content="width=device-width, initial-scale=1">

<style>

body{
margin:0;
background:#000;
display:flex;
align-items:center;
justify-content:center;
height:100vh;
}

img{
width:220px;
}

</style>

</head>

<body>

<img src="https://raw.githubusercontent.com/prihodko0501-gif/aion-bot/main/B0AEE152-2F0A-4DD9-8A25-D25C1D6AFE54.png">

</body>

</html>
"""