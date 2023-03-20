import datetime
import collections
from django.utils.timezone import make_aware


# Date情報をいろいろな形に変換
# date_type_date：date型 or datetime型
# str_type_date_jp：「年月日」表記
# str_type_date_jp_with_t：時刻付き「年月日」表記
# str_type_date_slash：「/」表記
# str_type_date_slash_with_t：時刻付き「/」表記
# str_type_date_hyphen：「-」表記
# str_type_date_hyphen_with_t：時刻付き「-」表記
# str_type_date_erp：ERP用表記

def date_to_many_type(target_date):
    if target_date is not "" and target_date is not None:
        if type(target_date) is datetime.date:
            date_type_date = target_date
            str_type_date_jp = target_date.strftime("%Y") + "年" + target_date.strftime("%m") + "月" + target_date.strftime("%d") + "日"
            str_type_date_jp_with_t = str_type_date_jp
            str_type_date_slash = target_date.strftime("%Y") + "/" + target_date.strftime("%m") + "/" + target_date.strftime("%d")
            str_type_date_slash_with_t = str_type_date_slash
            str_type_date_hyphen = date_type_date.strftime("%Y") + "-" + date_type_date.strftime("%m") + "-" + date_type_date.strftime("%d")
            str_type_date_hyphen_with_t = str_type_date_hyphen
            str_type_date_erp = target_date.strftime("%Y%m%d")
        elif type(target_date) is datetime.datetime:
            if target_date.tzinfo is None:
                date_type_date = make_aware(target_date)
            else:
                date_type_date = target_date
            str_type_date_jp = date_type_date.strftime("%Y") + "年" + date_type_date.strftime("%m") + "月" + date_type_date.strftime("%d") + "日"
            str_type_date_jp_with_t = str_type_date_jp + " " + date_type_date.strftime("%H") + ":" + date_type_date.strftime("%M") + ":" + date_type_date.strftime("%S")
            str_type_date_slash = date_type_date.strftime("%Y") + "/" + date_type_date.strftime("%m") + "/" + date_type_date.strftime("%d")
            str_type_date_hyphen = date_type_date.strftime("%Y") + "-" + date_type_date.strftime("%m") + "-" + date_type_date.strftime("%d")
            str_type_date_slash_with_t = str_type_date_slash + " " + date_type_date.strftime("%H") + ":" + date_type_date.strftime("%M") + ":" + date_type_date.strftime("%S")
            str_type_date_hyphen_with_t = str_type_date_hyphen + " " + date_type_date.strftime("%H") + ":" + date_type_date.strftime("%M") + ":" + date_type_date.strftime("%S")
            str_type_date_erp = target_date.strftime("%Y%m%d")
        elif type(target_date) is str:
            if ':' in target_date:
                date_type_date = datetime.datetime.strptime(target_date, "%Y年%m月%d日 %H:%M:%S")
                if date_type_date.tzinfo is None:
                    date_type_date = make_aware(date_type_date)
            else:
                # date_type_date = datetime.datetime.strptime(target_date, "%Y年%m月%d日")
                date_type_date = datetime.datetime.strptime(target_date, "%Y年%m月%d日")
                if date_type_date.tzinfo is None:
                    date_type_date = make_aware(date_type_date)
            str_type_date_jp = date_type_date.strftime("%Y") + "年" + date_type_date.strftime("%m") + "月" + date_type_date.strftime("%d") + "日"
            str_type_date_slash = date_type_date.strftime("%Y") + "/" + date_type_date.strftime("%m") + "/" + date_type_date.strftime("%d")
            str_type_date_hyphen = date_type_date.strftime("%Y") + "-" + date_type_date.strftime("%m") + "-" + date_type_date.strftime("%d")
            if ':' in target_date:
                str_type_date_jp_with_t = str_type_date_jp + " " + date_type_date.strftime("%H") + ":" + date_type_date.strftime("%M") + ":" + date_type_date.strftime("%S")
                str_type_date_slash_with_t = str_type_date_slash + " " + date_type_date.strftime("%H") + ":" + date_type_date.strftime("%M") + ":" + date_type_date.strftime("%S")
                str_type_date_hyphen_with_t = str_type_date_hyphen + " " + date_type_date.strftime("%H") + ":" + date_type_date.strftime("%M") + ":" + date_type_date.strftime("%S")
            else:
                str_type_date_jp_with_t = str_type_date_jp
                str_type_date_slash_with_t = str_type_date_slash
                str_type_date_hyphen_with_t = str_type_date_hyphen
            str_type_date_erp = date_type_date.strftime("%Y%m%d")
    else:
        date_type_date = ""
        str_type_date_jp = ""
        str_type_date_jp_with_t = ""
        str_type_date_slash = ""
        str_type_date_slash_with_t = ""
        str_type_date_hyphen = ""
        str_type_date_hyphen_with_t = ""
        str_type_date_erp = ""

    date_str = collections.namedtuple('date_str', 'date_type_date, str_type_date_jp, str_type_date_jp_with_t, str_type_date_slash, str_type_date_slash_with_t, str_type_date_hyphen, str_type_date_hyphen_with_t, str_type_date_erp')

    return date_str(date_type_date=date_type_date, str_type_date_jp=str_type_date_jp, str_type_date_jp_with_t=str_type_date_jp_with_t, str_type_date_slash=str_type_date_slash, str_type_date_slash_with_t=str_type_date_slash_with_t, str_type_date_hyphen=str_type_date_hyphen, str_type_date_hyphen_with_t=str_type_date_hyphen_with_t, str_type_date_erp=str_type_date_erp)

