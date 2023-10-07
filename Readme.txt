home.html 為一開始的主頁面
gameclient.html 為答題者
gamehost.html 為出題者(即主持人)
serverH.py 要先開啟才可玩遊戲
(pip install websockets --user)

裡面的防呆:
1.只有一位主持人可以連線
2.玩家不可取一樣的暱稱
3.當沒有玩家連線時，主持人不可開啟遊戲
4.欄位有空白不可提交訊息
5.玩家不可取有#跟*跟,的字元
6.遊戲開啟後其他玩家不可進入