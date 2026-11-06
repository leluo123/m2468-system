#!/usr/bin/env python3
"""Dump every TLV of DMS Get Operating Mode + NAS Serving System."""
import ctypes, select, struct, subprocess, sys, time

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


def dump(svc_name, svc, mid, out_port):
    fd = libc.socket(AF_QIPCRTR, 2, 0)
    sa = SA()
    ln = ctypes.c_uint(12)
    libc.getsockname(fd, ctypes.byref(sa), ctypes.byref(ln))
    sa.p = 0
    libc.bind(fd, ctypes.byref(sa), 12)
    tid = 0x3000
    pkt = struct.pack("<BHHH", 0, tid, mid, 0)
    d = SA(AF_QIPCRTR, 0, out_port)
    libc.sendto(fd, pkt, len(pkt), 0, ctypes.byref(d), ctypes.sizeof(d))
    deadline = time.time() + 8
    while time.time() < deadline:
        r, _, _ = select.select([fd], [], [], max(0.1, deadline - time.time()))
        if not r:
            break
        b = ctypes.create_string_buffer(16384)
        s = SA()
        l = ctypes.c_uint(12)
        n = libc.recvfrom(fd, b, 16384, 0, ctypes.byref(s), ctypes.byref(l))
        if n < 7:
            continue
        data = b.raw[:n]
        typ, rtid, rmid, hl = struct.unpack("<BHHH", data[:7])
        if rtid != tid:
            continue
        body = data[7:7 + hl]
        print("== %s msg 0x%04x ==" % (svc_name, rmid))
        i = 0
        while i + 3 <= len(body):
            t, ll = struct.unpack("<BH", body[i:i + 3])
            v = body[i + 3:i + 3 + ll]
            print("   TLV 0x%02x len=%d  %s" % (t, ll, v.hex(" ")))
            i += 3 + ll
        return
    print("== %s: no response ==" % svc_name)


p = ports()
dump("DMS-OPERATING-MODE", 2, 0x002D, p[2])
dump("NAS-SERVING-SYSTEM", 3, 0x0024, p[3])
dump("DMS-CAPABILITIES", 2, 0x0021, p[2])
