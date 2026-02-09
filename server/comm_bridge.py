import os
import time
import json
import paho.mqtt.client as mqtt
from dotenv import load_dotenv

load_dotenv()

MQTT_BROKER = os.getenv("MQTT_BROKER", "localhost")
MQTT_PORT   = int(os.getenv("MQTT_PORT", 0))
TOPIC_SENSOR = "sensor/data"
TOPIC_MOTOR  = "motor/command"

def on_message(client, userdata, message):
    try:
        # decode sensor data
        # sensor_val = int(message.payload.decode())
        # print(f"sensor value received: {sensor_val}")

        # run core logic
        # if sensor_val > 50:
        #     target_pos = 3000
        # else:
        #     target_pos = 0

        # send motor command
        client.publish(TOPIC_MOTOR, str(target_pos))
        print(f"command send to motor: {target_pos}")

    except ValueError:
        pass

client = mqtt.Client()
client.connect(MQTT_BROKER, MQTT_PORT, 60)

# client.on_message = on_message
# client.subscribe(TOPIC_SENSOR)

# print("Started... listening for sensors")
# client.loop_forever()

while True:
    # testing by hardcoding
    target_id = 2
    target_pos = 1000

    payload = {
        "id": target_id,
        "position": target_pos
    }
    
    client.publish(TOPIC_MOTOR, json.dumps(payload))
    print(f"Sent: {payload}")
    
    time.sleep(3.0)