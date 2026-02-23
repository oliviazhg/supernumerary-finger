import asyncio
import websockets
import json
import random
import math
import time
import os
import paho.mqtt.client as mqtt
from dotenv import load_dotenv

load_dotenv()

PORT = 8765
MQTT_BROKER = os.getenv("MQTT_BROKER", "localhost")
MQTT_TOPIC  = "motor/command"
mqtt_client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
mqtt_client.connect(MQTT_BROKER, 1883, 60)
mqtt_client.loop_start()

async def handle_connection(websocket):
    print(f"React Client Connected")
    
    # send dummy sensor data to React
    async def send_sensor_data():
        try:
            while True:
                t = time.time()
                payload = {
                    "angles": {
                        "j1": math.sin(t * 1.5) * 0.6,
                        "j2": math.sin(t * 1.2) * 0.8,
                        "j3": math.sin(t * 0.9) * 0.4 
                    },
                    "sensors": {
                        "flex": int(45 + math.sin(t) * 20),
                        "force": round(2.0 + math.cos(t) * 1.5, 2)
                    },
                    "myo": {
                        "emg": [random.randint(10, 90) for _ in range(8)]
                    }
                }
                await websocket.send(json.dumps(payload))
                await asyncio.sleep(0.02)
        except websockets.exceptions.ConnectionClosed:
            pass

    # receive manual control commands from React
    async def receive_commands():
        try:
            async for message in websocket:
                try:
                    command = json.loads(message)
                except json.JSONDecodeError:
                    print("Received invalid JSON.")
                    continue 

                if command.get("type") == "control":
                    motor_id = command.get("motor")
                    action = command.get("action")
                    direction = command.get("dir", "forward")                    
                    mqtt_payload = {}

                    if action == "start":
                        # Forward = Max Position, Backward = Min Position
                        target_pos = 0
                        if motor_id == 1:
                            target_pos = 500 if direction == "forward" else -1000
                        elif motor_id == 2:
                            target_pos = 8000 if direction == "forward" else 2000

                        mqtt_payload = {
                            "id": motor_id, 
                            "mode": "move", 
                            "position": target_pos
                        }
                        print(f"-> MQTT: Motor {motor_id} GO {direction.upper()} ({target_pos})")
                        
                    elif action == "stop":
                        # Stop = Tell motor driver to hold current position
                        mqtt_payload = {
                            "id": motor_id, 
                            "mode": "stop"
                        }
                        print(f"-> MQTT: Motor {motor_id} STOP")

                    if mqtt_payload:
                        mqtt_client.publish(MQTT_TOPIC, json.dumps(mqtt_payload))

                elif command.get("type") == "set_mode":
                    new_mode = command.get("mode")
                    print(f"Control mode changed to: {new_mode}")
                    mqtt_client.publish("system/control_mode", new_mode)
                
        except websockets.exceptions.ConnectionClosed:
            pass

    # run tasks concurrently
    await asyncio.gather(send_sensor_data(), receive_commands())

async def main():
    print(f"Starting Finger_OS Server on ws://localhost:{PORT}")
    async with websockets.serve(handle_connection, "localhost", PORT):
        await asyncio.get_running_loop().create_future()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        mqtt_client.loop_stop()
        print("Stopped.")
