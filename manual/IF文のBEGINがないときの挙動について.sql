

DECLARE @タグ NVARCHAR(20)	= 'U4_FC2747_1.PV'

IF @タグ = 'U4_FC2747_1.PV'
PRINT '通る'

IF @タグ = '%U4_FC2746%'
PRINT '通らない'

PRINT @タグ

