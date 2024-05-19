# mock-mqtt.py
# version: python 3
# 用于模拟一个基于mqtt协议传输虚拟设备驱动

import paho.mqtt.client as mqtt
import json
import time
import queue
import threading,random

BROKER_HOST_ADDR   = "192.168.31.101"
BROKER_HOST_PORT   = 1883
USERNAME    = "huaqiao"
PWD         = "1234"
#cmd topic本质上就是你的设备监听的topic，
#也是在UI上添加device的时候，地址中所填数据，和用户名密码等一起组成当前设备的唯一标识。
CMD_TOPIC   = "command/my-ds18b20-01/#"
RESPONSE_TOPIC = "ResponseTopic"# "command/response/"+ uuid;
DATA_TOPIC  = "incoming/data/my-ds18b20-01/temperature"

message = "test-message"
json_data = {"name": "My JSON"}

globalQueue = queue.Queue()

# DS18B20 设备文件地址
device_file ='/sys/bus/w1/devices/28-092170455eaa/w1_slave'

# cat 文件
def read_temp_raw():
    f = open(device_file,'r')
    lines = f.readlines()
    f.close()
    return lines

# 从文件中获得温度数据
def read_temp():
    lines = read_temp_raw()
    while lines[0].strip()[-3:] != 'YES':
        # print('--------------Eeeor----------------')
        time.sleep(0.2)
        lines = read_temp_raw()
    # print('--------------Success----------------')
    equals_pos = lines[1].find('t=')
    if equals_pos != -1:
        temp_string = lines[1][equals_pos+2:]
        temp_c = float(temp_string)/1000.0
    return temp_c

def gen():
       return round(random.uniform(0, 50),2)

def send_data():
    #java版本, name的值为添加的设备名
    #data = {"randnum":520.1314,"name":"mqtt-device-01"}

    #go版本, name的值为添加的设备名, go版本的区别是必须带上cmd字段
    #var data = {"randnum":520.1314,"name":"","cmd":"randnum"}
    data = {"temperature":round(read_temp(), 3),"name":"my-ds18b20-01","cmd":"temperature"}
    print("sending data actively! " + json.dumps(data))
    client.publish(DATA_TOPIC,json.dumps(data) , qos=0, retain=False)

class SendDataActiveServer(threading.Thread):
    def __init__(self,threadID,name,queue):
        super(SendDataActiveServer,self).__init__()
        self.threadID = threadID
        self.name = name
        self.queue = queue
        self.active = False

    def run(self):
        while 1==1 :
          if self.active:
             send_data()
             time.sleep(1)
             print("发送温度")
             self.getItemFromQueue()
          else:
             time.sleep(1)
             self.getItemFromQueue()

    def getItemFromQueue(self):
        try:
          #这个地方为啥用字符串判断，但是device profile文件中的collect属性是Boolean，
          #这个是因为现有的device-mqtt发送命令时，参数一律是string，可参见MqttDriver.java的402行的CmdMsg类的param属性就是string类型
          if self.queue.get(block=False) == "true":
             self.active = True
          else:
             self.active = False
        except queue.Empty:
          #quene.get()方法在队列中为空是返回异常，捕获异常什么都不做，保持active原状
          time.sleep(0.1)

#当接收到命令，响应命令
# command/my-ds18b20-01/message/get/85c9e1e6-8a01-4303-9588-804564dbbaf8 b''
def on_message(client, userdata, msg):
    print(msg.topic+" "+str(msg.payload)+'\n')
    # d = json.loads(msg.payload.decode('utf-8'))
    topic = msg.topic
    words = topic.split('/')
    cmd = words[2]
    method = words[3]
    uuid = words[4]
    response = {}

    if method == "set":
        data = json.loads(msg.payload.decode('utf-8'))
        if cmd == "message":
            global message
            message = data[cmd]
        elif cmd == "json":
            global json_data
            json_data = data[cmd]
    else:
        if cmd == "ping":
            response["ping"] = "pong"
        elif cmd == "message":
            response["message"] = message
        elif cmd == "temperature":
            response["temperature"] = round(read_temp(), 3)
        elif cmd == "json":
            response["json"] = json_data

    RESPONSE_TOPIC = f"command/response/{uuid}"
    print(json.dumps(response))
    client.publish(RESPONSE_TOPIC, json.dumps(response))

def on_connect(client, userdata, flags, rc):
    print("Connected with result code "+str(rc))
    #监听命令
    client.subscribe(CMD_TOPIC)

client = mqtt.Client()
client.username_pw_set(USERNAME, PWD)
client.on_message = on_message
client.on_connect = on_connect

client.connect(BROKER_HOST_ADDR, BROKER_HOST_PORT, 60)

#开始独立线程用于主动发送数据
#thread = SendDataActiveServer("Thread-1", "SendDataServerThread", globalQueue)
#thread.setDaemon(True)
#thread.start()

def schedule(interval, func):
    while True:
        func()
        time.sleep(interval)

threading.Thread(target=lambda: schedule(3, send_data)).start()

client.loop_forever()

