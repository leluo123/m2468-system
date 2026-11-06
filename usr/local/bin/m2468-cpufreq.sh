#!/bin/sh
# m2468: 内核默认 governor 在开机时落成 performance，
# 三簇全锁最高频(2.02/2.80/2.96GHz) -> 持续 1A 电流 + 58C 高温
# -> 电池压降 -> SoC 供电跌破阈值 -> PMIC 复位 = 随机重启/掉 fastboot。
# 改为 schedutil + 限到倒数第二档：实测 1084mA->741mA，58C->38C。
# 注意顺序：必须先写 scaling_max_freq 再写 governor，
# 反过来切 governor 会把 max_freq 重置回最高档。
for p in /sys/devices/system/cpu/cpufreq/policy*; do
	[ -d "$p" ] || continue
	S=$(awk '{print $(NF-1)}' "$p/scaling_available_frequencies" 2>/dev/null)
	[ -n "$S" ] && echo "$S" > "$p/scaling_max_freq" 2>/dev/null
	echo schedutil > "$p/scaling_governor" 2>/dev/null
done
