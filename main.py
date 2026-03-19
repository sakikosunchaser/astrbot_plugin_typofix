from astrbot.api.event import filter, AstrMessageEvent, MessageEventResult
from astrbot.api.star import Context, Star, register
from astrbot.api import logger
import asyncio
import os

TYPOFIX_CMD = r"D:/python312/Scripts/typofix.exe"

@register("typofix_sentence_check", "sakikosunchaser", "自动检测病句并给出理由和修改建议，/病句【内容】", "1.0.0")
class TypofixPlugin(Star):
    def __init__(self, context: Context):
        super().__init__(context)

    async def initialize(self):
        logger.info("[typofix_sentence_check] 插件初始化完成")

    @filter.command("病句")
    async def check_typofix(self, event: AstrMessageEvent):
        """
        检查一句话是否为病句，并给出理由与修改建议。（用typofix CLI）
        用法：/病句 一句话
        """
        content = event.message_str.strip()
        if not content:
            yield event.plain_result("请提供需要检测的句子，例如：/病句 这个例子不太合适。")
            return

        # 路径检测
        if not os.path.exists(TYPOFIX_CMD):
            yield event.plain_result(
                f"无法找到 typofix.exe，请确认路径是否正确：{TYPOFIX_CMD}\n"
                "请用 dir 命令检查文件是否存在，并确认bot运行环���对该文件有访问权限。"
            )
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
            logger.error(f"Typofix 插件异常：{e}")
            yield event.plain_result(f"插件内部错误：{e}")

    async def terminate(self):
        logger.info("[typofix_sentence_check] 插件销毁完成")
