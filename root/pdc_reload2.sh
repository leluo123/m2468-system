#!/bin/sh
# Load CMCC + platform RF configs into PDC and activate CMCC.
# Requires /root/shim.so (LD_PRELOAD workaround for the qmicli g_free segfault).
L=/root/pdc_load2.log
: > $L
B=/lib/firmware/qcom/sm8550/meizu/modem_pr/mcfg/configs/mcfg_sw/generic/China
RF=/lib/firmware/qcom/sm8550/meizu/modem_pr/mcfg/configs/mcfg_ddr/rf

echo "=== START $(date +%T) rmtfs=$(systemctl is-active rmtfs-dir) shim=$(ls -l /root/shim.so 2>/dev/null | awk '{print $5}') ===" >> $L

echo "--- SW CMCC $(date +%T) ---" >> $L
LD_PRELOAD=/root/shim.so qmicli -d qrtr://0 --pdc-load-config=$B/CMCC/Commercial/Volte_OpenMkt/mcfg_sw.mbn >> $L 2>&1
echo "rc=$? $(date +%T)" >> $L
sleep 2

for f in rf_static_473_00_00.mbn rf_static_463_00_00.mbn; do
  echo "--- PLATFORM $f $(date +%T) ---" >> $L
  PDC_FORCE_PLATFORM=1 LD_PRELOAD=/root/shim.so qmicli -d qrtr://0 --pdc-load-config=$RF/$f >> $L 2>&1
  echo "rc=$? $(date +%T)" >> $L
  sleep 2
done

echo "=== LIST $(date +%T) ===" >> $L
timeout 30 qmicli -d qrtr://0 --pdc-list-configs=software >> $L 2>&1
echo "=== LIST PLATFORM ===" >> $L
timeout 30 qmicli -d qrtr://0 --pdc-list-configs=platform >> $L 2>&1

echo "=== ACTIVATE (CMCC) $(date +%T) ===" >> $L
ID=$(timeout 30 qmicli -d qrtr://0 --pdc-list-configs=software 2>/dev/null | grep -B4 -i "cmcc\|volte_openmkt" | grep -oE "[0-9A-F]{2}(:[0-9A-F]{2}){19}" | head -1)
echo "config id = $ID" >> $L
if [ -n "$ID" ]; then
  timeout 60 qmicli -d qrtr://0 --pdc-activate-config=software,$ID >> $L 2>&1
  echo "activate rc=$?" >> $L
fi

echo "=== VERIFY $(date +%T) ===" >> $L
timeout 25 qmicli -d qrtr://0 --dms-get-band-capabilities >> $L 2>&1
timeout 25 qmicli -d qrtr://0 --nas-get-serving-system >> $L 2>&1
echo "ALLDONE $(date +%T)" >> $L
