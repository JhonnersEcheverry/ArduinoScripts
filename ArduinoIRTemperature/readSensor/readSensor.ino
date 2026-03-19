#include <Wire.h>
#include <Adafruit_MLX90614.h>
#include <Arduino_LED_Matrix.h>

namespace {
constexpr unsigned long READ_INTERVAL_MS = 30000UL;
constexpr uint8_t MATRIX_ROWS = 8;
constexpr uint8_t MATRIX_COLUMNS = 12;
constexpr uint8_t GLYPH_WIDTH = 3;
constexpr uint8_t GLYPH_HEIGHT = 5;
constexpr uint8_t GLYPH_TOP_OFFSET = 1;
constexpr unsigned int ERROR_BLINK_MS = 150;

const uint8_t DIGIT_FONT[10][GLYPH_HEIGHT] = {
  {0b111, 0b101, 0b101, 0b101, 0b111},  // 0
  {0b010, 0b110, 0b010, 0b010, 0b111},  // 1
  {0b111, 0b001, 0b111, 0b100, 0b111},  // 2
  {0b111, 0b001, 0b111, 0b001, 0b111},  // 3
  {0b101, 0b101, 0b111, 0b001, 0b001},  // 4
  {0b111, 0b100, 0b111, 0b001, 0b111},  // 5
  {0b111, 0b100, 0b111, 0b101, 0b111},  // 6
  {0b111, 0b001, 0b001, 0b001, 0b001},  // 7
  {0b111, 0b101, 0b111, 0b101, 0b111},  // 8
  {0b111, 0b101, 0b111, 0b001, 0b111},  // 9
};

const uint8_t LETTER_C[GLYPH_HEIGHT] = {
  0b111,
  0b100,
  0b100,
  0b100,
  0b111,
};

const uint8_t BLANK_GLYPH[GLYPH_HEIGHT] = {
  0b000,
  0b000,
  0b000,
  0b000,
  0b000,
};

const uint8_t ERROR_FRAME[MATRIX_ROWS][MATRIX_COLUMNS] = {
  {1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1},
  {0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0},
  {0, 0, 1, 0, 0, 0, 0, 0, 0, 1, 0, 0},
  {0, 0, 0, 1, 0, 0, 0, 0, 1, 0, 0, 0},
  {0, 0, 0, 0, 1, 0, 0, 1, 0, 0, 0, 0},
  {0, 0, 0, 0, 0, 1, 1, 0, 0, 0, 0, 0},
  {0, 0, 0, 0, 1, 0, 0, 1, 0, 0, 0, 0},
  {0, 0, 0, 1, 0, 0, 0, 0, 1, 0, 0, 0},
};

Adafruit_MLX90614 mlx;
ArduinoLEDMatrix matrix;
unsigned long lastReadMillis = 0;
uint8_t frameBuffer[MATRIX_ROWS][MATRIX_COLUMNS];

void clearFrameBuffer() {
  memset(frameBuffer, 0, sizeof(frameBuffer));
}

void drawGlyph(const uint8_t glyph[GLYPH_HEIGHT], uint8_t startColumn) {
  for (uint8_t row = 0; row < GLYPH_HEIGHT; ++row) {
    for (uint8_t column = 0; column < GLYPH_WIDTH; ++column) {
      bool pixelOn = (glyph[row] >> (GLYPH_WIDTH - 1 - column)) & 0x01;
      frameBuffer[GLYPH_TOP_OFFSET + row][startColumn + column] = pixelOn ? 1 : 0;
    }
  }
}

void showFrameBuffer() {
  matrix.loadPixels(&frameBuffer[0][0], sizeof(frameBuffer));
}

void showObjectTemperature(float objectTempC) {
  int roundedTemp = objectTempC >= 0 ? (int)(objectTempC + 0.5f)
                                     : (int)(objectTempC - 0.5f);
  roundedTemp = constrain(roundedTemp, 0, 99);

  uint8_t tens = roundedTemp / 10;
  uint8_t units = roundedTemp % 10;

  clearFrameBuffer();
  drawGlyph(tens > 0 ? DIGIT_FONT[tens] : BLANK_GLYPH, 0);
  drawGlyph(DIGIT_FONT[units], 4);
  drawGlyph(LETTER_C, 8);
  showFrameBuffer();
}

void printReadings(float ambientTempC, float objectTempC) {
  Serial.print(ambientTempC, 2);
  Serial.print(",");
  Serial.println(objectTempC, 2);
}

void readAndReportTemperature() {
  float ambientTempC = mlx.readAmbientTempC();
  float objectTempC = mlx.readObjectTempC();

  printReadings(ambientTempC, objectTempC);
  showObjectTemperature(objectTempC);
}

void haltOnSensorError() {
  matrix.loadPixels((uint8_t *)&ERROR_FRAME[0][0], sizeof(ERROR_FRAME));

  while (true) {
    digitalWrite(LED_BUILTIN, HIGH);
    delay(ERROR_BLINK_MS);
    digitalWrite(LED_BUILTIN, LOW);
    delay(ERROR_BLINK_MS);
  }
}
}  // namespace

void setup() {
  pinMode(LED_BUILTIN, OUTPUT);
  digitalWrite(LED_BUILTIN, LOW);

  Serial.begin(9600);
  delay(2000);

  if (!matrix.begin()) {
    Serial.println("ERROR,MATRIX");
    while (true) {
      digitalWrite(LED_BUILTIN, HIGH);
      delay(ERROR_BLINK_MS);
      digitalWrite(LED_BUILTIN, LOW);
      delay(ERROR_BLINK_MS);
    }
  }

  if (!mlx.begin()) {
    Serial.println("ERROR,ERROR");
    haltOnSensorError();
  }

  lastReadMillis = millis();
  readAndReportTemperature();
}

void loop() {
  unsigned long now = millis();

  if (now - lastReadMillis >= READ_INTERVAL_MS) {
    lastReadMillis = now;
    readAndReportTemperature();
  }
}
