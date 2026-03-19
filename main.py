from astrbot.api.event import filter, AstrMessageEvent, MessageEventResult
from astrbot.api.star import Context, Star, register
from astrbot.api import logger
import asyncio
import os

# 自动当前用户的 pipx typofix venv路径
TYPOFIX_CMD = os.path.expanduser("~/.local/pipx/venvs/typofix/bin/typofix")

@register("typofix_sentence_check", "sakikosunchaser", "自动检测病句并给出理由和修改建议，/病句【内容】", "1.0.0")
class TypofixPlugin(Star):
    def __init__(self, context: Context):
        super().__init__(context)

    async def initialize(self):
        logger.info("[typofix_sentence_check] 插件初始化完成")

    @filter.command("病句")
    async def check_typofix(self, event: AstrMessageEvent):
        content = event.message_str.strip()

        # 路径检测和用户身份调试
        yield event.plain_result(f"getuid: {os.getuid()}, HOME: {os.environ.get('HOME')}, typofix路径: {TYPOFIX_CMD}, exists: {os.path.exists(TYPOFIX_CMD)}")

        if not os.path.exists(TYPOFIX_CMD):
            yield event.plain_result(f"无法找到 typofix命令：{TYPOFIX_CMD}，请用bot的运行账户安装 pipx typofix，或联系运维。")
            return

        if not content:
            yield event.plain_result("请提供需要检测的句子，例如：/病句 这个例子不太合适。")
            return

        try:
            proc = await asyncio.create_subprocess_exec(
                TYPOFIX_CMD, "--pipe",
                stdin=asyncio.subprocess.PIPE,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await proc.communicate(content.encode())
            if proc.returncode != 0:
                err = stderr.decode().strip()
                yield event.plain_result(f"typofix 出错：{err}")
                return

            result = stdout.decode().strip()
            if not result:
                yield event.plain_result("未检测到任何语病。")
                return

            reply = f"【原句】\n{content}\n\n【检测结果】\n{result}"
            yield event.plain_result(reply)
        except Exception as e:
            logger.error(f"Typofix 调用异常：{e}")
            yield event.plain_result(f"插件内部错误：{e}")

    async def terminate(self):
        logger.info("[typofix_sentence_check] 插件销毁完成")
