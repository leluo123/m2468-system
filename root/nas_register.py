#!/usr/bin/env python3
"""Kick the modem into searching: Initiate Network Register (NAS 0x0022)."""
import sys
import time

sys.path.insert(0, "/root")
from modem_daemon import Modem, tlv8, ok

m = Modem()
print("services:", len(m.ports))

# 1) Initiate Network Register, automatic (TLV 0x01 = 0)
res, err = m.call(3, 0x0022, tlv8(0x01, 0))
print("Initiate Network Register ->", res, err or "")

time.sleep(5)

# 2) 读服务系统
res, err = m.call(3, 0x0024, b"")
print("Serving system ->", res, err or "")
