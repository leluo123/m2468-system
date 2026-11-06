#!/usr/bin/env python3
"""Complete data bringup: bring rmnet UP first, then WDS sequence, then apply IP.

Order matters: the modem starts pushing data as soon as Start Network succeeds.
If the AP-side rmnet interface is still DOWN, the data path stalls and the modem
hits the offline-PLL assertion.
"""
import ctypes, os, select, struct, subprocess, sys, time

AF_QIPCRTR = 42


class SA(ctypes.Structure):
    _fields_ = [("f", ctypes.c_uint16), ("n", ctypes.c_uint32), ("p", ctypes.c_uint32)]


libc = ctypes.CDLL("libc.so.6", use_errno=True)


def sh(*a):
    r = subprocess.run(a, capture_output=True, text=True)
    return (r.stdout + r.stderr).strip()


def ports():
    out = sh("qrtr-lookup")
    d = {}
    for line in out.splitlines()[1:]:
        f = line.split()
        if len(f) >= 5 and f[3] == "0":
            try:
                d.setdefault(int(f[0]), int(f[4]))
            except ValueError:
                pass
    return d


fd = libc.socket(AF_QIPCRTR, 2, 0)
sa = SA()
ln = ctypes.c_uint(12)
libc.getsockname(fd, ctypes.byref(sa), ctypes.byref(ln))
sa.p = 0
libc.bind(fd, ctypes.byref(sa), 12)
P = ports()
tid = 0x7000


def call(svc, mid, tlvs, timeout=10):
    global tid
    tid += 1
    pkt = struct.pack("<BHHH", 0, tid, mid, len(tlvs)) + tlvs
    d = SA(AF_QIPCRTR, 0, P[svc])
    libc.sendto(fd, pkt, len(pkt), 0, ctypes.byref(d), ctypes.sizeof(d))
    dl = time.time() + timeout
    while time.time() < dl:
        r, _, _ = select.select([fd], [], [], max(0.1, dl - time.time()))
        if not r:
            break
        b = ctypes.create_string_buffer(16384)
        s = SA()
        l = ctypes.c_uint(12)
        n = libc.recvfrom(fd, b, 16384, 0, ctypes.byref(s), ctypes.byref(l))
        if n < 7:
            continue
        data = b.raw[:n]
        _, rtid, rmid, hl = struct.unpack("<BHHH", data[:7])
        if rtid != tid:
            continue
        body = data[7:7 + hl]
        out = []
        i = 0
        while i + 3 <= len(body):
            t, ll = struct.unpack("<BH", body[i:i + 3])
            out.append((t, body[i + 3:i + 3 + ll]))
            i += 3 + ll
        return out
    return None


def tlv(t, v):
    return struct.pack("<BH", t, len(v)) + v


def u32(v):
    return struct.pack("<I", v)


def result(res):
    if not res:
        return None
    for t, v in res:
        if t == 0x02 and len(v) >= 4:
            return struct.unpack("<HH", v[:4])
    return None


def ip_of(res, tag):
    if not res:
        return None
    for t, v in res:
        if t == tag and len(v) == 4:
            return ".".join(str(x) for x in reversed(v))
    return None


IF = "rmnet_ipa0"
apn = sys.argv[1] if len(sys.argv) > 1 else "cmnet"
MUX = int(sys.argv[2], 0) if len(sys.argv) > 2 else 0xF7

print("WDS port:", P.get(1), " mux=0x%02X" % MUX)

# 0) 先把网卡拉起来，避免数据面卡死
print("0) bring %s up first" % IF, flush=True)
sh("ip", "link", "set", IF, "up")
time.sleep(1)
print("   ", sh("ip", "-br", "link", "show", IF))
sh("ip", "addr", "flush", "dev", IF, "scope", "global")

# 1) Bind Mux Data Port
r = call(1, 0x00A2, tlv(0x10, u32(4) + u32(1)) + tlv(0x11, bytes([MUX])) + tlv(0x13, u32(1)))
print("1) Bind Mux Data Port ->", result(r))

# 2) Bind Subscription
r = call(1, 0x00AF, tlv(0x01, u32(1)))
print("2) Bind Subscription  ->", result(r))

# 3) Start Network
r = call(1, 0x0020, tlv(0x14, apn.encode()) + tlv(0x19, bytes([4])), timeout=45)
print("3) Start Network      ->", result(r))

# 4) Get Current Settings
r4 = call(1, 0x002D, b"", timeout=15)
addr = ip_of(r4, 0x1E)
dns1 = ip_of(r4, 0x15)
dns2 = ip_of(r4, 0x16)
mask = ip_of(r4, 0x21)
print("4) settings: addr=%s dns=%s,%s mask=%s" % (addr, dns1, dns2, mask))

if addr:
    plen = 32
    if mask and mask != "255.255.255.255":
        plen = sum(bin(int(x)).count("1") for x in mask.split("."))
    print("   applying %s/%d to %s" % (addr, plen, IF), flush=True)
    print("   ", sh("ip", "addr", "add", "%s/%d" % (addr, plen), "dev", IF))
    print("   ", sh("ip", "link", "set", IF, "up"))
    print("   ", sh("ip", "route", "add", "default", "dev", IF, "metric", "50"))
    print("=== 最终接口 ===")
    print(sh("ip", "-br", "addr", "show", IF))
    print(sh("ip", "route", "get", "223.5.5.5"))
