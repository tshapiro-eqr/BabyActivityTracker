from google import googleSheetsUtils
from machine import Pin
import urequests as requests
import gc
import time
import ntptime
import secrets
import network

# enable garbage collection
gc.enable()

# timestamp string
def now():
    ntptime.settime()
    OFFSET = -6 * 3600
    ct = time.localtime(time.time() + OFFSET)
    ct_fixed = []
    for i in ct:
        if len(str(i))<2:
            ct_fixed.append('0'+str(i))
        else:
            ct_fixed.append(str(i))

    return '{}-{}-{} {}:{}:{}'.format(*ct_fixed[0:6])

def write_to_sheet(workbook_id, sheet_name):
    # post all important info to Google Sheets
    gs = googleSheetsUtils.gsheets(REFRESH_TOKEN)
    message = [now()]

    # get cells max
    r = gs.get_cells(workbook_id, f'{sheet_name}!I2')
    next_cell = int(r)+1
    next_cell_range = f'{sheet_name}!A{next_cell}'
    # write to next cell
    r = gs.write_cells(message, workbook_id, next_cell_range)
    return r.json()

# internet
wlan = network.WLAN(network.STA_IF)
wlan.active(True)
if ~wlan.isconnected():
    wlan.connect(secrets.WIFI_NAME, secrets.WIFI_PWD)
elif wlan.isconnected():
    print('Connected to {}'.format(secrets.WIFI_NAME))

# config
CLIENT_ID = secrets.CLIENT_ID
CLIENT_SECRET = secrets.CLIENT_SECRET
REFRESH_TOKEN = secrets.REFRESH_TOKEN
WORKBOOK_ID = secrets.WORKBOOK_ID


buttons = list([Pin(i, Pin.IN, Pin.PULL_UP) for i in range(0,8)])
leds = list([Pin(i, Pin.OUT, value=0) for i in range(8,16)])
button_default_value = 1
board_led = Pin('LED', Pin.OUT)
board_led.off()

sheets = {
    0:'Pee',
    1:'Poop',
    2:'Pump',
    3:'Bottle',
    4:'Breast',
    5:'Special',
    6:'Vitamin-D',
    7:'Etc'
}

led_map = {
    0:0,
    1:1,
    2:3,
    3:4,
    4:5,
    5:6,
    6:7,
    7:2
}


def flash_button(sheet_id):
    leds[led_map[sheet_id]].off()
    time.sleep(0.25)
    for i in range(0,3):
        leds[led_map[sheet_id]].on()
        time.sleep(0.25)
        leds[led_map[sheet_id]].off()
        time.sleep(0.25)


while True:
    try:
        if any([button.value()!=button_default_value for button in buttons]):
            current_pin = [i for i in buttons if i.value() == 0][0]
            sheet_id = buttons.index(current_pin)
            leds[led_map[sheet_id]].on()
            sheet_name = sheets[sheet_id]
            print(f'writing record to {sheet_name}')
            try:
                return_json = write_to_sheet(WORKBOOK_ID, sheet_name)
                print(f'record written to {sheet_name}')
                leds[led_map[sheet_id]].off()
            except Exception as exc:
                with open('log.txt','a') as f:
                    f.write(f'{now()}: Error writing to {sheet_name}: {exc.args[0]}\n')
                    time.sleep(0.5)
                    f.close()
                    flash_button(sheet_id)
                pass
        time.sleep(0.1)
    except Exception as exc:
        with open('log.txt','a') as f:
            f.write(f'{now()}: Error in main function: {exc.args[0]}\n')
            time.sleep(0.5)
            f.close()
            flash_button(6)
        pass
            



