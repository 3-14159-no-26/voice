#include <WiFi.h>
#include <HTTP_Method.h>
#include <Uri.h>
#include <WebServer.h>
#include <ArduinoJson.h>
#include <Arduino.h>
#include <IRremoteESP8266.h>
#include <IRsend.h>
#include <ir_Daikin.h>

const uint16_t kIrLed = 4;  // ESP8266 GPIO pin to use. Recommended: 4 (D2).
IRsend irsend(kIrLed);  // Set the GPIO to be used to sending the message.
//IRDaikinESP ac(kIrLed);

const char *SSID = "COVID-19";
const char *PWD = "Think1995";
WebServer server(80);
void connectToWiFi() {
  Serial.print("Connecting to ");
  Serial.println(SSID);

  WiFi.begin(SSID, PWD);

  while (WiFi.status() != WL_CONNECTED) {
    Serial.print(".");
    delay(500);
    // we can even make the ESP32 to sleep
  }

  Serial.print("Connected. IP: ");
  Serial.println(WiFi.localIP());
}
void setup() {
  // put your setup code here, to run once:
  Serial.begin(115200);
  irsend.begin();
  //  ac.begin();
#if ESP8266
  Serial.begin(115200, SERIAL_8N1, SERIAL_TX_ONLY);
#else   // ESP8266
  Serial.begin(115200, SERIAL_8N1);
#endif  // ESP8266

  connectToWiFi();
  // server.on("/", getIR);

  //POST
  server.on("/", HTTP_POST, getIR);

  server.begin();
}

void getIR() {
  // POST 参数
  // {
  //   "mode": 1,
  //   "protocols": "sharp",
  //   "device": "tv",
  //   "signal": ["0x41A2","15","3"]
  // }
  // {
  //   "mode": 2,
  //   "protocols": "aircon",
  //   "device": "aircon",
  //   "signal": ["0x41A2","15","3"]
  // }
  // {
  //   "mode": 3,
  //   "protocols": "aircon",
  //   "device": "aircon",
  //   "signal": [508, 368,  456, 410,  458, 414,  454, 414,  456, 414,  454, 25372,  3524, 1718,  454, 1284,  458, 410,  454, 416,  480, 396,  456, 1276,  456, 412,  454, 414,  456, 412,  458, 414,  456, 1282,  454, 414,  456, 1280,  454, 1284,  454, 414,  456, 1282,  456, 1282,  456, 1284,  456, 1284,  456, 1284,  454, 420,  458, 402,  454, 1288,  454, 414,  454, 414,  456, 418,  452, 410,  454, 416,  454, 416,  454, 412,  456, 414,  456, 416,  454, 412,  454, 418,  454, 412,  456, 414,  456, 414,  454, 414,  456, 414,  454, 416,  454, 412,  456, 1284,  458, 410,  456, 414,  454, 416,  456, 410,  456, 412,  456, 412,  456, 418,  454, 412,  456, 1284,  454, 1284,  454, 412,  458, 1282,  454, 1282,  456, 414,  456, 414,  456, 410,  458, 414,  458, 410,  456, 412,  456, 414,  456, 412,  456, 414,  454, 414,  456, 414,  454, 416,  454, 416,  454, 410,  456, 416,  454, 1284,  456, 414,  456, 1282,  454, 414,  454, 412,  456, 418,  454, 412,  454, 412,  456, 412,  456, 414,  454, 412,  456, 414,  454, 414,  456, 412,  454, 412,  454, 414,  456, 414,  454, 412,  456, 412,  456, 418,  456, 412,  454, 414,  456, 414,  454, 412,  454, 416,  454, 414,  454, 414,  456, 414,  456, 410,  456, 416,  458, 410,  456, 412,  456, 414,  454, 416,  456, 410,  456, 418,  456, 410,  456, 410,  458, 412,  456, 414,  456, 414,  454, 414,  456, 412,  456, 416,  454, 414,  458, 412,  454, 416,  454, 414,  456, 412,  454, 412,  456, 412,  458, 1282,  456, 412,  456, 1282,  456, 414,  454, 412,  454, 416,  454, 1284,  456, 1284,  454, 414,  454, 416,  454, 412,  454, 412,  456, 414,  456, 412,  456, 412,  456, 414,  456, 412,  456, 414,  456, 412,  454, 1284,  454, 414,  454, 412,  456, 414,  456, 414,  456, 412,  454, 1286,  454, 1282,  456, 414,  454, 1284,  454, 1282,  456, 412,  456, 1284,  452]
  // }
  // 1. 获取请求体
  String body = server.arg("plain");
  Serial.println(body);
  // 2. 解析请求体
  // StaticJsonDocument<1000> doc;
  // 不限制大小 自動擴充
  Serial.println("內存大小" + String(ESP.getMaxAllocHeap()));
  DynamicJsonDocument doc(ESP.getMaxAllocHeap());
  deserializeJson(doc, body);
  // 3. 获取请求体中的参数
  int mode = doc["mode"];
  String protocols = doc["protocols"];
  String devices = doc["devices"];
  bool channel = doc["channel"];
  JsonArray signal = doc["signal"];
  // 4. 发送红外信号
  if (mode == 1) {
    // 使用IRremote.hpp模組
    if (devices == "fan") {
      if (protocols == "SYMPHONY") {
        //         irsend.sendSymphony(0xDC3,12 , 3);
        Serial.println(signal);
        irsend.sendSymphony((uint16_t)strtoul(signal[0], NULL, 16), (uint8_t)strtoul(signal[1], NULL, 10), (uint8_t)strtoul(signal[2], NULL, 10));
        Serial.println("SYMPHONY發送");
      }
    }
    // 如果 signal     "signal": [
    //   [
    //     "15",
    //     "0x4202",
    //     3
    //   ],
    //   [
    //     "15",
    //     "0x4102",
    //     3
    //   ]
    // ]

    if (devices == "tv") {
            if (channel == true) {
              for (int i = 0; i < signal.size(); i++) {
                if (protocols == "SHARP") {
                  irsend.sendSharpRaw((uint16_t)strtoul(signal[i][0], NULL, 16), (uint8_t)strtoul(signal[i][1], NULL, 10), (uint8_t)strtoul(signal[i][2], NULL, 10));
                  delay(100);
                }
              }
            } else {
              if (protocols == "SHARP") {
                irsend.sendSharpRaw((uint16_t)strtoul(signal[0], NULL, 16), (uint8_t)strtoul(signal[1], NULL, 10), (uint8_t)strtoul(signal[2], NULL, 10));
              }
            }
      Serial.println("SHARP發送");
//      Serial.println(signal[0].is<char*>());
    }
  }
  else if (mode == 2) {
    // 使用ir_Daikin.h模組
    //    ac.on();
    //    ac.setFan(kDaikinFanAuto);
    //    ac.setMode(kDaikinAuto);
    //    ac.setTemp(27);
    //    ac.setSwingVertical(false);
    //    ac.setSwingHorizontal(false);
    //    // Set the current time to 1:33PM (13:33)
    //    // Time works in minutes past midnight
    //    //  ac.setCurrentTime(13 * 60 + 33);
    //    // Turn off about 1 hour later at 2:30PM (14:30)
    //    //  ac.enableOffTimer(14 * 60 + 30);
    //    ac.disableOffTimer();
    //    ac.send();
  }
  else if (mode == 3) {
    // uint16_t rawData[319] = {508, 368,  456, 410,  458, 414,  454, 414,  456, 414,  454, 25372,  3524, 1718,  454, 1284,  458, 410,  454, 416,  480, 396,  456, 1276,  456, 412,  454, 414,  456, 412,  458, 414,  456, 1282,  454, 414,  456, 1280,  454, 1284,  454, 414,  456, 1282,  456, 1282,  456, 1284,  456, 1284,  456, 1284,  454, 420,  458, 402,  454, 1288,  454, 414,  454, 414,  456, 418,  452, 410,  454, 416,  454, 416,  454, 412,  456, 414,  456, 416,  454, 412,  454, 418,  454, 412,  456, 414,  456, 414,  454, 414,  456, 414,  454, 416,  454, 412,  456, 1284,  458, 410,  456, 414,  454, 416,  456, 410,  456, 412,  456, 412,  456, 418,  454, 412,  456, 1284,  454, 1284,  454, 412,  458, 1282,  454, 1282,  456, 414,  456, 414,  456, 410,  458, 414,  458, 410,  456, 412,  456, 414,  456, 412,  456, 414,  454, 414,  456, 414,  454, 416,  454, 416,  454, 410,  456, 416,  454, 1284,  456, 414,  456, 1282,  454, 414,  454, 412,  456, 418,  454, 412,  454, 412,  456, 412,  456, 414,  454, 412,  456, 414,  454, 414,  456, 412,  454, 412,  454, 414,  456, 414,  454, 412,  456, 412,  456, 418,  456, 412,  454, 414,  456, 414,  454, 412,  454, 416,  454, 414,  454, 414,  456, 414,  456, 410,  456, 416,  458, 410,  456, 412,  456, 414,  454, 416,  456, 410,  456, 418,  456, 410,  456, 410,  458, 412,  456, 414,  456, 414,  454, 414,  456, 412,  456, 416,  454, 414,  458, 412,  454, 416,  454, 414,  456, 412,  454, 412,  456, 412,  458, 1282,  456, 412,  456, 1282,  456, 414,  454, 412,  454, 416,  454, 1284,  456, 1284,  454, 414,  454, 416,  454, 412,  454, 412,  456, 414,  456, 412,  456, 412,  456, 414,  456, 412,  456, 414,  456, 412,  454, 1284,  454, 414,  454, 412,  456, 414,  456, 414,  456, 412,  454, 1286,  454, 1282,  456, 414,  454, 1284,  454, 1282,  456, 412,  456, 1284,  452};
    uint16_t rawData[signal.size()];

    for (int i = 0; i < signal.size(); i++) {
      rawData[i] = (uint16_t)signal[i];
    }

    irsend.sendRaw(rawData, signal.size(), 38);
    Serial.println("rawData發送");
  }

  // 5. 回傳接收到的参数
  server.send(200, "application/json", body);
}

void loop() {
  // put your main code here, to run repeatedly:
  server.handleClient();
}
