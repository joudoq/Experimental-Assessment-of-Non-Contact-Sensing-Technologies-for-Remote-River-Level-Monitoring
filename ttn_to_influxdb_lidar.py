import json
import paho.mqtt.client as mqtt
from influxdb_client import InfluxDBClient, Point
from influxdb_client.client.write_api import SYNCHRONOUS

# --- 1. TTN Information ---
TTN_BROKER = "eu1.cloud.thethings.network"
TTN_PORT = 1883
TTN_USERNAME = "lidar-sensor-joud@ttn"
TTN_PASSWORD = "NNSXS.EGEWHCIKV3YPICSJTGOCUJC75NRLLL6WWIJN5LY.UZGC4WYYRFF256FQKDFS7XZRBOQZXONKZKQS5FCZ7RE6ELRZP63A"

# --- 2. InfluxDB Information ---
INFLUX_URL = "https://us-east-1-1.aws.cloud2.influxdata.com"
INFLUX_ORG = "ictp"
INFLUX_BUCKET = "radar_sensor"
INFLUX_TOKEN = "O0h6xc3e6qMxvZ-6vecCYSBnJgC8EQ_cBh9wcwNmpSx7nupWKqbXUXYx9j7eDMTZEXwfmTuq3eCyBhxbxeY6Qg=="

# Connect to InfluxDB
influx_client = InfluxDBClient(url=INFLUX_URL, token=INFLUX_TOKEN, org=INFLUX_ORG)
write_api = influx_client.write_api(write_options=SYNCHRONOUS)


def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print("Connected to TTN successfully!")
        client.subscribe("v3/+/devices/+/up")
    else:
        print(f"Failed to connect, return code {rc}")


def on_message(client, userdata, msg):
    try:
        payload = json.loads(msg.payload.decode('utf-8'))
        device_id = payload['end_device_ids']['device_id']

        if 'decoded_payload' in payload['uplink_message']:
            data = payload['uplink_message']['decoded_payload']

            # استخراج قيمة المسافة للايدار
            distance = data.get('distance')

            # التأكد من وجود قيمة للمسافة قبل الإرسال
            if distance is not None:
                print(f"Received from {device_id}, Distance: {distance}")

                # تجهيز نقطة البيانات للإرسال تحت اسم جديد للايدار
                point = Point("lidar_measurements") \
                    .tag("device_id", device_id) \
                    .field("distance", float(distance))

                # حفظ في الانفلوكس
                write_api.write(bucket=INFLUX_BUCKET, org=INFLUX_ORG, record=point)
                print("Data saved to InfluxDB!")

    except Exception as e:
        print("Error processing message:", e)


# Setup MQTT client
mqtt_client = mqtt.Client()
mqtt_client.username_pw_set(TTN_USERNAME, TTN_PASSWORD)
mqtt_client.on_connect = on_connect
mqtt_client.on_message = on_message

print("Connecting to TTN...")
mqtt_client.connect(TTN_BROKER, TTN_PORT, 60)
mqtt_client.loop_forever()