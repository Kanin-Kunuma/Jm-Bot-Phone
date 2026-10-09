# JM-Bot 手机端部署指南

本文档介绍如何在 root 权限的 Android 手机上使用 Termux + proot-distro + NapCat + ncatbot 部署 JM-Bot。

## 📋 目录

- [系统要求](#系统要求)
- [环境准备](#环境准备)
- [NapCat 安装与配置](#napcat-安装与配置)
- [ncatbot 补丁](#ncatbot-补丁)
- [JM-Bot 配置](#jm-bot-配置)
- [插件优化](#插件优化)
- [Android 保活配置](#android-保活配置)
- [启动流程](#启动流程)
- [故障排除](#故障排除)

---

## 系统要求

- **Android 设备**：已 root，推荐 Android 7.0+
- **存储空间**：至少 5GB 可用空间
- **网络**：稳定的网络连接
- **QQ 账号**：用于机器人的 QQ 小号

## 环境准备

### 1. 安装 Termux

从 [F-Droid](https://f-droid.org/packages/com.termux/) 或 [GitHub Releases](https://github.com/termux/termux-app/releases) 下载安装 Termux（不要使用 Google Play 版本）。

### 2. 更新软件包

```bash
pkg update && pkg upgrade
```

### 3. 安装必要工具

```bash
pkg install python git proot-distro
```

### 4. 安装 proot-distro 容器

```bash
proot-distro install debian
proot-distro rename debian napcat
```

---

## NapCat 安装与配置

### 1. 进入 proot 容器

```bash
proot-distro login napcat
```

### 2. 容器内安装依赖

```bash
apt update
apt install -y curl xvfb
```

### 3. 安装 NapCat

```bash
curl -o napcat.sh https://nclatest.znin.net/NapCat-Installer/main/script/install.sh && bash napcat.sh
```

安装时选择：
- QQ 版本：`3.2.34-53644-arm64`（或最新支持版本）
- NapCat 版本：推荐 `4.18.28` 或更高

### 4. 配置 OneBot WebSocket

编辑配置文件：

```bash
nano /root/Napcat/opt/QQ/resources/app/app_launcher/napcat/config/onebot11_<你的QQ号>.json
```

找到 WebSocket 部分，修改为：

```json
{
  "name": "JM",
  "enable": true,
  "host": "127.0.0.1",
  "port": 3001,
  "heartInterval": 30000,
  "token": "jmbot3001",
  "messagePostFormat": "array"
}
```

**重要**：`token` 必须与后续 JM-Bot 的 `config.yaml` 中 `ws_token` 一致。

### 5. 启动 NapCat

```bash
xvfb-run -a /root/Napcat/opt/QQ/qq --no-sandbox -q <你的QQ号>
```

首次启动会打开 WebUI，访问 `http://127.0.0.1:6099/webui?token=<webui_token>` 完成 QQ 登录。


---

## 插件优化

### JmComicPlugin 手机版特性

本项目的 JmComicPlugin 已针对手机环境进行优化，**代码中已包含所有修复，无需额外配置**：

1. ✅ **asyncio.Lock** - 避免事件循环阻塞（原版使用 threading.Lock 会导致机器人卡死）
2. ✅ **共享存储路径** - 自动复制 PDF 到 `/storage/emulated/0/Download/JM-Bot-pdf`，解决 proot 容器权限问题
3. ✅ **180秒上传超时** - 防止 NapCat 文件上传时无限等待
4. ✅ **简化消息输出** - 减少回复刷屏，只发送关键信息
5. ✅ **2天 PDF 过期** - 节省手机存储空间（PC版默认7天）
6. ✅ **3个下载 worker** - 平衡下载速度与资源占用

直接使用即可，无需手动修改代码。

---

## Android 保活配置

Android 系统会主动杀死后台应用，导致 Termux 和 NapCat 进程终止。需要以下配置：

### 1. 电池控制

- 设置 → 应用 → Termux → 电池 → **无限制**（或"不限制"）

### 2. 后台运行权限

```bash
# 在 Termux 中执行
termux-wake-lock

# 在 adb shell 或 root shell 中执行
dumpsys deviceidle whitelist +com.termux
appops set com.termux RUN_IN_BACKGROUND allow
```

---

## 启动流程

### 启动顺序

1. **启动 NapCat**（proot 容器内）
2. **启动 JM-Bot**（Termux 主环境）

### 方法 1：手动启动（建议此操作，方便查看异常）

#### 会话 1：启动 NapCat

```bash
proot-distro login napcat
termux-wake-lock
xvfb-run -a /root/Napcat/opt/QQ/qq --no-sandbox -q <你的QQ号>
```

#### 会话 2：启动 JM-Bot

在 Termux 中新建会话（下拉通知栏 → New Session）：

```bash
cd ~/JM-Bot
termux-wake-lock
python main.py
```

### 方法 2：后台启动（懒人方案）

```bash
# 启动 NapCat（后台）
proot-distro login napcat -- bash -c "xvfb-run -a /root/Napcat/opt/QQ/qq --no-sandbox -q <你的QQ号> > /tmp/napcat.log 2>&1 &"

# 等待 2 秒让 NapCat 完全启动
sleep 2

# 启动 JM-Bot（前台）
cd ~/JM-Bot
python main.py
```

### 验证启动成功

1. 检查 WebSocket 连接：

```bash
netstat -tlnp | grep 3001
```

应显示：`tcp  0  0 127.0.0.1:3001  0.0.0.0:*  LISTEN`

2. 发送测试消息：

在 QQ 中向机器人发送 `/jm 114514`，应正常下载并发送 PDF。

---

## 故障排除

### 问题 1：WebSocket Token 填写错误

**错误信息**：`WebSocket Token 填写错误`

**原因**：NapCat 和 JM-Bot 的 `ws_token` 不一致，或者 ncatbot 未打补丁。

**解决方案**：
1. 检查 NapCat 配置文件中的 `token` 字段
2. 检查 `config.yaml` 中的 `ws_token` 字段
3. 确保两者完全一致
4. 应用 [ncatbot 补丁](#ncatbot-补丁)

### 问题 2：PDF 下载完成但未发送

**症状**：日志显示"合成PDF成功"，但文件未发送，后续命令无响应。

**原因**：
- `threading.Lock` 阻塞 asyncio 事件循环
- NapCat 文件上传超时
- proot 容器无法访问 Termux 文件路径

**解决方案**：应用 [插件优化](#插件优化) 中的所有修复。

### 问题 3：Termux 后台被杀

**症状**：锁屏或切换应用后，Termux 进程消失。

**解决方案**：
1. 检查 [Android 保活配置](#android-保活配置)
2. 确认 `termux-wake-lock` 已执行
3. 检查系统日志：`logcat | grep termux`

### 问题 4：xvfb-run 未安装

**错误信息**：`The program xvfb-run is not installed`

**原因**：在 Termux 主环境执行了 proot 容器命令。

**解决方案**：
```bash
# 先进入 proot 容器
proot-distro login napcat

# 然后再执行 xvfb-run 命令
xvfb-run -a /root/Napcat/opt/QQ/qq --no-sandbox -q <你的QQ号>
```

### 问题 5：文件发送失败 (Permission Denied)

**错误信息**：`PermissionError: [Errno 13] Permission denied`

**原因**：NapCat（运行在 proot 内）无法访问 Termux 私有目录。

**解决方案**：插件已自动将 PDF 复制到 `/storage/emulated/0/Download/JM-Bot-pdf`，无需手动操作。如果仍失败：

```bash
# 检查共享存储权限
termux-setup-storage

# 检查目录权限
ls -la /storage/emulated/0/Download/
```

### 问题 6：PacketBackend 警告

**警告信息**：`QQ version 3.2.34-53644-arm64 not supported`

**影响**：通常不影响基本功能，文件发送仍可正常工作。

**处理**：忽略此警告，除非实际发送失败。

---

## 常用命令速查

### 启动命令

```bash
# 会话1：启动 NapCat
proot-distro login napcat
xvfb-run -a /root/Napcat/opt/QQ/qq --no-sandbox -q 2250386460

# 会话2：启动 JM-Bot
cd ~/JM-Bot
python main.py
```

### 检查命令

```bash
# 检查 WebSocket 端口
netstat -tlnp | grep 3001

# 检查进程
ps aux | grep qq
ps aux | grep python

# 查看日志
tail -f ~/JM-Bot/logs/latest.log
```

### 重启命令

```bash
# 杀死所有相关进程
pkill -f "qq --no-sandbox"
pkill -f "python main.py"

# 重新启动（按启动流程操作）
```

---

## 参考资料

- [NapCat 官方文档](https://napneko.github.io/)
- [NcatBot 项目](https://github.com/liyihao1110/NcatBot)
- [JMComic-Crawler-Python](https://github.com/hect0x7/JMComic-Crawler-Python)
- [Termux Wiki](https://wiki.termux.com/)
- [proot-distro](https://github.com/termux/proot-distro)

---

## 更新日志

- **2026-10-08**：初始版本，包含所有已知修复和优化
  - 修复 asyncio 死锁问题
  - 添加文件上传超时保护
  - 实现共享存储路径
  - 简化消息输出
  - 完善 Android 保活配置

---

## 许可证

本项目遵循 MIT License。详见 [LICENSE](LICENSE) 文件。
