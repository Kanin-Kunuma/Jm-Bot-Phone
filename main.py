import os
import sys
import time
import socket
import signal
from ncatbot.core import BotClient, GroupMessage, PrivateMessage
from ncatbot.utils import get_log

bot = BotClient()
_log = get_log()

def cleanup():
    """清理资源"""
    _log.info("正在清理资源...")
    try:
        os._exit(0)
    except:
        pass

def signal_handler(signum, frame):
    """信号处理器"""
    _log.info(f"收到终止信号 {signum}，正在关闭...")
    cleanup()

# 注册信号处理器
signal.signal(signal.SIGINT, signal_handler)  # Ctrl+C
signal.signal(signal.SIGTERM, signal_handler)  # 终止信号

def check_shamrock_running(host='127.0.0.1', port=3001):
    """检查 Shamrock 是否运行"""
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(1)
        result = sock.connect_ex((host, port))
        sock.close()
        return result == 0
    except:
        return False

# ========== 菜单功能 ==========
@bot.group_event()
async def on_group_message(msg: GroupMessage):
    if msg.raw_message == "/菜单":
        menu_text = """🤖 QQ机器人功能菜单 🤖

📚 禁漫本子下载 (JmComicPlugin)
• /jm <本子ID> - 下载禁漫本子并发送PDF
• 例如: /jm 114514

🎨 二次元图片 (Lolicon)
• /loli [数量] [标签] - 发送随机二次元图片
• 示例: /loli 3 萝莉、/loli 白丝
"""
        await msg.reply(text=menu_text)

@bot.private_event()
async def on_private_message(msg: PrivateMessage):
    if msg.raw_message == "/菜单":
        menu_text = """🤖 QQ机器人功能菜单 🤖

📚 禁漫本子下载 (JmComicPlugin)
• /jm <本子ID> - 下载禁漫本子并发送PDF
• 例如: /jm 114514

🎨 二次元图片 (Lolicon)
• /loli [数量] [标签] - 发送随机二次元图片
• /r18 [数量] [标签] - 发送R18图片(私聊可用)
• 示例: /loli 3 萝莉、/loli 白丝
"""
        await bot.api.post_private_msg(msg.user_id, text=menu_text)

# ========== 启动 BotClient ==========
if __name__ == "__main__":
    _log.info("========== 启动 Bot (Phone 版 - Shamrock) ==========")

    # 手机环境必须先启动 Shamrock (Xposed 模块 hook QQ)
    if not check_shamrock_running():
        _log.error("未检测到 ws://127.0.0.1:3001")
        _log.error("请先启动 Shamrock:")
        _log.error("1. 确认 LSPosed 已启用 Shamrock 模块")
        _log.error("2. 确认 Shamrock 作用域已勾选 QQ")
        _log.error("3. 打开 QQ 登录账号")
        _log.error("4. 打开 Shamrock 应用，启动 WebSocket 服务（127.0.0.1:3001）")
        sys.exit(1)
    else:
        _log.info("Shamrock 已运行 (ws://127.0.0.1:3001)")

    bot.run(bt_uin=2250386460, root="1437996009")
