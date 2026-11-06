#!/usr/bin/env python3
"""Full data bringup in ONE client, then dump Start Network response TLVs.

Start Network (WDS 0x0020) output TLVs of interest:
  0x01 Packet Data Handle (u32)
  0x1E IPv4 Address
  0x1F IPv4 Gateway
  0x15 Primary DNS
  0x16 Secondary DNS
"""
import ctypes, os, select, struct, subprocess, sys, time

AF_QIPCRTR = 42


class SA(ctypes.Structure):
    _fields_ = [("f", ctypes.c_uint16), ("n", ctypes.c_uint32), ("p", ctypes.c_uint32)]


libc = ctypes.CDLL("libc.so.6", use_errno=True)


def ports():
    out = subprocess.run(["qrtr-lookup"], capture_output=True, text=True, timeout=10).stdout
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
tid = 0x6000


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


WDS = 1
apn = sys.argv[1] if len(sys.argv) > 1 else "cmnet"
# mux id 冲突会让 Bind Mux 返回 INTERNAL(3)，每次换一个
MUX = int(sys.argv[2], 0) if len(sys.argv) > 2 else 0xF5

print("WDS port:", P[WDS], " mux=0x%02X" % MUX)

r = call(WDS, 0x00A2, tlv(0x10, u32(4) + u32(1)) + tlv(0x11, bytes([MUX])) + tlv(0x13, u32(1)))
print("1) Bind Mux Data Port ->", result(r))

r = call(WDS, 0x00AF, tlv(0x01, u32(1)))
print("2) Bind Subscription  ->", result(r))

r = call(WDS, 0x0020, tlv(0x14, apn.encode()) + tlv(0x19, bytes([4])), timeout=45)
print("3) Start Network      ->", result(r))

if r:
    print("\n=== Start Network 响应 TLV ===")
    for t, v in r:
        pretty = ""
        if t == 0x01 and len(v) == 4:
            pretty = "pdh=%d" % struct.unpack("<I", v)[0]
        elif len(v) == 4 and t in (0x15, 0x16, 0x1E, 0x1F):
            pretty = "addr=%d.%d.%d.%d" % tuple(reversed(v))
        print("  TLV 0x%02x len=%-3d %-24s %s" % (t, len(v), v[:16].hex(" "), pretty))

# 4) Get Current Settings —— 取 IP/网关/DNS（同一客户端）
r4 = call(WDS, 0x002D, b"", timeout=15)
print("\n=== Get Current Settings (0x002D) TLV ===")
if r4:
    for t, v in r4:
        pretty = ""
        if len(v) == 4 and t in (0x15, 0x16, 0x1E, 0x1F, 0x20, 0x21):
            pretty = "addr=%d.%d.%d.%d" % tuple(reversed(v))
        print("  TLV 0x%02x len=%-3d %-24s %s" % (t, len(v), v[:16].hex(" "), pretty))
else:
    print("  no response")
