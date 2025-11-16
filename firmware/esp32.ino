/*
 * Sleep Tracker - ESP32
 * Sensor: INMP441 MEMS Microphone (I2S)
 * 
 * Hardware Connections:
 * INMP441:
 *   VDD -> 3.3V
 *   GND -> GND
 *   WS (LRCL) -> GPIO 25
 *   SCK (BCLK) -> GPIO 26
 *   SD (DOUT) -> GPIO 27
 * 
 * Note: INMP441 requires I2S interface which is only available on ESP32
 */

#include <WiFi.h>
#include <driver/i2s.h>

// I2S pins for INMP441
#define I2S_WS 25
#define I2S_SD 27
#define I2S_SCK 26

// I2S configuration
#define I2S_SAMPLE_RATE 16000
#define I2S_SAMPLE_BITS 16
#define I2S_READ_LEN (16 * 1024)
#define I2S_CHANNEL_NUM 1

// Audio buffer
char* i2s_read_buff = (char*)calloc(I2S_READ_LEN, sizeof(char));

// Sensor status
bool inmp441_connected = false;
unsigned long lastStatusCheck = 0;
const unsigned long STATUS_INTERVAL = 5000; // Check status every 5 seconds

void i2sInit() {
  i2s_config_t i2s_config = {
    .mode = (i2s_mode_t)(I2S_MODE_MASTER | I2S_MODE_RX),
    .sample_rate = I2S_SAMPLE_RATE,
    .bits_per_sample = (i2s_bits_per_sample_t)I2S_SAMPLE_BITS,
    .channel_format = I2S_CHANNEL_FMT_ONLY_LEFT,
    .communication_format = I2S_COMM_FORMAT_STAND_I2S,
    .intr_alloc_flags = 0,
    .dma_buf_count = 8,
    .dma_buf_len = 1024,
    .use_apll = false
  };
  
  i2s_pin_config_t pin_config = {
    .bck_io_num = I2S_SCK,
    .ws_io_num = I2S_WS,
    .data_out_num = I2S_PIN_NO_CHANGE,
    .data_in_num = I2S_SD
  };
  
  i2s_driver_install(I2S_NUM_0, &i2s_config, 0, NULL);
  i2s_set_pin(I2S_NUM_0, &pin_config);
  i2s_zero_dma_buffer(I2S_NUM_0);
  
  inmp441_connected = true;
  Serial.println("INMP441 I2S initialized");
}

void setup() {
  Serial.begin(115200);
  Serial.println("Sleep Tracker - ESP32 Starting...");
  Serial.println("INMP441 MEMS Microphone");
  
  // Initialize I2S for INMP441
  i2sInit();
  
  // Send initial status
  sendSensorStatus();
  
  delay(1000);
}

void loop() {
  unsigned long currentMillis = millis();
  
  // Check sensor status periodically
  if (currentMillis - lastStatusCheck >= STATUS_INTERVAL) {
    checkSensorStatus();
    sendSensorStatus();
    lastStatusCheck = currentMillis;
  }
  
  // Read audio data from INMP441
  if (inmp441_connected) {
    size_t bytes_read;
    i2s_read(I2S_NUM_0, i2s_read_buff, I2S_READ_LEN, &bytes_read, portMAX_DELAY);
    
    if (bytes_read > 0) {
      sendAudioData(i2s_read_buff, bytes_read);
    }
  }
}

void checkSensorStatus() {
  // Simple check - if I2S is installed, assume connected
  // In a real scenario, you might want to check for actual data
  inmp441_connected = true;
}

void sendSensorStatus() {
  Serial.print("STATUS:");
  Serial.print("INMP441=");
  Serial.print(inmp441_connected ? "1" : "0");
  Serial.println();
}

void sendAudioData(char* buffer, size_t bytes_read) {
  // Send audio data as base64 encoded for efficiency
  // Format: AUDIO:timestamp,base64_data
  Serial.print("AUDIO:");
  Serial.print(millis());
  Serial.print(",");
  
  // For simplicity, send raw bytes (in production, use base64)
  // Note: This is a simplified version - for real implementation,
  // you'd want to encode to base64 or send in chunks
  for (size_t i = 0; i < min(bytes_read, (size_t)512); i++) {
    Serial.print((int)buffer[i]);
    if (i < min(bytes_read, (size_t)512) - 1) Serial.print(",");
  }
  Serial.println();
}

