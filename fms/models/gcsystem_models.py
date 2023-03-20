from django.db import models


# 品目グループマスタ
class ItemGroupMaster(models.Model):
    品目グループコード = models.CharField(primary_key=True, max_length=9)
    品目グループテキスト = models.CharField(max_length=20, blank=True, null=True)

    class Meta:
        managed = False
        db_table = '品目グループマスタ'


# 数量単位マスタ
class QuantityUnitMaster(models.Model):
    数量単位コード = models.CharField(primary_key=True, max_length=3)
    単位テキスト = models.CharField(max_length=30, blank=True, null=True)
    備考 = models.CharField(max_length=100, blank=True, null=True)

    class Meta:
        managed = False
        db_table = '数量単位マスタ'


# 指図書マスタ
class InstructionNoMaster(models.Model):
    指図書コード = models.CharField(primary_key=True, max_length=17)
    テキスト短 = models.CharField(max_length=40, blank=True, null=True)
    指図書タイプ = models.CharField(max_length=4, blank=True, null=True)
    指図書タイプ名称 = models.CharField(max_length=30, blank=True, null=True)
    利益センター = models.CharField(max_length=10, blank=True, null=True)
    指図ステータス = models.DecimalField(max_digits=2, decimal_places=0, blank=True, null=True)

    class Meta:
        managed = False
        db_table = '指図書マスタ'


# 原価センタマスタ
class CostCenterMaster(models.Model):
    原価センタ = models.CharField(primary_key=True, max_length=10)
    原価センタテキスト = models.CharField(max_length=20, blank=True, null=True)
    原価属性コード = models.CharField(max_length=2, blank=True, null=True)

    class Meta:
        managed = False
        db_table = '原価センタマスタ'


# 勘定コードマスタ
class AccountCodeMaster(models.Model):
    勘定コード = models.CharField(primary_key=True, max_length=16)
    テキスト短 = models.CharField(max_length=20, blank=True, null=True)

    class Meta:
        managed = False
        db_table = '勘定コードマスタ'


# 保管場所マスタ
class StorageSpaceMaster(models.Model):
    プラントコード = models.CharField(primary_key=True, max_length=4)
    保管場所コード = models.CharField(max_length=4)
    保管場所テキスト = models.CharField(max_length=16, blank=True, null=True)

    class Meta:
        managed = False
        db_table = '保管場所マスタ'
        unique_together = (('プラントコード', '保管場所コード'),)


# 仕入先マスタ
class VendorMaster(models.Model):
    仕入先コード = models.CharField(primary_key=True, max_length=10)
    仕入先名称 = models.CharField(max_length=40, blank=True, null=True)
    会社コード = models.CharField(max_length=4, blank=True, null=True)
    購買組織コード = models.CharField(max_length=4)
    購買発注通貨 = models.CharField(max_length=5, blank=True, null=True)
    購買グループコード = models.CharField(max_length=3, blank=True, null=True)

    class Meta:
        managed = False
        db_table = '仕入先マスタ'
        unique_together = (('仕入先コード', '購買組織コード'),)


# 依頼部署マスタ
class OrderDepartment(models.Model):
    部署コード = models.CharField(primary_key=True, max_length=4)
    部署名称 = models.CharField(max_length=40, blank=True, null=True)
    部署グループコード = models.CharField(max_length=2, blank=True, null=True)

    class Meta:
        managed = False
        db_table = '依頼部署マスタ'


# 勘定コード定義マスタ
class AccountCodeDefinitionMaster(models.Model):
    品目グループコード = models.CharField(primary_key=True, max_length=2)
    原価属性コード = models.CharField(max_length=2)
    勘定コード = models.CharField(max_length=16, blank=True, null=True)

    class Meta:
        managed = False
        db_table = '勘定コード定義マスタ'
        unique_together = (('品目グループコード', '原価属性コード'),)


# 品目マスタ
class ItemMaster(models.Model):
    品目コード = models.CharField(primary_key=True, max_length=18)
    テキスト品目コード = models.CharField(max_length=8, blank=False, null=False)
    プラントコード = models.CharField(max_length=4, blank=False, null=False)
    ＶＢ区分 = models.CharField(max_length=1, blank=False, null=False)
    品目テキスト = models.CharField(max_length=40, blank=True, null=True)
    基本数量単位 = models.CharField(max_length=3, blank=True, null=True)
    品目グループ = models.CharField(max_length=9, blank=True, null=True)
    購買発注テキスト１ = models.CharField(max_length=40, blank=True, null=True)
    購買発注テキスト２ = models.CharField(max_length=40, blank=True, null=True)
    カタログ名 = models.CharField(max_length=25, blank=True, null=True)
    カタログＮＯ = models.CharField(max_length=15, blank=True, null=True)
    カタログページ = models.CharField(max_length=20, blank=True, null=True)
    ＣＡＳＮＯ = models.CharField(max_length=20, blank=True, null=True)
    レジストリＮＯ = models.CharField(max_length=1840, blank=True, null=True)
    商品備考１ = models.CharField(max_length=40, blank=True, null=True)
    商品備考２ = models.CharField(max_length=40, blank=True, null=True)
    商品備考３ = models.CharField(max_length=40, blank=True, null=True)
    商品備考４ = models.CharField(max_length=40, blank=True, null=True)
    発注日 = models.CharField(max_length=8, blank=True, null=True)
    発注価格 = models.DecimalField(max_digits=11, decimal_places=0, blank=True, null=True)
    通貨コード = models.CharField(max_length=5, blank=True, null=True)
    購買価格単位 = models.DecimalField(max_digits=5, decimal_places=0, blank=True, null=True)
    発注仕入先コード = models.CharField(max_length=10, blank=True, null=True)
    購買グループ = models.CharField(max_length=4, blank=True, null=True)
    購買組織 = models.CharField(max_length=5, blank=True, null=True)
    発注ＮＯ = models.CharField(max_length=10, blank=True, null=True)
    発注明細ＮＯ = models.CharField(max_length=5, blank=True, null=True)
    バッチ処理フラグ = models.CharField(max_length=1, blank=True, null=True)
    失効区分 = models.CharField(max_length=1, blank=True, null=True)

    class Meta:
        managed = False
        db_table = '品目マスタ'


# ユーザー管理マスタ
class UserMaster(models.Model):
    ＮＴユーザー名 = models.CharField(primary_key=True, max_length=30)
    会社コード = models.CharField(max_length=4, blank=True, null=True)
    漢字氏名 = models.CharField(max_length=16, blank=True, null=True)
    社員コード = models.CharField(max_length=8, blank=True, null=True)
    メールアドレス = models.CharField(max_length=40, blank=True, null=True)
    部署コード = models.CharField(max_length=4, blank=True, null=True)
    兼務部署コード１ = models.CharField(max_length=4, blank=True, null=True)
    兼務部署コード２ = models.CharField(max_length=4, blank=True, null=True)
    兼務部署コード３ = models.CharField(max_length=4, blank=True, null=True)
    兼務部署コード４ = models.CharField(max_length=4, blank=True, null=True)
    兼務部署コード５ = models.CharField(max_length=4, blank=True, null=True)
    兼務部署コード６ = models.CharField(max_length=4, blank=True, null=True)
    兼務部署コード７ = models.CharField(max_length=4, blank=True, null=True)
    兼務部署コード８ = models.CharField(max_length=4, blank=True, null=True)
    兼務部署コード９ = models.CharField(max_length=4, blank=True, null=True)
    兼務部署コード１０ = models.CharField(max_length=4, blank=True, null=True)
    承認権限 = models.CharField(max_length=1, blank=True, null=True)
    システム権限 = models.CharField(max_length=1, blank=True, null=True)
    上長メールアドレス = models.CharField(max_length=40, blank=True, null=True)
    代理メールアドレス１ = models.CharField(max_length=40, blank=True, null=True)
    代理メールアドレス２ = models.CharField(max_length=40, blank=True, null=True)
    代理メールアドレス３ = models.CharField(max_length=40, blank=True, null=True)
    代理メールアドレス４ = models.CharField(max_length=40, blank=True, null=True)
    代理メールアドレス５ = models.CharField(max_length=40, blank=True, null=True)
    購買依頼者 = models.CharField(max_length=12, blank=True, null=True)
    購買依頼追跡番号 = models.CharField(max_length=10, blank=True, null=True)
    プラントコード = models.CharField(max_length=4, blank=True, null=True)
    購買グループ = models.CharField(max_length=3, blank=True, null=True)
    担当別購買グループ = models.CharField(max_length=3, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'ユーザー管理マスタ'
