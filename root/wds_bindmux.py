#!/usr/bin/env python3
"""Try 0x00B1 / 0x00B5 as WDS Bind Mux Data Port, then Start Network."""
import struct, sys, time
sys.path.insert(0, "/root")
from modem_daemon import Modem

WDS = 1
MUX = 0xF0
m = Modem()


def tlv(t, v):
    return struct.pack("<BH", t, len(v)) + v


# endpoint info: u32 ep_type(1=EMBEDDED) + u32 iface(1)
ep = struct.pack("<II", 1, 1)
variants = [
    ("ep(TLV01)+mux(TLV02)", tlv(0x01, ep) + tlv(0x02, bytes([MUX]))),
    ("mux(TLV01)+ep(TLV02)", tlv(0x01, bytes([MUX])) + tlv(0x02, ep)),
    ("ep(TLV01) only", tlv(0x01, ep)),
    ("mux(TLV02) only", tlv(0x02, bytes([MUX]))),
]

for mid in (0x00B1, 0x00B5):
    for name, body in variants:
        res, err = m.call(WDS, mid, body, timeout=8)
        print("mid=0x%04x %-22s -> %s %s" % (mid, name, res, err or ""))
        if res and res[0] == 0:
            print("  *** %s accepted ***" % name)
        time.sleep(2)
