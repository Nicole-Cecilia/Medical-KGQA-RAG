import os
import sys
import json
from py2neo import Graph

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD

# 连接 Neo4j
graph = Graph(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))

# 读取文献数据
with open("data/literature/papers.json", "r", encoding="utf-8") as f:
    papers = json.load(f)

for paper in papers:
    # ========== 1. 创建 Paper 节点 ==========
    graph.run("""
    MERGE (p:Paper {title: $title})
    SET p.source = $source,
        p.year = $year,
        p.url = $url,
        p.reliability = $reliability
    """, **paper)

    # ========== 2. Disease → Paper ==========
    for disease in paper["related_diseases"]:
        graph.run("""
        MATCH (d:Disease {name: $disease})
        MATCH (p:Paper {title: $title})
        MERGE (d)-[:SUPPORTED_BY]->(p)
        """, disease=disease, title=paper["title"])

        # ========== 3. Disease → Concept ==========
        # 简化版：人为定义疾病概念
        concept_name = "代谢性疾病" if "糖尿病" in disease else "一般疾病"

        graph.run("""
        MERGE (c:Concept {name: $concept})
        MERGE (d:Disease {name: $disease})
        MERGE (d)-[:IS_A]->(c)
        """, concept=concept_name, disease=disease)

    # ========== 4. Symptom 示例（可扩展） ==========
    if "糖尿病" in paper["related_diseases"]:
        symptoms = ["多饮", "多尿", "消瘦"]

        for symptom in symptoms:
            graph.run("""
            MERGE (s:Symptom {name: $symptom})
            MERGE (d:Disease {name: '糖尿病'})
            MERGE (d)-[:HAS_SYMPTOM]->(s)
            MERGE (s)-[:SUPPORTED_BY]->(p)
            """, symptom=symptom)

print("✅ 文献 + 概念 + 症状 全部导入完成")
