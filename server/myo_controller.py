import multiprocessing
import time
import json
import os
import paho.mqtt.client as mqtt
from dotenv import load_dotenv

load_dotenv()
MQTT_BROKER = os.getenv("MQTT_BROKER", "localhost")
MQTT_PORT = int(os.getenv("MQTT_PORT", 1883))

TOPIC_MOTOR = "motor/command"

def classifier_worker(shared_position):
    """
    Worker process that runs the Myo classifier isolated in the background.
    """
    from fingerposition import run_classification_mode_with_shared_value

    try:
        run_classification_mode_with_shared_value(shared_position)
    except Exception as e:
        print(f"[Classifier Worker] Error: {e}")

def main():
    # Create shared value for hand position
    # 'i' = signed integer, initial value = 0 (Relaxed)
    hand_position = multiprocessing.Value('i', 0)

    # Start classifier in background process
    classifier_process = multiprocessing.Process(
        target=classifier_worker,
        args=(hand_position,),
        daemon=True  # Process will terminate when main exits
    )

    client = None
    
    try:
        classifier_process.start()

        # Give classifier time to initialize
        print("Waiting for classifier to initialize...")
        time.sleep(3)
        print("Server ready!\n")
        
        client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
        client.connect(MQTT_BROKER, MQTT_PORT, 60)
        print(f"Connected to MQTT")

        last_state = -1

        while True:
            # 0 = Relaxed, 1 = Fist
            current_state = hand_position.value
            # print(current_state)

            if current_state != last_state:
                if current_state == 1:
                    m1_target = -1000
                    m2_target = 7000
                    state_name = "CLOSED (FIST)"
                else:
                    m1_target = -1000
                    m2_target = 3000
                    state_name = "OPEN (RELAXED)"
                
                # motor 1
                payload1 = {"id": 1, "position": m1_target}
                client.publish(TOPIC_MOTOR, json.dumps(payload1))

                # motor 2
                payload2 = {"id": 2, "position": m2_target}
                client.publish(TOPIC_MOTOR, json.dumps(payload2))

                print(f"State: {state_name} -> Sending M1:{m1_target}, M2:{m2_target}")
                last_state = current_state

            # fast polling
            time.sleep(0.02)

    except KeyboardInterrupt:
        print("\n\nShutting down server...")
    except Exception as e:
        print(f"\nCRASH: {e}")
    finally:
        # Clean up background process
        if classifier_process.is_alive():
            print("Terminating classifier process...")
            classifier_process.terminate()
            classifier_process.join(timeout=2)
            if classifier_process.is_alive():
                print("Force killing classifier process...")
                classifier_process.kill()
        if client:
            client.disconnect()

if __name__ == "__main__":
    # Required for Windows multiprocessing
    multiprocessing.freeze_support()
    main()