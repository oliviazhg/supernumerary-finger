'''
Server script that polls hand position from fingerposition.py using multiprocessing

This implementation uses shared memory (multiprocessing.Value) for fast,
reliable inter-process communication.

Usage:
1. Make sure fingerposition.py is configured with TRAINING_MODE = False
2. Make sure you have trained the model (vals0.dat and vals1.dat exist)
3. Run this script: python server.py
4. The classifier will run in a background process
5. This server will continuously poll and respond to hand position changes
'''

import multiprocessing
import time
import sys


def classifier_worker(shared_position):
    '''
    Worker process that runs the Myo classifier.

    Args:
        shared_position: multiprocessing.Value that will be updated with hand position
    '''
    # Import here to avoid issues with pygame in main process
    from fingerposition import run_classification_mode_with_shared_value

    try:
        run_classification_mode_with_shared_value(shared_position)
    except Exception as e:
        print(f"[Classifier Worker] Error: {e}")
        import traceback
        traceback.print_exc()


def handle_hand_position(position, last_position):
    '''
    Handle hand position changes.

    Args:
        position: Current hand position (0=relaxed, 1=fist)
        last_position: Previous hand position

    Returns:
        bool: True if position changed, False otherwise
    '''
    if position != last_position:
        if position == 1:
            print("[SERVER] FIST DETECTED - Triggering action!")
            # Add your custom logic here
            # Examples:
            # - Send command to device
            # - Trigger automation
            # - Control robot
            # - Play sound
            # etc.
        else:
            print("[SERVER] Hand relaxed - Idle")
        return True
    return False


def main():
    print("=" * 50)
    print("HAND POSITION SERVER (Multiprocessing)")
    print("=" * 50)
    print()
    print("Starting classifier in background process...")
    print("Server will poll hand position every 20ms (low latency mode)")
    print()
    print("Press Ctrl+C to stop")
    print()

    # Create shared value for hand position
    # 'i' = signed integer, initial value = 0 (relaxed)
    hand_position = multiprocessing.Value('i', 0)

    # Start classifier in background process
    classifier_process = multiprocessing.Process(
        target=classifier_worker,
        args=(hand_position,),
        daemon=True  # Process will terminate when main exits
    )

    try:
        classifier_process.start()

        # Give classifier time to initialize
        print("Waiting for classifier to initialize...")
        time.sleep(3)
        print("Server ready!\n")

        last_position = -1

        # Main server loop
        while True:
            # Read from shared memory (very fast, no I/O)
            current_position = hand_position.value

            # Handle position changes
            handle_hand_position(current_position, last_position)
            last_position = current_position

            # Poll every 20ms (50Hz) - faster polling
            time.sleep(0.015)

    except KeyboardInterrupt:
        print("\n\nShutting down server...")

    finally:
        # Clean shutdown
        if classifier_process.is_alive():
            print("Terminating classifier process...")
            classifier_process.terminate()
            classifier_process.join(timeout=2)

            if classifier_process.is_alive():
                print("Force killing classifier process...")
                classifier_process.kill()

        print("Server stopped")


if __name__ == '__main__':
    # Required for Windows multiprocessing
    multiprocessing.freeze_support()
    main()
