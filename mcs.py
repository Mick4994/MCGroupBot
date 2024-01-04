import json
import os
import traceback

import requests
import time
from wxauto import *
from typing import List
from getMCServer import search_minecraft_server
from traceback import print_exc
from io import StringIO
from mcstatus import JavaServer

# 参数
servers = {
    "sztumc.cn":25567,
    "sztumc.top":25566,
}
private_ip = "10.108.0.209"
who = 'MC群'
# who = 'test'
# who = '水滴火熵'
help_msg = "\n\ntips：输入/help获取命令表"
key = ''
try:
    with open('key.txt', 'r') as f:
        key = f.read()
except:
    f = open('key.txt', 'w')
    f.close()
if not key:
    print('请在key.txt文件中输入正确的中转apikey')


def checkMCServer() -> str:
    """
    获取服务器状态

    :return sendmsg获取的结果格式化文本
    """
    sendmsg = '检测到服务器：'
    for host, port in servers.items():
        server = JavaServer.lookup(private_ip+':'+str(port))

        sendmsg += '\n'

        status, protocol, version, title, numplayers, maxplayers \
            = search_minecraft_server(host, port)

        if status == "在线":
            sendmsg += f"""{title}:
服务器ip(外网): {host}:{port}
内网(校园网): {private_ip}:{port}
服务器状态:{status}
游戏版本:{version}
当前玩家数:{numplayers}"""
            try:
                names = server.query().players.names
                if len(names) > 0:
                    sendmsg += '\n玩家列表：'
                    for name in names:
                        sendmsg += f'\n{name}'
                sendmsg += '\n'
            except:
                traceback.print_exc()
        else:
            sendmsg += f"""离线服务器:
服务器ip(外网): {host}:{port}
内网(校园网): {private_ip}:{port}
"""
    return sendmsg[:-1]


def getLiveStatus() -> str:
    """
    获取直播间状态的接口

    :return status 有四种状态['未知'，'未开播'，'直播中'，'轮播中']
    """
    response = requests.request("GET",
        url="https://api.live.bilibili.com/room/v1/Room/room_init?id=31149017",
        headers={
        'User-Agent': 'Apifox/1.0.0 (https://apifox.com)',
        'Accept': '*/*',
        'Host': 'api.live.bilibili.com',
        'Connection': 'keep-alive',
        'Cookie': 'LIVE_BUVID=AUTO4617024351366173'
    }, data={})
    live_status = response.json()['data']['live_status']
    status = '未知'
    if live_status == 0:
        status = '未开播'

    if live_status == 1:
        status = '直播中'

    if live_status == 2:
        status = '轮播中'

    return status


def getDailyNews() -> tuple[str, str]:
    """
    获取东南大学Minecraft社的【每日冷知识】动态
    """
    newsUrl = "https://api.vc.bilibili.com/dynamic_svr/v1/dynamic_svr/space_history?host_uid=1377901474"
    res = requests.get(newsUrl)

    # 解析需要的字段
    context = res.json()['data']['cards'][0]['card']
    context_dict = json.loads(context)
    newsMsg = context_dict['item']['description']
    img_url = context_dict['item']['pictures'][0]['img_src']

    # 存图片
    filename = time.strftime('%Y_%m_%d', time.localtime(time.time()))
    filename = 'C:/ImgData/' + filename + '.png'
    imgRes = requests.get(img_url)
    with open(filename, 'wb') as f:
        f.write(imgRes.content)

    return newsMsg, filename


def getGPT(history_context:List, new_message:str) -> List:
    """
    封装gptapi，可以发送文本提问，返回文本回答

    :params histort_context 上次历史消息记录
    :params new_message 提问的消息
    :return history_context 合并后的历史消息记录
    """

    with open('text/system_prompt.txt', mode='r', encoding='utf-8') as f:
        sys_context = f.read()
    sys_prompt = [
      {
         "role": "system",
         "content": sys_context
      }
    ]
    new_prompt = [
        {
            "role": "user",
            "content": new_message
        }
    ]
    if len(history_context) > 10:
        history_context = history_context[5:]
    messages = sys_prompt + history_context + new_prompt
    payload = json.dumps({
        "model": "gpt-3.5-turbo",
        "messages": messages
    })
    print('sendtoGPT!')
    response = requests.request("POST",
        url="https://api.nextapi.fun/openai/v1/chat/completions",
        headers={
            'Accept': 'application/json',
            'Authorization': 'Bearer ' + key,
            'User-Agent': 'Apifox/1.0.0 (https://apifox.com)',
            'Content-Type': 'application/json',
            'Host': 'api.nextapi.fun',
            'Connection': 'keep-alive'
        }, data=payload)
    ans = response.json()["choices"][0]["message"]
    history_context = messages + [ans]
    with open('text/historyGPT.txt', 'a') as f:
        f.write(str(history_context)+'\n')
    return history_context


if __name__ == "__main__":

    # 初始化
    last_traceback_msg = ''
    last_status = '未开播'

    history_context = []

    wx = WeChat()
    wx.ChatWith(who)

    tick = 0

    # 循环度消息
    while True:

        # 取最新一条的内容
        msgs = wx.GetAllMessage()
        last_msg = msgs[-1]
        context = last_msg[1]

        # 检测到是查询服务器状态
        try:

            sendmsg = ''

            # 早睡助手
            hour, min, sec = time.strftime('%H %M %S', time.localtime(time.time())).split(' ')
            print('time:', hour, min, sec, end='\r')
            if hour == '00' and min == '11' and (sec == '00' or sec == '01'):
                with open('text/tips.txt', mode='r', encoding='utf-8') as f:
                    sendmsg = f.read()

            # 迎新助手
            if context.find('加入了群聊') != -1:
                with open('text/join.txt', mode='r', encoding='utf-8') as f:
                    sendmsg = f.read()

            # 开播检测
            if tick % 100 == 0:
                status = getLiveStatus()
                # print('getting live status')
                if status == '直播中' and status != last_status:
                    sendmsg += '检测到官号开播：\n深圳技术大学Minecraft社直播间\n直播间地址：https://live.bilibili.com/31149017'
                    last_status = status

            # 每日冷知识
            if hour == '15' and min == '45' and (sec == '00' or sec == '01'):
                newMsg, filename = getDailyNews()
                newMsg += '\n--转自东南大学Minecraft社B站动态'
                newMsg += help_msg
                wx.SendMsg(newMsg, who)
                wx.SendFiles(filename, who)

            if not context:
                continue

            # 命令功能
            if context[0] == '/':

                if context == '/mcs':
                    sendmsg = checkMCServer()

                elif context == '/live':
                    status = getLiveStatus()
                    sendmsg += f'深圳技术大学Minecraft社直播间：\n直播状态：{status}\n直播间地址：https://live.bilibili.com/31149017'
                    last_status = status

                else:
                    try:
                        with open('cmd'+context+'.txt', mode='r', encoding='utf-8') as f:
                            sendmsg = f.read()

                    except:
                        print('error context:', context)
                        traceback.print_exc()
                        sendmsg = '未知命令'
                        print(sendmsg)

            # 请求GPT
            if context[:4] == "@Bot":
                asker = last_msg[0]
                wx.SendMsg('正在思考中，回复完成前不会有响应', who)
                new_msg = f'玩家{asker}说:'+context[5:] + '\n回复简短，限制在100字以内，用文言文回复'
                history_context = getGPT(history_context, new_msg)
                answer = history_context[-1]["content"]
                sendmsg += f'@{asker}{context[4]}{answer}'

            # 发送查询结果
            if sendmsg:
                if context != '/help':
                    sendmsg += help_msg
                print(sendmsg)
                wx.SendMsg(sendmsg, who)

        # 异常处理
        except:
            f = StringIO()
            print_exc(file=f)
            traceback_msg = f.getvalue()
            if last_traceback_msg != traceback_msg:
                print(traceback_msg)
            last_traceback_msg = traceback_msg

        time.sleep(0.1)
        tick += 1
        try:
            with open('@AutomationLog.txt', 'w') as f:
                f.write('')
            # print('remove!')
        except:
            pass

