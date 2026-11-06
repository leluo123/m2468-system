#!/usr/bin/env python3
"""Read EFS files via raw QMI EFS service (read-only).

QMI EFS message ids (Qualcomm QMI EFS spec):
  0x0003 = Get File
  0x0004 = Put File
Get File input: TLV 0x01 = file path (string, no NUL)
Get File output: TLV 0x01 = result, TLV 0x02 = file content
"""
import struct, sys, time
sys.path.insert(0, "/root")

from modem_daemon import Modem, tlv

EFS_SVC = 21

PATHS = [
    "/nv/item_files/mcfg/mcfg_autoselect_by_uim",
    "/nv/item_files/mcfg/mcfg_autoselect_by_uim_Subscription01",
    "/nv/item_files/modem/uim/uimdrv/uim_hw_config",
    "/nv/item_files/modem/mmode/nr_band_pref",
]

m = Modem()
print("services:", len(m.ports))
print("EFS port:", m.ports.get(EFS_SVC))


def get_file(p):
    res, err = m.call(EFS_SVC, 0x0003, tlv(0x01, p.encode()), timeout=8)
    return res, err


for p in PATHS:
    res, err = get_file(p)
    print("\n%-62s -> %s %s" % (p, res, err or ""))
    time.sleep(1.5)
