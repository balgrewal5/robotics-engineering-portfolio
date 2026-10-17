#include <Wire.h>

// L298N motor driver pins
const int ENA = 5;
const int IN1 = 7;
const int IN2 = 8;

const int ENB = 6;
const int IN3 = 9;
const int IN4 = 10;

// Motor control
const int MOTOR_SPEED = 125;
const unsigned long TIMEOUT_MS = 300;

unsigned long lastCommandTime = 0;
char currentCommand = 'S';

// MPU-6050 gyroscope
const byte MPU_ADDR = 0x68;
const float GYRO_SCALE = 131.0;  // +/-250 deg/s range
float gyroZOffset = 0.0;


void stopMotors() {
  analogWrite(ENA, 0);
  analogWrite(ENB, 0);

  digitalWrite(IN1, LOW);
  digitalWrite(IN2, LOW);
  digitalWrite(IN3, LOW);
  digitalWrite(IN4, LOW);
}


void rotateLeft() {
  // Directions verified on the physical robot
  digitalWrite(IN1, HIGH);
  digitalWrite(IN2, LOW);

  digitalWrite(IN3, LOW);
  digitalWrite(IN4, HIGH);

  analogWrite(ENA, MOTOR_SPEED);
  analogWrite(ENB, MOTOR_SPEED);
}


void rotateRight() {
  digitalWrite(IN1, LOW);
  digitalWrite(IN2, HIGH);

  digitalWrite(IN3, HIGH);
  digitalWrite(IN4, LOW);

  analogWrite(ENA, MOTOR_SPEED);
  analogWrite(ENB, MOTOR_SPEED);
}


bool readGyroZ(float &gyroZ) {
  Wire.beginTransmission(MPU_ADDR);
  Wire.write(0x47);

  if (Wire.endTransmission(false) != 0) {
    return false;
  }

  if (Wire.requestFrom(MPU_ADDR, (byte)2) != 2) {
    return false;
  }

  byte highByte = Wire.read();
  byte lowByte = Wire.read();

  int16_t raw = (int16_t)(
    (uint16_t(highByte) << 8) | lowByte
  );

  gyroZ = raw / GYRO_SCALE;
  return true;
}


void calibrateGyro() {
  float total = 0.0;
  int validSamples = 0;

  // Keep the robot stationary during calibration
  for (int i = 0; i < 200; i++) {
    float reading;

    if (readGyroZ(reading)) {
      total += reading;
      validSamples++;
    }

    delay(5);
  }

  if (validSamples > 0) {
    gyroZOffset = total / validSamples;
  }
}


void setup() {
  pinMode(ENA, OUTPUT);
  pinMode(ENB, OUTPUT);

  pinMode(IN1, OUTPUT);
  pinMode(IN2, OUTPUT);
  pinMode(IN3, OUTPUT);
  pinMode(IN4, OUTPUT);

  stopMotors();

  Serial.begin(115200);
  Wire.begin();
  Wire.setWireTimeout(3000, true);

  // Wake the MPU-6050
  Wire.beginTransmission(MPU_ADDR);
  Wire.write(0x6B);
  Wire.write(0x00);
  Wire.endTransmission();

  delay(100);
  calibrateGyro();

  lastCommandTime = millis();
}


void loop() {
  while (Serial.available() > 0) {
    char command = Serial.read();

    if (command == 'L' || command == 'R' || command == 'S') {
      lastCommandTime = millis();

      if (command != currentCommand) {
        stopMotors();

        if (command == 'L') {
          rotateLeft();
        }
        else if (command == 'R') {
          rotateRight();
        }

        currentCommand = command;
      }
    }
    else if (command == 'G') {
      float gyroZ;

      if (readGyroZ(gyroZ)) {
        gyroZ -= gyroZOffset;

        Serial.print("GYRO_Z,");
        Serial.println(gyroZ, 2);
      }
      else {
        Serial.println("GYRO_ERROR");
      }
    }
  }

  // Stop the motors if movement commands stop arriving
  if (millis() - lastCommandTime > TIMEOUT_MS) {
    if (currentCommand != 'S') {
      stopMotors();
      currentCommand = 'S';
    }
  }
}
