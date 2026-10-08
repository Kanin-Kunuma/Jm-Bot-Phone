# JM-Bot 手机版部署指南 (NapCat.Termux)

## 环境要求
- ✅ 黑鲨1 (SKR-A0) Android 10 + Magisk root
- Termux (F-Droid 版本，不是 Google Play 版)
- NapCat.Termux (官方 Termux 部署方案)

## 为什么选择 NapCat.Termux？

| 方案 | 需要 root | 风控风险 | 部署难度 | 维护状态 |
|------|----------|----------|----------|----------|
| **NapCat.Termux** | ❌ 不需要 | 🟢 低 | 🟢 简单 | ✅ 官方维护 |
| Shamrock (OpenShamrock) | ✅ 必须 | 🟢 低 | 🟡 中等 | ❌ 项目404 |
| Lagrange | ❌ 不需要 | 🔴 高 | 🟢 简单 | ✅ 活跃 |

**NapCat.Termux 是当前最佳方案：**
- 基于 NTQQ，不是模拟协议，风控风险低
- 官方维护，有专门的 Termux 脚本
- 不需要 root（虽然你已经 root 了）
- 不需要 Xposed/LSPosed/Shamrock

## 部署步骤

### 1. 安装 Termux

**重要：必须从 F-Droid 安装，不要用 Google Play 版本！**

下载地址：https://f-droid.org/packages/com.termux/

或者直接下载 APK：https://github.com/termux/termux-app/releases

### 2. Termux 基础配置

```bash
# 更新包管理器
pkg update && pkg upgrade

# 安装必要工具
pkg install python git wget curl
```

### 3. 安装 NapCat.Termux

**官方一键脚本：**

```bash
curl -o napcat.termux.sh https://nclatest.znin.net/NapNeko/NapCat-Installer/main/script/install.termux.sh && bash napcat.termux.sh
```

脚本会自动：
- 下载并安装 QQ (如果没有)
- 安装 NapCat
- 配置 OneBot 协议 (ws://127.0.0.1:3001)
- 生成启动脚本

按照提示操作，用 QQ 扫码登录。

### 4. 将机器人代码复制到手机

方法1 - 通过 USB：
```bash
# 在 PC 上，将 JM-Bot-phone 文件夹复制到手机存储
# 然后在 Termux 中：
cd ~
ln -s /storage/emulated/0/JM-Bot-phone JM-Bot
```

方法2 - 直接在 Termux 下载：
```bash
cd ~
# 如果你的代码在 GitHub
git clone <你的仓库地址> JM-Bot
# 或者手动创建
mkdir -p JM-Bot
cd JM-Bot
```

### 5. 安装 Python 依赖

```bash
cd ~/JM-Bot

# 升级 pip
pip install --upgrade pip

# 重要：Termux 特殊处理
# ncatbot 需要 --no-deps (Termux psutil 有问题)
pip install ncatbot==4.4.1.post1 --no-deps

# img2pdf 使用 0.4.4
pip install img2pdf==0.4.4

# 其他依赖正常安装
pip install jmcomic requests aiohttp Pillow
```

如果遇到问题：
```bash
# img2pdf 降级方案
pip install img2pdf==0.3.16 --no-deps
```

### 6. 启动机器人

**方法1 - 简单启动 (两个 Termux 会话):**

打开第一个 Termux 会话：
```bash
# 启动 NapCat (按照安装脚本的提示)
# 通常是类似这样的命令：
napcat start
# 或者
cd ~/napcat && ./start.sh
```

打开第二个 Termux 会话（下拉通知栏 → New session）：
```bash
cd ~/JM-Bot
termux-wake-lock  # 防止休眠
python main.py
```

**方法2 - 使用 tmux (推荐):**

```bash
pkg install tmux

# 创建 NapCat 会话
tmux new -s napcat
# 启动 NapCat，然后按 Ctrl+B 再按 D 退出

# 创建 Bot 会话
tmux new -s bot
cd ~/JM-Bot
termux-wake-lock
python main.py
# 按 Ctrl+B 再按 D 退出

# 重新进入会话：
# tmux attach -t napcat
# tmux attach -t bot
```

### 7. 验证运行

在 QQ 中发送 `/菜单`，机器人应该会回复功能列表。

测试禁漫功能：`/jm 123456` (随便一个本子ID)

## 手机版特性

相比 PC 版的优化：
1. ✅ PDF 过期：7天 → **2天** (节省手机存储)
2. ✅ 下载 workers：2 → **3**
3. ✅ 文件上传序列化：`_file_send_lock`
4. ✅ PDF 发送：**始终作为文件**，不转图片
5. ✅ 使用 NapCat.Termux

## 常见问题

### Q: NapCat 安装失败
A: 
1. 确保使用 F-Droid 版 Termux（不是 Google Play）
2. 检查网络连接
3. 尝试手动下载脚本后再运行

### Q: psutil 报错
A:
```bash
pip uninstall psutil
pip install ncatbot==4.4.1.post1 --no-deps
```

### Q: img2pdf 报错
A:
```bash
pip install img2pdf==0.3.16 --no-deps
```

### Q: 手机休眠后 Bot 停止
A:
```bash
# 启用 wake lock
termux-wake-lock

# 或在 Android 设置中：
# 电池 → Termux → 允许后台运行
# 电池 → Termux → 无限制
```

### Q: 会不会风控？
A: NapCat 基于 NTQQ，不是模拟协议，风控风险比 Lagrange 低得多。但建议：
- 不要频繁发送大量消息
- 不要短时间内下载大量本子
- 正常使用一般不会有问题

### Q: NapCat 和 Lagrange 的区别？
A:
- **NapCat**: 基于官方 NTQQ，hook 方式，风控风险低
- **Lagrange**: 独立协议实现，模拟 QQ，风控风险较高

你之前账号被风控，所以用 NapCat 更安全。

### Q: 需要签名服务器吗？
A: NapCat 通常不需要单独配置签名服务器，它会处理好协议签名。如果遇到登录问题，查看 NapCat 文档配置签名。

## 性能优化

1. **省电优化**：
   - Termux 后台运行限制放开
   - 使用 tmux 管理会话
   - 启用 wake-lock

2. **内存优化**：
   - 黑鲨1 内存有限，关闭不必要的应用
   - 定期清理 `pdf/` 和 `stock/` 目录

3. **存储优化**：
   - PDF 2天自动过期
   - 手动清理 stock 目录：`rm -rf ~/JM-Bot/stock/*`



## 更新日志

- 2026-09-25: 从 Shamrock 方案改为 NapCat.Termux (Shamrock 项目 404)
- 手机版优化：2天PDF过期，3个下载worker，序列化文件上传

---

有任何问题随时问我！NapCat.Termux 是目前最稳定的 Android 方案。
