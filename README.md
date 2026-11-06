# m2468 系统层

魅族 21 Note 上跑 Linux 时，我们自己写的系统配置和用户态脚本。

主仓库是 [m2468-mainline](https://github.com/leluo123/m2468-mainline)（内核 + 文档 + 踩坑），
固件在 [m2468-firmware](https://github.com/leluo123/m2468-firmware)。
这个仓库放的是两者之间那一层：让系统能真正用起来的 configuration 和 daemon。

rootfs 本体是 postmarketOS v26.06（Alpine 系）+ phosh 桌面，我们没有重造轮子，只在上面加东西。
下面这些都是手写或改出来的。

## 目录

```
etc/systemd/system/
  m2468-data.service              WDS 拨号 daemon
  m2468-rf-keeper.service         射频自愈，掉了自动上下电
  m2468-modem-bringup.service     基带初始化（SIM 会话 + bind subscription + online）
  m2468-cpufreq.service           CPU 调频限制，缓解随机重启
  m2468-charge-limit.service      USB 输入电流提到 900mA
  fix-shm-perm.service            修 /dev/shm 权限（phoc 起来之前必须先跑）
  seatd.service                   seat 管理，phoc 依赖

etc/udev/rules.d/
  99-m2468-charge.rules           充电电流规则

etc/NetworkManager/conf.d/
  20-connectivity-cn.conf         connectivity 检测换成国内可达的 204 端点

etc/fstab                         根分区 + /dev/shm
usr/share/phosh/phoc.ini          屏幕参数（mode 必须带 Hz 后缀）
usr/local/bin/m2468-cpufreq.sh    调频脚本

root/                             设备上 /root 下的全部脚本
  modem_daemon.py                 基带初始化 daemon
  data_daemon.py                  WDS 常驻客户端，拿 IP 并配 rmnet_ipa0
  rf_keeper.py                    射频自愈
  dms_mode.py                     DMS 工作模式读写（qmicli 的读数不可信）
  bind_all.py                     NAS/VOICE/WMS/DSD/WDS 全部 Bind Subscription
  mux_matrix.py                   WDS mux 扫描
  wds_probe.py / wds_bindmux.py   WDS 报文探测
  tlv_dump.py                     QMI TLV 解析
  nas_lte.py / nas_register.py    网络注册
  power_cycle.py                  DMS 上下电
  efs_get.py / efs_probe.py       EFS 读写探测
  restore_efs.sh / restore_rb.sh  EFS 回灌与回滚
  collect_state.sh                一键收集基带状态
  keep_online.sh / full_bringup.sh
  pdc_reload2.sh                  PDC 配置加载
  data_up.py / data_up2.py / data_full.py  早期拨号脚本（保留作参考）
```

## 怎么用

把这些文件按同样的路径放回 rootfs，然后：

```bash
systemctl daemon-reload
systemctl enable --now seatd fix-shm-perm m2468-cpufreq m2468-charge-limit
systemctl enable --now m2468-data m2468-rf-keeper
```

基带那几个服务依赖 `rmtfs` 和 `tqftpserv`，先把它们装好并跑起来
（`linux-msm/rmtfs`、`linux-msm/tqftpserv`，配置方法见主仓库的踩坑合集）。

## 几个容易踩的点

`/dev/shm` 的权限必须显式修。phoc 在 `/dev/shm` 权限不对的时候起不来，
而且报错不会告诉你是这个原因。所以 `fix-shm-perm.service` 的 `Before=greetd.service` 不能删。

`phoc.ini` 里的 mode 必须带 `Hz`，写 `1264x2780@120.00` 不生效，
要写 `1264x2780@120.00Hz`。

`99-m2468-charge.rules` 用的是 `ENV{POWER_SUPPLY_NAME}` 不是 `ATTR{name}`。
写成 `ATTR{name}` 规则永远不会触发，而且不报错。

`m2468-modem-bringup.service` 现在在我们的机器上是 mask 掉的。
它会发 `--uim-change-provisioning-session`，那个操作会把 SIM 弄成 eUICC 误判。
如果射频已经起来了，别启用它。

## 没有放进来的东西

WiFi 密码（`/etc/NetworkManager/system-connections/*.nmconnection`）、
SSH host key、`/etc/shadow`、shell 历史、`/var/log`。
这些要么是隐私，要么是机器唯一的，换成你的环境得重新生成。

## 许可

配置和脚本按 MIT。用的时候不用问。
