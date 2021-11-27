# Nov13, 2021, ms
# study-game-coding-timer.py

# pin connections
# color  | LED | button
# Blue   | D2  | D10
# Green  | D3  | D11
# Yellow | D4  | D12

# Airlift
# esp_cs -> D8
# esp_ready -> D7
# esp_reset -> D5


import board
import adafruit_datetime
import time
from adafruit_debouncer import Debouncer
from adafruit_ht16k33.segments import Seg7x4
from digitalio import DigitalInOut, Direction

import busio
import adafruit_requests as requests
import adafruit_esp32spi.adafruit_esp32spi_socket as socket
from adafruit_esp32spi import adafruit_esp32spi

import toggltrack

# Get wifi details and more from a secrets.py file
try:
    from secrets import secrets
except ImportError as e:
    print("Credentials are kept in secrets.py, please add them there!")

# ==================
#    common vars
# ==================
idx2color = {
    0: 'blue',
    1: 'green',
    2: 'yellow'
}

# to link project id in secrets
idx2pid = {
    0: secrets['pid-b'],
    1: secrets['pid-g'],
    2: secrets['pid-y']
}

# fixed description for the time entry
idx2desc = {
    0: 'project b',
    1: 'project g',
    2: 'project y'
}

# =================
#    7 seg vars
# =================
i2c = board.I2C()

# Seg7x4 obj holder
DISPLAYS = [
    {   # blue
        'address': 0x72,  # will be Seg7x4 obj
        'colon': True,
        'brightness': 0.5
    },
    {   # green
        'address': 0x73,  # will be Seg7x4 obj
        'colon': True,
        'brightness': 0.5
    },
    {   # yellow
        'address': 0x74,  # will be Seg7x4 obj
        'colon': True,
        'brightness': 0.5
    }
]

# instantiate Seg7x4 objects
for disp in DISPLAYS:
    disp['address'] = Seg7x4(i2c, disp['address'])
    disp['address'].brightness = disp['brightness']
    disp['address'].print("88:88")


# ===============
#    LED pins
# ===============
LEDS = [
    {   # blue
        'pin': board.D2  # will be DigitalInOut obj
    },
    {   # green
        'pin': board.D3  # will be DigitalInOut obj
    },
    {   # yellow
        'pin': board.D4  # will be DigitalInOut obj
    },
]

# instantiate DigitalInOut obj
for led in LEDS:
    led['pin'] = DigitalInOut(led['pin'])
    led['pin'].direction = Direction.OUTPUT


# ==============
#    buttons
# ==============
BUTTONS = [
    {
        # blue
        'pin': board.D10,  # will be DigitalInOut obj
        'running': False,
        'prev_update': -1.0,
        'delta_total': -1
    },
    {
        # green
        'pin': board.D11,  # will be DigitalInOut obj
        'running': False,
        'prev_update': -1.0,
        'delta_total': -1
    },
    {
        # yellow
        'pin': board.D12,  # will be DigitalInOut obj
        'running': False,
        'prev_update': -1.0,
        'delta_total': -1
    },
]

for btn in BUTTONS:
    btn['pin'] = DigitalInOut(btn['pin'])
    btn['pin'].direction = Direction.INPUT
    # add item
    btn['debouncer'] = Debouncer(btn['pin'], interval=0.05)  # 50 ms


# ==============
#    Airlift
# ==============
print("Airlift part started...")
# pins
esp32_cs = DigitalInOut(board.D8)
esp32_ready = DigitalInOut(board.D7)
esp32_reset = DigitalInOut(board.D5)

spi = busio.SPI(board.SCK, board.MOSI, board.MISO)
esp = adafruit_esp32spi.ESP_SPIcontrol(spi, esp32_cs, esp32_ready, esp32_reset)
requests.set_socket(socket, esp)

if esp.status == adafruit_esp32spi.WL_IDLE_STATUS:
    print("ESP32 found and in idle mode")
print("Firmware vers.", esp.firmware_version)
print("MAC addr:", [hex(i) for i in esp.MAC_address])
# ================================================================= (1)
DISPLAYS[2]['address'].print("--:--")  # yellow display tells status (1)

for ap in esp.scan_networks():
    print("\t%s\t\tRSSI: %d" % (str(ap["ssid"], "utf-8"), ap["rssi"]))
# ================================================================= (2)
DISPLAYS[1]['address'].print("--:--")  # yellow display tells status (2)

print("Connecting to AP...")
while not esp.is_connected:
    try:
        esp.connect_AP(secrets["ssid"], secrets["password"])
    except RuntimeError as e:
        print("could not connect to AP, retrying: ", e)
        continue
print("Connected to", str(esp.ssid, "utf-8"), "\tRSSI:", esp.rssi)
print("My IP address is", esp.pretty_ip(esp.ip_address))
# ================================================================= (3)
DISPLAYS[0]['address'].print("--:--")  # yellow display tells status (3)


# ===================
#    my functions
# ===================
def updateDisplay(display, delta_total):
    run_time = str(adafruit_datetime.timedelta(seconds=delta_total))
    run_time = run_time.rsplit(':', 1)[0]
    if len(run_time) == 4:
        run_time = '0' + run_time
    display['address'].print(run_time)
    print('[debug] run_time is: ' + run_time + ';', ' delta =', delta_total)


# ================
#    main loop
# ================
now_running = -1  # idx in the list
while True:
    now = time.monotonic()
    # update btn status
    for i, btn in enumerate(BUTTONS):
        btn['debouncer'].update()
        if btn['debouncer'].fell:
            if now_running == -1:
                # start timer
                btn['running'] = True
                now_running = i
                btn['prev_update'] = now
                print()
                print('[debug] ' + idx2color[i] + ' timer started.')
                # Note: start time entry on ToggleTrack
                desc = idx2desc[i]
                pid = idx2pid[i]
                entry_id = toggltrack.startTimeEntry(desc, pid,
                                                     secrets['wid'],
                                                     secrets['authB'])
                # ToDo: announce what is started
            elif i == now_running:
                # stop timer
                # Note: stop the time entry
                toggltrack.stopTimeEntry(entry_id, secrets['authB'])
                # ToDo: announce what is stopped
                print('[debug] ' + idx2color[i] + ' timer stopped.')
                print()
                btn['running'] = False
                now_running = -1
                DISPLAYS[i]['colon'] = True
                DISPLAYS[i]['address'].colon = DISPLAYS[i]['colon']
                LEDS[i]['pin'].value = False
            else:
                # 1 is pressed when 2 is running etc. neglect
                msg = '[debug] ' + idx2color[i] + ' pressed while '
                msg += idx2color[now_running] + ' is running. '
                msg += 'This action is voided.'
                print(msg)

    # count up timer if something is running
    if now_running != -1:
        running_btn = BUTTONS[now_running]
        running_display = DISPLAYS[now_running]
        # delta calculation
        if running_btn['delta_total'] == -1:  # for the very first time
            print('[debug] ' + idx2color[now_running] + ' FIRST TIME.')
            delta = 0
            updateDisplay(running_display, delta)  # "0:00" will be displayed
            running_btn['delta_total'] = delta
            running_btn['prev_update'] = now
        else:  # for second time onwards
            delta = now - running_btn['prev_update']

        if delta >= 1:
            running_btn['delta_total'] += delta
            # update display
            updateDisplay(running_display, running_btn['delta_total'])
            # toggle colon
            running_display['colon'] = not running_display['colon']
            running_display['address'].colon = running_display['colon']
            # toggle LED
            LEDS[now_running]['pin'].value = not LEDS[now_running]['pin'].value
            # update prev_update
            running_btn['prev_update'] = now
