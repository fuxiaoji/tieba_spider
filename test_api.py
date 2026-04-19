import hashlib
import urllib.request
import json

def sign(params):
    keys = sorted(params.keys())
    sign_str = ""
    for k in keys:
        sign_str += k + "=" + str(params[k])
    sign_str += "tiebaclient!!!"
    return hashlib.md5(sign_str.encode('utf-8')).hexdigest().upper()

params = {
    "_client_id": "wappc_1534235498291_633",
    "_client_type": "2",
    "_client_version": "9.7.8.0",
    "_phone_imei": "000000000000000",
    "kz": "7487460366",
    "pn": "1",
    "rn": "30",
    "r": "0",
    "lz": "0",
    "st": "0",
    "z": "0",
}
params["sign"] = sign(params)

post_data = "&".join([f"{k}={v}" for k, v in params.items()])
print("POST data:", post_data[:200])

req = urllib.request.Request(
    "http://c.tieba.baidu.com/c/f/pb/page",
    data=post_data.encode('utf-8'),
    headers={
        "User-Agent": "bdtb for Android 9.7.8.0",
        "Content-Type": "application/x-www-form-urlencoded",
        "Accept": "application/json"
    }
)
try:
    with urllib.request.urlopen(req, timeout=10) as resp:
        data = json.loads(resp.read().decode('utf-8'))
        print(json.dumps(data, indent=2, ensure_ascii=False)[:5000])
except Exception as e:
    print("Error:", e)
