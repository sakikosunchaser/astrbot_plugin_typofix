from astrbot.api.event import filter, AstrMessageEvent
from astrbot.api.star import Context, Star, register
from astrbot.api import logger
import asyncio
import os
import requests

TYPOFIX_CMD = "/opt/typofix_venv/bin/typofix"
SILICONFLOW_API_KEY = "sk-chkuxaaabozelsyqjyyexsqypkzlehogajptsrxdsrshvovr"
SILICONFLOW_BASE_URL = os.environ.get(
    "SILICONFLOW_BASE_URL", "https://api.siliconflow.cn/v1/chat/completions"
)
# 如果只需 /v1/ ，换 "https://api.siliconflow.cn/v1/"

@register("typofix_sentence_check", "sakikosunchaser", "自动检测病句并给出理由和修改建议（中文），/病句【内容】", "1.0.0")
class TypofixPlugin(Star):
    def __init__(self, context: Context):
        super().__init__(context)

    async def initialize(self):
        logger.info("[typofix_sentence_check] 插件初始化完成")

    def siliconflow_translate(self, text):
        headers = {
            "Authorization": f"Bearer {SILICONFLOW_API_KEY}",
            "Content-Type": "application/json"
        }
        data = {
            "model": "deepseek-ai/DeepSeek-V3.2",   # 如有更强模型可自行更改
            "messages": [
                {"role": "system", "content": "你是专业的中英翻译助手。请忠实准确地将用户的英文文本翻译为书面中文，输出只有翻译结果。"},
                {"role": "user", "content": f"请把如下英文内容完整翻译为书面中文：\n{text}"}
            ],
            "max_tokens": 1024,
            "temperature": 0.4
        }
        try:
            resp = requests.post(SILICONFLOW_BASE_URL, json=data, headers=headers, timeout=60)
            resp.raise_for_status()
            result = resp.json()
            # 按硅基流动API标准取文本
            return result['choices'][0]['message']['content'].strip()
        except Exception as e:
            return f"[翻译失败] {e}"

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
            # 英文转中文
            translated = await asyncio.get_event_loop().run_in_executor(
                None, self.siliconflow_translate, result
            )
            reply = f"【原句】\n{content}\n\n【检测结果（中文）】\n{translated}"
            yield event.plain_result(reply)
        except Exception as e:
            logger.error(f"Typofix 调用异常：{e}")
            yield event.plain_result(
                f"插件内部错误：{e}\n"
                f"请在容器 shell 执行 {TYPOFIX_CMD} fix --suggest \"你好\" 并贴输出，我协助诊断。"
            )

    async def terminate(self):
        logger.info("[typofix_sentence_check] 插件销毁完成")
