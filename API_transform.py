# API_transform.py
# 设备命令下发转发

import paho.mqtt.client as mqtt
import json
import time
import queue    # pthon2.7 Queue 用于多线程处理
import threading
import requests
import socket

"""
mapper流程:解析配置-获取设备列表-设置期望值-sub & set pub
线程  -----  获取期望值  获取data  获取设备status
# 公网ip
res = requests.get('http://myip.ipip.net', timeout=5).text
print(res)

get(url, params, args)
post(url, data, json, args) # 新增数据
put(url, data, args) # 修改现存数据
delete(url, args) # 删除数据
request(method, url, args) # 向指定的 url 发送指定的请求方法

head(url, args)
patch(url, data, args)

"""


# mqtt broker information
BROKER_HOST_ADDR  = "192.168.31.101"    # edgex/edgecore IP
# HOST_ADDR           = socket.gethostbyname(socket.gethostname())
BROKER_HOST_PORT    = 1883
USERNAME            = "Tramsform"
PWD                 = "123"

baseurl = "http://192.168.31.101:59882/api/v3/device/name"
headers_put = {
	'Content-Type': "application/json"
}

desire_change = "$hw/events/device/+/twin/update/delta"

def on_connect(client, userdata, flags, rc):
    """
    链接mqtt成功、失败都会回调此函数
    :param client:
    :param userdata:
    :param flags:
    :param rc:0.成功 1.错误的协议版本 2.无效的 client ID  3.服务器不可用  4.错误的用户名或密码  5.无法验证
    :return:
     client.subscribe(subscribe_topic_array )  # 订阅多个主题
    """
    print("Connected with result code " + str(rc))
    client.subscribe(desire_change)  # 订阅消息

'''
def on_message(client, userdata, msg):
    print("on_message 主题:" + msg.topic + " 消息:" + str(msg.payload.decode('utf-8')))
'''
# 当接收到消息时调用
def on_message(client, userdata, msg):
    print(f"Message received on topic {msg.topic}: {msg.payload.decode('utf-8')}")
    
    # 提取主题名中某一级的字符串
    topic_levels = msg.topic.split('/')
    if len(topic_levels) > 3:
        devicename = topic_levels[3]
        print(f"Device Name: {devicename}")
    else:
        print("Topic does not have enough levels")

    try:
        payload_json = json.loads(msg.payload.decode('utf-8'))
        delta = payload_json["delta"]
        valuename = list(delta.keys())
        print("改变的参数有:",valuename[0])
        for key in valuename:
            value = delta[key]
            data = {key: value}
            url = f"{baseurl}/{devicename}/{key}"
            while(1):
                response = requests.put(url=url, json=data, headers=headers_put)
                if response.status_code ==200:
                    print(f"处理设备{devicename}的变量{key},期望值为:{value}")
                    break
                else:
                    print("==========失败,status_code={1}===================".format(response.status_code))
                time.sleep(1)

    except json.JSONDecodeError as e:
        print(f"Error decoding JSON: {e}")

# 创建MQTT客户端实例
client = mqtt.Client()

# 设置连接的回调函数
client.on_connect = on_connect
# 设置接收消息的回调函数
client.on_message = on_message

# 连接到MQTT服务器
client.connect(BROKER_HOST_ADDR, BROKER_HOST_PORT, 60)

# 阻塞调用，客户端将自动处理重连操作
client.loop_forever()










# node device membership
sub_list_change = "$hw/events/node/+/membership/updated"  #16. mapper sub 通知设备添加/删除
pub_node = "$hw/events/node/+/membership/get"  #27. mapper 发布节点关联的设备？ # 需要发什么数据?
sub_node = "$hw/events/node/+/membership/get/result" #38. sub 查询设备列表的结果

# 将预期值更新到云
pub_twin_update = "$hw/events/device/+/twin/update" #62 pub更新 deviceID/name 的devicetwin       # 上传数据
sub_twin_update = "$hw/events/device/+/twin/update/result"#43. mapper查询更新是否成功

sub_twin_update_value = "$hw/events/device/+/twin/update/delta" #51 mapper sub 通知预期值已更改

# 官方mapper文档未提及v1.13.2
xub_twin_cloud_get = "$hw/events/device/+/twin/cloud_get"   # 获取设备的孪生状态
sub_twin_cloud_get = "$hw/events/device/+/twin/get/result" # mapper sub获取设备属性的值
sub_twin_get = "$hw/events/device/+/twin/get" # pub 设备属性的值

#device state
pub_state = "$hw/events/device/+/state/update"  #75 pub更新设备状态
sub_state = "$hw/events/device/+/state/update/result" # sub 设备状态更新结果

# 不用topic
# pub="$ke/events/+/device/data/update"   # x4 不由 edgecore 处理，由 EMQ Kuiper 等边缘节点上的第三方组件处理
# sub_twin_cloud_updated = "$hw/events/device/+/twin/cloud_updated" # 同步边缘和云之间的孪生状态
# "$hw/events/upload/#" # 暂无使用
# "SYS/dis/upload_records" # x 9 暂无使用
# $hw/events/device/+/twin/update/document # mapper sub获取设备属性更新的操作记录
# $hw/events/device/+/updated # 0 mapper 订阅设备属性描述的变化

# edgex
# one 设备 http://192.168.31.34:59882/api/v3/device/name/Random-Integer-Device

# http://192.168.31.34:59882/api/v3/device/name/{name}/{command}

# /device/name/{name}/{command} get / put  读取/写入
# /device/name/{name}/  与设备关联的所有命令
# 
baseurl = "http://192.168.31.101:59882/api/v3"
# http://192.168.31.34:59882/api/v3/device/name/Random-Integer-Device
# core-command
command = "/device/name/{name}/{command}"       # get / put
deviceallcommand = "/device/name/{name}"
allcommand = "/device/all"
config = "/config"  # 服务当前配置
ping = "/ping"  # 服务连通性
version = "version"

# core-data //event
'''
curl http://localhost:59882/api/v3/device/name/Modbus-TCP-Temperature-Sensor/AlarmThreshold \
    -H "Content-Type:application/json" -X PUT  \
    -d '{"ThermostatL":"15","ThermostatH":"100"}'

curl http://localhost:59882/api/v3/device/name/my-custom-device/message \
    -H "Content-Type:application/json" -X PUT  \
    -d '{"message":"Hello!"}'

'''
