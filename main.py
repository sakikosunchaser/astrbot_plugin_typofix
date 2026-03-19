from astrbot.api.event import filter, AstrMessageEvent
from astrbot.api.star import Context, Star, register
from astrbot.api import logger
import asyncio
import os

@register("typofix_sentence_check_debug", "sakikosunchaser", "调试 typofix 可见路径，/病句【内容】", "0.0.1")
class TypofixDebugPlugin(Star):
    def __init__(self, context: Context):
        super().__init__(context)

    async def initialize(self):
        logger.info("[typofix_sentence_check_debug] 插件初始化完成")

    @filter.command("病句")
    async def debug_typofix(self, event: AstrMessageEvent):
        content = event.message_str.strip() or "你好"
        # 检查路径可见性
        exists_usr_local = os.path.exists("/usr/local/bin/typofix")
        exists_root_local = os.path.exists("/root/.local/bin/typofix")
        exists_home_local = os.path.exists(os.path.expanduser("~/.local/bin/typofix"))
        yield event.plain_result(
            f"os.path.exists('/usr/local/bin/typofix'): {exists_usr_local}\n"
            f"os.path.exists('/root/.local/bin/typofix'): {exists_root_local}\n"
            f"os.path.exists('~/.local/bin/typofix'): {exists_home_local}\n"
            f"HOME: {os.environ.get('HOME')}, UID: {os.getuid()}\n"
        )
        # 列举目录文件内容
        proc = await asyncio.create_subprocess_shell(
            'ls -l /usr/local/bin',
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        stdout, stderr = await proc.communicate()
        yield event.plain_result(f"ls -l /usr/local/bin 输出：\n{stdout.decode() or stderr.decode()}\n")
        
        proc2 = await asyncio.create_subprocess_shell(
            'ls -l /root/.local/bin',
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        stdout2, stderr2 = await proc2.communicate()
        yield event.plain_result(f"ls -l /root/.local/bin 输出：\n{stdout2.decode() or stderr2.decode()}\n")

        proc3 = await asyncio.create_subprocess_shell(
            f'ls -l {os.path.expanduser("~/.local/bin")}',
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        stdout3, stderr3 = await proc3.communicate()
        yield event.plain_result(f'ls -l ~/.local/bin 输出：\n{stdout3.decode() or stderr3.decode()}\n')

        # 运行whoami和pwd方便确认bot身份
        proc4 = await asyncio.create_subprocess_shell(
            'whoami',
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        stdout4, _ = await proc4.communicate()
        yield event.plain_result(f"whoami 输出：\n{stdout4.decode()}\n")
        
        proc5 = await asyncio.create_subprocess_shell(
            'pwd',
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        stdout5, _ = await proc5.communicate()
        yield event.plain_result(f"pwd 输出：\n{stdout5.decode()}\n")

        yield event.plain_result("请将所有输出完整贴给我，方便定位 bot 的真实运行文件系统和用户。")

    async def terminate(self):
        logger.info("[typofix_sentence_check_debug] 插件销毁完成")
