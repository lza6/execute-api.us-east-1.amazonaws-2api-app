import json, time, sys
sys.path.insert(0,'.')
from fetch_quix import fetch

live = json.load(open('serverlist_live.json'))['data']['servers']
pairs, seen = [], set()
for s in live:
    h = s['hostName']
    cc = ''.join(c for c in h.split('.')[0] if c.isalpha())[:2].upper()
    if h not in seen and h != 'app.quix-vpn.com':
        seen.add(h); pairs.append((h, cc))

by_host = {p['host']: p for p in json.load(open('wg_profiles_ok.json'))}

def extract(r):
    for key in ('wgprofile','awgprofile'):
        if r.get(key): return key, r[key]
    return None, None

for round_n in range(1, 4):
    todo = [(h,cc) for h,cc in pairs if h not in by_host]
    print(f"--- round {round_n}: {len(todo)} remaining ---", flush=True)
    if not todo: break
    for h, cc in todo:
        for proto in ('wg','awg'):
            try:
                r = fetch(h, cc, proto)
                key, p = extract(r)
                if p:
                    extra = ''
                    if 'Jc' in p['Interface']:
                        i = p['Interface']
                        extra = f"Jc = {i['Jc']}\nJmin = {i['Jmin']}\nJmax = {i['Jmax']}\nS1 = {i['S1']}\nS2 = {i['S2']}\n"
                        if 'S3' in i: extra += f"S3 = {i['S3']}\nS4 = {i['S4']}\n"
                        extra += f"H1 = {i['H1']}\nH2 = {i['H2']}\nH3 = {i['H3']}\nH4 = {i['H4']}\n"
                    peer = p['Peer']
                    by_host[h] = {"host":h,"cc":cc,"proto":proto,"profile_id":r["profile_id"],
                        "endpoint":peer["Endpoint"],
                        "conf":f"""[Interface]
PrivateKey = {p['Interface']['PrivateKey']}
Address = {p['Interface']['Address']}
DNS = {p['Interface']['DNS']}
MTU = {p['Interface'].get('MTU','1280')}
{extra}
[Peer]
PublicKey = {peer['PublicKey']}
PresharedKey = {peer.get('PresharedKey','')}
Endpoint = {peer['Endpoint']}
AllowedIPs = 0.0.0.0/0
PersistentKeepalive = 25"""}
                    print(f"OK   {h:26s} {proto:3s} {peer['Endpoint']}", flush=True)
                    break
            except Exception as e:
                pass
        time.sleep(0.3)
json.dump(list(by_host.values()), open('wg_profiles_ok.json','w'), indent=2)
print(f"TOTAL: {len(by_host)}/{len(pairs)+1}", flush=True)
