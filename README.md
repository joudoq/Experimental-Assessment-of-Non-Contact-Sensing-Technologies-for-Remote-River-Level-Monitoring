# River Sensor Monitoring

Comparing LiDAR, Radar, and Ultrasonic sensors for river water level monitoring. Sensors send data over LoRaWAN through TTN into InfluxDB.

## Structure

- firmware/ - Arduino code for the LiDAR sensor
- scripts/ - Python scripts that read data from TTN and write it to InfluxDB
- data/ - CSV of manual sensor comparison readings
- docs/ - experiment reports

## Setup

```
pip install -r requirements.txt
python scripts/ttn_to_influxdb_lidar.py
```
