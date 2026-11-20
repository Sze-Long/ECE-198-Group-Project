#include <DFRobot_MAX30102.h>

DFRobot_MAX30102 particleSensor;


//Priyanshu this is the global heart rate variable. It is now filtered: spikes from pressing too hard or outside light are thrown out,
//and the value is the median of the last few good readings. It is 0 when no finger is on the sensor.
//For the heart attack detector, only trust global_heart_rate when global_heart_rate_stable is true, and still require it to stay
//above your limit for several readings in a row so you don't get false positives.
int32_t global_heart_rate = 0;
bool    global_heart_rate_stable = false;   // true once there are enough agreeing readings to trust the value


// ---------------- Noise filter settings ----------------
const uint32_t FINGER_MIN_IR = 50000;    // IR below this = no finger on the sensor
const uint32_t SATURATED_IR  = 250000;   // IR above this = pressed too hard or too much light (sensor max is 262143)
const int32_t  MIN_BPM  = 40;            // readings outside this range are not a real human resting/active pulse
const int32_t  MAX_BPM  = 180;
const int32_t  MIN_SPO2 = 80;            // a "valid" SpO2 below this almost always means a bad signal
const int32_t  MAX_JUMP_BPM = 20;        // a reading this far from the recent median is treated as a spike
const uint8_t  HISTORY_SIZE = 5;         // how many good readings the median filter keeps
const uint8_t  MIN_FOR_STABLE = 3;       // readings needed before the value is trusted
const uint8_t  MAX_REJECTS  = 3;         // this many spikes in a row = heart rate really changed, so start over

int32_t history[HISTORY_SIZE];
uint8_t historyCount = 0;
uint8_t historyIndex = 0;
uint8_t rejectStreak = 0;
bool    fingerJustPlaced = true;   // the first reading after the finger goes down is usually too high, so it is skipped


void setup()
{
  Serial.begin(115200);

  while (!particleSensor.begin()) {
    Serial.println("MAX30102 was not found");
    delay(1000);
  }

  // The library's heart rate math assumes 25 samples per second.
  // 100 samples/s averaged in groups of 4 = 25 samples/s. (The old 400 setting gave 100/s, which made the BPM wrong.)
  particleSensor.sensorConfiguration(/*ledBrightness=*/60, /*sampleAverage=*/SAMPLEAVG_4, \
                                  /*ledMode=*/MODE_MULTILED, /*sampleRate=*/SAMPLERATE_100, \
                                  /*pulseWidth=*/PULSEWIDTH_411, /*adcRange=*/ADCRANGE_16384);
}


// Median of the stored readings. A median ignores one-off outliers, unlike an average.
int32_t medianOfHistory()
{
  int32_t sorted[HISTORY_SIZE];
  for (uint8_t i = 0; i < historyCount; i++) sorted[i] = history[i];

  for (uint8_t i = 1; i < historyCount; i++) {   // insertion sort (tiny array)
    int32_t key = sorted[i];
    int8_t j = i - 1;
    while (j >= 0 && sorted[j] > key) {
      sorted[j + 1] = sorted[j];
      j--;
    }
    sorted[j + 1] = key;
  }
  // Odd count: the middle value. Even count: the average of the two middle values (so 2 readings don't just pick the higher one).
  if (historyCount % 2 == 1) {
    return sorted[historyCount / 2];
  }
  return (sorted[historyCount / 2 - 1] + sorted[historyCount / 2]) / 2;
}

void addToHistory(int32_t bpm)
{
  history[historyIndex] = bpm;
  historyIndex = (historyIndex + 1) % HISTORY_SIZE;
  if (historyCount < HISTORY_SIZE) historyCount++;
}

void resetHistory()
{
  historyCount = 0;
  historyIndex = 0;
  rejectStreak = 0;
  global_heart_rate_stable = false;
}

// Checks the raw IR light level to make sure a finger is on the sensor and the signal isn't maxed out.
bool signalOk()
{
  uint32_t ir = particleSensor.getIR();

  if (ir < FINGER_MIN_IR) {
    Serial.println("No finger detected. Place your finger on the sensor.");
    return false;
  }
  if (ir > SATURATED_IR) {
    Serial.println("Signal saturated. Press more lightly and block outside light.");
    return false;
  }
  return true;
}


void loop()
{
  int32_t blood_oxygen_percentage;
  int8_t blood_oxygen_valid;
  int32_t heart_rate;
  int8_t heart_rate_valid;

  // 1) Don't measure at all without a good finger signal.
  if (!signalOk()) {
    resetHistory();
    global_heart_rate = 0;
    fingerJustPlaced = true;
    delay(250);
    return;
  }

  // This collects ~4 seconds of samples and runs the library's algorithm.
  particleSensor.heartrateAndOxygenSaturation(&blood_oxygen_percentage, &blood_oxygen_valid, &heart_rate, &heart_rate_valid);

  // 2) If the finger moved off or was pressed down during those 4 seconds, the reading is junk.
  if (!signalOk()) {
    resetHistory();
    global_heart_rate = 0;
    fingerJustPlaced = true;
    return;
  }

  // The first reading is taken while the finger is still settling and pressing in, so it runs high. Skip it.
  if (fingerJustPlaced) {
    fingerJustPlaced = false;
    Serial.println("Finger detected. Warming up...");
    return;
  }

  // 3) Throw out readings the algorithm flags as invalid or that aren't physically sensible.
  if (heart_rate_valid != 1 || blood_oxygen_valid != 1 ||
      heart_rate < MIN_BPM || heart_rate > MAX_BPM ||
      blood_oxygen_percentage < MIN_SPO2 || blood_oxygen_percentage > 100) {
    Serial.println("Noisy reading ignored. Keep your finger perfectly still.");
    return;
  }

  // 4) Spike check: reject a reading that jumps far away from the recent median.
  if (historyCount >= MIN_FOR_STABLE) {
    int32_t recent = medianOfHistory();
    if (abs(heart_rate - recent) > MAX_JUMP_BPM) {
      rejectStreak++;
      if (rejectStreak < MAX_REJECTS) {
        Serial.print("Spike ignored (");
        Serial.print(heart_rate);
        Serial.println(" BPM).");
        return;
      }
      // Several "spikes" in a row means the heart rate really changed, so start fresh.
      resetHistory();
    }
  }
  rejectStreak = 0;

  // 5) Good reading: store it and report the median of recent good readings.
  addToHistory(heart_rate);
  global_heart_rate = medianOfHistory();
  global_heart_rate_stable = (historyCount >= MIN_FOR_STABLE);

  Serial.print("Heart Rate: ");
  Serial.print(global_heart_rate);
  Serial.print(" BPM | SpO2: ");
  Serial.print(blood_oxygen_percentage);
  Serial.print("%");
  if (!global_heart_rate_stable) {
    Serial.print("  (settling...)");
  }
  Serial.println();
}
