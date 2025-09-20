import gpiozero
import Adafruit_DHT
from time import sleep
import I2C_LCD_driver
import requests

# ----------------------------
# 🔹 Blynk Configuration
# ----------------------------
BLYNK_AUTH = "_6_ag02pR10gIt75SFDisljIfkmjAHkO"   # your token
BLYNK_URL = "https://blynk.cloud/external/api"

def blynk_update(pin, value):
    """Send data to Blynk Virtual Pin"""
    url = f"{BLYNK_URL}/update?token={BLYNK_AUTH}&{pin}={value}"
    try:
        r = requests.get(url)
        if r.status_code != 200:
            print(f"⚠ Blynk update failed: {r.text}")
    except Exception as e:
        print(f"❌ Blynk Exception: {e}")

# ----------------------------
# 🔹 Hardware Setup
# ----------------------------
pump = gpiozero.LED(23)       # Water supply
fan = gpiozero.PWMLED(18)     # Cooling fan
red = gpiozero.LED(17)         # Red LED
yellow = gpiozero.LED(27)      # Yellow LED
buzzer = gpiozero.LED(22)     # Example GPIO pin for buzzer (adjust if needed)

lcd = I2C_LCD_driver.lcd()
DHT_SENSOR = Adafruit_DHT.DHT22
DHT_PIN = 4 

HUMIDITY_THRESHOLD = 70 
temp_state = 0
fan_speed = 0

print("🌡 Smart Cooling System Started...")

try:
    while True:
        humidity, temperature = Adafruit_DHT.read_retry(DHT_SENSOR, DHT_PIN)  

        if humidity is not None and temperature is not None:
            # ---------------- LCD ----------------
            lcd.lcd_display_string(f"Temp:{temperature:.1f}C", 1) 
            lcd.lcd_display_string(f"Hum:{humidity:.1f}%", 2)

            # ---------------- Humidity / Pump ----------------
            if humidity > HUMIDITY_THRESHOLD:
                pump.on()
                blynk_update("V4", 1)   # Pump ON
            else:
                pump.off()
                blynk_update("V4", 0)   # Pump OFF

            # ---------------- Temperature / Fan State ----------------
            if temperature >= 50:
                temp_state = 2
            elif 30 <= temperature < 50:
                temp_state = 1
            else:
                temp_state = 0

            match temp_state:
                case 0:  # Cool
                    red.off()
                    yellow.off()
                    fan_speed = 0
                    buzzer.off()
                    blynk_update("V6", 0)   # Red LED OFF
                    blynk_update("V5", 0)   # Yellow LED OFF
                    blynk_update("V2", 0)   # Buzzer OFF
                case 1:  # Warm
                    red.off()
                    yellow.on()
                    fan_speed = 0.5
                    buzzer.off()
                    blynk_update("V6", 0)
                    blynk_update("V5", 1)
                    blynk_update("V2", 0)
                case 2:  # Hot
                    red.on()
                    yellow.off()
                    fan_speed = 1
                    buzzer.on()
                    blynk_update("V6", 1)
                    blynk_update("V5", 0)
                    blynk_update("V2", 1)
                case _:
                    print("⚠ Temperature state error")

            fan.value = fan_speed

            # ---------------- Send Data to Blynk ----------------
            blynk_update("V0", f"{temperature:.1f}")   # Temp
            blynk_update("V1", f"{humidity:.1f}")      # Humidity
            blynk_update("V3", int(fan_speed*100))     # Fan %
            
        else:
            lcd.lcd_display_string("Sensor failure", 1) 
            lcd.lcd_display_string("Retrying...", 2)

        sleep(5)

except KeyboardInterrupt:
    print("🛑 Shutting down...")
    pump.off()
    fan.off()
    red.off()
    yellow.off()
    buzzer.off()
