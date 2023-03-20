BEGIN TRY
  -- TRYブロック内に実行するTransact-SQLステートメントを記述する
  SELECT 1/0;
  -- ERROR以降の処理は実行されない
  SELECT 'test';
END TRY
BEGIN CATCH
  -- CATCHブロック内にエラー処理のコードを記述する
  SELECT
    ERROR_NUMBER() AS ErrorNumber,
    ERROR_SEVERITY() AS ErrorSeverity,
    ERROR_STATE() AS ErrorState,
    ERROR_PROCEDURE() AS ErrorProcedure,
    ERROR_LINE() AS ErrorLine,
    ERROR_MESSAGE() AS ErrorMessage;
END CATCH