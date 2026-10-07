import os
import sys
import json
from py2neo import Graph

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD, MEDICAL_JSON_PATH

# 连接 Neo4j
graph = Graph(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))

file_path = MEDICAL_JSON_PATH

count = 0

with open(file_path, "r", encoding="utf-8") as f:
    for line in f:
        line = line.strip()
        if not line:
            continue

        try:
            item = json.loads(line)
        except json.JSONDecodeError:
            continue

        disease_name = item.get("name")
        symptoms = item.get("symptom", [])

        if not disease_name or not symptoms:
            continue

        for symptom in symptoms:
            graph.run("""
            MATCH (d:Disease {name: $disease})
            MERGE (s:Symptom {name: $symptom})
            MERGE (d)-[:HAS_SYMPTOM]->(s)
            """, disease=disease_name, symptom=symptom)

            count += 1

print(f"✅ 已成功创建 {count} 条 HAS_SYMPTOM 关系")
