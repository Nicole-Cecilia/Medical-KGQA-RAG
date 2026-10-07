#!/usr/bin/env python3
# coding: utf-8

class QuestionPaser:

    '''构建实体节点'''
    def build_entitydict(self, args):
        entity_dict = {}
        for arg, types in args.items():
            for type in types:
                if type not in entity_dict:
                    entity_dict[type] = [arg]
                else:
                    entity_dict[type].append(arg)
        return entity_dict

    '''解析主函数'''
    def parser_main(self, res_classify):
        args = res_classify['args']
        entity_dict = self.build_entitydict(args)
        question_types = res_classify['question_types']
        sqls = []
        for question_type in question_types:
            sql_ = {}
            sql_['question_type'] = question_type
            sql = []
            
            # 简化逻辑：直接根据类型获取实体
            entities = []
            if 'disease' in question_type.split('_')[0]:
                entities = entity_dict.get('disease', [])
            elif 'symptom' in question_type:
                entities = entity_dict.get('symptom', [])
            elif 'drug' in question_type:
                entities = entity_dict.get('drug', [])
            elif 'food' in question_type:
                entities = entity_dict.get('food', [])
            elif 'check' in question_type:
                entities = entity_dict.get('check', [])
            
            # 调用统一转换函数
            if entities:
                sql = self.sql_transfer(question_type, entities)

            if sql:
                sql_['sql'] = sql
                sqls.append(sql_)

        return sqls

    '''
    针对不同的问题，分开进行处理
    核心修改：统一使用 AS subject, AS relation, AS object，方便后续处理
    '''
    def sql_transfer(self, question_type, entities):
        if not entities:
            return []

        sql = []
        # 查询疾病的原因
        if question_type == 'disease_cause':
            sql = ["MATCH (m:Disease) where m.name = '{0}' return m.name as subject, '病因' as relation, m.cause as object".format(i) for i in entities]
        elif question_type == 'disease_prevent':
            sql = ["MATCH (m:Disease) where m.name = '{0}' return m.name as subject, '预防措施' as relation, m.prevent as object".format(i) for i in entities]
        elif question_type == 'disease_lasttime':
            sql = ["MATCH (m:Disease) where m.name = '{0}' return m.name as subject, '治疗周期' as relation, m.cure_lasttime as object".format(i) for i in entities]
        elif question_type == 'disease_cureprob':
            sql = ["MATCH (m:Disease) where m.name = '{0}' return m.name as subject, '治愈概率' as relation, m.cured_prob as object".format(i) for i in entities]
        elif question_type == 'disease_cureway':
            sql = ["MATCH (m:Disease) where m.name = '{0}' return m.name as subject, '治疗方式' as relation, m.cure_way as object".format(i) for i in entities]
        elif question_type == 'disease_easyget':
            sql = ["MATCH (m:Disease) where m.name = '{0}' return m.name as subject, '易感人群' as relation, m.easy_get as object".format(i) for i in entities]
        elif question_type == 'disease_desc':
            sql = ["MATCH (m:Disease) where m.name = '{0}' return m.name as subject, '简介' as relation, m.desc as object".format(i) for i in entities]
        
        # 关系查询 (统一别名)
        elif question_type == 'disease_symptom':
            sql = ["MATCH (m:Disease)-[r:has_symptom]->(n:Symptom) where m.name = '{0}' return m.name as subject, r.name as relation, n.name as object".format(i) for i in entities]
        elif question_type == 'symptom_disease':
            sql = ["MATCH (m:Disease)-[r:has_symptom]->(n:Symptom) where n.name = '{0}' return m.name as subject, r.name as relation, n.name as object".format(i) for i in entities]
        elif question_type == 'disease_acompany':
            sql1 = ["MATCH (m:Disease)-[r:acompany_with]->(n:Disease) where m.name = '{0}' return m.name as subject, r.name as relation, n.name as object".format(i) for i in entities]
            sql2 = ["MATCH (m:Disease)-[r:acompany_with]->(n:Disease) where n.name = '{0}' return m.name as subject, r.name as relation, n.name as object".format(i) for i in entities]
            sql = sql1 + sql2
        elif question_type == 'disease_not_food':
            sql = ["MATCH (m:Disease)-[r:no_eat]->(n:Food) where m.name = '{0}' return m.name as subject, r.name as relation, n.name as object".format(i) for i in entities]
        elif question_type == 'disease_do_food':
            sql1 = ["MATCH (m:Disease)-[r:do_eat]->(n:Food) where m.name = '{0}' return m.name as subject, r.name as relation, n.name as object".format(i) for i in entities]
            sql2 = ["MATCH (m:Disease)-[r:recommand_eat]->(n:Food) where m.name = '{0}' return m.name as subject, r.name as relation, n.name as object".format(i) for i in entities]
            sql = sql1 + sql2
        elif question_type == 'food_not_disease':
            sql = ["MATCH (m:Disease)-[r:no_eat]->(n:Food) where n.name = '{0}' return m.name as subject, r.name as relation, n.name as object".format(i) for i in entities]
        elif question_type == 'food_do_disease':
            sql1 = ["MATCH (m:Disease)-[r:do_eat]->(n:Food) where n.name = '{0}' return m.name as subject, r.name as relation, n.name as object".format(i) for i in entities]
            sql2 = ["MATCH (m:Disease)-[r:recommand_eat]->(n:Food) where n.name = '{0}' return m.name as subject, r.name as relation, n.name as object".format(i) for i in entities]
            sql = sql1 + sql2
        elif question_type == 'disease_drug':
            sql1 = ["MATCH (m:Disease)-[r:common_drug]->(n:Drug) where m.name = '{0}' return m.name as subject, r.name as relation, n.name as object".format(i) for i in entities]
            sql2 = ["MATCH (m:Disease)-[r:recommand_drug]->(n:Drug) where m.name = '{0}' return m.name as subject, r.name as relation, n.name as object".format(i) for i in entities]
            sql = sql1 + sql2
        elif question_type == 'drug_disease':
            sql1 = ["MATCH (m:Disease)-[r:common_drug]->(n:Drug) where n.name = '{0}' return m.name as subject, r.name as relation, n.name as object".format(i) for i in entities]
            sql2 = ["MATCH (m:Disease)-[r:recommand_drug]->(n:Drug) where n.name = '{0}' return m.name as subject, r.name as relation, n.name as object".format(i) for i in entities]
            sql = sql1 + sql2
        elif question_type == 'disease_check':
            sql = ["MATCH (m:Disease)-[r:need_check]->(n:Check) where m.name = '{0}' return m.name as subject, r.name as relation, n.name as object".format(i) for i in entities]
        elif question_type == 'check_disease':
            sql = ["MATCH (m:Disease)-[r:need_check]->(n:Check) where n.name = '{0}' return m.name as subject, r.name as relation, n.name as object".format(i) for i in entities]

        return sql

if __name__ == '__main__':
    handler = QuestionPaser()