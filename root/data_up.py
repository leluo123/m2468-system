#!/usr/bin/env python3
"""m2468 data bringup with the CORRECT QMI ids/TLVs.

WDS 0x00A2 Bind Mux Data Port
    TLV 0x10 Endpoint Info  = u32 endp_type + u32 iface   (EMBEDDED=4)
    TLV 0x11 Mux ID         = u8
    TLV 0x13 Client Type    = u32                        (TETHERED=1)
WDS 0x00AF Bind Subscription
    TLV 0x01                = u32 sub                     (1=primary)
WDS 0x0020 Start Network
    TLV 0x14 APN            = string
    TLV 0x19 IP family      = u8                          (4=IPv4)

Bind Mux first, then Bind Subscription (mux bind resets the subscription).
"""
import struct, sys, time
sys.path.insert(0, "/root")
from modem_daemon import Modem

WDS = 1
MUX = 0xF0
ENDP_EMBEDDED = 4
CLIENT_TETHERED = 1


def tlv(t, v):
    return struct.pack("<BH", t, len(v)) + v


def u8(v):
    return bytes([v])


def u32(v):
    return struct.pack("<I", v)


apn = sys.argv[1] if len(sys.argv) > 1 else "cmnet"
m = Modem()
print("WDS port:", m.ports.get(WDS))

# 1) Bind Mux Data Port
body = (tlv(0x10, u32(ENDP_EMBEDDED) + u32(1)) +
        tlv(0x11, u8(MUX)) +
        tlv(0x13, u32(CLIENT_TETHERED)))
r1 = m.call(WDS, 0x00A2, body, timeout=10)
print("1) Bind Mux Data Port (mux=0x%02X) -> %s %s" % (MUX, r1[0], r1[1] or ""))

# 2) Bind Subscription
r2 = m.call(WDS, 0x00AF, tlv(0x01, u32(1)), timeout=10)
print("2) Bind Subscription (sub=1)        -> %s %s" % (r2[0], r2[1] or ""))

# 3) Start Network
body3 = tlv(0x14, apn.encode()) + tlv(0x19, u8(4))
r3 = m.call(WDS, 0x0020, body3, timeout=45)
print("3) Start Network (apn=%s ipv4)      -> %s %s" % (apn, r3[0], r3[1] or ""))

time.sleep(3)
