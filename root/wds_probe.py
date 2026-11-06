#!/usr/bin/env python3
"""Find WDS Bind Mux Data Port message id by probing 0xB0-0xB8 (slow)."""
import struct, sys, time
sys.path.insert(0, "/root")
from modem_daemon import Modem

WDS = 1
m = Modem()
print("WDS port:", m.ports.get(WDS))
for mid in range(0x00B0, 0x00B9):
    res, err = m.call(WDS, mid, b"", timeout=5)
    print("  mid=0x%04x -> %s %s" % (mid, res, err or ""))
    time.sleep(2)
