#include <SoftwareSerial.h>
#include <Wire.h>
#include <LIDARLite.h>

// RX = 2, TX = 3 (LoRa pins)
SoftwareSerial loraSerial(2, 3); 
LIDARLite myLidarLite;

// Variable to store distance
int distance_cm = 0; 

// --- Adaptive transmission interval settings ---
const float STABLE_THRESHOLD_PCT = 1.0;     // stable: less than 1%
const float MODERATE_THRESHOLD_PCT = 3.5;   // moderate: 1% - 3.5%, above this = rapid change

const unsigned long STABLE_INTERVAL_MS = 15UL * 60UL * 1000UL;   // 15 minutes
const unsigned long MODERATE_INTERVAL_MS = 5UL * 60UL * 1000UL;  // 5 minutes
const unsigned long RAPID_INTERVAL_MS = 1UL * 60UL * 1000UL;     // 1 minute

int lastDistance_cm = -1; // -1 = no previous reading yet (first boot)

void setup() {
  // Start PC serial monitor
  Serial.begin(19200);
  
  // Start LoRa serial
  loraSerial.begin(19200);

  // Start LiDAR
  myLidarLite.begin(0, true); 
  myLidarLite.configure(0);   // Default mode for general distance measurement
  
  delay(2000);
  Serial.println("System Started...");
  Serial.println("Attempting to Join LoRaWAN Network...");
  
  // Send JOIN command to LoRa
  loraSerial.println("AT+JOIN");
  
  // Wait 10 seconds for network join
  delay(10000); 
}

void loop() {
  // 1. Read distance from Garmin LiDAR
  distance_cm = readLidarDistance();
  
  // Print distance to Serial Monitor
  Serial.print("Measured Distance: ");
  Serial.print(distance_cm);
  Serial.println(" cm");

  // 2. Convert distance to Hex payload (4 characters)
  char payload[10];
  sprintf(payload, "%04X", distance_cm);

  // 3. Send payload via LoRa
  Serial.print("Sending Payload: ");
  Serial.println(payload);
  
  loraSerial.print("AT+CMSGHEX=");
  loraSerial.println(payload);

  // 4. Wait and print LoRa response for 5 seconds
  long startTime = millis();
  while(millis() - startTime < 5000) {
    if (loraSerial.available()) {
      Serial.write(loraSerial.read());
    }
  }

  // 5. Task: decide the next transmission interval from the % change
  // between the previous and current distance readings (adaptive duty-cycle)
  unsigned long nextInterval = computeNextIntervalMs(lastDistance_cm, distance_cm);
  lastDistance_cm = distance_cm;

  Serial.print("Next reading in ");
  Serial.print(nextInterval / 1000);
  Serial.println(" s");

  // 6. Wait the adaptive interval before next reading
  Serial.println("\nWaiting for next reading...\n");
  delay(nextInterval);
}

int readLidarDistance() {
  // Return distance in centimeters
  return myLidarLite.distance(); 
}

// Task: adaptive duty-cycle - maps % change between readings to the
// next transmission interval (stable / moderate / rapid change)
unsigned long computeNextIntervalMs(int previous, int current) {
  if (previous <= 0) {
    return STABLE_INTERVAL_MS; // no valid baseline yet, start conservative
  }
  float pctChange = abs(current - previous) / (float)abs(previous) * 100.0;
  if (pctChange > MODERATE_THRESHOLD_PCT) {
    return RAPID_INTERVAL_MS;
  } else if (pctChange > STABLE_THRESHOLD_PCT) {
    return MODERATE_INTERVAL_MS;
  }
  return STABLE_INTERVAL_MS;
}