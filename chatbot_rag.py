import time
from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.live import Live
from rich.text import Text
from rich.style import Style
from run_rag_stream import rag_answer_stream

# 初始化 Rich 控制台
console = Console()

class MedicalRAGChatbot:
    def __init__(self):
        # 打印欢迎界面
        welcome_text = """
[bold cyan]🩺 智能医疗知识图谱问答系统[/bold cyan]
[dim]基于 Neo4j + Qwen-1.8B[/dim]

[green]功能特点：[/green]
1. 支持疾病、药物、症状查询
2. 基于知识图谱检索，回答有据可依
3. 严格遵循参考信息，拒绝幻觉

输入 [bold red]exit[/bold red] 或 [bold red]q[/bold red] 退出系统
"""
        console.print(Panel(welcome_text, title="系统启动", border_style="blue"))

    def chat(self, question: str):
        # 使用 Live 上下文管理器来实现流式输出效果
        # 我们需要累积文本，因为 Markdown 渲染需要完整的上下文
        collected_text = ""
        reference_text = ""
        is_parsing_ref = False
        
        # 创建一个占位符，用于实时更新
        with Live(console=console, refresh_per_second=10) as live:
            # 初始状态
            live.update(Panel("正在思考并检索知识图谱...", title="助手", border_style="green"))
            
            for chunk in rag_answer_stream(question):
                # 简单的逻辑分离参考信息
                # 原逻辑中参考信息以 "\n\n---(参考信息)---\n" 开头
                if "---(参考信息)---" in chunk:
                    is_parsing_ref = True
                    # 分割出参考信息部分（如果它和回答粘在一起）
                    parts = chunk.split("---(参考信息)---")
                    if parts[0]: 
                        collected_text += parts[0]
                    # 标记参考信息开始
                    reference_text = "📚 **参考信息来源：**\n"
                    if len(parts) > 1:
                        reference_text += parts[1]
                    continue

                if is_parsing_ref:
                    reference_text += chunk
                else:
                    collected_text += chunk

                # 实时渲染：将 Markdown 文本转换为渲染对象
                # 组合 回答部分 + 分割线 + 参考部分
                display_content = collected_text
                if reference_text:
                    display_content += f"\n\n---\n{reference_text}"
                
                md = Markdown(display_content)
                live.update(Panel(md, title="助手", border_style="green"))

        # 结束后的空行
        console.print()

if __name__ == "__main__":
    bot = MedicalRAGChatbot()

    while True:
        try:
            # 使用 Rich 的 input 样式
            question = console.input("[bold yellow]用户 > [/bold yellow]")
            
            if not question.strip():
                continue
            if question.lower() in ["exit", "quit", "q"]:
                console.print(Panel("[bold cyan]感谢使用，祝您健康！[/bold cyan]", border_style="blue"))
                break
            
            bot.chat(question)
            
        except KeyboardInterrupt:
            console.print("\n[bold red]系统：强制中断[/bold red]")
            break
        except Exception as e:
            console.print(f"\n[bold red]系统错误: {e}[/bold red]")