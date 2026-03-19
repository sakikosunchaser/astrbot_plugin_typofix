from astrbot.api.event import filter, AstrMessageEvent
from astrbot.api.star import Context, Star, register
from astrbot.api import logger
import asyncio
import shutil
import os

@register("typofix_sentence_check", "sakikosunchaser", "自动检测病句并给出理由和修改建议，/病句【内容】", "1.0.0")
class TypofixPlugin(Star):
    def __init__(self, context: Context):
        super().__init__(context)

    async def initialize(self):
        logger.info("[typofix_sentence_check] 插件初始化完成")

    @filter.command("病句")
    async def check_typofix(self, event: AstrMessageEvent):
        content = event.message_str.strip()

        typofix_path = shutil.which("typofix") or "/root/.local/bin/typofix"
        exists = os.path.exists(typofix_path)
        yield event.plain_result(f"查找typofix路径: {typofix_path}，exists: {exists}, PATH: {os.environ.get('PATH','')}")

        if not exists:
            yield event.plain_result("无法找到 typofix 命令，如 shell能用 typofix fix --suggest \"文本\"，插件才可用。")
            return

        if not content:
            yield event.plain_result("请提供需要检测的句子，例如：/病句 这个例子不太合适。")
            return

        try:
            proc = await asyncio.create_subprocess_exec(
                typofix_path, "fix", "--suggest", content,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await proc.communicate()
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
            yield event.plain_result(
                f"插件内部错误：{e}\n"
                f"请贴上面的调试信息和shell命令行结果，我帮你定位。"
            )

    async def terminate(self):
        logger.info("[typofix_sentence_check] 插件销毁完成")
