import utime
from machine import I2C, Pin, SPI
import st7789
from ws2812 import WS2812

spi = SPI(0, baudrate=40000000, polarity=1, phase=0, bits=8, endia=0, sck=Pin(6), mosi=Pin(8))

display = st7789.ST7789(spi, 240, 240, reset=Pin(11, func=Pin.GPIO, dir=Pin.OUT), dc=Pin(7, func=Pin.GPIO, dir=Pin.OUT))

display.init()

# I2C通信初始化
i2c = I2C(0, sda=Pin(9), scl=Pin(10), freq=40000)
i2c_add = 0x5B
i2c = I2C(0, sda=Pin(9), scl=Pin(10), freq=40000)
devices = i2c.scan()  # 扫描I2C总线上的设备
print("I2C devices found:", devices)

# WS2812 LED初始化
chain = WS2812(spi_bus=1, led_count=64)

# 定义LED数据列表
led_data = [(125, 125, 125)] * 64  # 将LED初始颜色设置为白色

class Bme:
    def __init__(self):
        self.P = 0
        self.Temp = 0
        self.Hum = 0
        self.Alt = 0

bme = Bme()

def setup():
    utime.sleep(0.001)

start_time = utime.time()

def loop():
    while True:
        Lux = get_lux()  # 获取光照强度值
        get_bme()

        # 根据光照强度值改变LED的亮度
        if Lux / 100 <= 200:
            num_leds = 64  # 光照强度小于等于200lux时，亮64个灯珠
        elif Lux / 100 <= 500:
            num_leds = 48  # 光照强度大于200lux，小于等于500lux时，亮56个灯珠
        else:
            num_leds = 32  # 光照强度大于500lux时，亮48个灯珠

        brightness = 1 - Lux / 1000  # 将光照强度值映射到LED的亮度范围
        for i in range(len(led_data)):
            if i < num_leds:
                r = int(125 * brightness)
                g = int(125 * brightness)
                b = int(125 * brightness)
                led_data[i] = (r, g, b)
            else:
                led_data[i] = (0, 0, 0)  # 关闭未亮灯珠

        chain.show(led_data)  # 更新LED的亮度

        # 在ST7789屏幕上显示温度、湿度
        display.fill(st7789.color565(0, 0, 0))
        display.draw_string(0, 0, 'T : {:.2f} C'.format(bme.Temp / 100), color=st7789.color565(66, 133, 244), bg=st7789.color565(0, 0, 0), size=3, vertical=False, rotate=st7789.ROTATE_0, spacing=1)
        display.draw_string(0, 40, 'H : {:.2f} %'.format(bme.Hum / 100), color=st7789.color565(66, 133, 244), bg=st7789.color565(0, 0, 0), size=3, vertical=False, rotate=st7789.ROTATE_0, spacing=1)

        current_time = utime.time()
        elapsed_time = current_time - start_time
        if elapsed_time >= 3000:
            display.draw_string(60, 100, 'break', color=st7789.color565(66, 133, 244), bg=st7789.color565(0, 0, 0), size=4, vertical=False, rotate=st7789.ROTATE_0, spacing=1)
            chain.show([])
            break  # 结束循环
        else:
            utime.sleep(0.2)

def get_lux():
    data = bytearray(10)
    data_16 = bytearray(2)
    data = iic_read(0x00, data, 4)
    data_16 = [(data[0] << 8) | data[1], (data[2] << 8) | data[3]]
    Lux = ((data_16[0]) << 16) | data_16[1]
    return Lux

def get_bme():
    data = bytearray(10)
    data_16 = bytearray(2)
    data = iic_read(0x04, data, 10)
    bme.Temp = (data[0] << 8) | data[1]
    data_16 = [(data[2] << 8) | data[3], (data[4] << 8) | data[5]]
    bme.P = ((data_16[0]) << 16) | data_16[1]
    bme.Hum = (data[6] << 8) | data[7]
    bme.Alt = (data[8] << 8) | data[9]

def iic_read(reg, data, length):
    utime.sleep_us(10)
    if length > 4:
        data = i2c.readfrom_mem(i2c_add, reg, 10)
    else:
        data = i2c.readfrom_mem(i2c_add, reg, 4)
    return data

setup()
loop()
