from astrbot.api.event import filter, AstrMessageEvent
from astrbot.api.star import Context, Star, register
from astrbot.api import logger
import asyncio
from googletrans import Translator

TYPOFIX_CMD = "/opt/typofix_venv/bin/typofix"

@register("typofix_sentence_check", "sakikosunchaser", "自动检测病句并给出理由和修改建议（中文），/病句【内容】", "1.0.0")
class TypofixPlugin(Star):
    def __init__(self, context: Context):
        super().__init__(context)
        self.translator = Translator()

    async def initialize(self):
        logger.info("[typofix_sentence_check] 插件初始化完成")

    @filter.command("病句")
    async def check_typofix(self, event: AstrMessageEvent):
        content = event.message_str.strip()
        if not content:
            yield event.plain_result("请提供需要检测的句子，例如：/病句 这个例子不太合适。")
            return

        try:
            proc = await asyncio.create_subprocess_exec(
                TYPOFIX_CMD, "fix", "--suggest", content,
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

            # 自动翻译为中文
            try:
                translated = self.translator.translate(result, dest='zh-cn').text
                reply = f"【原句】\n{content}\n\n【检测结果（中文）】\n{translated}"
            except Exception as trans_e:
                reply = f"【原句】\n{content}\n\n【检测结果（英文）】\n{result}\n\n自动翻译失败：{trans_e}"

            yield event.plain_result(reply)
        except Exception as e:
            logger.error(f"Typofix 调用异常：{e}")
            yield event.plain_result(
                f"插件内部错误：{e}\n"
                f"请在容器 shell 执行 {TYPOFIX_CMD} fix --suggest \"你好\" 并贴输出，我协助诊断。"
            )

    async def terminate(self):
        logger.info("[typofix_sentence_check] 插件销毁完成")
        
