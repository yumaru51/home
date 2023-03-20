'''
from django.db import connection
import psycopg2
from collections import namedtuple

# connection.get_backend_pid()

def dictfetchall(cursor):
    # "Return all rows from a cursor as a dict"
    columns = [col[0] for col in cursor.description]
    return [
        dict(zip(columns, row))
        for row in cursor.fetchall()
    ]

def namedtuplefetchall(cursor):
    # "Return all rows from a cursor as a namedtuple"
    desc = cursor.description
    nt_result = namedtuple('Result', [col[0] for col in desc])
    return [nt_result(*row) for row in cursor.fetchall()]


def setPlt(pk):
    connection = psycopg2.connect("host='YPLANTIAV05' port=5432 dbname=PLANTIA_PROD_DB user=fujitsu password=fujitsu00")

    with connection.cursor() as cursor:
        sql = """ SELECT * FROM m_mgt_cls WHERE mgt_cls='M'"""
        cursor.execute(sql)
        mgt_cls_data = dictfetchall(cursor)

        m_site_skey = mgt_cls_data.m_site_skey

    print(m_site_skey)



test_str1 = '20210421_地震計配置図.pdf'
test_str2 = '2021042a_Preview_Shiyousho.pdf'

len_test_str1 = len(test_str1)

print(len_test_str1)

if len_test_str1 > 8:
    test_str1_first_8_chara = test_str1[0:8]

    if test_str1_first_8_chara.isdecimal() == True:
        if test_str1[8:9] == '_':
            result_str = test_str1[9:len_test_str1]
        else:
            result_str = test_str1[8:len_test_str1]

test_str2_first_8_chara = test_str2[0:8]

print(result_str)

print(test_str1_first_8_chara)
print(test_str2_first_8_chara)

print('isdecimal:', test_str1_first_8_chara.isdecimal())
print('isdecimal:', test_str2_first_8_chara.isdecimal())

print(test_str1.find('_'))
print(test_str2.find('_'))

'''