def tg_request(method, payload):
    try:
        r = requests.post(f"{API_URL}/{method}", json=payload)
        return r.json()
    except Exception as e:
        print("TG REQUEST ERROR:", e)
        return {"ok": False, "error": str(e)}