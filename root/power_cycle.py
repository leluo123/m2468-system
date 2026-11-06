#!/usr/bin/env python3
"""Power-cycle the modem's RF stack: low-power -> online, and watch radio interfaces."""
import sys, time
sys.path.insert(0, "/root")
from modem_daemon import Modem, tlv8

m = Modem()
print("services:", len(m.ports))

print("-> low-power")
print("   ", m.call(2, 0x002E, tlv8(0x01, 0), timeout=8))
time.sleep(5)

print("-> online")
print("   ", m.call(2, 0x002E, tlv8(0x01, 1), timeout=8))

for i in range(8):
    time.sleep(10)
    res, err = m.call(3, 0x0024, b"", timeout=6)
    r = m.call(3, 0x0022, tlv8(0x01, 0), timeout=6)
    print("  t=%3ds serving=%s register=%s %s" % (i * 10, res, r[0], r[1] or ""))
