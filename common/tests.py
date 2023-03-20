'''
from django.test import TestCase
import psycopg2
from common.test import dictfetchall, namedtuplefetchall

connection = psycopg2.connect("host='YPLANTIAV05' port=5432 dbname=PLANTIA_PROD_DB user=fujitsu password=fujitsu00")

with connection.cursor() as cursor:
    sql = """ SELECT * FROM m_mgt_cls WHERE mgt_cls='m' """
    cursor.execute(sql)
    # mgt_cls_data = cursor.fetchall()
    mgt_cls_data = namedtuplefetchall(cursor)

for data in mgt_cls_data:
    print(data)

mgt_cls_nm_1 = mgt_cls_data[0].mgt_cls_nm_1

print(mgt_cls_nm_1)

'''
