function enterSystem(){
window.location="/modules"
}

async function loadBioTime(){

let r = await fetch("/api/biotime")
let data = await r.json()

document.getElementById("biotime").innerText=data.value
}

loadBioTime()