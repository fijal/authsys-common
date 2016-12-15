#include <MFRC522.h>
#include <SPI.h>

/* minimum reader for MFRC522 */

#define SS_PIN 10
#define RST_PIN 9
MFRC522 mfrc522(SS_PIN, RST_PIN);	// Create MFRC522 instance.

void setup() {
  pinMode(8, OUTPUT);
  pinMode(7, OUTPUT);
	Serial.begin(9600);	// Initialize serial communications with the PC
	SPI.begin();			// Init SPI bus
	mfrc522.PCD_Init();	// Init MFRC522 card
	//Serial.print("Scan PICC to see UID and type...\n");
}

void loop()
{
   int response;
  
  // Look for new cards
  if ( ! mfrc522.PICC_IsNewCardPresent()) {
    return;
  }

  // Select one of the cards
  if ( ! mfrc522.PICC_ReadCardSerial()) {
    return;
  }

  for (byte i = 0; i < mfrc522.uid.size; i++) {
    if(mfrc522.uid.uidByte[i] < 0x10)
      Serial.print(F("0"));
    Serial.print(mfrc522.uid.uidByte[i], HEX);
  }
  if(mfrc522.uid.sak < 0x10)
    Serial.print(F("0"));
  Serial.print(mfrc522.uid.sak, HEX);
  Serial.write("\n");
  while (Serial.available() == 0)
    ;
  response = Serial.read();
  if (response == 'n') {
    digitalWrite(8, HIGH);
  } else {
    digitalWrite(7, HIGH);
  }
  delay(1000);
  digitalWrite(7, LOW);
  digitalWrite(8, LOW);
  mfrc522.PICC_HaltA();
  // Dump debug info about the card. PICC_HaltA() is automatically called.   
  //mfrc522.PICC_DumpToSerial(&(mfrc522.uid));
}

