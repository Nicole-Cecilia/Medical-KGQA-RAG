import os
import sys
import json
from py2neo import Graph

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD, MEDICAL_JSON_PATH

# 连接 Neo4j
graph = Graph(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))

file_path = MEDICAL_JSON_PATH

count_common = 0
count_recommend = 0
count_detail = 0

with open(file_path, "r", encoding="utf-8") as f:
    for line in f:
        line = line.strip()
        if not line:
            continue

        try:
            item = json.loads(line)
        except json.JSONDecodeError:
            continue

        disease = item.get("name")
        if not disease:
            continue

        # 常用药
        for drug in item.get("common_drug", []):
            graph.run("""
            MATCH (d:Disease {name: $disease})
            MERGE (m:Drug {name: $drug})
            MERGE (d)-[:COMMON_DRUG]->(m)
            """, disease=disease, drug=drug)
            count_common += 1

        # 推荐药
        for drug in item.get("recommand_drug", []):
            graph.run("""
            MATCH (d:Disease {name: $disease})
            MERGE (m:Drug {name: $drug})
            MERGE (d)-[:RECOMMEND_DRUG]->(m)
            """, disease=disease, drug=drug)
            count_recommend += 1

        # 商品药
        for drug in item.get("drug_detail", []):
            graph.run("""
            MATCH (d:Disease {name: $disease})
            MERGE (m:Drug {name: $drug})
            MERGE (d)-[:DRUG_DETAIL]->(m)
            """, disease=disease, drug=drug)
            count_detail += 1

print("✅ 药物关系导入完成")
print(f"COMMON_DRUG: {count_common}")
print(f"RECOMMEND_DRUG: {count_recommend}")
print(f"DRUG_DETAIL: {count_detail}")
