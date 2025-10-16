from machine import Pin, RTC
from patterns.finish import Finish
from patterns.paused import Paused
from patterns.progress import Progress
from utime import sleep
from modules.mqtt_as import MQTTClient, config
# from modules.umqtt.simple import MQTTClient
import ssl
import time
import gc
import json
import neopixel
import machine
import network
import asyncio
from patterns.idle import Idle
from patterns.error import Error
from patterns.prepare import Prepare

with open('settings.json', 'r') as f:
    settings = json.load(f)

debug_led = Pin('LED', Pin.OUT)

serial = settings.get("serial", "none")
num_leds = settings.get("num_leds", 64)
led_pin = settings.get("led_pin", 0)
mqtt_ip = settings.get("mqtt_ip", "192.168.1.117")
current_pattern = Idle()
frame_count = 0

hms = []
printer_chamber_light_on = False
gcode = "IDLE"
progress = 0
stage = 0

main_thread_rgb_lock = True

start_time = time.time()

np = neopixel.NeoPixel(machine.Pin(led_pin), num_leds)

wlan = network.WLAN(network.STA_IF)
wlan.active(True)
def connect_to_wifi():
    if not wlan.isconnected():
        print('Connecting to network: ' + settings.get("ssid", "") + ":" + settings.get("wifi_password", ""))
        wlan.connect(settings.get("ssid", ""), settings.get("wifi_password", ""))
        sleep(5)
        for _ in range(2):
            if wlan.isconnected():
                break
            wlan.connect(settings.get("ssid", ""), settings.get("wifi_password", ""))
            sleep(5)
        if not wlan.isconnected():
            return False
    print('Network config:', wlan.ifconfig())
    return True

if not connect_to_wifi():
    print("Failed to connect to WiFi, restarting...")
    for _ in range(5):
        debug_led.toggle()
        for i in range(num_leds):
            np[i] = (255, 0, 0)
        np.write()
        sleep(1.0)
        for i in range(num_leds):
            np[i] = (0, 0, 0)
        np.write()
        sleep(1.0)
    machine.reset()

def sub_cb(_, msg, __):
    data = msg.decode('utf-8')
    if "print" not in data:
        print(f"Encountered message with size of: {len(data)}, but print object not present, ignoring.")
    else:
        print(f"Got message with size of: {len(data)}, parsing.")
    try:
        data_dict = json.loads(data)
    except:
        print("Failed to parse JSON")
        return

    try:
        light_status = data_dict["print"]["lights_report"][0]["mode"]
        global printer_chamber_light_on 
        if light_status == "on":
            printer_chamber_light_on = True
        else:
            printer_chamber_light_on = False
    except KeyError:
        pass

    try:
        global hms
        hms = data_dict["print"]["hms"]
    except KeyError:
        pass

    try:
        global gcode
        gcode = data_dict["print"]["gcode_state"]
    except KeyError:
        pass

    
    try:
        global progress
        progress = int(data_dict["print"]["mc_percent"])
    except KeyError:
        pass

    try:
        global stage
        stage = int(data_dict["print"]["stg_cur"])
    except KeyError:
        pass

    del data_dict
    del data
    gc.collect()

async def update_pattern():
    while True:
        pattern_changed = False
        global main_thread_rgb_lock
        if main_thread_rgb_lock:
            continue
        global current_pattern
        if len(hms) > 0 or gcode == "FAILED" and not isinstance(current_pattern, Error):
            current_pattern = Error()
            pattern_changed = True
        elif gcode == "RUNNING" and stage == 0 and not isinstance(current_pattern, Progress):
            current_pattern = Progress()
            pattern_changed = True
        elif gcode == "IDLE" and printer_chamber_light_on and not isinstance(current_pattern, Idle):
            current_pattern = Idle()
            pattern_changed = True
        elif gcode == "IDLE" and not printer_chamber_light_on:
            current_pattern = None
            pattern_changed = True
        elif gcode == "PAUSE" and not isinstance(current_pattern, Progress):
            # Orange progress bar
            current_pattern = Paused()
            pattern_changed = True
        elif gcode == "FINISH" and printer_chamber_light_on and not isinstance(current_pattern, Finish):
            current_pattern = Finish()
            pattern_changed = True
        elif stage != 0 or gcode == "PREPARE" and not isinstance(current_pattern, Prepare):
            current_pattern = Prepare() 
            pattern_changed = True

        if pattern_changed and current_pattern is not None:
            global num_leds
            current_pattern.num_leds = num_leds
            print("Pattern changed")

        if current_pattern:
            global progress
            current_pattern.update(time.time() - start_time, progress / 100.0)
            if current_pattern.all_same:
                color = current_pattern.at(0)
                # Don't rewrite the pixels if the color hasn't changed
                if np[0] != color:    
                    for i in range(num_leds):
                        np[i] = color
                    np.write()
            else:
                for i in range(num_leds):
                    color = current_pattern.at(i)
                    np[i] = color
                np.write()
        else:
            for i in range(num_leds):
                np[i] = (0, 0, 0)
            np.write()

        global frame_count
        frame_count += 1
        print("Pixel 0:", np[0])
        # print("Memory:", gc.mem_free(), "Frames:", frame_count)
        await asyncio.sleep_ms(10)

context = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
context.verify_mode = ssl.CERT_NONE

topic = f'device/{serial}/report'

config["server"] = mqtt_ip
config["port"] = 8883
config["wifi_pw"] = settings.get("wifi_password", "")
config["ssid"] = settings.get("ssid", "")
config["ssl"] = context
config["password"] = settings.get("lan_access_code", "")
config["user"] = 'bblp'
config["subs_cb"] = sub_cb
config["keepalive"] = 3600

async def main():
    client = MQTTClient(config)
    try:
        await client.connect()
        print("Finished connecting to MQTT")
    except Exception as e:
        print(e)
        for _ in range(5):
            debug_led.toggle()
            await asyncio.sleep(1.0)
        machine.soft_reset()
    await client.subscribe(topic, 0)
    await client.publish(f'device/{serial}/request', '{"pushing":{"sequence_id": "0", "command": "pushall"}}')
    asyncio.create_task(update_pattern())
    debug_led.on()
    while True:
        gc.collect()
        global main_thread_rgb_lock
        if not client.isconnected():
            global main_thread_rgb_lock
            main_thread_rgb_lock = True
            debug_led.off()
            for i in range(num_leds):
                np[i] = (255, 0, 0)
            np.write()
        elif main_thread_rgb_lock:
            global main_thread_rgb_lock
            main_thread_rgb_lock = False
            debug_led.on()
        else:
            global frame_count
            print("Memory:", gc.mem_free(), "Frames:", frame_count)
            print("Pattern:", type(current_pattern).__name__ if current_pattern else "None", "GCode:", gcode, "Progress:", progress, "Chamber Light:", printer_chamber_light_on, "Stage:", stage)
            frame_count = 0
        await asyncio.sleep(1.0)

# async def main():
#     client = MQTTClient(server=mqtt_ip, client_id="printer-rgb", port=8883, user='emqx', password='public', ssl=context)
#     client.set_callback(sub_cb)
#     try:
#         client.connect()
#         print("Finished connecting to MQTT")
#     except Exception as e:
#         print(e)
#         # machine.soft_reset()
#     asyncio.create_task(update_pattern())
#     client.subscribe(topic, 0)
#     client.publish(f'device/{serial}/request', '{"pushing": {"sequence_id": "0","command": "pushall","version": 1,"push_target": 1}}')
#     # await asyncio.sleep(1.0)

#     while True:
#         global frame_count
#         print("Memory:", gc.mem_free(), "Frames:", frame_count)
#         frame_count = 0
#         client.check_msg()
#         await asyncio.sleep(1.0)

try:
    asyncio.run(main())
except:
    debug_led.off()

