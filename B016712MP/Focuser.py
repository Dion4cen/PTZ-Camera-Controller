'''
    Arducam programable zoom-lens control component.

    Copyright (c) 2019-4 Arducam <http://www.arducam.com>.

    Permission is hereby granted, free of charge, to any person obtaining a copy
    of this software and associated documentation files (the "Software"), to deal
    in the Software without restriction, including without limitation the rights
    to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
    copies of the Software, and to permit persons to whom the Software is
    furnished to do so, subject to the following conditions:

    The above copyright notice and this permission notice shall be included in all
    copies or substantial portions of the Software.

    THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
    EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
    MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.
    IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM,
    DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR
    OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE
    OR OTHER DEALINGS IN THE SOFTWARE.
'''

import sys
import time
import math

class Focuser:
    bus = None
    CHIP_I2C_ADDR = 0x0C
    BUSY_REG_ADDR = 0x04

    # starting_point = [
    #     17320, 13870, 10470,
    #     7820, 5470, 3720,
    #     2320, 1220, 370,
    #     0, 0, 0, 0,
    #     0, 0, 0, 0,
    #     0, 0, 0, 0
    # ]
    
    # end_point = [
    #     20000, 20000, 17370,
    #     14470, 12170, 10270,
    #     8770, 7670, 6820,
    #     5970, 5520, 5220,
    #     4970, 4820, 4770,
    #     4820, 4870, 5020,
    #     5270, 5520, 5770
    # ]
    
    starting_point =     [
        0, 0, 0, 
        0, 0, 0, 
        0, 0, 0, 
        0, 0, 0, 0, 
        0, 0, 0, 0, 0, 0, 
        0, 0
    ]

    end_point = [
        2100, 2100, 2100, 
        2100, 2100, 2100, 
        2100, 2100, 2100, 
        2100, 2100, 2100, 
        2100, 2100, 2100, 
        2100, 2100, 2100, 
        2100, 2100, 2100
    ]

    debug = False

    def __init__(self, bus):
        # try:
            import smbus2 # sudo apt-get install python-smbus
            self.bus = smbus2.SMBus(bus)
        # except:
        #     sys.exit(0)
        
    def read(self,chip_addr,reg_addr):
        value = self.bus.read_word_data(chip_addr,reg_addr)
        value = ((value & 0x00FF)<< 8) | ((value & 0xFF00) >> 8)
        return value
    def write(self,chip_addr,reg_addr,value):
        if value < 0:
            value = 0
        value = ((value & 0x00FF)<< 8) | ((value & 0xFF00) >> 8)
        return self.bus.write_word_data(chip_addr,reg_addr,value)
    def write32(self,chip_addr,reg_addr,value,value1):
        if value < 0:
            value = 0
        if value1 < 0:
            value1 = 0
        data = []
        data.append((value & 0xFF00) >> 8)
        data.append(value & 0x00FF)
        data.append((value1 & 0xFF00) >> 8)
        data.append(value1 & 0x00FF)
        return self.bus.write_i2c_block_data(chip_addr,reg_addr,data)
    
    def write_block(self,chip_addr,reg_addr,data):
        data_u8 = []
        for item in data:  
            data_u8.append((item & 0xFF00) >> 8)
            data_u8.append(item & 0x00FF)
        return self.bus.write_i2c_block_data(chip_addr,reg_addr,data_u8)
    
    def read_block(self,chip_addr,reg_addr):
        return self.bus.read_i2c_block_data(chip_addr,reg_addr,22)
    
    def isBusy(self):
        return self.read(self.CHIP_I2C_ADDR,self.BUSY_REG_ADDR)
    
    def waitingForFree(self):
        count = 0
        begin = time.time()
        if self.debug:
            print('waitingForFree',end='',flush=True)

        while self.isBusy() and count < 600:
            count += 1
            time.sleep(0.01)
            if self.debug:
                print(".",end='',flush=True)
        if self.debug:
            print("return",self.isBusy(),count)

    OPT_BASE    = 0x1000
    OPT_FOCUS   = OPT_BASE | 0x01
    OPT_ZOOM    = OPT_BASE | 0x02
    OPT_MOTOR_X = OPT_BASE | 0x03
    OPT_MOTOR_Y = OPT_BASE | 0x04
    OPT_IRCUT   = OPT_BASE | 0x05
    OPT_MODE    = OPT_BASE | 0x06
    OPT_RESET   = OPT_BASE | 0x07

    opts = {
        OPT_FOCUS : {
            "REG_ADDR" : 0x00,
            "MIN_VALUE": 0,
            "MAX_VALUE": 2100,
            "RESET_ADDR": 0x0A,
        },
        OPT_ZOOM  : {
            "REG_ADDR" : 0x01,
            "MIN_VALUE": 0,
            "MAX_VALUE": 2100,
            "RESET_ADDR": 0x0B,
        },
        OPT_MOTOR_X : {
            "REG_ADDR" : 0x05,
            "MIN_VALUE": 0,
            "MAX_VALUE": 180,
            "RESET_ADDR": None,
        },
        OPT_MOTOR_Y : {
            "REG_ADDR" : 0x06,
            "MIN_VALUE": 0,
            "MAX_VALUE": 180,
            "RESET_ADDR": None,
        },
        OPT_IRCUT : {
            "REG_ADDR" : 0x0C, 
            "MIN_VALUE": 0x00,
            "MAX_VALUE": 0x01,   #0x0001 open, 0x0000 close
            "RESET_ADDR": None,
        },
        OPT_MODE : {
            "REG_ADDR" : 0x30, 
            "MIN_VALUE": 0x00,
            "MAX_VALUE": 0x01,   #0x0001 open, 0x0000 close
            "RESET_ADDR": None,
        },
        OPT_RESET : {
            "REG_ADDR" : 0x10, 
            "MIN_VALUE": 0x00,
            "MAX_VALUE": 0x01,   #0x0001 open, 0x0000 close
            "RESET_ADDR": None,
        }
    }
    
    def reset(self,opt,flag = 1):
        self.waitingForFree()
        info = self.opts[opt]
        if info == None or info["RESET_ADDR"] == None:
            return

        self.write(self.CHIP_I2C_ADDR,info["RESET_ADDR"],0x0000)
        # self.set(opt,info["MIN_VALUE"])
        if flag & 0x01 != 0:
            self.waitingForFree()

    def get(self,opt,flag = 0):
        self.waitingForFree()
        info = self.opts[opt]
        return self.read(self.CHIP_I2C_ADDR,info["REG_ADDR"])

    def set(self,opt,value,flag = 1):
        # print("SET VALUE")
        self.waitingForFree()
        info = self.opts[opt]
        if value > info["MAX_VALUE"]:
            value = info["MAX_VALUE"]
        elif value < info["MIN_VALUE"]:
            value = info["MIN_VALUE"]
        fix_delays = abs(self.read(self.CHIP_I2C_ADDR,info["REG_ADDR"]) - value) 
        # print(0.1*math.ceil(fix_delays/100))
        self.write(self.CHIP_I2C_ADDR,info["REG_ADDR"],value)
        if flag & 0x01 != 0:
            self.waitingForFree()
        # time.sleep(0.2*math.ceil(fix_delays/100))

    def move(self,focus,zoom,flag = 1):
        self.waitingForFree()
        if focus > self.opts[self.OPT_FOCUS]["MAX_VALUE"]:
            focus = self.opts[self.OPT_FOCUS]["MAX_VALUE"]
        elif focus < self.opts[self.OPT_FOCUS]["MIN_VALUE"]:
            focus = self.opts[self.OPT_FOCUS]["MIN_VALUE"]
        if zoom > self.opts[self.OPT_ZOOM]["MAX_VALUE"]:
            zoom = self.opts[self.OPT_ZOOM]["MAX_VALUE"]
        elif zoom < self.opts[self.OPT_ZOOM]["MIN_VALUE"]:
            zoom = self.opts[self.OPT_ZOOM]["MIN_VALUE"]
        
        if self.opts[self.OPT_ZOOM]["REG_ADDR"] == 0x00:
            self.write32(self.CHIP_I2C_ADDR,0x0f,focus,zoom)
        else: 
            self.write32(self.CHIP_I2C_ADDR,0x0f,zoom,focus)
        if flag & 0x01 != 0:
            self.waitingForFree()
    
    def read_map(self):
        self.waitingForFree()
        data = self.read_block(self.CHIP_I2C_ADDR,0x50)
        self.waitingForFree()
        data += self.read_block(self.CHIP_I2C_ADDR,0x51)
        map_data = []
        for i in range(0,len(data),2):
            map_data.append(data[i]<<8|data[i+1])
        return map_data
    def write_map(self,data):
        if len(data) != 22:
            return -1
        self.waitingForFree()
        self.write_block(self.CHIP_I2C_ADDR,0x50,data[:11])
        self.waitingForFree()
        self.write_block(self.CHIP_I2C_ADDR,0x51,data[11:])
        return 0
    
    def driver_version(self):
        self.waitingForFree()
        return self.read(self.CHIP_I2C_ADDR,0x40)

def test():

    focuser = Focuser(1)
    # while focuser.get(Focuser.OPT_FOCUS) < 18000:
    #     focuser.set(Focuser.OPT_FOCUS,focuser.get(Focuser.OPT_FOCUS) + 50)
    # focuser.set(Focuser.OPT_FOCUS,0)
    # focuser.set(Focuser.OPT_FOCUS,10000)
    # focuser.set(Focuser.OPT_MODE,0x01)
    # print("Change mode")
    # print(focuser.get(Focuser.OPT_FOCUS) )
    # print(focuser.get(Focuser.OPT_ZOOM) )

    # focuser.set(Focuser.OPT_FOCUS,2100)
    # print("Get value:",focuser.get(Focuser.OPT_FOCUS) )

    # focuser.set(Focuser.OPT_ZOOM,2100)
    # print("Get value:",focuser.get(Focuser.OPT_ZOOM) )

    # # time.sleep(1.11)
    # print("reset")
    # focuser.reset(Focuser.OPT_FOCUS)

    # # while focuser.isBusy():
    # #     print(focuser.isBusy())
    # #     time(0.01)
    # # print(focuser.isBusy())
    # print("reset")

    # focuser.reset(Focuser.OPT_ZOOM)
    
    # print(focuser.isBusy())
    # print(focuser.read_map())
    # data = [2100, 2101,0,195,200,270,400,340,600,420 ,800,500,1000,610,1200,750,1400,920,1600,1150,1800,1710]
    # focuser.write_map(data)
    # time.sleep(1)
    print(hex(focuser.driver_version()))
    if focuser.driver_version() >= 0x105:
        print(focuser.read_map())
    else :
        print("firmware version too low!")
        sys.exit(0)

pass

if __name__ == "__main__":
    test()