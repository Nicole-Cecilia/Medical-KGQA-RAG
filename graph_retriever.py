"""
知识图谱检索模块：连接 Neo4j，执行 Cypher 查询，
统一把结果映射成三元组 schema：{subject, relation, object}。
"""
from py2neo import Graph
from config import NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD

graph = Graph(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))


def execute_cypher_and_map(sqls):
    """
    执行一组 Cypher 语句，并把每一行结果映射为：
        {"subject": xxx, "relation": xxx, "object": xxx}
    空值和重复结果会被过滤掉。
    """
    results = []

    for sql in sqls:
        try:
            data = graph.run(sql).data()
            for row in data:
                mapped = {
                    "subject": row.get("subject", ""),
                    "relation": row.get("relation", ""),
                    "object": row.get("object", ""),
                }
                if mapped["subject"] and mapped["object"]:
                    results.append(mapped)
        except Exception as e:
            print(f"Error executing Cypher: {sql}\n  Error: {e}")

    return results
