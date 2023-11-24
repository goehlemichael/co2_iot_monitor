import os
import json
import time
import ssl
import wifi
import socketpool
import adafruit_requests
import board
import adafruit_scd4x
import microcontroller

# The amount of time between each datapoint in seconds
SEND_DATA_PERIOD = 300
ADAFRUIT_API_URL = "https://io.adafruit.com"
CO2_FEED_URL = "{}/api/v2/{}/feeds/{}/data".format(ADAFRUIT_API_URL,
                                                   os.getenv("AIO_USERNAME"),
                                                   os.getenv("CO2_FEED_NAME")
                                                   )
TEMP_FEED_URL = "{}/api/v2/{}/feeds/{}/data".format(ADAFRUIT_API_URL,
                                                    os.getenv("AIO_USERNAME"),
                                                    os.getenv("TEMP_FEED_NAME")
                                                    )
REL_HUM_FEED_URL = "{}/api/v2/{}/feeds/{}/data".format(ADAFRUIT_API_URL,
                                                       os.getenv("AIO_USERNAME"),
                                                       os.getenv("REL_HUM_FEED_NAME")
                                                       )

i2c = board.I2C()
scd4x = adafruit_scd4x.SCD4X(i2c)

print(f"Connecting to {os.getenv('CIRCUITPY_WIFI_SSID')}")
wifi.radio.connect(os.getenv("CIRCUITPY_WIFI_SSID"),
                   os.getenv("CIRCUITPY_WIFI_PASSWORD")
                   )
print(f"Connected to {os.getenv('CIRCUITPY_WIFI_SSID')}")
print(f"My local IP address: {wifi.radio.ipv4_address}")
pool = socketpool.SocketPool(wifi.radio)
requests = adafruit_requests.Session(pool, ssl.create_default_context())


def send_co2_data(co2_data_point, feed_location):
    payload = {
        "value": co2_data_point
    }
    headers = {
        "Content-Type": "application/json",
        "X-AIO-Key": os.getenv("AIO_KEY")
    }
    try:
        response = requests.post(feed_location, data=json.dumps(payload), headers=headers)
        if response.status_code == 200:
            print("CO2 data sent successfully! {}".format(response.content))
        else:
            print("Failed to send CO2 data. {}".format(response.content))
    except wifi.WiFiError as error:
        print("WiFi error occurred:", str(error))
        print("Reconnecting to WiFi...")
        wifi.radio.connect(os.getenv("CIRCUITPY_WIFI_SSID"), os.getenv("CIRCUITPY_WIFI_PASSWORD"))
        print("Connected to WiFi.")
        print(f"My IP address: {wifi.radio.ipv4_address}")
    except adafruit_requests.RequestError as error:
        print("Request error occurred:", str(error))
        print("Skipping request.")


while True:
    try:
        scd4x.measure_single_shot()
        print("Waiting for sensor data..")
        if scd4x.data_ready:
            co2_data = scd4x.CO2
            temp_data = scd4x.temperature
            rel_hum_data = scd4x.relative_humidity

            send_co2_data(co2_data, CO2_FEED_URL)
            send_co2_data(temp_data, TEMP_FEED_URL)
            send_co2_data(rel_hum_data, REL_HUM_FEED_URL)

            time.sleep(SEND_DATA_PERIOD)
    except Exception as e:
        print("An error occurred:", str(e))
        microcontroller.reset()
