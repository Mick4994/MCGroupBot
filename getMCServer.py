import socket

def search_minecraft_server (host, port):
    try:
        status,protocol,version,title,numplayers,maxplayers = "未知状态","\000","\000","\000","\000","\000"
        #初始化变量
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect((host, port))
        s.sendall(b'\xFE\x01')
        #向服务器发送请求
        data = s.recv(1024).split(b'\x00\x00')
        #把接受到的数据中00 00 之间的数据进行隔段操作以方便对数据操作
        s.close()
        #结束请求

        #检查data是否为空数据,可以使用print(data)查看数据结构
        if len(data) >= 3:
            packet_id = data[0][0]
            if packet_id == 255:
                status = "在线"
                protocol = data[1].decode('utf-8', 'ignore').replace("\x00","")
                version = data[2].decode('utf-8', 'ignore').replace("\x00","")
                title = data[3].decode('utf-8', 'ignore').replace("\x00","")
                numplayers = data[4].decode('utf-8', 'ignore').replace("\x00","")
                maxplayers = data[5].decode('utf-8', 'ignore').replace("\x00","")
            else:
                status = "未知状态"
        else:
            status = "未知状态"

        return status,protocol,version,title,numplayers,maxplayers

    except Exception as e:
        print("Error:", e)
        return "离线","\000","\000","\000","\000","\000"

if __name__ == "__main__":
    host="sztumc.top"
    port=25566

    status,protocol,version,title,numplayers,maxplayers=search_minecraft_server(host, port)
    print("服务器状态:", status)
    print("协议版本:", protocol)
    print("游戏版本:",version)
    print("服务器标题:", title)
    print("当前玩家数:", numplayers)