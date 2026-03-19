from astrbot.api.event import filter, AstrMessageEvent, MessageEventResult
from astrbot.api.star import Context, Star, register
from astrbot.api import logger
import asyncio
import os
import sys
import shutil

@register("typofix_env_debug", "sakikosunchaser", "病句检测+环境定位调试，/病句【内容】", "1.0.0")
class TypofixPlugin(Star):
    def __init__(self, context: Context):
        super().__init__(context)

    async def initialize(self):
        logger.info("[typofix_env_debug] 插件初始化完成")

    @filter.command("病句")
    async def check_typofix(self, event: AstrMessageEvent):
        """
        病句检测 + 环境调试定位。
        用法：/病句 一句话
        """
        content = event.message_str.strip()

        # 定位实际环境
        typofix_path = shutil.which("typofix")  # PATH方式查找
        typofix_pip = os.path.join(os.path.dirname(sys.executable), "Scripts", "typofix.exe")  # pip方式
        typofix_local = os.path.join(os.path.dirname(__file__), "typofix.exe")  # 插件目录下

        debug_info = (
            f"【环境调试】\n"
            f"sys.executable: {sys.executable}\n"
            f"sys.version: {sys.version}\n"
            f"当前工作目录: {os.getcwd()}\n"
            f"PATH变量: {os.environ.get('PATH','')}\n"
            f"typofix 在环境PATH查找: {typofix_path}，存在: {os.path.exists(typofix_path) if typofix_path else False}\n"
            f"typofix pip路径: {typofix_pip}，存在: {os.path.exists(typofix_pip)}\n"
            f"typofix 插件目录路径: {typofix_local}，存在: {os.path.exists(typofix_local)}\n"
        )

        # 环境调试先输出
        yield event.plain_result(debug_info)

        # 检测可执行路径，优先PATH，其次pip目录，其次本地目录
        exec_path = None
        if typofix_path and os.path.exists(typofix_path):
            exec_path = typofix_path
        elif os.path.exists(typofix_pip):
            exec_path = typofix_pip
        elif os.path.exists(typofix_local):
            exec_path = typofix_local

        if not exec_path:
            yield event.plain_result("无法找到 typofix 可执行文件，请根据上面的环境信息检查、安装或拷贝到适当目录。\n")
            return

        # 如果用户没输入内容，直接返回
        if not content:
            yield event.plain_result("请提供需要检测的句子，例如：/病句 这个例子不太合适。")
            return

        # 调用 typofix 检测病句
        try:
            proc = await asyncio.create_subprocess_exec(
                exec_path, "--pipe",
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
        logger.info("[typofix_env_debug] 插件销毁完成")
