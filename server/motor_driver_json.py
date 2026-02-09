import time
import json
import os
import paho.mqtt.client as mqtt
from dynamixel_sdk import *
from dotenv import load_dotenv

load_dotenv()

# MQTT config
MQTT_BROKER = os.getenv("MQTT_BROKER", "localhost")
MQTT_PORT   = int(os.getenv("MQTT_PORT", 0))
MQTT_TOPIC = "motor/command"

# motor config
DXL_ID_1 = 1           # Left Motor?
DXL_ID_2 = 2           # Right Motor?
BAUDRATE = 1000000
DEVICENAME = 'COM3' # /dev/ttyUSB0 on Pi
PROTOCOL_VERSION = 2.0

ADDR_OPERATING_MODE = 11
ADDR_TORQUE_ENABLE = 64
ADDR_GOAL_POSITION = 116
ADDR_PRESENT_POSITION = 132
ADDR_PROFILE_ACCELERATION = 108
ADDR_PROFILE_VELOCITY = 112

portHandler = PortHandler(DEVICENAME)
packetHandler = PacketHandler(PROTOCOL_VERSION)

def get_signed_position(unsigned_val):
    if unsigned_val > 2147483647:
        return unsigned_val - 4294967296
    return unsigned_val

def setup_motors():
    if portHandler.openPort():
        print("Succeeded to open the port")
    else:
        print("Failed to open the port")
        quit()

    # set baud rate
    if portHandler.setBaudRate(BAUDRATE):
        print("Succeeded to change the baudrate")
    else:
        print("Failed to change the baudrate")
        quit()

    # enable torque
    for motor_id in [DXL_ID_1, DXL_ID_2]:
        packetHandler.write1ByteTxRx(portHandler, motor_id, ADDR_TORQUE_ENABLE, 0)
        packetHandler.write1ByteTxRx(portHandler, motor_id, ADDR_OPERATING_MODE, 4)
        packetHandler.write4ByteTxRx(portHandler, motor_id, ADDR_PROFILE_ACCELERATION, 50)
        packetHandler.write4ByteTxRx(portHandler, motor_id, ADDR_PROFILE_VELOCITY, 300)
        dxl_comm_result, dxl_error = packetHandler.write1ByteTxRx(portHandler, motor_id, ADDR_TORQUE_ENABLE, 1)
        
        if dxl_comm_result != COMM_SUCCESS:
            print(f"ID {motor_id} Setup Error: {packetHandler.getTxRxResult(dxl_comm_result)}")
        else:
            print(f"Dynamixel {motor_id} Ready (Extended Mode)")

def move_motor(motor_id, position):
    if position < 0:
        position = 4294967296 + position

    # goal position
    dxl_comm_result, dxl_error = packetHandler.write4ByteTxRx(portHandler, motor_id, ADDR_GOAL_POSITION, position)
    
    if dxl_comm_result != COMM_SUCCESS:
        print(f"move motor {motor_id} Comm Error: {packetHandler.getTxRxResult(dxl_comm_result)}")
    elif dxl_error != 0:
        print(f"move motor {motor_id} Packet Error: {packetHandler.getRxPacketError(dxl_error)}")

def stop_motor(motor_id):
    # stops motor by reading current position and setting it as goal
    current_pos, _, _ = packetHandler.read4ByteTxRx(portHandler, motor_id, ADDR_PRESENT_POSITION)
    packetHandler.write4ByteTxRx(portHandler, motor_id, ADDR_GOAL_POSITION, current_pos)
    print(f"Motor {motor_id} Halted at {current_pos}")

def shutdown_motors():
    # disable torque before quitting
    for motor_id in [DXL_ID_1, DXL_ID_2]:
        packetHandler.write1ByteTxRx(portHandler, motor_id, ADDR_TORQUE_ENABLE, 0)
    portHandler.closePort()
    print("motors shutdown")

def on_message(client, userdata, msg):
    try:
        payload = json.loads(msg.payload.decode())
        
        target_id = int(payload['id'])
        target_position = int(payload['position'])
        
        print(f"motor id: {target_id}, position: {target_position}")

        # define physical bounds
        if target_id == 1:
            print('motor 1 found')
            if target_position < -1000:
                target_position = -1000
            if target_position > 500: 
                target_position = 500

        move_motor(target_id, target_position)

        time.sleep(2.0) 
        dxl_present_position, _, _ = packetHandler.read4ByteTxRx(portHandler, target_id, ADDR_PRESENT_POSITION)
        real_position = get_signed_position(dxl_present_position)
        print(f"[motor id:{target_id}] reached: {real_position}")

    except json.JSONDecodeError:
        print("Error: Message was not valid JSON")
    except KeyError:
        print("Error: JSON missing 'id' or 'val' keys")
    except ValueError:
        print("Error: Invalid number format")

if __name__ == "__main__":
    setup_motors()

    # setup MQTT
    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
    client.on_message = on_message
    
    print(f"Connecting to MQTT...")
    try:
        client.connect(MQTT_BROKER, MQTT_PORT, 60)
        client.subscribe(MQTT_TOPIC)
        print(f"Listening for commands on '{MQTT_TOPIC}'...")

        client.loop_forever()
        
    except KeyboardInterrupt:
        print("\nDisconnecting...")
    except Exception as e:
        print(f"Connection Failed: {e}")
    finally:
        shutdown_motors()