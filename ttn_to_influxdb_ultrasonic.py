import json
import base64
import struct
import paho.mqtt.client as mqtt
from influxdb_client import InfluxDBClient, Point
from influxdb_client.client.write_api import SYNCHRONOUS

# --- 1. TTN Information ---
TTN_BROKER = "eu1.cloud.thethings.network"
TTN_PORT = 1883
TTN_USERNAME = "ultrasonic-sensor-joud@ttn"
TTN_PASSWORD = "NNSXS.K6PMCMBIJEGHFYSI26URZUWSQFPTPWPU3MKU2EI.JN3WIGFHHM2TMD2NIMP6TFZSEFILALAOHSZDKPUVD4IVFJ3HCGOQ"

# --- 2. InfluxDB Information ---
INFLUX_URL = "https://us-east-1-1.aws.cloud2.influxdata.com"
INFLUX_ORG = "ictp"
INFLUX_BUCKET = "radar_sensor"
INFLUX_TOKEN = "2wI4ztPgzBLOYBMEsH_7vAPG2MXLhVSoVM_D2j1-f3w__oHm91-W01SxDoQlUE9d-WaKP-3xAtNBi_lniPqX3g=="

# Connect to InfluxDB
influx_client = InfluxDBClient(url=INFLUX_URL, token=INFLUX_TOKEN, org=INFLUX_ORG)
write_api = influx_client.write_api(write_options=SYNCHRONOUS)

# --- 3. Adaptive transmission interval settings ---
STABLE_THRESHOLD_PCT = 1        # stable: less than 1%
MODERATE_THRESHOLD_PCT = 3.5    # moderate: 1% - 3.5%, above this = rapid change

STABLE_INTERVAL_S = 15 * 60     # 15 minutes
MODERATE_INTERVAL_S = 5 * 60    # 5 minutes
RAPID_INTERVAL_S = 1 * 60       # 1 minute

DOWNLINK_PORT = 85  # Milesight's default downlink port

_last_distance = {}
_last_requested_interval = {}


def compute_interval_seconds(previous, current):
    if previous in (None, 0):
        return STABLE_INTERVAL_S, 0.0
    pct = abs(current - previous) / abs(previous) * 100.0
    if pct > MODERATE_THRESHOLD_PCT:
        return RAPID_INTERVAL_S, pct
    elif pct > STABLE_THRESHOLD_PCT:
        return MODERATE_INTERVAL_S, pct
    return STABLE_INTERVAL_S, pct


def send_report_interval_downlink(client, application_id, device_id, seconds):
    payload = bytes([0xff, 0x03]) + struct.pack('<H', seconds)
    topic = f"v3/{application_id}/devices/{device_id}/down/push"
    body = {
        "downlinks": [{
            "f_port": DOWNLINK_PORT,
            "frm_payload": base64.b64encode(payload).decode(),
            "priority": "NORMAL",
        }]
    }
    client.publish(topic, json.dumps(body))


def on_connect(client, userdata, flags, rc):
    print("Connected to TTN successfully!")
    client.subscribe("v3/+/devices/+/up")


def on_message(client, userdata, msg):
    try:
        payload = json.loads(msg.payload.decode('utf-8'))
        device_id = payload['end_device_ids']['device_id']
        application_id = payload['end_device_ids']['application_ids']['application_id']

        if 'decoded_payload' in payload['uplink_message']:
            data = payload['uplink_message']['decoded_payload']

            # Extract distance value
            distance = data.get('distance')

            print(f"Received from {device_id}, Distance: {distance}")

            if distance is not None:
                # Prepare the data point for InfluxDB
                point = Point("ultrasonic_measurements") \
                    .tag("device_id", device_id) \
                    .field("distance", float(distance))
                # Save to InfluxDB
                write_api.write(bucket=INFLUX_BUCKET, org=INFLUX_ORG, record=point)
                print("Data saved to InfluxDB!")

                # --- Adaptive transmission interval ---
                previous = _last_distance.get(device_id)
                target_interval, pct = compute_interval_seconds(previous, distance)
                _last_distance[device_id] = distance

                if _last_requested_interval.get(device_id) != target_interval:
                    send_report_interval_downlink(client, application_id, device_id, target_interval)
                    _last_requested_interval[device_id] = target_interval
                    print(f"[{device_id}] change={pct:.2f}% -> requested interval={target_interval}s")

    except Exception as e:
        print("Error processing message:", e)


mqtt_client = mqtt.Client()
mqtt_client.username_pw_set(TTN_USERNAME, TTN_PASSWORD)
mqtt_client.on_connect = on_connect
mqtt_client.on_message = on_message

print("Connecting to TTN...")
mqtt_client.connect(TTN_BROKER, TTN_PORT, 60)
mqtt_client.loop_forever()