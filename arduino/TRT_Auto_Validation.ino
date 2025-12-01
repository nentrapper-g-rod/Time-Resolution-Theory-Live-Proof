// TRT AUTO-VALIDATION — GIGA R1 WiFi + Display Shield
// Runs ALL control tests + main experiment FOREVER
// Phase 0: LED OFF (5min) → Phase 1: LED ON (5min)
// Phase 2-5: Freq sweep 100Hz,1kHz,10kHz,20kHz (5min each)
// Phase 6+: Main 10kHz TRT experiment (forever)
// github.com/nentrapper-g-rod/Time-Resolution-Theory-Live-Proof

#include <Arduino_GigaDisplay_GFX.h>
#include <WiFi.h>
#include <ArduinoHttpClient.h>
#include <mbed.h>

using namespace mbed;

GigaDisplay_GFX gfx;

// Use mbed PwmOut for precise frequency control
PwmOut *ledPwm = nullptr;

#define LED_PIN 9
#define PHOTO_PIN A0

// Wi-Fi credentials
const char* ssid = "Girod-House-of-Big-Nuts";
const char* password = "qwe12345";
const char* githubToken = "YOUR_GITHUB_TOKEN_HERE";
const char* githubHost = "api.github.com";

// GitHub paths for each phase (separate files so nothing overwrites)
const char* repoPaths[] = {
  "/repos/nentrapper-g-rod/Time-Resolution-Theory-Live-Proof/contents/data/control_off.json",
  "/repos/nentrapper-g-rod/Time-Resolution-Theory-Live-Proof/contents/data/control_on.json",
  "/repos/nentrapper-g-rod/Time-Resolution-Theory-Live-Proof/contents/data/sweep_100hz.json",
  "/repos/nentrapper-g-rod/Time-Resolution-Theory-Live-Proof/contents/data/sweep_1khz.json",
  "/repos/nentrapper-g-rod/Time-Resolution-Theory-Live-Proof/contents/data/sweep_10khz.json",
  "/repos/nentrapper-g-rod/Time-Resolution-Theory-Live-Proof/contents/data/sweep_20khz.json",
  "/repos/nentrapper-g-rod/Time-Resolution-Theory-Live-Proof/contents/data/live_trt.json"
};

const char* repoPath; // Will be updated based on current phase

WiFiSSLClient wifi;
HttpClient client = HttpClient(wifi, githubHost, 443);

// Web server on port 80
WiFiServer server(80);

float samples[1024]; // Buffer for ~1s data
int idx = 0;
unsigned long lastUpdate = 0;
unsigned long lastGitHubPost = 0;

// Statistics for display
float current_mean100 = 0;
float current_var100 = 0;
float current_mean10 = 0;
float current_var10 = 0;
float current_mean1 = 0;

// Chart history for variance (last 30 readings)
#define CHART_HISTORY_SIZE 30
float var100_history[CHART_HISTORY_SIZE];
float var10_history[CHART_HISTORY_SIZE];
float var1_history[CHART_HISTORY_SIZE];
int chart_index = 0;

// Flag for first display update
bool firstDisplayUpdate = true;

// GitHub status tracking
String lastGitHubStatus = "Waiting...";
int lastGitHubCode = 0;
unsigned long lastSuccessfulPost = 0;
unsigned long gitHubUploadCount = 0;  // Total successful uploads

// Debug logging
#define DEBUG_LOG_SIZE 5
String debugLog[DEBUG_LOG_SIZE];
int debugLogIndex = 0;
unsigned long lastDebugUpdate = 0;
String currentActivity = "Starting...";
int activityCounter = 0;

// AUTO-VALIDATION Phase tracking
int currentPhase = 0;
unsigned long phaseStartTime = 0;
const unsigned long phaseDuration = 300000; // 5 minutes per phase (300000ms)

// Phase names and colors
const char* phaseNames[] = {
  "LED OFF", "LED ON", "100 Hz", "1 kHz", "10 kHz", "20 kHz", "LIVE TRT"
};
const uint16_t phaseColors[] = {
  0xFF0000, 0x00FF00, 0xFFFF00, 0xFFFF00, 0xFFFF00, 0xFFFF00, 0x00FFFF
};

// Add message to debug log
void addDebugLog(String message) {
  debugLog[debugLogIndex] = message;
  debugLogIndex = (debugLogIndex + 1) % DEBUG_LOG_SIZE;
  Serial.print("[DEBUG] ");
  Serial.println(message);
}

// Set PWM frequency using mbed
void setPWMFrequency(int freqHz) {
  if (ledPwm) {
    delete ledPwm;
  }
  ledPwm = new PwmOut(digitalPinToPinName(LED_PIN));
  ledPwm->period_us(1000000 / freqHz);
  ledPwm->write(0.5f); // 50% duty cycle

  Serial.print("PWM set to ");
  Serial.print(freqHz);
  Serial.println(" Hz");
}

void setup() {
  Serial.begin(115200);

  // Initialize display
  gfx.begin();
  gfx.setRotation(2); // Rotate display 180 degrees
  gfx.fillScreen(0x000000); // Black
  gfx.setTextColor(0xFF0000);
  gfx.setTextSize(2);
  gfx.setCursor(20, 20);
  gfx.print("AUTO-VALIDATION");

  gfx.setTextSize(2);
  gfx.setTextColor(0xFFFFFF);
  gfx.setCursor(20, 60);
  gfx.print("Initializing...");

  // Initialize LED (Phase 0: LED OFF)
  pinMode(LED_PIN, OUTPUT);
  digitalWrite(LED_PIN, LOW); // Start with LED OFF
  phaseStartTime = millis();
  repoPath = repoPaths[0]; // Start with Phase 0 path
  addDebugLog("Phase 0: LED OFF started");

  // Set ADC resolution to 12-bit (GIGA default)
  analogReadResolution(12); // 0-4095

  // Wi-Fi setup
  gfx.setCursor(20, 90);
  gfx.setTextColor(0xFFFF00);
  gfx.print("Connecting WiFi...");

  WiFi.begin(ssid, password);
  int attempts = 0;
  while (WiFi.status() != WL_CONNECTED && attempts < 30) {
    delay(500);
    attempts++;
    gfx.fillRect(300, 90, 160, 30, 0x000000);
    gfx.setCursor(300, 90);
    gfx.print(attempts);
    gfx.print("/30");
  }

  if (WiFi.status() == WL_CONNECTED) {
    gfx.fillRect(20, 90, 440, 30, 0x000000);
    gfx.setCursor(20, 90);
    gfx.setTextColor(0x00FF00);
    gfx.print("WiFi Connected!");
    gfx.setCursor(20, 120);
    gfx.setTextSize(1);
    gfx.print("IP: ");
    gfx.print(WiFi.localIP());

    Serial.println("WiFi connected!");
    Serial.print("IP: ");
    Serial.println(WiFi.localIP());
    addDebugLog("WiFi: " + String(WiFi.localIP().toString()));
  } else {
    gfx.fillRect(20, 90, 440, 30, 0x000000);
    gfx.setCursor(20, 90);
    gfx.setTextColor(0xFF0000);
    gfx.print("WiFi FAILED!");
    Serial.println("WiFi connection failed!");
    addDebugLog("WiFi: FAILED");
  }

  delay(2000);

  // Start web server
  if (WiFi.status() == WL_CONNECTED) {
    server.begin();
    Serial.print("Web server started at http://");
    Serial.println(WiFi.localIP());
    addDebugLog("Web server started");
    addDebugLog("System ready");
  }

  // Clear for main display - WiFi status will be shown by updateDisplay()
  gfx.fillScreen(0x000000);

  Serial.println("# TRT Live — GIGA Display + WiFi");
  Serial.println("# time(s),voltage");

  lastGitHubPost = millis();
}

void loop() {
  currentActivity = "Sampling";
  int raw = analogRead(PHOTO_PIN);
  float v = raw * (3.3f / 4095.0f); // GIGA 12-bit ADC, 3.3V reference
  unsigned long ms = millis();

  samples[idx % 1024] = v;
  idx++;

  // Print to Serial
  Serial.print(ms / 1000.0, 6);
  Serial.print(",");
  Serial.println(v, 6);

  // AUTO-VALIDATION: Check if we need to advance to next phase
  if (millis() - phaseStartTime >= phaseDuration && currentPhase < 6) {
    currentPhase++;
    phaseStartTime = millis();
    firstDisplayUpdate = true; // Force full screen redraw
    repoPath = repoPaths[currentPhase]; // Update GitHub path

    // Set LED state based on new phase
    switch (currentPhase) {
      case 0: digitalWrite(LED_PIN, LOW); addDebugLog("Phase 0: LED OFF"); break;
      case 1: digitalWrite(LED_PIN, HIGH); addDebugLog("Phase 1: LED ON"); break;
      case 2: setPWMFrequency(100); addDebugLog("Phase 2: 100 Hz"); break;
      case 3: setPWMFrequency(1000); addDebugLog("Phase 3: 1 kHz"); break;
      case 4: setPWMFrequency(10000); addDebugLog("Phase 4: 10 kHz"); break;
      case 5: setPWMFrequency(20000); addDebugLog("Phase 5: 20 kHz"); break;
      case 6: setPWMFrequency(10000); addDebugLog("Phase 6: LIVE TRT"); break;
    }
  }

  // Update display every 500 samples (~0.5s)
  if (idx % 500 == 0) {
    currentActivity = "Updating display";
    updateDisplay();

    // Log milestone samples
    if (idx % 5000 == 0) {
      addDebugLog("Samples: " + String(idx));
    }
  }

  // Post to GitHub every 60 seconds
  if (millis() - lastGitHubPost >= 60000) {
    currentActivity = "Posting to GitHub";
    addDebugLog("Starting GitHub post...");
    postToGitHub();
    lastGitHubPost = millis();
  }

  // Handle web server requests
  handleWebClient();

  delayMicroseconds(1000); // 1 kHz sampling (1ms)
}

void updateDisplay() {
  // On first update, draw static labels; on subsequent updates, only clear value areas
  bool isFirstUpdate = firstDisplayUpdate;
  if (isFirstUpdate) {
    // Full screen setup on first run
    gfx.fillScreen(0x000000);
    firstDisplayUpdate = false;
  }

  // PROJECT TITLE at top
  if (isFirstUpdate) {
    gfx.setTextSize(2);
    gfx.setTextColor(0x00FFFF);
    gfx.setCursor(20, 5);
    gfx.print("TRT LIVE PROOF");
  }

  // Current Phase under title - BIGGER TEXT
  gfx.fillRect(110, 25, 330, 20, 0x000000);  // Clear only phase name area, not "Phase:" label
  gfx.setTextSize(2);
  gfx.setTextColor(0xFFFFFF);  // White for "Phase:" label
  gfx.setCursor(20, 25);
  gfx.print("Phase: ");
  gfx.setTextColor(0xFFFFFF);  // White for phase name too
  gfx.print(phaseNames[currentPhase]);

  // Time remaining in current phase (only if not in final phase)
  if (currentPhase < 6) {
    gfx.setTextSize(1);
    gfx.setTextColor(0xCCCCCC);
    gfx.setCursor(380, 30);
    unsigned long timeLeft = (phaseDuration - (millis() - phaseStartTime)) / 1000;
    gfx.print("Next:");
    gfx.print(timeLeft);
    gfx.print("s");
  }

  gfx.drawFastHLine(0, 48, 480, 0x00FFFF); // Separator line after title

  // Calculate 0.1s window (~100 samples)
  current_mean100 = 0;
  current_var100 = 0;
  int count100 = min(100, idx);
  for (int i = 0; i < count100; i++) {
    current_mean100 += samples[(idx - 1 - i + 1024) % 1024];
  }
  current_mean100 /= count100;

  for (int i = 0; i < count100; i++) {
    float d = samples[(idx - 1 - i + 1024) % 1024] - current_mean100;
    current_var100 += d * d;
  }
  current_var100 /= count100;

  // Calculate 0.01s window (~10 samples)
  current_mean10 = 0;
  current_var10 = 0;
  int count10 = min(10, idx);
  for (int i = 0; i < count10; i++) {
    current_mean10 += samples[(idx - 1 - i + 1024) % 1024];
  }
  current_mean10 /= count10;

  for (int i = 0; i < count10; i++) {
    float d = samples[(idx - 1 - i + 1024) % 1024] - current_mean10;
    current_var10 += d * d;
  }
  current_var10 /= count10;

  // 0.001s (~1 sample)
  current_mean1 = samples[(idx - 1 + 1024) % 1024];

  // Update chart history every update
  var100_history[chart_index % CHART_HISTORY_SIZE] = current_var100;
  var10_history[chart_index % CHART_HISTORY_SIZE] = current_var10;
  var1_history[chart_index % CHART_HISTORY_SIZE] = 0; // Single sample has no variance
  chart_index++;

  // Display statistics (only redraw labels on first update)
  gfx.setTextSize(2);

  if (isFirstUpdate) {
    gfx.setTextColor(0xFFFF00);
    gfx.setCursor(20, 55);
    gfx.print("Delta t = 0.1s (100ms)");
    gfx.setTextColor(0x00FF00);
    gfx.setCursor(20, 145);
    gfx.print("Delta t = 0.01s (10ms)");
    gfx.setTextColor(0xFF00FF);
    gfx.setCursor(20, 235);
    gfx.print("Delta t = 0.001s (1ms)");
    gfx.setTextColor(0xFFFFFF);
    gfx.setCursor(20, 285);
    gfx.print("Variance Level (0.1s):");
    gfx.drawRect(20, 300, 440, 50, 0xFFFFFF);
  }

  // Clear and redraw changing values only
  // 0.1s values
  gfx.fillRect(40, 80, 430, 20, 0x000000);
  gfx.setTextColor(0xFFFFFF);
  gfx.setCursor(40, 80);
  gfx.print("Mean: ");
  gfx.print(current_mean100, 4);
  gfx.print(" V");

  gfx.fillRect(40, 105, 430, 20, 0x000000);
  gfx.setCursor(40, 105);
  gfx.print("Var:  ");
  gfx.print(current_var100, 6);

  // 0.01s values
  gfx.fillRect(40, 170, 430, 20, 0x000000);
  gfx.setCursor(40, 170);
  gfx.print("Mean: ");
  gfx.print(current_mean10, 4);
  gfx.print(" V");

  gfx.fillRect(40, 195, 430, 20, 0x000000);
  gfx.setCursor(40, 195);
  gfx.print("Var:  ");
  gfx.print(current_var10, 6);

  // 0.001s value
  gfx.fillRect(40, 260, 430, 20, 0x000000);
  gfx.setCursor(40, 260);
  gfx.print("Value: ");
  gfx.print(current_mean1, 4);
  gfx.print(" V");

  // Variance bar graph (clear and redraw)
  gfx.fillRect(22, 302, 436, 46, 0x000000); // Clear bar area
  int barWidth = constrain(current_var100 * 50000, 0, 436);
  uint16_t barColor = barWidth > 100 ? 0xFF0000 : 0x00FF00;
  gfx.fillRect(22, 302, barWidth, 46, barColor);

  // Sample count and time
  gfx.setTextColor(0x00FFFF);
  gfx.fillRect(20, 365, 450, 20, 0x000000); // Clear full line
  gfx.setCursor(20, 365);
  gfx.print("Samples: ");
  gfx.print(idx);

  gfx.fillRect(20, 390, 450, 20, 0x000000); // Clear full line
  gfx.setCursor(20, 390);
  gfx.print("Runtime: ");
  gfx.print(millis() / 1000);
  gfx.print(" s");

  // Next GitHub update countdown
  gfx.fillRect(20, 415, 450, 20, 0x000000); // Clear entire line
  gfx.setCursor(20, 415);
  gfx.setTextColor(0xFFFF00);
  gfx.print("Next GitHub: ");

  unsigned long elapsed = (millis() - lastGitHubPost) / 1000;
  if (elapsed < 60) {
    unsigned long nextUpdate = 60 - elapsed;
    gfx.print(nextUpdate);
    gfx.print(" s");
  } else {
    gfx.print("uploading...");
  }

  // Variance Trend Chart - MOVED to fit 480px width display
  // Removing chart to make room for essential data display
  // Chart would go off-screen at x=500 (display is only 480px wide)
  int chartX = -1000;  // Move off-screen to disable
  int chartY = -1000;
  int chartW = 0;
  int chartH = 0;

  if (isFirstUpdate) {
    gfx.drawRect(chartX, chartY, chartW, chartH, 0xFFFFFF);
    gfx.setTextSize(1);
    gfx.setTextColor(0x00FFFF);
    gfx.setCursor(chartX + 5, chartY + 5);  // Changed from chartY - 12 to avoid WiFi bar overlap
    gfx.print("Variance Trend (0.1s)");
  }

  // Draw variance trend line
  gfx.fillRect(chartX + 1, chartY + 1, chartW - 2, chartH - 2, 0x000000); // Clear chart

  int pointsToShow = min(chart_index, CHART_HISTORY_SIZE);
  if (pointsToShow > 1) {
    // Find max variance for scaling
    float maxVar = 0.0001; // Minimum to avoid divide by zero
    for (int i = 0; i < pointsToShow; i++) {
      int histIdx = (chart_index - pointsToShow + i) % CHART_HISTORY_SIZE;
      if (var100_history[histIdx] > maxVar) maxVar = var100_history[histIdx];
    }

    // Draw grid lines
    gfx.drawFastHLine(chartX + 1, chartY + chartH/2, chartW - 2, 0x333333);
    gfx.drawFastHLine(chartX + 1, chartY + chartH - 1, chartW - 2, 0x666666);

    // Draw line chart
    for (int i = 1; i < pointsToShow; i++) {
      int histIdx1 = (chart_index - pointsToShow + i - 1) % CHART_HISTORY_SIZE;
      int histIdx2 = (chart_index - pointsToShow + i) % CHART_HISTORY_SIZE;

      int x1 = chartX + 1 + ((i - 1) * (chartW - 2)) / (pointsToShow - 1);
      int x2 = chartX + 1 + (i * (chartW - 2)) / (pointsToShow - 1);

      int y1 = chartY + chartH - 2 - (int)((var100_history[histIdx1] / maxVar) * (chartH - 4));
      int y2 = chartY + chartH - 2 - (int)((var100_history[histIdx2] / maxVar) * (chartH - 4));

      gfx.drawLine(x1, y1, x2, y2, 0xFFFF00); // Yellow line
    }

    // Draw current value indicator
    gfx.setTextSize(1);
    gfx.setTextColor(0xFFFFFF);
    gfx.setCursor(chartX + 5, chartY + chartH + 5);
    gfx.print("Max:");
    gfx.print(maxVar, 6);
  }

  // GitHub Status
  gfx.fillRect(20, 440, 460, 30, 0x000000); // Clear full area
  gfx.setTextSize(2);
  gfx.setCursor(20, 440);
  if (lastGitHubStatus == "Success") {
    gfx.setTextColor(0x00FF00);
    gfx.print("GitHub: SUCCESS");
  } else if (lastGitHubStatus == "Posting...") {
    gfx.setTextColor(0xFFFF00);
    gfx.print("GitHub: POSTING...");
  } else if (lastGitHubStatus == "Waiting...") {
    gfx.setTextColor(0xFFFFFF);
    gfx.print("GitHub: Waiting...");
  } else {
    gfx.setTextColor(0xFF0000);
    gfx.print("GitHub: ");
    gfx.print(lastGitHubStatus);
  }

  // WiFi Status Bar at BOTTOM (moved from top)
  gfx.fillRect(0, 465, 480, 55, 0x001a33); // Dark blue background at bottom
  gfx.setTextSize(1);

  // WiFi status indicator
  if (WiFi.status() == WL_CONNECTED) {
    gfx.fillCircle(10, 472, 5, 0x00FF00); // Green dot
    gfx.setTextColor(0x00FF00);
    gfx.setCursor(20, 468);
    gfx.print("WiFi: CONNECTED");
  } else {
    gfx.fillCircle(10, 472, 5, 0xFF0000); // Red dot
    gfx.setTextColor(0xFF0000);
    gfx.setCursor(20, 468);
    gfx.print("WiFi: DISCONNECTED");
  }

  // IP Address (if connected)
  if (WiFi.status() == WL_CONNECTED) {
    gfx.setTextColor(0xFFFFFF);
    gfx.setCursor(20, 483);
    gfx.print("IP: ");
    gfx.setTextColor(0xFFFF00);
    gfx.print(WiFi.localIP());

    // Signal strength
    long rssi = WiFi.RSSI();
    gfx.setTextColor(0xFFFFFF);
    gfx.setCursor(200, 483);
    gfx.print("Signal: ");
    if (rssi > -60) {
      gfx.setTextColor(0x00FF00); // Strong - green
    } else if (rssi > -75) {
      gfx.setTextColor(0xFFFF00); // Medium - yellow
    } else {
      gfx.setTextColor(0xFF8000); // Weak - orange
    }
    gfx.print(rssi);
    gfx.print("dBm");
  }

  // GitHub upload count in WiFi bar
  gfx.setTextSize(1);
  gfx.setTextColor(0xFFFFFF);
  gfx.setCursor(20, 498);
  gfx.print("GitHub Updates: ");
  gfx.setTextColor(0x00FF00);
  gfx.print(gitHubUploadCount);

  // Status indicator
  gfx.setTextColor(0x888888);
  gfx.setCursor(200, 498);
  gfx.print("Status: ");
  gfx.setTextColor(0xFFFF00);
  gfx.print(currentActivity);
}

void postToGitHub() {
  lastGitHubStatus = "Posting...";

  // Calculate latest statistics
  float mean100 = current_mean100;
  float var100 = current_var100;
  float mean10 = current_mean10;
  float var10 = current_var10;
  float mean1 = current_mean1;
  float var1 = 0.0; // Single sample has no variance

  // Build JSON data
  String jsonData = "{\n";
  jsonData += "  \"delta_t_100ms\": {\n";
  jsonData += "    \"mean\": " + String(mean100, 6) + ",\n";
  jsonData += "    \"variance\": " + String(var100, 6) + "\n";
  jsonData += "  },\n";
  jsonData += "  \"delta_t_10ms\": {\n";
  jsonData += "    \"mean\": " + String(mean10, 6) + ",\n";
  jsonData += "    \"variance\": " + String(var10, 6) + "\n";
  jsonData += "  },\n";
  jsonData += "  \"delta_t_1ms\": {\n";
  jsonData += "    \"mean\": " + String(mean1, 6) + ",\n";
  jsonData += "    \"variance\": " + String(var1, 6) + "\n";
  jsonData += "  },\n";
  jsonData += "  \"timestamp_ms\": " + String(millis()) + ",\n";
  jsonData += "  \"sample_count\": " + String(idx) + ",\n";
  jsonData += "  \"timestamp_iso\": \"" + String(millis()/1000) + "s\"\n";
  jsonData += "}";

  Serial.println("\n=== Posting to GitHub ===");
  Serial.println("JSON Data:");
  Serial.println(jsonData);

  // Step 1: GET the file to retrieve its SHA (if it exists)
  Serial.println("Step 1: Getting current file SHA...");

  client.beginRequest();
  client.get(repoPath);
  client.sendHeader("Host", githubHost);
  client.sendHeader("Authorization", String("Bearer ") + githubToken);
  client.sendHeader("User-Agent", "TRT-GIGA-R1");
  client.sendHeader("Accept", "application/vnd.github.v3+json");
  client.endRequest();

  int getStatusCode = client.responseStatusCode();
  String getResponse = client.responseBody();

  Serial.print("GET Status: ");
  Serial.println(getStatusCode);

  String fileSHA = "";

  // Extract SHA from response if file exists
  if (getStatusCode == 200) {
    // Parse SHA from JSON response
    int shaIndex = getResponse.indexOf("\"sha\":");
    if (shaIndex != -1) {
      int shaStart = getResponse.indexOf("\"", shaIndex + 6) + 1;
      int shaEnd = getResponse.indexOf("\"", shaStart);
      fileSHA = getResponse.substring(shaStart, shaEnd);
      Serial.print("Found SHA: ");
      Serial.println(fileSHA);
    }
  } else if (getStatusCode == 404) {
    Serial.println("File doesn't exist yet, will create it");
  } else {
    Serial.print("GET failed with code: ");
    Serial.println(getStatusCode);
  }

  client.stop();
  delay(100); // Small delay between requests

  // Step 2: PUT/Update the file with SHA (if exists)
  Serial.println("Step 2: Uploading new content...");

  // Base64 encode the JSON
  String base64Content = base64Encode(jsonData);

  // Build GitHub API request body
  String requestBody = "{\n";
  requestBody += "  \"message\": \"Update TRT data from GIGA at " + String(millis()/1000) + "s\",\n";
  requestBody += "  \"content\": \"" + base64Content + "\"";

  // Include SHA if file exists
  if (fileSHA.length() > 0) {
    requestBody += ",\n  \"sha\": \"" + fileSHA + "\"";
  }

  requestBody += "\n}";

  Serial.println("Request body prepared");

  // Make HTTP PUT request
  client.beginRequest();
  client.put(repoPath);
  client.sendHeader("Host", githubHost);
  client.sendHeader("Authorization", String("Bearer ") + githubToken);
  client.sendHeader("User-Agent", "TRT-GIGA-R1");
  client.sendHeader("Content-Type", "application/json");
  client.sendHeader("Accept", "application/vnd.github.v3+json");
  client.sendHeader("Content-Length", requestBody.length());
  client.beginBody();
  client.print(requestBody);
  client.endRequest();

  // Get response
  int statusCode = client.responseStatusCode();
  String response = client.responseBody();

  Serial.print("PUT Status code: ");
  Serial.println(statusCode);
  Serial.print("Response: ");
  Serial.println(response);

  lastGitHubCode = statusCode;

  if (statusCode == 200 || statusCode == 201) {
    Serial.println("GitHub update SUCCESS!");
    lastGitHubStatus = "Success";
    lastSuccessfulPost = millis();
    gitHubUploadCount++;  // Increment upload counter
    addDebugLog("GitHub: OK (" + String(statusCode) + ")");
  } else if (statusCode == 409 || statusCode == 422) {
    Serial.println("GitHub update FAILED - Conflict");
    lastGitHubStatus = "Conflict " + String(statusCode);
    addDebugLog("GitHub: Conflict " + String(statusCode));
  } else if (statusCode == 401 || statusCode == 403) {
    Serial.println("GitHub update FAILED - Authentication error");
    lastGitHubStatus = "Auth failed";
    addDebugLog("GitHub: Auth error " + String(statusCode));
  } else if (statusCode <= 0) {
    Serial.println("GitHub update FAILED - Connection error");
    lastGitHubStatus = "Connection failed";
    addDebugLog("GitHub: No connection");
  } else {
    Serial.println("GitHub update FAILED!");
    lastGitHubStatus = "Error " + String(statusCode);
    addDebugLog("GitHub: Error " + String(statusCode));
  }

  client.stop();
}

// Simple Base64 encoding for GitHub API
String base64Encode(String input) {
  const char* base64_chars = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/";
  String output = "";
  int val = 0;
  int valb = -6;

  for (unsigned int i = 0; i < input.length(); i++) {
    unsigned char c = input.charAt(i);
    val = (val << 8) + c;
    valb += 8;
    while (valb >= 0) {
      output += base64_chars[(val >> valb) & 0x3F];
      valb -= 6;
    }
  }

  if (valb > -6) {
    output += base64_chars[((val << 8) >> (valb + 8)) & 0x3F];
  }

  while (output.length() % 4) {
    output += '=';
  }

  return output;
}

// Handle web server requests
void handleWebClient() {
  WiFiClient webClient = server.available();
  if (webClient) {
    Serial.println("New web client");
    String currentLine = "";
    String requestPath = "";
    bool headerComplete = false;

    while (webClient.connected()) {
      if (webClient.available()) {
        char c = webClient.read();

        if (c == '\n') {
          // End of HTTP request
          if (currentLine.length() == 0) {
            headerComplete = true;

            // Check if requesting JSON data
            if (requestPath.indexOf("GET /data") >= 0) {
              // Send JSON response
              webClient.println("HTTP/1.1 200 OK");
              webClient.println("Content-Type: application/json");
              webClient.println("Connection: close");
              webClient.println();

              // Build JSON
              webClient.print("{");
              webClient.print("\"ssid\":\""); webClient.print(ssid); webClient.print("\",");
              webClient.print("\"ip\":\""); webClient.print(WiFi.localIP()); webClient.print("\",");
              webClient.print("\"rssi\":"); webClient.print(WiFi.RSSI()); webClient.print(",");
              webClient.print("\"samples\":"); webClient.print(idx); webClient.print(",");
              webClient.print("\"runtime\":"); webClient.print(millis() / 1000); webClient.print(",");
              webClient.print("\"mean100\":"); webClient.print(current_mean100, 6); webClient.print(",");
              webClient.print("\"var100\":"); webClient.print(current_var100, 8); webClient.print(",");
              webClient.print("\"mean10\":"); webClient.print(current_mean10, 6); webClient.print(",");
              webClient.print("\"var10\":"); webClient.print(current_var10, 8); webClient.print(",");
              webClient.print("\"mean1\":"); webClient.print(current_mean1, 6); webClient.print(",");
              webClient.print("\"githubStatus\":\""); webClient.print(lastGitHubStatus); webClient.print("\",");
              webClient.print("\"githubCode\":"); webClient.print(lastGitHubCode); webClient.print(",");
              webClient.print("\"lastSuccess\":"); webClient.print(lastSuccessfulPost / 1000); webClient.print(",");

              // Add chart history data (last 20 points)
              webClient.print("\"chartHistory\":[");
              int pointsToSend = min(chart_index, 20);
              for (int i = 0; i < pointsToSend; i++) {
                int histIdx = (chart_index - pointsToSend + i) % CHART_HISTORY_SIZE;
                if (i > 0) webClient.print(",");
                webClient.print(var100_history[histIdx], 8);
              }
              webClient.print("]");

              webClient.println("}");
            } else {
              // Send HTML response
              webClient.println("HTTP/1.1 200 OK");
              webClient.println("Content-Type: text/html");
              webClient.println("Connection: close");
              webClient.println();

            // HTML page with live data
            webClient.println("<!DOCTYPE html>");
            webClient.println("<html><head>");
            webClient.println("<meta charset='UTF-8'>");
            webClient.println("<meta name='viewport' content='width=device-width, initial-scale=1.0'>");
            webClient.println("<title>TRT Live Proof - GIGA R1</title>");
            webClient.println("<script src='https://cdn.jsdelivr.net/npm/chart.js'></script>");
            webClient.println("<style>");
            webClient.println("body { font-family: 'Courier New', monospace; background: #000; color: #0ff; margin: 20px; }");
            webClient.println("h1 { color: #0ff; text-align: center; border-bottom: 2px solid #0ff; padding-bottom: 10px; }");
            webClient.println(".container { max-width: 800px; margin: 0 auto; }");
            webClient.println(".data-block { background: #001a33; border: 2px solid #0ff; border-radius: 10px; padding: 15px; margin: 20px 0; }");
            webClient.println(".data-block h2 { color: #ff0; margin-top: 0; }");
            webClient.println(".stat { display: flex; justify-content: space-between; padding: 8px 0; border-bottom: 1px solid #004466; }");
            webClient.println(".stat:last-child { border-bottom: none; }");
            webClient.println(".label { color: #fff; }");
            webClient.println(".value { color: #0f0; font-weight: bold; }");
            webClient.println(".variance { color: #f80; }");
            webClient.println(".info { color: #aaa; font-size: 12px; text-align: center; margin-top: 20px; }");
            webClient.println(".status { background: #003; padding: 10px; border-radius: 5px; margin-bottom: 20px; }");
            webClient.println(".download-btn { background: #0a0; color: #000; border: 2px solid #0f0; padding: 12px 24px; font-size: 16px; font-weight: bold; cursor: pointer; border-radius: 8px; margin: 20px auto; display: block; transition: all 0.3s; }");
            webClient.println(".download-btn:hover { background: #0f0; transform: scale(1.05); }");
            webClient.println("</style>");
            webClient.println("</head><body>");
            webClient.println("<div class='container'>");
            webClient.println("<h1>⚡ TIME RESOLUTION THEORY ⚡</h1>");
            webClient.println("<h1>LIVE PROOF - GIGA R1 WiFi</h1>");

            // Status info
            webClient.println("<div class='status'>");
            webClient.print("<div class='stat'><span class='label'>WiFi Network:</span><span class='value' id='ssid'>");
            webClient.print(ssid);
            webClient.println("</span></div>");
            webClient.print("<div class='stat'><span class='label'>IP Address:</span><span class='value' id='ip'>");
            webClient.print(WiFi.localIP());
            webClient.println("</span></div>");
            webClient.print("<div class='stat'><span class='label'>Signal Strength:</span><span class='value' id='rssi'>");
            webClient.print(WiFi.RSSI());
            webClient.println(" dBm</span></div>");
            webClient.print("<div class='stat'><span class='label'>Samples Collected:</span><span class='value' id='samples'>");
            webClient.print(idx);
            webClient.println("</span></div>");
            webClient.print("<div class='stat'><span class='label'>Runtime:</span><span class='value' id='runtime'>");
            webClient.print(millis() / 1000);
            webClient.println(" seconds</span></div>");
            webClient.print("<div class='stat'><span class='label'>GitHub Status:</span><span class='value' id='github'>");
            webClient.print(lastGitHubStatus);
            if (lastGitHubCode > 0) {
              webClient.print(" (");
              webClient.print(lastGitHubCode);
              webClient.print(")");
            }
            webClient.println("</span></div>");
            webClient.println("</div>");

            // Delta t = 0.1s (100ms)
            webClient.println("<div class='data-block'>");
            webClient.println("<h2>Δt = 0.1s (100ms)</h2>");
            webClient.print("<div class='stat'><span class='label'>Mean:</span><span class='value' id='mean100'>");
            webClient.print(current_mean100, 6);
            webClient.println(" V</span></div>");
            webClient.print("<div class='stat'><span class='label'>Variance:</span><span class='variance' id='var100'>");
            webClient.print(current_var100, 8);
            webClient.println("</span></div>");
            webClient.println("</div>");

            // Delta t = 0.01s (10ms)
            webClient.println("<div class='data-block'>");
            webClient.println("<h2>Δt = 0.01s (10ms)</h2>");
            webClient.print("<div class='stat'><span class='label'>Mean:</span><span class='value' id='mean10'>");
            webClient.print(current_mean10, 6);
            webClient.println(" V</span></div>");
            webClient.print("<div class='stat'><span class='label'>Variance:</span><span class='variance' id='var10'>");
            webClient.print(current_var10, 8);
            webClient.println("</span></div>");
            webClient.println("</div>");

            // Delta t = 0.001s (1ms)
            webClient.println("<div class='data-block'>");
            webClient.println("<h2>Δt = 0.001s (1ms)</h2>");
            webClient.print("<div class='stat'><span class='label'>Current Value:</span><span class='value' id='mean1'>");
            webClient.print(current_mean1, 6);
            webClient.println(" V</span></div>");
            webClient.print("<div class='stat'><span class='label'>Variance:</span><span class='variance'>N/A (single sample)</span></div>");
            webClient.println("</div>");

            // Variance Trend Chart
            webClient.println("<div class='data-block'>");
            webClient.println("<h2>Variance Trend (Δt = 0.1s)</h2>");
            webClient.println("<canvas id='varianceChart' width='400' height='200'></canvas>");
            webClient.println("</div>");

            // Download button
            webClient.println("<button class='download-btn' onclick='downloadData()'>⬇️ Download Data (CSV)</button>");

            // Footer
            webClient.println("<div class='info'>");
            webClient.println("<p>Live data updates every 2 seconds (no page refresh)</p>");
            webClient.println("<p>Time Resolution Theory Live Proof</p>");
            webClient.println("<p>github.com/nentrapper-g-rod/Time-Resolution-Theory-Live-Proof</p>");
            webClient.println("</div>");

            // JavaScript for live updates
            webClient.println("<script>");
            webClient.println("// Initialize Chart");
            webClient.println("const ctx = document.getElementById('varianceChart').getContext('2d');");
            webClient.println("const chart = new Chart(ctx, {");
            webClient.println("  type: 'line',");
            webClient.println("  data: {");
            webClient.println("    labels: [],");
            webClient.println("    datasets: [{");
            webClient.println("      label: 'Variance (Δt=0.1s)',");
            webClient.println("      data: [],");
            webClient.println("      borderColor: '#ffff00',");
            webClient.println("      backgroundColor: 'rgba(255,255,0,0.1)',");
            webClient.println("      tension: 0.3");
            webClient.println("    }]");
            webClient.println("  },");
            webClient.println("  options: {");
            webClient.println("    responsive: true,");
            webClient.println("    plugins: {");
            webClient.println("      legend: { labels: { color: '#0ff' } }");
            webClient.println("    },");
            webClient.println("    scales: {");
            webClient.println("      y: {");
            webClient.println("        ticks: { color: '#0ff' },");
            webClient.println("        grid: { color: '#333' }");
            webClient.println("      },");
            webClient.println("      x: {");
            webClient.println("        ticks: { color: '#0ff' },");
            webClient.println("        grid: { color: '#333' }");
            webClient.println("      }");
            webClient.println("    }");
            webClient.println("  }");
            webClient.println("});");
            webClient.println("");
            webClient.println("function updateData() {");
            webClient.println("  fetch('/data')");
            webClient.println("    .then(response => response.json())");
            webClient.println("    .then(data => {");
            webClient.println("      document.getElementById('ssid').textContent = data.ssid;");
            webClient.println("      document.getElementById('ip').textContent = data.ip;");
            webClient.println("      document.getElementById('rssi').textContent = data.rssi + ' dBm';");
            webClient.println("      document.getElementById('samples').textContent = data.samples;");
            webClient.println("      document.getElementById('runtime').textContent = data.runtime + ' seconds';");
            webClient.println("      document.getElementById('mean100').textContent = data.mean100.toFixed(6) + ' V';");
            webClient.println("      document.getElementById('var100').textContent = data.var100.toFixed(8);");
            webClient.println("      document.getElementById('mean10').textContent = data.mean10.toFixed(6) + ' V';");
            webClient.println("      document.getElementById('var10').textContent = data.var10.toFixed(8);");
            webClient.println("      document.getElementById('mean1').textContent = data.mean1.toFixed(6) + ' V';");
            webClient.println("      let ghStatus = data.githubStatus;");
            webClient.println("      if (data.githubCode > 0) { ghStatus += ' (' + data.githubCode + ')'; }");
            webClient.println("      document.getElementById('github').textContent = ghStatus;");
            webClient.println("      const ghEl = document.getElementById('github');");
            webClient.println("      if (data.githubStatus === 'Success') { ghEl.style.color = '#0f0'; }");
            webClient.println("      else if (data.githubStatus === 'Posting...') { ghEl.style.color = '#ff0'; }");
            webClient.println("      else if (data.githubStatus === 'Waiting...') { ghEl.style.color = '#fff'; }");
            webClient.println("      else { ghEl.style.color = '#f00'; }");
            webClient.println("      ");
            webClient.println("      // Update chart");
            webClient.println("      if (data.chartHistory && data.chartHistory.length > 0) {");
            webClient.println("        chart.data.labels = Array.from({length: data.chartHistory.length}, (_, i) => i);");
            webClient.println("        chart.data.datasets[0].data = data.chartHistory;");
            webClient.println("        chart.update('none');");
            webClient.println("      }");
            webClient.println("    })");
            webClient.println("    .catch(err => console.error('Error fetching data:', err));");
            webClient.println("}");
            webClient.println("");
            webClient.println("// Download data as CSV");
            webClient.println("function downloadData() {");
            webClient.println("  fetch('/data')");
            webClient.println("    .then(response => response.json())");
            webClient.println("    .then(data => {");
            webClient.println("      const timestamp = new Date().toISOString();");
            webClient.println("      let csv = 'Time Resolution Theory - Live Data Export\\n';");
            webClient.println("      csv += 'Exported: ' + timestamp + '\\n\\n';");
            webClient.println("      csv += 'WiFi Network,' + data.ssid + '\\n';");
            webClient.println("      csv += 'IP Address,' + data.ip + '\\n';");
            webClient.println("      csv += 'Signal Strength (dBm),' + data.rssi + '\\n';");
            webClient.println("      csv += 'Total Samples,' + data.samples + '\\n';");
            webClient.println("      csv += 'Runtime (seconds),' + data.runtime + '\\n';");
            webClient.println("      csv += 'GitHub Status,' + data.githubStatus + '\\n\\n';");
            webClient.println("      csv += 'Measurement Parameters\\n';");
            webClient.println("      csv += 'Time Interval,Mean (V),Variance\\n';");
            webClient.println("      csv += '0.1s (100ms),' + data.mean100.toFixed(6) + ',' + data.var100.toFixed(8) + '\\n';");
            webClient.println("      csv += '0.01s (10ms),' + data.mean10.toFixed(6) + ',' + data.var10.toFixed(8) + '\\n';");
            webClient.println("      csv += '0.001s (1ms),' + data.mean1.toFixed(6) + ',N/A\\n\\n';");
            webClient.println("      csv += 'Variance History (Last 20 samples)\\n';");
            webClient.println("      csv += 'Sample,Variance (0.1s)\\n';");
            webClient.println("      if (data.chartHistory) {");
            webClient.println("        data.chartHistory.forEach((v, i) => {");
            webClient.println("          csv += (i+1) + ',' + v.toFixed(8) + '\\n';");
            webClient.println("        });");
            webClient.println("      }");
            webClient.println("      const blob = new Blob([csv], { type: 'text/csv' });");
            webClient.println("      const url = window.URL.createObjectURL(blob);");
            webClient.println("      const a = document.createElement('a');");
            webClient.println("      a.href = url;");
            webClient.println("      a.download = 'TRT_data_' + timestamp.replace(/[:.]/g, '-') + '.csv';");
            webClient.println("      a.click();");
            webClient.println("      window.URL.revokeObjectURL(url);");
            webClient.println("    })");
            webClient.println("    .catch(err => console.error('Error downloading data:', err));");
            webClient.println("}");
            webClient.println("setInterval(updateData, 2000);"); // Update every 2 seconds
            webClient.println("</script>");

            webClient.println("</div></body></html>");
            }

            break;
          } else {
            currentLine = "";
          }
        } else if (c != '\r') {
          currentLine += c;
        }

        // Capture the request path
        if (requestPath.length() == 0 && currentLine.startsWith("GET ")) {
          requestPath = currentLine;
        }
      }
    }

    webClient.stop();
    Serial.println("Web client disconnected");
  }
}
