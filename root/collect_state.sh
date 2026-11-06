#!/bin/sh
# Collect a full modem/baseband state snapshot for the reconstruction ledger.
# Read-only: no QMI writes, no service restarts.
OUT=/tmp/m2468_state.log
: > $OUT

echo "=== collected_at ===" >> $OUT
date >> $OUT
echo "=== kernel ===" >> $OUT
uname -a >> $OUT
echo "=== uptime ===" >> $OUT
uptime >> $OUT
echo "=== remoteproc0_state ===" >> $OUT
cat /sys/class/remoteproc/remoteproc0/state >> $OUT 2>&1
echo "=== modem_crash_count ===" >> $OUT
dmesg 2>/dev/null | grep -c "crash detected in modem" >> $OUT
echo "=== modem_last_fatal ===" >> $OUT
dmesg 2>/dev/null | grep "fatal error received" | tail -3 >> $OUT
echo "=== services ===" >> $OUT
for s in tqftpserv rmtfs-dir ModemManager m2468-data; do
  printf "%s=%s\n" "$s" "$(systemctl is-active $s 2>/dev/null)" >> $OUT
done
echo "=== serving_system ===" >> $OUT
qmicli -d qrtr://0 --nas-get-serving-system 2>&1 | head -20 >> $OUT
echo "=== dms_band_capabilities ===" >> $OUT
qmicli -d qrtr://0 --dms-get-band-capabilities 2>&1 | head -6 >> $OUT
echo "=== uim_card_status ===" >> $OUT
qmicli -d qrtr://0 --uim-get-card-status 2>&1 | head -32 >> $OUT
echo "=== uim_slot_status ===" >> $OUT
qmicli -d qrtr://0 --uim-get-slot-status 2>&1 | head -16 >> $OUT
echo "=== pdc_platform ===" >> $OUT
qmicli -d qrtr://0 --pdc-list-configs=platform 2>&1 | head -20 >> $OUT
echo "=== pdc_software ===" >> $OUT
qmicli -d qrtr://0 --pdc-list-configs=software 2>&1 | head -12 >> $OUT
echo "=== rf_firmware_dir ===" >> $OUT
ls -la /lib/firmware/qcom/sm8550/meizu/modem_pr/mcfg/configs/mcfg_ddr/rf/ >> $OUT 2>&1
echo "=== pm_genpd ===" >> $OUT
cat /sys/kernel/debug/pm_genpd/pm_genpd_summary 2>/dev/null | grep -E "^(cx|cx_ao|mss|mmcx|mx) " -A2 >> $OUT
echo "=== nm_connectivity ===" >> $OUT
nmcli networking connectivity 2>&1 | head -2 >> $OUT
echo "=== connectivity_conf ===" >> $OUT
cat /etc/NetworkManager/conf.d/20-connectivity-cn.conf 2>/dev/null >> $OUT
echo "=== wlan ===" >> $OUT
ip -br addr show wlan0 >> $OUT 2>&1
echo "=== END ===" >> $OUT
echo "written $OUT"
