#!/bin/sh
# Full bringup: SIM session -> bind subscriptions -> keep online -> watch registration
set -u

echo "=== 1) 激活 SIM 会话 ==="
qmicli -d qrtr://0 --uim-change-provisioning-session="slot=1,activate=yes,session-type=primary-gw-provisioning,aid=a0000000871002ff86ffff89ffffffff" 2>&1 | tail -1
sleep 5
qmicli -d qrtr://0 --uim-get-card-status 2>/dev/null | grep -E "Application state|Personalization" | head -2

echo "=== 2) Bind Subscription ==="
python3 /root/bind_all.py 2>&1 | grep -E "Bind|Dual|online" | head -10

echo "=== 3) 保持 online 并观察 ==="
i=0
while [ $i -lt 20 ]; do
  qmicli -d qrtr://0 --dms-set-operating-mode=online >/dev/null 2>&1
  R=$(qmicli -d qrtr://0 --nas-get-serving-system 2>/dev/null | grep "Registration state" | sed "s/.*: //" | tr -d "'")
  N=$(qmicli -d qrtr://0 --nas-get-serving-system 2>/dev/null | grep "Selected network" | sed "s/.*: //" | tr -d "'")
  S=$(qmicli -d qrtr://0 --nas-get-signal-strength 2>/dev/null | grep -m1 "Network" | sed "s/.*: //")
  echo "  t=$((i*12))s reg=[$R] net=[$N] sig=$S"
  if [ "$R" = "registered" ]; then
    echo "*** REGISTERED ***"
    qmicli -d qrtr://0 --nas-get-serving-system 2>/dev/null | head -12
    break
  fi
  i=$((i+1))
  sleep 12
done
