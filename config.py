"""
集中配置：所有敏感信息和路径都从环境变量读取，
不要把密码写进代码，也不要把 .env 提交到 git。
"""
import os
from dotenv import load_dotenv

load_dotenv()

# ---- Neo4j 连接 ----
NEO4J_URI = os.getenv("NEO4J_URI", "bolt://localhost:7687")
NEO4J_USER = os.getenv("NEO4J_USER", "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "")

# ---- 本地大模型路径 ----
# 可以填本地模型目录，例如 D:/models/Qwen1.5-1.8B-Chat
# 也可以填 HuggingFace 模型名，例如 Qwen/Qwen1.5-1.8B-Chat
MODEL_PATH = os.getenv("MODEL_PATH", "Qwen/Qwen1.5-1.8B-Chat")

# ---- 数据路径 ----
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MEDICAL_JSON_PATH = os.path.join(BASE_DIR, "data", "medical.json")
