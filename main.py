from astrbot.api.event import filter, AstrMessageEvent
from astrbot.api.star import Context, Star, register
from astrbot.api import logger
import asyncio
import os
import requests
import time

TYPOFIX_CMD = "/opt/typofix_venv/bin/typofix"
SILICONFLOW_API_KEY = "sk-chkuxaaabozelsyqjyyexsqypkzlehogajptsrxdsrshvovr"
SILICONFLOW_BASE_URL = os.environ.get("SILICONFLOW_BASE_URL", "https://api.siliconflow.cn/v1/chat/completions")

@register("typofix_sentence_check", "sakikosunchaser", "自动检测病句并给出理由和修改建议（输出中文），/病句【内容】", "1.0.0")
class TypofixPlugin(Star):
    def __init__(self, context: Context):
        super().__init__(context)

    async def initialize(self):
        logger.info("[typofix_sentence_check] 插件初始化完成")

    def siliconflow_translate(self, text):
        """用硅基流动 API 翻译英文为中文"""
        headers = {
            "Authorization": f"Bearer {SILICONFLOW_API_KEY}",
            "Content-Type": "application/json"
        }
        data = {
            "model": "deepseek-ai/DeepSeek-V3.2",   # 按你的账号实际模型名修改
            "messages": [
                {"role": "system", "content": "你是专业的中英翻译助手。只输出翻译结果，保持书面中文，忠实还原逻辑结构，不要省略、不要解释，不要添加任何附言。"},
                {"role": "user", "content": f"请把如下英文内容完整、精准地翻译为书面中文，只输出翻译结果，无需解释说明：\n{text}"}
            ],
            "max_tokens": 2048,
            "temperature": 0.3
        }
        for attempt in range(2):  # 尝试两次，防止timeout
            try:
                t0 = time.monotonic()
                resp = requests.post(SILICONFLOW_BASE_URL, json=data, headers=headers, timeout=30)
                t1 = time.monotonic()
                logger.info(f"[siliconflow_translate] API耗时: {t1 - t0:.2f}s，响应内容: {resp.text}")
                resp.raise_for_status()
                result = resp.json()
                # 打印响应便于debug
                logger.info(f"[siliconflow_translate] API返回结构：{result}")
                # 解析中文翻译结果
                return result['choices'][0]['message']['content'].strip()
            except Exception as e:
                logger.error(f"[siliconflow_translate] 翻译失败（第{attempt+1}次）：{e}")
                time.sleep(1)  # 间隔一秒重试
        return f"[翻译失败] {e}, 响应内容: {resp.text if 'resp' in locals() else '无响应'}"

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

            # 将英文检测结果整体自动翻译为中文
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
