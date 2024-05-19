# mock-modbus.py
# version: python 3
# 用于模拟一个基于modbus协议传输虚拟设备驱动

from pyModbusTCP.server import ModbusServer
from time import sleep
from random import uniform

# device value
ThermostatL = 3999
ThermostatH = 4000
AlarmMode = 4001    #"1 - OFF (disabled), 2 - Lower, 3 - Higher, 4 - Lower or Higher"
Temperature = 4003


temperature = 0
# update Temperature fun
def updateTemperature():
    server.data_bank.set_holding_registers(Temperature, [int(uniform(-550,1250))])

# Create an instance of ModbusServer
server = ModbusServer("192.168.31.101",502, no_block=True)

# set holding registers
server.data_bank.set_holding_registers(ThermostatL, [-550]) # -55摄氏度
server.data_bank.set_holding_registers(ThermostatH, [1250]) # 125摄氏度
server.data_bank.set_holding_registers(AlarmMode, [1]) # 125摄氏度
server.data_bank.set_holding_registers(Temperature, [0]) # 0摄氏度

# device start
try:
    print("start server...")
    server.start()
    print("server is online")
    server.data_bank.set_holding_registers(4002, [0])
    state = [0]
    while True:
        # server.data_bank.set_holding_registers(4003, [round(uniform(-10,0), 1)])
        updateTemperature()
        print("Value of Register 3999--4003 has changed to "+ str(server.data_bank.get_holding_registers(3999, 5)))
        sleep(2)
except KeyError:
    print("Shutdown server...")
    server.stop()
    print("server is offline")
