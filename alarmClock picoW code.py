from machine import Pin, I2C, ADC, PWM
import time
from lcd1602 import LCD
from ds3231_gen import DS3231

#setup
but1 = Pin(15, Pin.IN, Pin.PULL_DOWN)
but2 = Pin(14, Pin.IN, Pin.PULL_DOWN)
but3 = Pin(13, Pin.IN, Pin.PULL_DOWN)
redButton = Pin(12, Pin.IN, Pin.PULL_DOWN)
potent = ADC(Pin(28))
buzzer = PWM(Pin(5))
buzzer.freq(1000)
i2c_ds = I2C(0, scl=Pin(17), sda=Pin(16))
rtc = DS3231(i2c_ds)

#other setup
alarm = None
timer = None


class redButton_special(Exception):  # custom error to use to leave nested loops with try/except
    pass

def lcd_start():  #LCD setup
    lcd = LCD(sda=2, scl=3, I2C=1, addr=0x3F) # initializing class with sda, scl, and I2C channel
    lcd.offlight()
    return lcd

def file_manager(clock_data):
    with open("/projects/alarmClock/alarm_manager.txt", "a") as f:
        if isinstance(clock_data, dict):
            alarm_str = f"alarm,{clock_data['hour']},{clock_data['minute']}"
            f.write(f"{alarm_str}|")
        if isinstance(clock_data, list):
            timer_str = f"timer,{timer_hour},{timer_minute},{timer_second},{timer},{timerSecond}"
            f.write(f"{timer_str}|")        
    return
    
def set_alarm():
    alarm = {"hour":0, "minute":0}
    while not (but2.value() or but3.value()):
        try:
            lcd.write(0,0,"Waiting to set")
            time.sleep(0.1)
        except: pass
    try: lcd.clear()
    except: pass
    while redButton.value() != True:
        while not (but2.value() or but3.value()):
            if redButton.value() == True: return alarm
            time.sleep(0.01)
        try: lcd.clear()
        except: pass
        if but2.value() == True:
            if alarm["hour"] == 23:
                alarm["hour"] = 0
            else:
                alarm["hour"] += 1
        if but3.value() == True:
            if alarm["minute"] == 59:
                alarm["minute"] = 0
            else:
                alarm["minute"] += 1
        try:
            lcd.write(0,0,f"alarm: {alarm['hour']}:{alarm['minute']}")
            time.sleep(0.05)
        except: pass
    return alarm

def set_timer():
    timer = {"minute":0, "second":0}
    time.sleep(0.5)
    while not (but1.value() or but2.value() or but3.value()):
        try:
            lcd.write(0,0,"Waiting to set")
            time.sleep(0.1)
        except: pass
    try: lcd.clear()    
    except: pass
    while redButton.value() != True:
        while not (but1.value() or but2.value() or but3.value()):
            if redButton.value() == True: break
            time.sleep(0.01)
        try: lcd.clear()
        except: pass
        if but1.value() == True and timer["second"] != 60: timer["second"] += 5
        elif but1.value() == True and timer["second"] == 60:
            timer["minute"] += 1
            timer["second"] = 0
        if but2.value() == True and timer["minute"] != 0: timer["minute"] -= 1
        if but3.value() == True: timer["minute"] += 1
        try:
            lcd.write(0,0,f"timer:{timer['minute']}min {timer['second']}sec")
            time.sleep(0.05)
        except: pass
    current_time = rtc.get_time()
    c_hour, c_minute, c_second = current_time[3], current_time[4], current_time[5]
    timer_second = c_second
    timer_minute = c_minute
    timer_hour = c_hour
    if c_second + timer["second"] < 60:
        timer_second = c_second + timer["second"]
    elif c_second + timer["second"] >= 60:
        if timer_minute < 59:
            timer_minute = timer_minute + 1
        else:
            timer_hour += 1
            timer_minute = 0      
        timer_second = (timer_second + timer["second"]) - 60
    if timer_minute + timer["minute"] < 60:
        timer_minute += timer["minute"]
    else:
        for i in range(timer["minute"]):
            if timer_minute < 59:
                timer_minute += 1
            else:
                timer_hour += 1
                timer_minute = 0
    return timer_hour,timer_minute,timer_second, timer["minute"],timer["second"] #return time that sets timer off


def alarm_ring():
    potent_value = potent.read_u16()/10
    alarm_scale = 0.1
    while redButton.value() != 1:
        if alarm_scale >= 1: alarm_scale = 1
        buzzer.duty_u16(int(potent_value * alarm_scale))
        time.sleep(0.1)
        buzzer.duty_u16(0)
        time.sleep(0.1)
        alarm_scale += 0.005
    return 
    
# Load alarm data at boot-up
with open("/projects/alarmClock/alarm_manager.txt", "r") as f:
    saved_alarms = f.read().split("|")
if len(saved_alarms) > 1:
    try:
        lcd = lcd_start()
        lcd.openlight()
        lcd.write(0,0,"Reload Data?")
        lcd.write(0,1,"Btn1/2:= Y/N")
        while not (but1.value() or but2.value()):
            time.sleep(0.1)
        if but1.value():
            for item in reversed(saved_alarms):  # go through each item in saved alarms (reversed holds most recent), initializing only the first alarm and timer
                item = item.split(",")
                if item[0] == "alarm":
                    if alarm == None:
                        alarm = {}
                        alarm["hour"] = int(item[1])
                        alarm["minute"] = int(item[2])
                if item[0] == "timer":
                    if timer == None:
                        timer_hour = int(item[1])
                        timer_minute = int(item[2])
                        timer_second = int(item[3])
                        timer = int(item[4])
                        timerSecond = int(item[5])
        if but2.value():
            with open("/projects/alarmClock/alarm_manager.txt", "w") as f:
                pass
        lcd.clear()
        lcd.offlight()
    except:
        with open("/projects/alarmClock/alarm_manager.txt", "w") as f:
            pass
        
        
while True:  # Infinite loop
    time.sleep(0.05)
    try:
        lcd.offlight()
    except:
        try:
            lcd = lcd_start()
        except:
            pass
    try:  # the whole but1 loop
        if but1.value() == True: #check time, set alarm, or set timer, and handle alarm/timer detection and ring
            but1StartTime = time.ticks_ms()
            while but1.value() == True:
                time.sleep(0.1)
                if redButton.value(): # if redButton is pressed at the same time
                    print("button 1 and redButton pressed together!")
                    # some special code, new features
                    # Maybe access weather api to obtain weather info?
                    
                    raise redButton_special # exists the whole but1 loop
                    
                    
            but1TimeDiff = time.ticks_diff(time.ticks_ms(),but1StartTime)
            if 0 <= but1TimeDiff <= 500: #check time
                current_time = rtc.get_time()
                c_hour, c_minute, c_second = current_time[3], current_time[4], current_time[5]
                try:
                    lcd.openlight()
                    lcd.write(0,0,f"Time= {c_hour}:{c_minute}:{c_second}")
                    if timer != None: lcd.write(0,1,f"Timer: {timer_hour}:{timer_minute}:{timer_second}")
                    if alarm != None and timer == None: lcd.write(0,1,f"Alarm {alarm['hour']}:{alarm['minute']}")
                    time.sleep(4)
                    lcd.clear()
                    lcd.offlight()
                except: pass
            if 500 <= but1TimeDiff <= 1000: #alarm
                alarm = set_alarm()
                file_manager(alarm)
                try:
                    lcd.openlight()
                    lcd.write(0,0,f"Alarm: {alarm['hour']}:{alarm['minute']}")
                    time.sleep(2)
                    lcd.clear()
                    lcd.offlight()
                except: pass
            if 1000 <= but1TimeDiff <= 4000: #timer
                timer_hour, timer_minute, timer_second, timer, timerSecond = set_timer()
                file_manager([timer_hour, timer_minute, timer_second, timer, timerSecond])
                try:
                    lcd.openlight()
                    lcd.clear()
                    lcd.write(0,0,"Time left:")
                    lcd.write(0,1,f"{timer}mins {timerSecond}secs")
                    time.sleep(2)
                    lcd.clear()
                    lcd.offlight()
                except: pass
    except redButton_special as e:
        print("redButton_condition triggered exit")
        
    if alarm != None: # checks if current time is alarm time
        current_time = rtc.get_time()
        c_hour, c_minute = current_time[3], current_time[4]
        if (c_hour, c_minute) == (alarm["hour"], alarm["minute"]):
            alarm_ring()
            current_time = rtc.get_time()
            c_hour, c_minute = current_time[3], current_time[4]
            if c_minute + 5 < 55: alarm["minute"] = c_minute + 5
            else:
                for i in range(5):
                    if c_minute + 1 < 60:
                        alarm["minute"] = c_minute + 1
                        c_minute += 1
                    else:
                        if c_hour + 1 < 24:
                            alarm["hour"] = c_hour + 1
                        else:
                            alarm["hour"] = 0
    if timer != None: # check timer time left.
        current_time = rtc.get_time()
        c_hour, c_minute, c_second = current_time[3], current_time[4], current_time[5]
        if timer_hour < c_hour:
            alarm_ring()
            timer = None
        if timer_minute < c_minute and timer_hour == c_hour:
            alarm_ring()
            timer = None
        if timer_second < c_second and timer_minute == c_minute:
            alarm_ring()
            timer = None
    if redButton.value() == True:  # Handles file reset and time reset (to computer local time)
        redBut_start_time = time.ticks_ms()
        while redButton.value():
            time.sleep(0.1)
        redButton_timeDiff = time.ticks_diff(time.ticks_ms(),redBut_start_time)
        
        if 0 <= redButton_timeDiff <= 500:   # Availible for assignment.  Could be related to another file which holds schedueling data...
            pass                             # Also could import schedule information that I set elsewhere onto alarm, to remind me for tasks. 
            
        if 500 <= redButton_timeDiff <= 3000: # reset everything
            alarm = None
            timer = None
            with open("/projects/alarmClock/alarm_manager.txt", "w") as f:
                pass
            try:
                lcd.openlight()
                lcd.write(0,0,"Reset")
                time.sleep(2)
                lcd.clear()
                lcd.offlight()
            except:
                pass
        if 3000 <= redButton_timeDiff <= 6000:
            rtc.set_time() #reset RTC to computer local time
            try:
                lcd.openlight()
                lcd.write(0,0,"Time set")
                time.sleep(2)
                lcd.clear()
                lcd.offlight()
            except:
                pass
            

           
        

    
    
            

        
        
        
