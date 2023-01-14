#simple websockets brocaster
import asyncio
import websockets
clients = [] #to store all connected cleints
lockSign=0#判斷有沒有搶到答題全
owner=None#存放搶到發言權人的名字
HostName=0#判斷是否為第一位主持人
players=[]#玩家名單，用來判斷有沒有同名者
score=[]#玩家的分數名單
Updatescore="0"#暫存上一題答對者的分數
determine=2#判斷答案是否正確
chk=1# 可以不用
answer='0'#暫存上一題的答案
PlayerRank=[]
startalready=0#遊戲開始沒


#handler for socket message activities
async def handler(websocket, path):
    global lockSign, owner,HostName
    #print(path) #path is not used currently
    userName='unknown'#可以移到最上面 嗎
    if websocket not in clients:
        clients.append(websocket) #append new cleint to the array
    async for message in websocket:
        print('收到message : ',message) #print to console
        msg = message.split("###")
        if msg[0]=='ifconnectTrue':#判斷主持人連線
            if HostName > 0:#不能有兩位主持人
                await websocket.send('ifconnectTrue###NO')
            else:
                HostName=1
                await websocket.send('ifconnectTrue###YES')
                userName=msg[1]
                print(userName+"已連線")
                print('startalready=',startalready)
        elif msg[0]=='chkclient':#判斷答題者連線
            if msg[1] in players :#已經有人取該名字了
                await websocket.send('chkclient###NO')
            elif msg[1]=='出題者':
                await websocket.send('chkclient###NO')
            else:#還要判斷有沒有人輸入特殊字元
                specialnum=await chkspecial(msg[1])
                print('specialnum=',specialnum)
                if specialnum>0:#有特殊字元
                    await websocket.send('chkclient###Special')
                else:
                    if startalready>0:
                        await websocket.send('chkclient###startalready')
                    else:
                        userName=msg[1]
                        print(userName+"已連線")
                        players.append(userName)#存放玩家
                        score.append(0)#分數一開始為0
                        await websocket.send('chkclient###YES')
        elif msg[0]=='START':#判斷是否可以開始遊戲
            #要先判斷有沒有玩家，有玩家才可以START
            if len(players)<=0:#代表沒有玩家進入
                await websocket.send('START###NO')
            else:
                print('players')
                playerlist=''
                for i in range(len(players)):
                    playerlist+=players[i]+'**'
                await brocast(playerlist)#websocket.send('START###'+msg)
        #收到題目和答案
        elif msg[0]=='Host':
            await saveq(msg[1],msg[2])#存題目,答案
        #搶答
        elif msg[0]=='GET':
            print("GET", lockSign,msg[1])#cmd 上
            #先通知大家有人按搶答扭了
            for websock in clients:
                try:
                    await websock.send("GETALL###"+msg[1]) #send message to each client
                except websockets.exceptions.ConnectionClosed:
                    #remove the client when it disconnects
                    print("Client disconnected.  Do cleanup")
                    clients.remove(websock)
            #再判斷是否有搶到
            if lockSign > 0:
                await websocket.send('GET###NO')
            else:
                lockSign = 1
                #owner=websocket
                #print(owner)
                await websocket.send('GET###YES')
                #iterate the clients
        #取消搶答
        elif msg[0]=="DROP":
            lockSign=0#釋放資源
            for websock in clients:
                try:
                    await websock.send("DROP###"+msg[1]) #send message to each client
                        #await websock.send("出題中...請稍後") #send message to each client
                except websockets.exceptions.ConnectionClosed:
                        #remove the client when it disconnects
                    print("Client disconnected.  Do cleanup")
                    clients.remove(websock)
        elif msg[0]=='ClientAnswer':
            lockSign=0#因為提交了，所以要釋放搶答資源
            determine=await chkAns(msg[1])#判斷答案是否正確，0為正確,1為錯誤
            await Plusscore(determine,msg[2])
            if determine==0:
                #如果回答正確 要記錄owner是誰
                owner=websocket
            else:
                owner='999'
            #if websocket==owner:
            print(websocket)
            print(owner)
            if websocket==owner:
                await websocket.send("UPDATE###"+str(Updatescore))
                print(str(Updatescore))
            else:
                print('更新失敗')
        elif msg[0]=='Clean':
            lockSign=0#因為換下一題了，所以要釋放資源
            await cleanQA()
        elif msg[0]=='Finish':
            await end()
        #提交答案
        else:
            print(message)#題目,答案
async def chkspecial(msg):
    specialstr=['#',',','*']
    specialnum=0
    for i in range(len(specialstr)):
        if specialstr[i] in msg:
            specialnum+=1
    return specialnum
async def brocast(msg):
    global startalready
    #iterate the clients
    startalready=1
    print('startalready=',startalready)
    for websock in clients:
        try:
            await websock.send('START###'+msg) #send message to each client
        except websockets.exceptions.ConnectionClosed:
            #remove the client when it disconnects
            print("Client disconnected.  Do cleanup")
            clients.remove(websock)
            #pass
async def saveq(ques,ans):
    global question
    global answer
    question = ques
    answer=ans
    print("題目為:",ques) 
    print("答案為:",ans)
    #iterate the clients
    for websock in clients:
        try:
            await websock.send("Host###"+ques) #send message to each client
        except websockets.exceptions.ConnectionClosed:
            #remove the client when it disconnects
            print("Client disconnected.  Do cleanup")
            clients.remove(websock)
async def chkAns(ans):
    if answer==ans:
        chk=0
    else:
        chk=1
    return chk
async def Plusscore(num,owner1):
    global Updatescore
    if num==0:#回答正確
        print(owner1,'回答正確!得分!')
        print(score)
        print(Updatescore)
        #加3分!
        score[players.index(owner1)]=score[players.index(owner1)]+3
        Updatescore=str(score[players.index(owner1)])
        for websock in clients:
            try:
                await websock.send('PLUS###'+owner1+'###'+answer) #send message to each client
            except websockets.exceptions.ConnectionClosed:
                print("Client disconnected.  Do cleanup")
                clients.remove(websock)
    else:
        print('回答錯誤!')
        for websock in clients:
            try:
                await websock.send('WrongAns###'+owner1)
            except websockets.exceptions.ConnectionClosed:
                print("Client disconnected.  Do cleanup")
                clients.remove(websock)
        
async def cleanQA():
    question=None
    answer=None
    for websock in clients:
        try:
            await websock.send("NEXT") #send message to each client
        except websockets.exceptions.ConnectionClosed:
            #remove the client when it disconnects
            print("Client disconnected.  Do cleanup")
            clients.remove(websock)
            #pass
async def end():
    HostName=0#主持人已結束遊戲，Host要釋放
    #結算成績
    print('玩家名字 players=',players)
    print('玩家相對應的分數 score=',score)
    print('_________________________________')
    
    sortlist=[]
    for i in range(len(players)):
        l=[]
        l.append(score[i])
        l.append(players[i])
        sortlist.append(l)
    print(sortlist)
    
    student_sort = sorted(sortlist, reverse=True)
    
    print(student_sort)
    
    playernum=len(student_sort)
    resulttext='Result###'+str(playernum)
    for i in range(len(student_sort)):
        resulttext+='###'+str(student_sort[i][0])+'###'+student_sort[i][1]
    
    print('resulttext=',resulttext)
    for websock in clients:
        try:
            await websock.send(resulttext) #send message to each client
        except websockets.exceptions.ConnectionClosed:
            #remove the client when it disconnects
            print("Client disconnected.  Do cleanup")
            clients.remove(websock)
            #pass

#starts the service and run forever
loop = asyncio.new_event_loop() #get an event loop
asyncio.set_event_loop(loop) #set the event loop to asyncio

loop.run_until_complete(
	websockets.serve(handler, 'localhost', 4545) #setup the websocket service and handler
    #連線要把localhost拿掉
	) #hook to localhost:4545
loop.run_forever() #keep it running