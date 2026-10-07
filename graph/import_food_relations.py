import os
import sys
import json
from py2neo import Graph

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD, MEDICAL_JSON_PATH

# 连接 Neo4j
graph = Graph(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))

file_path = MEDICAL_JSON_PATH

count_do = 0
count_not = 0
count_rec = 0

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

        # 宜吃
        for food in item.get("do_eat", []):
            graph.run("""
            MATCH (d:Disease {name: $disease})
            MERGE (f:Food {name: $food})
            MERGE (d)-[:DO_EAT]->(f)
            """, disease=disease, food=food)
            count_do += 1

        # 忌吃
        for food in item.get("not_eat", []):
            graph.run("""
            MATCH (d:Disease {name: $disease})
            MERGE (f:Food {name: $food})
            MERGE (d)-[:NOT_EAT]->(f)
            """, disease=disease, food=food)
            count_not += 1

        # 推荐食谱
        for food in item.get("recommand_eat", []):
            graph.run("""
            MATCH (d:Disease {name: $disease})
            MERGE (f:Food {name: $food})
            MERGE (d)-[:RECOMMEND_EAT]->(f)
            """, disease=disease, food=food)
            count_rec += 1

print("✅ 饮食关系导入完成")
print(f"DO_EAT: {count_do}")
print(f"NOT_EAT: {count_not}")
print(f"RECOMMEND_EAT: {count_rec}")
