#!/usr/bin/env python3
"""Probe QMI EFS message ids slowly (2s apart) to find Get/Put File."""
import struct, sys, time
sys.path.insert(0, "/root")
from modem_daemon import Modem

EFS = 21
PATH = "/nv/item_files/mcfg/mcfg_autoselect_by_uim"


def tlv(t, v):
    return struct.pack("<BH", t, len(v)) + v


m = Modem()
print("EFS port:", m.ports.get(EFS))

# 先用空 body 探哪些 mid 存在（有响应且不是 57 = 该 mid 存在）
for mid in [0x0001, 0x0002, 0x0003, 0x0004, 0x0005, 0x0006, 0x0007, 0x0008]:
    res, err = m.call(EFS, mid, b"", timeout=6)
    print("  mid=0x%04x -> %s %s" % (mid, res, err or ""))
    time.sleep(2)

print("\n--- 用 TLV 0x01=path 试 Get ---")
for mid in [0x0003, 0x0004, 0x0001, 0x0002]:
    res, err = m.call(EFS, mid, tlv(0x01, PATH.encode()), timeout=6)
    print("  mid=0x%04x path-tlv -> %s %s" % (mid, res, err or ""))
    time.sleep(2)
