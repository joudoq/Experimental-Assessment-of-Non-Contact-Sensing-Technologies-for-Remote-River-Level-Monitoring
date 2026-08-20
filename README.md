# River Sensor Monitoring

An experimental study of three non-contact water level sensors, Ultrasonic, Radar, and LiDAR, to evaluate their performance, limitations, and overall reliability for monitoring rivers in remote areas without cellular coverage. As a complete solution, the system is designed to be a low-cost and battery-efficient system, with a long operational lifetime that makes it well suited for remote river deployments. Sensor data is transmitted over LoRaWAN and Cellular networks to a live visualization platform, helping decision-makers act quickly on flood risk, agriculture, and hydroelectric planning.

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
