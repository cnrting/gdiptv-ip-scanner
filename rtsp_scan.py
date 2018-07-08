#! /usr/bin/python3
# coding: utf-8
# iptv直播源可用ip扫描脚本

import socket
from netaddr import IPNetwork
import threadpool
import time
import sys

#广东电信iptv默认ip段
host_cidr = [
    "125.88.0.0/16",
    "183.59.0.0/16",
    "14.29.0.0/16",
    "183.232.0.0/16",
    "113.100.0.0/16",
    "103.229.0.0/16",
    "59.37.0.0/16"
]

#支持命令行直接输入要扫面的ip段(cidr),用法:rtsp_scan.py 125.88.0.0/16 183.59.0.0/16
if len(sys.argv) > 1:
    host_cidr.clear()
    for cidr in sys.argv[1:]:
        host_cidr.append(cidr)

#线程池大小
poolsize = 200
ipList = []
ipResult = []
idx  = 0

for cidr in host_cidr:
    for ip in IPNetwork(cidr):
        ipList.append(str(ip))
    scanrange = ipList[idx] + "-" + ipList[-1]
    idx = len(ipList)
    print(time.strftime("%Y/%m/%d %H:%M:%S %a %z"),"Added Sacn Range:", scanrange)

class RTSP_Message:
    def __init__(self, Stream_url=None):
        # pass
        self.url = Stream_url
        self.cseq = 1
        self.userAgent = "Lavf58.16.100"
        self.sessionID = None

    def OPTIONS(self):
        msg = 'OPTIONS ' + self.url + ' RTSP/1.0\r\n'
        msg += 'CSeq: ' + str(self.cseq) + '\r\n'
        msg += 'User-Agent: ' + self.userAgent + '\r\n'
        msg += '\r\n'
        #print(msg)
        msg = msg.encode('utf8')
        return msg

    def DESCRIBE(self):
        msg = 'DESCRIBE ' + self.url + ' RTSP/1.0\r\n'
        msg += 'CSeq: ' + str(self.cseq) + '\r\n'
        msg += 'User-Agent: ' + self.userAgent + '\r\n'
        msg += 'Accept: application/sdp\r\n'
        msg += '\r\n'
        #print(msg)
        msg = msg.encode('utf8')
        return msg

    def SETUP(self):
        msg = 'SETUP ' + self.url + ' RTSP/1.0\r\n'
        msg += 'CSeq: ' + str(self.cseq) + '\r\n'
        msg += 'User-Agent: ' + self.userAgent + '\r\n'
        msg += 'Transport: RTP/AVP/TCP;unicast;interleaved=0-1\r\n'
        msg += 'Session: ' + self.sessionID + '\r\n'
        msg += '\r\n'
        #print(msg)
        msg = msg.encode('utf8')
        return msg

    def PLAY(self):
        msg = 'PLAY ' + self.url + ' RTSP/1.0\r\n'
        msg += 'CSeq: ' + str(self.cseq) + '\r\n'
        msg += 'User-Agent: ' + self.userAgent + '\r\n'
        msg += 'Session: ' + self.sessionID + '\r\n'
        msg += '\r\n'
        #print(msg)
        msg = msg.encode('utf8')
        return msg

class RTSP_Client():
    def __init__(self, host):
        self.ipept = (host, 554)
        self.response = None
        self.socket = None
        self.rtsp_message = None
        self.url = 'rtsp://' + self.ipept[0] + ':554/PLTV/88888905/224/3221227610/10000100000000060000000004462931_0.smil'

    def options(self):
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        socket.setdefaulttimeout(2)
        self.socket.connect(self.ipept)
        # print('-------------OPTIONS----------------')
        self.rtsp_message = RTSP_Message(Stream_url=self.url)
        self.socket.send(self.rtsp_message.OPTIONS())
        self.rtsp_message.cseq += 1
        data = self.socket.recv(1024)
        self.response = data.decode('utf8')
        print(time.strftime("%Y/%m/%d %H:%M:%S %a %z"), self.ipept[0], self.response.split("\r\n")[0], self.response.split("\r\n")[1])
        if "HMS_V1R2" in self.response or "HWServer/1.0.0.1" in self.response:
            ipResult.append(self.ipept[0])
        self.socket.close()
    def describe(self):
        # print('-------------DESCRIBE----------------')
        self.socket.send(self.rtsp_message.DESCRIBE())
        self.rtsp_message.cseq += 1
        data = self.socket.recv(1024)
        self.response = data.decode('utf8')
        self.socket.close()
        # print(time.strftime("%Y/%m/%d %H:%M:%S %a %z"), self.ipept[0], self.response.split("\r\n")[0], self.response.split("\r\n")[1])
        if "302 Moved Temporarily" in self.response:
            # print("302 Moved Temporarily:",self.ipept[0])
            self.url = self.response.split("\r\n")[1].split(" ")[1]
            self.rtsp_message.cseq = 1
            self.ipept = (self.rtsp_message.url.split(":")[1][2:], 554)
            # self.socket.close()
            self.options()
            self.describe()

        # if "Server: HMS_V1R2" in self.response:
        #     ipResult.append(self.ipept[0])
        # else: print(time.strftime("%Y/%m/%d %H:%M:%S %a %z"),self.ipept[0], self.response.split("\r\n")[0])

    def setup(self):
        sessionid = self.response.split("Session: ")[1].split("\r\n")[0]
        # #print("sessionid:"+sessionid)
        # sys.exit(0)
        self.rtsp_message.sessionID = sessionid

        #print('-------------SETUP----------------')
        self.socket.send(self.rtsp_message.SETUP())
        self.rtsp_message.cseq += 1
        data = self.socket.recv(1024)
        self.response = data.decode('utf8')
        # print(self.response)

    def play(self):
        #print('-------------PLAY----------------')
        self.socket.send(self.rtsp_message.PLAY())
        self.rtsp_message.cseq += 1
        data = self.socket.recv(1024)
        self.response = data.decode('utf8')
        #print(self.response)

def scan(host):
    try:
        # print("Testing:",host)
        rtspobj = RTSP_Client(host)
        rtspobj.options()
        # sleep(1)
        # rtspobj.describe()
        # sleep(1)
        # rtspobj.setup()
        # sleep(1)
        # rtspobj.play()
    except Exception as e:
        pass
        # print(e)
        # traceback.print_exc()

pool = threadpool.ThreadPool(poolsize)
reqs = threadpool.makeRequests(scan, ipList)
[pool.putRequest(req) for req in reqs]
pool.wait()

#每次扫描结果写入文件
with open(time.strftime("%Y%m%d_%H%M%S_%a.result"), 'x') as fi:
    fi.write("Scan Result for:"+ str(host_cidr)+"\r\n"+str(ipResult))