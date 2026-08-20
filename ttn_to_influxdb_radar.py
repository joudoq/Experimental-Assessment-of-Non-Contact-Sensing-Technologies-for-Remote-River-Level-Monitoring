import json
import paho.mqtt.client as mqtt
from influxdb_client import InfluxDBClient, Point
from influxdb_client.client.write_api import SYNCHRONOUS

# --- 1. TTN Information ---
TTN_BROKER = "eu1.cloud.thethings.network"
TTN_PORT = 1883
TTN_USERNAME = "radar-sensor-joud@ttn"
TTN_PASSWORD = "NNSXS.PSL6K72S2KPOVNBDQ7DE6GBVCUKJSBVL6I4QG6I.KG4U3HD7LEDOXGBMLU3EXKZO5EOZS5RSOGF7QMFVXTYE2EX4XD4A"

INFLUX_URL = "https://us-east-1-1.aws.cloud2.influxdata.com"
INFLUX_ORG = "ictp"
INFLUX_BUCKET = "radar_sensor"  # Put your bucket name here
INFLUX_TOKEN = "fXoqeyAYNrABikPXBdllRe6oPPZZXoMvlTJro_RFVKbAkKzWdS2uiufcMiTE3anplQZN9uFfdVQ4it9reRsJAA=="

# Connect to InfluxDB
influx_client = InfluxDBClient(url=INFLUX_URL, token=INFLUX_TOKEN, org=INFLUX_ORG)
write_api = influx_client.write_api(write_options=SYNCHRONOUS)


# Function to run when connected to TTN
def on_connect(client, userdata, flags, rc):
    print("Connected to TTN successfully!")
    client.subscribe("v3/+/devices/+/up")


# Function to run when a new message arrives from TTN
def on_message(client, userdata, msg):
    try:
        # Read the message as JSON
        payload = json.loads(msg.payload.decode('utf-8'))

        # Get device ID
        device_id = payload['end_device_ids']['device_id']

        # Check if decoded payload exists
        if 'decoded_payload' in payload['uplink_message']:
            data = payload['uplink_message']['decoded_payload']

            # Get sensor values exactly as they come from TTN
            battery = data.get('battery')
            distance = data.get('distance')
            position = data.get('position')
            radar_rssi = data.get('radar_signal_rssi')

            print(f"Received from {device_id} -> Battery: {battery}, Distance: {distance}, RSSI: {radar_rssi}")

            # Prepare the data point for InfluxDB
            # Strings like 'position' are saved as tags, numbers are saved as fields
            point = Point("radar_measurements") \
                .tag("device_id", device_id) \
                .tag("position", position) \
                .field("battery", float(battery)) \
                .field("distance", float(distance)) \
                .field("radar_signal_rssi", float(radar_rssi))

            # Save the point to InfluxDB
            write_api.write(bucket=INFLUX_BUCKET, org=INFLUX_ORG, record=point)
            print("Data saved to InfluxDB!")

    except Exception as e:
        print("Error processing message:", e)


# Setup MQTT client
mqtt_client = mqtt.Client()
mqtt_client.username_pw_set(TTN_USERNAME, TTN_PASSWORD)
mqtt_client.on_connect = on_connect
mqtt_client.on_message = on_message

# Connect and keep running to listen for new data
print("Connecting to TTN...")
mqtt_client.connect(TTN_BROKER, TTN_PORT, 60)
mqtt_client.loop_forever()