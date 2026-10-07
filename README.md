# 医疗知识图谱问答系统（Medical KGQA + RAG）

基于 Neo4j 知识图谱与本地大语言模型的医疗领域问答系统。系统从结构化医疗数据中构建疾病、药物、症状、检查、食物等实体及其关系图谱，用户提问时先通过规则与实体识别定位问题意图，再用 Cypher 从图数据库中检索出证据三元组，最后交由本地 Qwen 大模型基于证据生成自然语言回答，避免大模型幻觉。

## 系统架构

```
用户问题
   │
   ▼
question_classifier.py  ──  AC 自动机实体识别 + 关键词规则意图分类（16 类问题）
   │
   ▼
question_parser.py     ──  按意图模板生成 Cypher 查询语句
   │
   ▼
graph_retriever.py     ──  连 Neo4j 执行 Cypher，拿回 (主语, 关系, 宾语) 三元组
   │
   ▼
run_rag_stream.py      ──  三元组转成参考文本，拼进 prompt
   │
   ▼
generator.py           ──  本地 Qwen1.5-1.8B 流式生成回答，强制"只依据参考信息"
   │
   ▼
chatbot_rag.py         ──  rich 终端流式 Markdown 渲染
```

## 技术栈

- **图数据库**：Neo4j（Bolt 协议，py2neo 驱动）
- **实体识别**：pyahocorasick（AC 自动机，在百万级词条里毫秒级匹配）
- **意图分类**：规则模板（关键词词典驱动，可解释、无需训练）
- **大模型**：Qwen1.5-1.8B-Chat（本地部署，FP16 流式生成）
- **终端 UI**：rich 实时渲染 Markdown
- **配置管理**：python-dotenv，敏感信息不入库

## 支持的问题类型

| 意图 | 示例 |
|------|------|
| 疾病简介 | 感冒是什么？ |
| 疾病病因 | 感冒是什么原因引起的？ |
| 疾病预防 | 怎么预防感冒？ |
| 疾病症状 | 感冒有哪些症状？ |
| 疾病并发症 | 感冒会引发什么病？ |
| 疾病用药 | 感冒吃什么药？ |
| 疾病检查 | 感冒需要做什么检查？ |
| 疾病饮食 | 感冒能吃什么 / 不能吃什么？ |
| 疾病治疗周期 | 感冒多久能好？ |
| 疾病治愈概率 | 感冒能治好吗？ |
| 疾病易感人群 | 什么人容易感冒？ |
| 症状反查疾病 | 发烧可能是什么病？ |
| 药物反查疾病 | 布洛芬治什么？ |
| 检查反查疾病 | 血常规能查出什么？ |

## 项目结构

```
├── chatbot_rag.py          # 终端交互入口（rich 流式 UI）
├── run_rag_stream.py        # RAG 流程编排：分类→检索→生成
├── question_classifier.py   # 实体识别 + 意图分类
├── question_parser.py       # 意图→Cypher 模板
├── graph_retriever.py       # Neo4j 检索，统一三元组输出
├── generator.py             # Qwen 本地模型加载与流式生成
├── config.py                # 配置读取（从 .env）
├── .env.example             # 配置模板
├── requirements.txt
├── data/
│   └── medical.json         # 原始结构化数据（47MB，不入库，见下方说明）
├── dict/                    # 实体词典（AC 自动机用）
│   ├── disease.txt
│   ├── symptom.txt
│   ├── drug.txt
│   ├── food.txt
│   ├── check.txt
│   ├── department.txt
│   ├── producer.txt
│   └── deny.txt
└── graph/
    ├── build_graph.py       # 一次性建图：节点 + 关系
    └── import_*.py          # 分批导入各类关系
```

## 快速开始

### 1. 环境要求

- Python 3.9 ~ 3.11（3.12 以上部分包暂无预编译 wheel）
- Neo4j 4.x / 5.x（本地启动，默认 bolt://localhost:7687）
- 约 8GB 显存（GPU 推理；CPU 也能跑，慢一些）
- Qwen1.5-1.8B-Chat 模型权重（从 HuggingFace 或 ModelScope 下载）

### 2. 安装依赖

```bash
pip install -r requirements.txt
# torch 请按自己的 CUDA 版本安装：https://pytorch.org/get-started/locally/
```

### 3. 配置

```bash
cp .env.example .env
# 编辑 .env，填入 Neo4j 密码和本地模型路径
```

### 4. 构建知识图谱

先启动 Neo4j，然后：

```bash
cd graph
python build_graph.py
```

这会读取 `data/medical.json`，在 Neo4j 中创建 7 类节点和 10 种关系。

### 5. 启动问答

```bash
python chatbot_rag.py
```

## 数据说明

`data/medical.json` 为从公开医疗站点爬取的结构化疾病数据（约 6000 种疾病，含症状、病因、用药、检查、饮食等字段），文件较大（47MB）未纳入 git。建图所需的实体词典已放在 `dict/` 目录下。

## 设计要点

- **为什么用规则而不是训练分类器**：医疗实体边界清晰，AC 自动机 + 关键词词典即可覆盖 90% 以上常见问法，零训练成本且结果可解释，方便后续加新词。
- **为什么要 RAG**：纯大模型回答医疗问题容易产生幻觉（编造药物、剂量），先用图谱检索出"证据"，再让模型基于证据组织语言，回答可追溯到具体三元组。
- **为什么统一三元组 schema**：检索层把 Cypher 结果统一映射成 `(subject, relation, object)`，上层 LLM 不用关心查询细节，换数据库或换查询语句都不影响生成层。

## 致谢

本项目基于 [liuhuanyong/QASystemOnMedicalKG](https://github.com/liuhuanyong/QASystemOnMedicalKG) 原始规则问答系统扩展，在此基础上增加了本地 LLM 生成层（RAG）、配置抽离与工程化整理。
