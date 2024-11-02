import paho.mqtt.client as mqtt
import time
import threading
import math
import json
import curses
from datetime import datetime
import random

# Configuration
MQTT_BROKER = "49.13.127.227"
MQTT_PORT = 1883
MQTT_USERNAME = "energy"
MQTT_PASSWORD = "*******"
MQTT_TOPIC = "data"

# Sensor Parameters
GRID_SIZE = 10
NUM_SENSORS = GRID_SIZE * GRID_SIZE
INITIAL_MEAN = 50.0
INITIAL_NOISE = 1.0
SINE_AMPLITUDE = 5.0
SINE_PERIOD = 300  # 5 minutes in seconds
UPDATE_INTERVAL = 1.0  # seconds
DISPLAY_UPDATE_INTERVAL = 1.0  # seconds

class SensorSimulator:
    def __init__(self, stdscr):
        self.stdscr = stdscr
        self.mean = INITIAL_MEAN
        self.noise = INITIAL_NOISE
        self.running = True
        self.start_time = time.time()
        self.sensors = []
        self.values = [[0.0] * GRID_SIZE for _ in range(GRID_SIZE)]
        
        # Initialize curses
        curses.start_color()
        curses.init_pair(1, curses.COLOR_WHITE, curses.COLOR_BLACK)
        curses.init_pair(2, curses.COLOR_GREEN, curses.COLOR_BLACK)
        curses.init_pair(3, curses.COLOR_YELLOW, curses.COLOR_BLACK)
        curses.init_pair(4, curses.COLOR_RED, curses.COLOR_BLACK)
        self.stdscr.nodelay(1)
        
        # Initialize sensors
        for i in range(NUM_SENSORS):
            client = mqtt.Client(
                client_id=f"sensor_{i}",
                protocol=mqtt.MQTTv5,
                callback_api_version=mqtt.CallbackAPIVersion.VERSION2
            )
            client.username_pw_set(MQTT_USERNAME, MQTT_PASSWORD)
            try:
                client.connect(MQTT_BROKER, MQTT_PORT)
                client.loop_start()
                
                self.sensors.append({
                    'client': client,
                    'id': i,
                    'offset': random.uniform(-2, 2)
                })
            except Exception as e:
                self.stdscr.addstr(GRID_SIZE+5, 0, f"Error connecting to MQTT broker: {e}")
                self.stdscr.refresh()

    def handle_input(self):
        while self.running:
            try:
                key = self.stdscr.getch()
                if key == ord('q'):
                    self.stop()
                elif key == curses.KEY_UP:
                    self.adjust_mean(1)
                elif key == curses.KEY_DOWN:
                    self.adjust_mean(-1)
                elif key == curses.KEY_RIGHT:
                    self.adjust_noise(0.1)
                elif key == curses.KEY_LEFT:
                    self.adjust_noise(-0.1)
                time.sleep(0.05)
            except:
                continue

    def adjust_mean(self, delta):
        self.mean += delta

    def adjust_noise(self, delta):
        self.noise = max(0, self.noise + delta)

    def stop(self):
        self.running = False
        for sensor in self.sensors:
            try:
                sensor['client'].loop_stop()
                sensor['client'].disconnect()
            except:
                pass

    def generate_reading(self, offset):
        current_time = time.time() - self.start_time
        sine = SINE_AMPLITUDE * math.sin(2 * math.pi * current_time / SINE_PERIOD + offset)
        noise = random.gauss(0, self.noise)
        return self.mean + sine + noise

    def update_display(self):
        while self.running:
            try:
                self.stdscr.clear()
                
                # Display grid
                for i in range(GRID_SIZE):
                    for j in range(GRID_SIZE):
                        value = self.values[i][j]
                        # Choose color based on value
                        if value < self.mean - SINE_AMPLITUDE:
                            color = curses.color_pair(1)
                        elif value > self.mean + SINE_AMPLITUDE:
                            color = curses.color_pair(4)
                        else:
                            color = curses.color_pair(2)
                        
                        self.stdscr.addstr(i+2, j*8, f"{value:6.1f}", color)
                
                # Display status
                self.stdscr.addstr(GRID_SIZE+3, 0, f"Mean: {self.mean:6.1f} | Noise: {self.noise:4.2f}")
                self.stdscr.addstr(GRID_SIZE+4, 0, "Controls: Arrow Keys - Adjust Mean/Noise, Q - Quit")
                self.stdscr.refresh()
                
                time.sleep(DISPLAY_UPDATE_INTERVAL)
            except:
                continue

    def run(self):
        while self.running:
            current_time = int(time.time())
            for idx, sensor in enumerate(self.sensors):
                try:
                    value = self.generate_reading(sensor['offset'])
                    
                    # Update grid values
                    row = idx // GRID_SIZE
                    col = idx % GRID_SIZE
                    self.values[row][col] = value
                    
                    payload = {
                        "t": current_time,
                        "v": round(value, 2),
                        "id": sensor['id']
                    }
                    
                    sensor['client'].publish( MQTT_TOPIC, json.dumps(payload))
                except Exception as e:
                    continue
            
            time.sleep(UPDATE_INTERVAL)

def main(stdscr):
    # Set up screen
    curses.curs_set(0)  # Hide cursor
    stdscr.nodelay(1)   # Non-blocking input
    
    simulator = SensorSimulator(stdscr)
    
    # Start threads
    threads = [
        threading.Thread(target=simulator.run),
        threading.Thread(target=simulator.update_display),
        threading.Thread(target=simulator.handle_input)
    ]
    
    for thread in threads:
        thread.start()
    
    for thread in threads:
        thread.join()

if __name__ == "__main__":
    curses.wrapper(main)