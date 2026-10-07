from graph_retriever import execute_cypher_and_map
from generator import generate_answer_stream
from question_classifier import QuestionClassifier
from question_parser import QuestionPaser

classifier = QuestionClassifier()
parser = QuestionPaser()

CHAT_INTENTS = [
    "你好", "您好", "你是谁", "你叫什么", "你能做什么",
    "你好呀", "哈喽", "hello", "hi"
]

def build_knowledge_text(triples):
    """
    将图谱查到的三元组列表转换为自然语言文本
    """
    if not triples:
        return None

    lines = []
    # 使用集合去重
    seen = set()
    
    for t in triples:
        sub = t.get('subject')
        rel = t.get('relation')
        obj = t.get('object')
        
        # 构造易读的字符串，例如 "感冒 的 常用药物 是 阿司匹林"
        # 也可以根据 relation 做一些特殊文本处理，但通用格式已足够 LLM 理解
        line = f"{sub} 的 {rel} 是：{obj}"
        
        if line not in seen:
            lines.append(line)
            seen.add(line)

    return "\n".join(lines)


# ... (之前的 import 和 helper 函数保持不变)

def rag_answer_stream(question: str):
    # ========== 0️⃣ 处理寒暄类对话 ==========
    for greet in CHAT_INTENTS:
        if greet == question.strip():
            yield "你好！我是智能医疗助手，可以帮你解答健康相关的问题。"
            return

    # ========== 1️⃣ 分类 ==========
    classify_result = classifier.classify(question)
    
    if not classify_result:
        yield "抱歉，我没有识别到医疗相关的实体。请尝试问具体的疾病、症状或药物，例如“感冒吃什么药？”"
        return

    # ========== 2️⃣ 查询知识图谱 ==========
    sqls = parser.parser_main(classify_result)
    
    triples = []
    if sqls:
        all_sqls = [s for x in sqls for s in x["sql"]]
        triples = execute_cypher_and_map(all_sqls)

    knowledge_text = build_knowledge_text(triples)

    # ========== 3️⃣ 构造 Prompt (核心修改部分) ==========
    
    # 如果没查到知识
    if not knowledge_text:
        yield "抱歉，知识库中暂时没有关于该问题的详细记录。"
        return

    # --- 修改后的 System Prompt：强调严格依赖上下文 ---
    system_prompt = """你是一个基于知识库的医疗问答助手。请严格遵循以下规则回答问题：
1. **绝对忠实**：你的回答必须完全基于提供的【参考信息】。严禁使用你自带的外部知识或编造内容。
2. **数据精确**：如果【参考信息】中包含具体的概率数值（如90%）、药物名称、治疗周期等，必须在回答中准确提及，不得忽略。
3. **不知道就说不知道**：如果【参考信息】无法回答用户的问题，请直接说明“参考信息中未提及”，不要试图编造通用建议。
4. **简洁直接**：回答要简练，不要输出长篇大论的废话。"""

    # --- 修改后的 User Prompt：结构优化 ---
    user_prompt = f"""
【参考信息】
{knowledge_text}

【用户问题】
{question}

请根据【参考信息】直接回答【用户问题】。如果参考信息中提到了具体的数值（如治愈率），请务必包含在回答中。
"""

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt}
    ]

    # ========== 4️⃣ 输出 LLM 回答 ==========
    has_answer = False
    for chunk in generate_answer_stream(messages):
        has_answer = True
        yield chunk

    # ========== 5️⃣ (可选) 展示知识来源 ==========
    if knowledge_text:
        yield "\n\n---(参考信息)---\n"
        yield knowledge_text