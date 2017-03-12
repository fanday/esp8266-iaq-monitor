import machine
import micropython
import ujson
import utime
import ustruct
import dht
import ubinascii
import gc
from machine import Timer
import ssd1306
import network
from machine import WDT


# ESP8266 ESP-12 modules have blue, active-low LED on GPIO2, replace
# with something else if needed.
#led = machine.Pin(2, machine.Pin.OUT, value=1)
# Default MQTT server to connect to
#SERVER = "183.230.40.39"
            
def pack_data(tmp,hum,voc):
    time = utime.localtime()
    print(time)
    h = time[3]+8
    if h >= 24:
        h = h-24
    now = "%d-%02d-%02d %02d:%02d:%02d"%(time[0],time[1],time[2],h,time[4],time[5])
    print(now)
    data = ujson.dumps({"datastreams":[{"id":"temperature", "datapoints":[{"at":now, "value":tmp}]},{"id":"humidity", "datapoints":[{"at":now, "value":hum}]},{"id":"voc", "datapoints":[{"at":now, "value":voc}]}]})
    print(data)
    gc.collect()
    return data
    #datafmt = "BBB%ds"%len(data)
    #print(datafmt)
    #senddata = ustruct.pack(datafmt, 1,0,len(data), data)
    #print(senddata)
    #return senddata



def get_tmp_hum():
    d = dht.DHT11(machine.Pin(5))
    d.measure()
    tmp = d.temperature()
    hum = d.humidity()
    print(tmp)
    print(hum)
    gc.collect()
    return (tmp,hum)

def get_voc():
    voc = 0.0
    voc_dev = machine.I2C(
    scl = machine.Pin(14), sda = machine.Pin(12), freq = 50000)
    print(voc_dev.scan())
    #voc_dev.init(scl = machine.Pin(14), sda = machine.Pin(12), freq = 100000)
    buf = voc_dev.readfrom(47, 4, True)
    #print(ubinascii.hexlify(buf, ))
    fmt = '>BHB'
    addr,ppm,chk_val = ustruct.unpack(fmt,buf)
    #print (addr,ppm, chk_val)
    if ppm == 65535:
        return None
    voc = ppm*0.1
    print(voc)
    gc.collect()
    return voc


i2c = machine.I2C(scl = machine.Pin(4), sda = machine.Pin(2), freq=100000)
oled = ssd1306.SSD1306_I2C(128, 64, i2c)
oled.poweron()
oled.init_display()
count = 0
wdt = WDT()

def general_display():
    global oled
    global count
    count=count+1
    oled.text('IAQ:'+str(count),1,1)
    wlan = network.WLAN(network.STA_IF)
    ipconfig = wlan.ifconfig()
    oled.text('I:'+ipconfig[0],0,36)
    oled.text('pwd:123456',0,45)
    host = ipconfig[2]
    oled.text('H:'+host, 0, 54)
    gc.collect()

def send_data(addr,data):
    global wdt
    from usocket import *
    try:
        client = socket(AF_INET, SOCK_STREAM)
        client.settimeout(1)
        client.connect(addr)
        client.sendall(data)
        wdt.feed()
        gc.collect()
        return True
    except MemoryError as e:
        print(e)
        pin = machine.Pin(9, machine.Pin.OUT)
        return False
    except Exception as e:
        print(e)
        #chip reset
        pin = machine.Pin(9, machine.Pin.OUT)
        return False
    finally:
        pass
        #pin = machine.Pin(9, machine.Pin.OUT)
        return False

def timer_cb(t = None):
    global oled
    tmp,hum = get_tmp_hum()
    voc = get_voc()
    if voc == None:
        return
    data = pack_data(tmp,hum,voc)
    oled.fill(0)
    general_display()
    oled.text('VOC(ppm):'+str(voc),1,9)
    oled.text('Temp(C):'+str(tmp),1,18)
    oled.text('Hum(%):'+str(hum), 1, 27)
    oled.show()
    host =  wlan = network.WLAN(network.STA_IF)
    ipconfig = wlan.ifconfig()
    host = ipconfig[2]
    send_data((host,9000), data)
    gc.collect()

def do_connect_hostspot():
    sta_if = network.WLAN(network.STA_IF)
    retry = 0
    if not sta_if.isconnected():
        print('connecting to network...')
        sta_if.active(True)
        sta_if.connect('iaq-server', '123456@iaq')
        while not sta_if.isconnected():
            utime.sleep(1)
            retry = retry +1
            #if retry >= 3:
                #break
        print('network config:', sta_if.ifconfig())
    #import ntptime
    #import utime
    #ntptime.settime()
    #print(utime.localtime())
    gc.collect()
    
def main():
    #webrepl.start()
    # Subscribed messages will be delivered to this callback 
    try:
        #webrepl.start()
        #c = MQTTClient(CLIENT_ID, server,6002,username,password)
        #c = MQTTClient("esp8266", server,10008)
       
        #tim = Timer(-1)
        #tim.init(period=10000, mode=Timer.PERIODIC, callback=timer_cb)
        while 1:
            #machine.idle()
            try:
                do_connect_hostspot()
                timer_cb()
                utime.sleep(60)
                gc.collect()
            except Exception as e:
                print(e)
                #chip reset
                pin = machine.Pin(9, machine.Pin.OUT)
            finally:
                pass
    except Exception as e:
        print(e)
    finally:
        pass

main()
