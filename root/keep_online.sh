#!/bin/sh
# Keep the modem online and watch registration for ~4 minutes.
i=0
while [ $i -lt 24 ]; do
  qmicli -d qrtr://0 --dms-set-operating-mode=online >/dev/null 2>&1
  M=$(qmicli -d qrtr://0 --dms-get-operating-mode 2>/dev/null | grep -oE "'[a-z-]+'" | head -1)
  R=$(qmicli -d qrtr://0 --nas-get-serving-system 2>/dev/null | grep "Registration state" | sed "s/.*: //" | tr -d "'")
  S=$(qmicli -d qrtr://0 --nas-get-signal-strength 2>/dev/null | grep -m1 "Network" | sed "s/.*: //")
  N=$(qmicli -d qrtr://0 --nas-get-serving-system 2>/dev/null | grep "Selected network" | sed "s/.*: //" | tr -d "'")
  echo "  t=$((i*10))s mode=$M reg=[$R] net=[$N] sig=$S"
  if [ "$R" = "registered" ]; then
    echo "  *** REGISTERED ***"
    break
  fi
  i=$((i+1))
  sleep 10
done
