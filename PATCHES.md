# 补丁说明文档

本文档包含 JM-Bot 手机版所需的各种补丁和修复代码。**注意：当前项目代码已包含所有修复，此文档仅供参考或从原版迁移时使用。**

---

## 📋 目录

- [ncatbot 补丁](#ncatbot-补丁)
- [JmComicPlugin 插件修复](#jmcomicplugin-插件修复)

---

## ncatbot 补丁

### 问题描述

NapCat 返回的 WebSocket 握手响应格式与 ncatbot 默认期望的格式不完全兼容，会导致连接失败并报错 `WebSocket Token 填写错误`。

### 修复方法

编辑 ncatbot 源码：

```bash
cd ~/JM-Bot
nano .venv/lib/python3.11/site-packages/ncatbot/client/launch.py
```

**修改 1：兼容 dict 格式的 status**

找到 `validate_napcat_response` 函数，替换为：

```python
def validate_napcat_response(response: Dict[str, Any], uri: str) -> None:
    if "status" in response:
        status_value = response["status"]
        # 兼容 dict 格式的 status
        if isinstance(status_value, dict):
            if status_value.get("ok") is True or status_value.get("success") is True:
                return
        elif status_value == "ok":
            return
    
    # 兼容 NapCat 的 post_type 字段
    if response.get("post_type"):
        return
    
    raise ValueError(f"NapCat handshake failed at {uri}: {response}")
```

**修改 2：处理空 token**

找到 `get_uri_with_token` 函数，替换为：

```python
def get_uri_with_token(uri: str, token: str) -> str:
    # 空 token 不追加参数
    if not token or not token.strip():
        return uri
    separator = "&" if "?" in uri else "?"
    return f"{uri}{separator}access_token={token}"
```

---

## JmComicPlugin 插件修复

### 问题描述

原版 JmComicPlugin 在手机环境存在以下问题：

1. **事件循环死锁** - 使用 `threading.Lock` 导致 asyncio 阻塞
2. **文件权限问题** - proot 容器无法访问 Termux 私有目录
3. **上传超时** - NapCat 上传卡住时无限等待
4. **消息刷屏** - 每个状态都回复并引用命令

### 手动修复（方法1）

编辑插件文件：

```bash
cd ~/JM-Bot
nano plugins/JmComicPlugin/main.py
```

#### 修复 1：使用 asyncio.Lock

找到第 38 行左右：

```python
# 原代码
self._file_send_lock = threading.Lock()

# 修改为
self._file_send_lock = asyncio.Lock()
```

同时在文件开头添加 `shutil` 导入：

```python
import shutil
```

#### 修复 2：添加共享存储路径方法

在 `_send_one_file` 方法之前插入：

```python
def _shared_pdf_path(self, file_path: str) -> str:
    """复制到 Download，给 proot 里的 NapCat 读。失败则用原路径。"""
    shared_dir = "/storage/emulated/0/Download/JM-Bot-pdf"
    try:
        os.makedirs(shared_dir, exist_ok=True)
        dest = os.path.join(shared_dir, os.path.basename(file_path))
        if os.path.abspath(file_path) != os.path.abspath(dest):
            src_mtime = os.path.getmtime(file_path)
            if not os.path.isfile(dest) or os.path.getmtime(dest) < src_mtime:
                shutil.copy2(file_path, dest)
        return dest
    except OSError as e:
        print(f"复制到共享目录失败，改用原路径: {e}")
        return file_path
```

#### 修复 3：修改 _send_one_file 方法

找到 `_send_one_file` 方法，替换为：

```python
async def _send_one_file(self, msg: BaseMessage, file_path: str, timeout: float = 180):
    send_path = self._shared_pdf_path(file_path)
    if hasattr(msg, "group_id"):
        await asyncio.wait_for(
            self.api.post_group_file(group_id=msg.group_id, file=send_path),
            timeout=timeout,
        )
    else:
        await asyncio.wait_for(
            self.api.post_private_file(user_id=msg.user_id, file=send_path),
            timeout=timeout,
        )
```

#### 修复 4：添加简化消息方法

在类中添加新方法：

```python
async def _notify(self, msg: BaseMessage, text: str):
    """普通群/私聊消息，不引用原指令。"""
    try:
        if hasattr(msg, "group_id"):
            await self.api.post_group_msg(group_id=msg.group_id, text=text)
        else:
            await self.api.post_private_msg(user_id=msg.user_id, text=text)
    except Exception as e:
        print(f"发送消息失败: {e}")
```

然后在需要发送通知的地方，将 `await msg.reply(text=...)` 改为 `await self._notify(msg, ...)`。

#### 修复 5：优化随机推荐

找到 `jm_download_handler` 方法，修改随机推荐部分：

```python
async def jm_download_handler(self, event: BaseMessage, album_id: str = ""):
    if not album_id:
        # 随机推荐
        album_id, title = await asyncio.to_thread(self._pick_random_album)
        title = (title or "").replace("\n", " ").strip()
        if len(title) > 40:
            title = title[:40] + "..."
        await self._notify(event, f"随机 {album_id}\n{title}")
        await self._request_album(event, album_id, silent=True)  # 添加 silent 参数
    else:
        await self._request_album(event, album_id, silent=False)
```

同时修改 `_request_album` 方法签名，添加 `silent` 参数：

```python
async def _request_album(self, event: BaseMessage, album_id: str, silent: bool = False):
    # ... 原有代码 ...
    
    # 在发送排队/下载消息时检查 silent
    if not silent:
        if queue_size > 0:
            await self._notify(event, f"{album_id} 排队中（前面还有 {queue_size} 个）")
        else:
            await self._notify(event, f"正在下载 {album_id}")
```

---

### 自动修复（方法2）

使用以下 Python 脚本自动应用所有修复：

```bash
cat > /tmp/patch_jm.py << 'PATCH_EOF'
import re
import sys

file_path = "/data/data/com.termux/files/home/JM-Bot/plugins/JmComicPlugin/main.py"

try:
    with open(file_path, "r", encoding="utf-8") as f:
        code = f.read()
except FileNotFoundError:
    print(f"错误：文件不存在 {file_path}")
    sys.exit(1)

# 1. 添加 shutil 导入
if "import shutil" not in code:
    code = re.sub(
        r'(import threading\n)',
        r'\1import shutil\n',
        code
    )
    print("✓ 添加 shutil 导入")

# 2. threading.Lock -> asyncio.Lock
if "threading.Lock()" in code:
    code = re.sub(
        r'self\._file_send_lock = threading\.Lock\(\)',
        'self._file_send_lock = asyncio.Lock()',
        code
    )
    print("✓ 修复 threading.Lock -> asyncio.Lock")

# 3. 添加 _shared_pdf_path 方法
if "_shared_pdf_path" not in code:
    shared_method = '''
    def _shared_pdf_path(self, file_path: str) -> str:
        """复制到 Download，给 proot 里的 NapCat 读。失败则用原路径。"""
        shared_dir = "/storage/emulated/0/Download/JM-Bot-pdf"
        try:
            os.makedirs(shared_dir, exist_ok=True)
            dest = os.path.join(shared_dir, os.path.basename(file_path))
            if os.path.abspath(file_path) != os.path.abspath(dest):
                src_mtime = os.path.getmtime(file_path)
                if not os.path.isfile(dest) or os.path.getmtime(dest) < src_mtime:
                    shutil.copy2(file_path, dest)
            return dest
        except OSError as e:
            print(f"复制到共享目录失败，改用原路径: {e}")
            return file_path
'''
    code = re.sub(
        r'(\n    async def _send_one_file)',
        shared_method + r'\1',
        code
    )
    print("✓ 添加 _shared_pdf_path 方法")

# 4. 修改 _send_one_file 添加超时和共享路径
if "asyncio.wait_for" not in code or "_shared_pdf_path" not in code:
    send_one_file_new = '''    async def _send_one_file(self, msg: BaseMessage, file_path: str, timeout: float = 180):
        send_path = self._shared_pdf_path(file_path)
        if hasattr(msg, "group_id"):
            await asyncio.wait_for(
                self.api.post_group_file(group_id=msg.group_id, file=send_path),
                timeout=timeout,
            )
        else:
            await asyncio.wait_for(
                self.api.post_private_file(user_id=msg.user_id, file=send_path),
                timeout=timeout,
            )
'''
    code = re.sub(
        r'    async def _send_one_file\(self, msg: BaseMessage, file_path: str.*?\):.*?(?=\n    async def|\n    def [a-z_])',
        send_one_file_new,
        code,
        flags=re.DOTALL
    )
    print("✓ 修改 _send_one_file 添加超时和共享路径")

# 5. 添加 _notify 方法
if "def _notify" not in code:
    notify_method = '''
    async def _notify(self, msg: BaseMessage, text: str):
        """普通群/私聊消息，不引用原指令。"""
        try:
            if hasattr(msg, "group_id"):
                await self.api.post_group_msg(group_id=msg.group_id, text=text)
            else:
                await self.api.post_private_msg(user_id=msg.user_id, text=text)
        except Exception as e:
            print(f"发送消息失败: {e}")
'''
    # 在 _send_one_file 之后插入
    code = re.sub(
        r'(    async def _send_one_file.*?timeout=timeout,\s*\))',
        r'\1' + notify_method,
        code,
        flags=re.DOTALL
    )
    print("✓ 添加 _notify 方法")

# 写回文件
try:
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(code)
    print("\n✅ 所有补丁应用成功！")
except Exception as e:
    print(f"\n❌ 写入文件失败: {e}")
    sys.exit(1)
PATCH_EOF

python /tmp/patch_jm.py
```

运行脚本：

```bash
python /tmp/patch_jm.py
```

---

## 验证修复

### 验证 ncatbot 补丁

启动机器人，检查是否能正常连接 WebSocket：

```bash
cd ~/JM-Bot
python main.py
```

应该看到类似输出：

```
[INFO] WebSocket 连接成功
[INFO] 机器人已上线
```

### 验证 JmComicPlugin 修复

1. 发送 `/jm 114514` 测试下载
2. 检查是否正常发送 PDF
3. 检查共享目录：

```bash
ls -lh /storage/emulated/0/Download/JM-Bot-pdf/
```

---

## 注意事项

1. **备份原文件** - 修改前建议备份：
   ```bash
   cp plugins/JmComicPlugin/main.py plugins/JmComicPlugin/main.py.bak
   ```

2. **Python 版本** - 脚本中的路径 `.venv/lib/python3.11/` 需要根据实际 Python 版本调整

3. **已修复版本** - 如果使用本项目最新代码，**无需应用这些补丁**

---

## 相关链接

- [主部署文档](./PHONE_DEPLOYMENT.md)
- [项目 README](./README.md)
