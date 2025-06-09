2025/04/24 コメント欄を追加&PDF出力にもコメント欄を追加 <br>
2025/04/25 テストデータ入力の名前入力欄にオートコンプリート機能を追加<br>
2025/05/08 グラフにZ統計量から算出したスコアを表示するように更新

## Database Configuration

This application now expects database files on a shared network drive. Set the
`SHARED_DB_DIR` environment variable to the directory containing
`id_database.db` and `physical_rawdata.db`. If the variable is not provided,
`/mnt/shared` is used by default.
