#!/bin/sh
# Restore modemst1/modemst2 from the 2026-10-27 Android-era backup.
# Stop everything that touches EFS first, write, verify by reading back, then restart.
set -x
L=/root/efs_restore.log
: > $L

echo "=== $(date) begin ===" >> $L
systemctl stop m2468-data 2>/dev/null
systemctl stop rmtfs-dir 2>/dev/null
sleep 3
echo "rmtfs=$(systemctl is-active rmtfs-dir) data=$(systemctl is-active m2468-data)" >> $L

P1=/dev/disk/by-partlabel/modemst1
P2=/dev/disk/by-partlabel/modemst2
ls -la $P1 $P2 >> $L 2>&1

dd if=/root/bk_ms1.img of=$P1 bs=1M conv=fsync >> $L 2>&1
echo "write ms1 rc=$?" >> $L
dd if=/root/bk_ms2.img of=$P2 bs=1M conv=fsync >> $L 2>&1
echo "write ms2 rc=$?" >> $L
sync

# read back and verify
dd if=$P1 of=/tmp/rb_ms1.img bs=1M >> $L 2>&1
dd if=$P2 of=/tmp/rb_ms2.img bs=1M >> $L 2>&1
echo "--- readback md5 (expect 06789fda... and 6ddc38dd...) ---" >> $L
md5sum /tmp/rb_ms1.img /tmp/rb_ms2.img >> $L 2>&1

systemctl start rmtfs-dir 2>/dev/null
echo "restarted rmtfs=$(systemctl is-active rmtfs-dir)" >> $L
echo "=== done ===" >> $L
cat $L
