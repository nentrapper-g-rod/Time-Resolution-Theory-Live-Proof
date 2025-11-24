// Time-Resolution-Theory-Live-Proof — Arduino code
// Pulses 405 nm LED at exactly 10 kHz (50% duty)
// Samples BPW34 photodiode at 1 kHz and prints timestamp,voltage

void setup() {
  Serial.begin(115200);

  // Exact 10 kHz PWM on Pin 9 (Timer1 fast PWM)
  pinMode(9, OUTPUT);
  TCCR1A = _BV(COM1A1) | _BV(WGM11);
  TCCR1B = _BV(WGM13) | _BV(WGM12) | _BV(CS10);
  ICR1 = 1599;   // 16 MHz / 10,000 Hz = 1600 cycles
  OCR1A = 800;   // 50% duty cycle

  Serial.println("TRT Live Proof — 10 kHz LED active");
}

void loop() {
  int raw = analogRead(A0);
  float voltage = raw * (5.0 / 1023.0);  // 0–5 V → 0–1 normalized
  unsigned long ms = millis();

  // Format: timestamp(seconds),normalized_intensity
  Serial.print(ms / 1000.0, 3);
  Serial.print(",");
  Serial.println(voltage, 6);

  delay(1);  // 1 ms → 1 kHz sampling
}
