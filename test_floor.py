import hashlib
import urllib.request
import json

def sign(params):
    keys = sorted(params.keys())
    s = ''.join(k + '=' + str(params[k]) for k in keys) + 'tiebaclient!!!'
    return hashlib.md5(s.encode('utf-8')).hexdigest().upper()

# 获取子回复 (楼中楼)
params = {
    '_client_id': 'wappc_1534235498291_633',
    '_client_type': '2',
    '_client_version': '9.7.8.0',
    '_phone_imei': '000000000000000',
    'pid': '140739419909',
    'pn': '1',
    'rn': '10'
}
params['sign'] = sign(params)
post_data = '&'.join(f'{k}={v}' for k, v in params.items())
req = urllib.request.Request(
    'http://c.tieba.baidu.com/c/f/pb/floor',
    data=post_data.encode(),
    headers={
        'User-Agent': 'bdtb for Android 9.7.8.0',
        'Content-Type': 'application/x-www-form-urlencoded'
    }
)
with urllib.request.urlopen(req, timeout=10) as resp:
    data = json.loads(resp.read().decode('utf-8'))
    print(json.dumps(data, indent=2, ensure_ascii=False)[:3000])
