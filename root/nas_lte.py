#!/usr/bin/env python3
"""Force LTE-only mode via NAS Set System Selection Preference (0x0033)."""
import struct, sys, time
sys.path.insert(0, "/root")
from modem_daemon import Modem


def tlv(t, val):
    return struct.pack("<BH", t, len(val)) + val


m = Modem()
print("services:", len(m.ports))

# TLV 0x11 = mode preference (u16 bitmask)
# 0x01 1x, 0x02 1xevdo, 0x04 gsm, 0x08 umts, 0x10 lte, 0x20 td-scdma, 0x40 5gnr
for label, mask in [("LTE-only", 0x0010), ("LTE+GSM+UMTS", 0x001C)]:
    res, err = m.call(3, 0x0033, tlv(0x11, struct.pack("<H", mask)), timeout=10)
    print("%-14s mask=0x%04x -> %s %s" % (label, mask, res, err or ""))
    if res and res[0] == 0:
        print("  applied.")
        break
    time.sleep(2)

time.sleep(5)
res, err = m.call(3, 0x0024, b"")
print("serving ->", res, err or "")
