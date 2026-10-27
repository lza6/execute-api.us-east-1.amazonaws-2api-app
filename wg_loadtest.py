"""
QuixVPN free WG profile harvest + local validation.
Validates each profile's server endpoint UDP reachability (send handshake-init-looking
noise packet, WG servers silently drop invalid ones - port open = no ICMP unreachable).
"""
import json, socket, time, statistics
from fetch_quix import fetch

def udp_probe(endpoint, timeout=3.0):
    host, port = endpoint.split(":")
    port = int(port)
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM); s.settimeout(timeout)
    t0=time.perf_counter()
    try:
        s.sendto(b"\x01\x00\x00\x00" + b"\x00"*144, (host, port))  # WG handshake init type 1
        try:
            s.recvfrom(512)  # real handshake reply means valid key (won't happen w/ fake)
        except socket.timeout:
            pass  # expected: silent drop = port alive
        return (time.perf_counter()-t0)*1000
    except ConnectionRefusedError:
        return None  # ICMP port unreachable = closed
    except OSError:
        return None
    finally:
        s.close()

def run_loadtest(n_probes=6):
    profiles = json.load(open("wg_profiles_ok.json"))
    results=[]
    for p in profiles:
        lat=[]
        for _ in range(n_probes):
            r=udp_probe(p["endpoint"])
            if r: lat.append(r)
            time.sleep(0.15)
        status = "ALIVE" if lat else "DEAD/REFUSED"
        med = f"{statistics.median(lat):.0f}ms" if lat else "-"
        results.append({"host":p["host"],"endpoint":p["endpoint"],"status":status,"median_rtt":med,"probes":len(lat)})
        print(f"{p['host']:28s} {p['endpoint']:26s} {status:6s} median {med}")
    json.dump(results, open("loadtest_results.json","w"), indent=2)

if __name__=="__main__":
    run_loadtest()
