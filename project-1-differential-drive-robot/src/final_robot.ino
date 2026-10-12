#include <Adafruit_MPU6050.h>
#include <Adafruit_Sensor.h>
#include <Wire.h>
#include <math.h>

// ========================================================
// MPU6050
// ========================================================

Adafruit_MPU6050 mpu;

float gyroZ = 0.0;


// ========================================================
// ULTRASONIC SENSOR
// ========================================================

const int TRIG_PIN = 12;
const int ECHO_PIN = 13;

const float OBSTACLE_DISTANCE = 20.0;   // cm

float distanceCM = 999.0;


// ========================================================
// ENCODERS
// ========================================================

const int LEFT_A  = 2;
const int LEFT_B  = 4;

const int RIGHT_A = 3;
const int RIGHT_B = 11;

volatile long leftCount  = 0;
volatile long rightCount = 0;


// ========================================================
// L298N MOTOR DRIVER
// ========================================================

// Left motor
const int ENA = 5;
const int IN1 = 7;
const int IN2 = 8;

// Right motor
const int ENB = 6;
const int IN3 = 9;
const int IN4 = 10;


// ========================================================
// ROBOT PARAMETERS
// ========================================================

// Measured encoder resolution
const float CPR = 960.0;

// Wheel radius
const float WHEEL_RADIUS = 0.0325;   // m

// Distance between wheel centres
const float WHEEL_BASE = 0.13;       // m


// ========================================================
// PI WHEEL-SPEED CONTROL
// ========================================================

const float TARGET_RPM = 20.0;

float Kp = 3.0;
float Ki = 1.0;

const int BASE_PWM = 115;

float leftIntegral  = 0.0;
float rightIntegral = 0.0;

int leftPWM  = BASE_PWM;
int rightPWM = BASE_PWM;

float leftRPM  = 0.0;
float rightRPM = 0.0;


// ========================================================
// SPEED MEASUREMENT
// ========================================================

long previousSpeedLeft  = 0;
long previousSpeedRight = 0;

unsigned long previousSpeedTime = 0;

const unsigned long SPEED_SAMPLE_TIME = 250;


// ========================================================
// ODOMETRY
// ========================================================

float x = 0.0;
float y = 0.0;
float theta = 0.0;

long previousOdomLeft  = 0;
long previousOdomRight = 0;


// ========================================================
// SENSOR / DISPLAY TIMING
// ========================================================

unsigned long previousSensorTime = 0;
unsigned long previousPrintTime  = 0;


// ========================================================
// ROBOT STATE MACHINE
// ========================================================

enum RobotState {
  DRIVE,
  STOP_BEFORE_TURN,
  TURN_RIGHT,
  STOP_AFTER_TURN
};

RobotState state = DRIVE;

unsigned long stateStartTime = 0;

float turnStartTheta = 0.0;


// ========================================================
// SETUP
// ========================================================

void setup() {

  Serial.begin(115200);


  // ------------------------------------------------------
  // Ultrasonic sensor
  // ------------------------------------------------------

  pinMode(TRIG_PIN, OUTPUT);
  pinMode(ECHO_PIN, INPUT);


  // ------------------------------------------------------
  // Encoders
  // ------------------------------------------------------

  pinMode(LEFT_A, INPUT);
  pinMode(LEFT_B, INPUT);

  pinMode(RIGHT_A, INPUT);
  pinMode(RIGHT_B, INPUT);


  attachInterrupt(
    digitalPinToInterrupt(LEFT_A),
    leftEncoderISR,
    RISING
  );


  attachInterrupt(
    digitalPinToInterrupt(RIGHT_A),
    rightEncoderISR,
    RISING
  );


  // ------------------------------------------------------
  // Motors
  // ------------------------------------------------------

  pinMode(ENA, OUTPUT);
  pinMode(IN1, OUTPUT);
  pinMode(IN2, OUTPUT);

  pinMode(ENB, OUTPUT);
  pinMode(IN3, OUTPUT);
  pinMode(IN4, OUTPUT);

  stopMotors();


  // ------------------------------------------------------
  // MPU6050
  // ------------------------------------------------------

  if (!mpu.begin()) {

    Serial.println("MPU6050 NOT FOUND");

    while (1) {
      delay(10);
    }
  }


  Serial.println("ROBOT READY");


  // Start moving
  kickForward();

  resetSpeedMeasurement();
}


// ========================================================
// MAIN LOOP
// ========================================================

void loop() {

  unsigned long currentTime = millis();


  // ------------------------------------------------------
  // Update encoder odometry
  // ------------------------------------------------------

  updateOdometry();


  // ------------------------------------------------------
  // Read ultrasonic sensor and IMU
  // ------------------------------------------------------

  if (currentTime - previousSensorTime >= 100) {

    distanceCM = readDistance();


    sensors_event_t accel;
    sensors_event_t gyro;
    sensors_event_t temp;


    mpu.getEvent(
      &accel,
      &gyro,
      &temp
    );


    gyroZ = gyro.gyro.z;


    previousSensorTime = currentTime;
  }


  // ======================================================
  // STATE: DRIVE
  // ======================================================

  if (state == DRIVE) {

    // Obstacle detected
    if (
      distanceCM > 0 &&
      distanceCM <= OBSTACLE_DISTANCE
    ) {

      stopMotors();

      leftIntegral  = 0;
      rightIntegral = 0;

      state = STOP_BEFORE_TURN;

      stateStartTime = currentTime;

      Serial.println("OBSTACLE DETECTED");
    }

    else {

      setForwardDirection();

      updateSpeedPI();
    }
  }


  // ======================================================
  // STATE: STOP BEFORE TURN
  // ======================================================

  else if (state == STOP_BEFORE_TURN) {

    stopMotors();


    if (
      currentTime - stateStartTime >= 300
    ) {

      turnStartTheta = theta;

      state = TURN_RIGHT;

      Serial.println("TURNING RIGHT");
    }
  }


  // ======================================================
  // STATE: TURN RIGHT
  // ======================================================

  else if (state == TURN_RIGHT) {

    turnRight();


    float turnedAngle =
      theta - turnStartTheta;


    // Right turn is approximately -90 degrees
    if (
      turnedAngle <= -PI / 2.0
    ) {

      stopMotors();

      state = STOP_AFTER_TURN;

      stateStartTime = currentTime;

      Serial.println("90 DEGREE TURN COMPLETE");
    }
  }


  // ======================================================
  // STATE: STOP AFTER TURN
  // ======================================================

  else if (state == STOP_AFTER_TURN) {

    stopMotors();


    if (
      currentTime - stateStartTime >= 300
    ) {

      kickForward();

      resetSpeedMeasurement();

      state = DRIVE;

      Serial.println("CONTINUING FORWARD");
    }
  }


  // ======================================================
  // SERIAL MONITORING
  // ======================================================

  if (
    currentTime - previousPrintTime >= 250
  ) {

    Serial.print("Distance: ");
    Serial.print(distanceCM);
    Serial.print(" cm");

    Serial.print(" | L RPM: ");
    Serial.print(leftRPM);

    Serial.print(" | R RPM: ");
    Serial.print(rightRPM);

    Serial.print(" | X: ");
    Serial.print(x, 3);

    Serial.print(" m | Y: ");
    Serial.print(y, 3);

    Serial.print(" m | Theta: ");
    Serial.print(
      theta * 180.0 / PI,
      1
    );

    Serial.print(" deg | Gyro Z: ");
    Serial.println(gyroZ);


    previousPrintTime = currentTime;
  }
}


// ========================================================
// PI WHEEL-SPEED CONTROL
// ========================================================

void updateSpeedPI() {

  unsigned long currentTime =
    millis();


  if (
    currentTime - previousSpeedTime
    < SPEED_SAMPLE_TIME
  ) {

    return;
  }


  float dt =
    (currentTime - previousSpeedTime)
    / 1000.0;


  // Copy encoder counts safely
  noInterrupts();

  long currentLeft =
    leftCount;

  long currentRight =
    rightCount;

  interrupts();


  // Encoder-count change
  long deltaLeft =
    abs(
      currentLeft
      - previousSpeedLeft
    );


  long deltaRight =
    abs(
      currentRight
      - previousSpeedRight
    );


  // ------------------------------------------------------
  // Encoder counts -> RPM
  // ------------------------------------------------------

  leftRPM =
    (deltaLeft / CPR)
    * (60.0 / dt);


  rightRPM =
    (deltaRight / CPR)
    * (60.0 / dt);


  // ------------------------------------------------------
  // Left PI controller
  // ------------------------------------------------------

  float leftError =
    TARGET_RPM - leftRPM;


  leftIntegral +=
    leftError * dt;


  leftIntegral =
    constrain(
      leftIntegral,
      -40.0,
      40.0
    );


  leftPWM =
    BASE_PWM
    + Kp * leftError
    + Ki * leftIntegral;


  leftPWM =
    constrain(
      leftPWM,
      0,
      255
    );


  // ------------------------------------------------------
  // Right PI controller
  // ------------------------------------------------------

  float rightError =
    TARGET_RPM - rightRPM;


  rightIntegral +=
    rightError * dt;


  rightIntegral =
    constrain(
      rightIntegral,
      -40.0,
      40.0
    );


  rightPWM =
    BASE_PWM
    + Kp * rightError
    + Ki * rightIntegral;


  rightPWM =
    constrain(
      rightPWM,
      0,
      255
    );


  // Apply motor commands
  analogWrite(
    ENA,
    leftPWM
  );

  analogWrite(
    ENB,
    rightPWM
  );


  previousSpeedLeft =
    currentLeft;

  previousSpeedRight =
    currentRight;

  previousSpeedTime =
    currentTime;
}


// ========================================================
// DIFFERENTIAL-DRIVE ODOMETRY
// ========================================================

void updateOdometry() {

  noInterrupts();

  long currentLeft =
    leftCount;

  long currentRight =
    rightCount;

  interrupts();


  // ------------------------------------------------------
  // Encoder sign convention
  //
  // Left forward  = negative raw count
  // Right forward = positive raw count
  // ------------------------------------------------------

  long deltaLeft =
    -(
      currentLeft
      - previousOdomLeft
    );


  long deltaRight =
    currentRight
    - previousOdomRight;


  // Encoder counts -> wheel angle
  float leftAngle =
    (deltaLeft / CPR)
    * 2.0 * PI;


  float rightAngle =
    (deltaRight / CPR)
    * 2.0 * PI;


  // Wheel angle -> wheel travel
  float leftDistance =
    WHEEL_RADIUS
    * leftAngle;


  float rightDistance =
    WHEEL_RADIUS
    * rightAngle;


  // Robot-centre displacement
  float deltaDistance =
    (
      leftDistance
      + rightDistance
    )
    / 2.0;


  // Change in robot heading
  float deltaTheta =
    (
      rightDistance
      - leftDistance
    )
    / WHEEL_BASE;


  // Update estimated x position
  x +=
    deltaDistance
    * cos(
      theta
      + deltaTheta / 2.0
    );


  // Update estimated y position
  y +=
    deltaDistance
    * sin(
      theta
      + deltaTheta / 2.0
    );


  // Update estimated heading
  theta +=
    deltaTheta;


  previousOdomLeft =
    currentLeft;

  previousOdomRight =
    currentRight;
}


// ========================================================
// ULTRASONIC DISTANCE MEASUREMENT
// ========================================================

float readDistance() {

  digitalWrite(
    TRIG_PIN,
    LOW
  );

  delayMicroseconds(2);


  digitalWrite(
    TRIG_PIN,
    HIGH
  );

  delayMicroseconds(10);


  digitalWrite(
    TRIG_PIN,
    LOW
  );


  long duration =
    pulseIn(
      ECHO_PIN,
      HIGH,
      30000
    );


  // No valid echo
  if (duration == 0) {

    return -1;
  }


  // Speed of sound ≈ 0.0343 cm/us
  // Divide by two because sound travels out and back
  return
    duration
    * 0.0343
    / 2.0;
}


// ========================================================
// FORWARD MOTOR DIRECTION
// ========================================================

void setForwardDirection() {

  // Left motor forward
  digitalWrite(
    IN1,
    LOW
  );

  digitalWrite(
    IN2,
    HIGH
  );


  // Right motor forward
  digitalWrite(
    IN3,
    LOW
  );

  digitalWrite(
    IN4,
    HIGH
  );
}


// ========================================================
// MOTOR STARTUP BOOST
// ========================================================

void kickForward() {

  setForwardDirection();


  // Start left motor
  analogWrite(
    ENA,
    180
  );

  delay(150);


  // Start right motor
  analogWrite(
    ENB,
    180
  );

  delay(150);


  // Drop to PI-controller starting PWM
  analogWrite(
    ENA,
    BASE_PWM
  );

  analogWrite(
    ENB,
    BASE_PWM
  );
}


// ========================================================
// RIGHT TURN
// ========================================================

void turnRight() {

  // Left motor forward
  digitalWrite(
    IN1,
    LOW
  );

  digitalWrite(
    IN2,
    HIGH
  );


  // Right motor reverse
  digitalWrite(
    IN3,
    HIGH
  );

  digitalWrite(
    IN4,
    LOW
  );


  analogWrite(
    ENA,
    120
  );

  analogWrite(
    ENB,
    120
  );
}


// ========================================================
// STOP MOTORS
// ========================================================

void stopMotors() {

  analogWrite(
    ENA,
    0
  );

  analogWrite(
    ENB,
    0
  );
}


// ========================================================
// RESET WHEEL-SPEED MEASUREMENT
// ========================================================

void resetSpeedMeasurement() {

  noInterrupts();

  previousSpeedLeft =
    leftCount;

  previousSpeedRight =
    rightCount;

  interrupts();


  previousSpeedTime =
    millis();


  leftIntegral  = 0;
  rightIntegral = 0;
}


// ========================================================
// LEFT ENCODER INTERRUPT
// ========================================================

void leftEncoderISR() {

  if (
    digitalRead(LEFT_B)
  ) {

    leftCount++;
  }

  else {

    leftCount--;
  }
}


// ========================================================
// RIGHT ENCODER INTERRUPT
// ========================================================

void rightEncoderISR() {

  if (
    digitalRead(RIGHT_B)
  ) {

    rightCount++;
  }

  else {

    rightCount--;
  }
}
