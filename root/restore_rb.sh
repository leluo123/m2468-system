#!/bin/sh
# Put back the pre-restore EFS snapshot (the state where the PDC still had the
# rf_static_463/473 platform configs loaded).
L=/root/efs_rollback.log
: > $L
echo "=== $(date) rollback to pre-restore snapshot ===" >> $L

systemctl stop m2468-data 2>/dev/null
systemctl stop rmtfs-dir 2>/dev/null
sleep 3

P1=/dev/disk/by-partlabel/modemst1
P2=/dev/disk/by-partlabel/modemst2

dd if=/root/rb1.img of=$P1 bs=1M conv=fsync >> $L 2>&1
echo "write ms1 rc=$?" >> $L
dd if=/root/rb2.img of=$P2 bs=1M conv=fsync >> $L 2>&1
echo "write ms2 rc=$?" >> $L
sync

dd if=$P1 of=/tmp/v1.img bs=1M >> $L 2>&1
dd if=$P2 of=/tmp/v2.img bs=1M >> $L 2>&1
echo "--- readback (expect cc322a5d..., b3c51273...) ---" >> $L
md5sum /tmp/v1.img /tmp/v2.img >> $L 2>&1

systemctl start rmtfs-dir 2>/dev/null
echo "restarted rmtfs=$(systemctl is-active rmtfs-dir)" >> $L
echo "=== done ===" >> $L
cat $L
