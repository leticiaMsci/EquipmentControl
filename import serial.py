#%%

""" 
//

const int  buttonPin = 5;    // the pin that the pushbutton is attached to
const int  ApathPin = 6;    // the pin that the pushbutton is attached 
const int  BpathPin = 7;    // the pin that the pushbutton is attached 
const int ledPin1 = 13; // the pin that the LED is attached to
const int ledPin2 = 4; // the pin that the LED is attached to
int incomingByte;      // a variable to read incoming serial data into
//
int Astate = 0;
int lastAstate = 0;
int Bstate = 0;
//button variables
int buttonPushCounter = 0;   // counter for the number of button presses
int buttonState = 0;         // current state of the button
int lastButtonState = 0;     // previous state of the button

//
void switch_state(int incByte) {
   if (incByte == 'A') {
      digitalWrite(ledPin1, HIGH);
      delay(50);
      digitalWrite(ledPin1, LOW);
    }  
    // if it's an L (ASCII 76) turn off the LED:
    if (incByte == 'B') {
      digitalWrite(ledPin2, HIGH);
      delay(50);
      digitalWrite(ledPin2, LOW);
}
}

void setup() {
  // initialize serial communication:
  Serial.begin(9600);
  // initialize the LED pin as an output:
  pinMode(ledPin1, OUTPUT);
  pinMode(ledPin2, OUTPUT);
  pinMode(buttonPin,INPUT_PULLUP);
  pinMode(ApathPin,INPUT_PULLUP);
  pinMode(BpathPin,INPUT_PULLUP);
}
//10-8 path  B
//10-7 path A
void loop() {
  //check status of optical paths
  Astate =  digitalRead(ApathPin);
  Bstate =  digitalRead(BpathPin);


    //******************************************
//  // compare the buttonState to its previous state
//  if (Astate != lastAstate) {
//    // if the state has changed, increment the counter
//    if (Astate == HIGH) {
//      Serial.print("A path (1->2, 4->3): ");
//      Serial.println(Astate);
//    } else {
//      // if the current state is LOW then the button went from on to off:
//        Serial.print("B path (1->3, 4->2): ");
//        Serial.println(Bstate);
//    }
//    // Delay a little bit to avoid bouncing
//    delay(50);
//  } // end if
//  lastAstate = Astate;
  //******************************************
  //button state
  buttonState = digitalRead(buttonPin);
  
  //******************************************
  // compare the buttonState to its previous state
  if (buttonState != lastButtonState) {
//    Serial.println(lastButtonState);
//    Serial.println(buttonState);
    Serial.println(buttonState-lastButtonState);
  
    if (Astate == LOW && Bstate == HIGH) {
      // change to B state
        if(buttonState-lastButtonState>0){
      switch_state('B');
      }
    } else if  (Astate == HIGH && Bstate == LOW){
      // if the current state is LOW then the button went from on to off:
      // change to B state
        if(buttonState-lastButtonState>0){
      switch_state('A');
      }
    }
    // Delay a little bit to avoid bouncing
    delay(200);
    Serial.print("A path (1->2, 4->3): ");
    Serial.println(Astate);
    Serial.print("B path (1->3, 4->2): ");
    Serial.println(Bstate);    
    lastButtonState = buttonState;
  } // end if
  delay(100);
  
  //******************************************

  //******************************************
  // see if there's incoming serial data:
  if (Serial.available() > 0) {
    // read the oldest byte in the serial buffer:
    incomingByte = Serial.read();
    // if it's an L (ASCII 76) turn off the LED:
    switch_state(incomingByte);
  }
   //******************************************
   
} """

# %%
import serial.tools.list_ports
ports = [comport.device for comport in serial.tools.list_ports.comports()]
print(ports)
# %%
import serial
import time
# Ensure the 'COM#' corresponds to what was seen in the Windows Device Manager
port = 'COM7'
# Define the serial port and baud rate.

# %%
def led_on_off(ser,user_input):
    if user_input =="A":
        print("LED is on...")
        time.sleep(0.1) 
        ser.write(b'A') 
    elif user_input =="B":
        print("LED is off...")
        time.sleep(0.1)
        ser.write(b'B')        
    else:
        print("Invalid input. Type on / off / quit.")      


# %%
ser = serial.Serial(port, 9600)

# %%
led_on_off(ser,'B')

# %% time.sleep(1)
ser.close()

# %% 
ser_bytes = ser.readline()
decoded_bytes = ser_bytes[0:len(ser_bytes)-2].decode("utf-8")
print(decoded_bytes)
# #led_on_off(ser,'B')
# %%
ser_bytes = ser.readline()
decoded_bytes = ser_bytes[0:len(ser_bytes)-2].decode("utf-8")
print(decoded_bytes)
# %%
ser = serial.Serial(port, 9600)
# %%
ser.close()
# %%
ser = serial.Serial(port, 9600)
for i in range(10):
    led_on_off(ser,'A')
    time.sleep(0.5)
    led_on_off(ser,'B')
    time.sleep(3)
ser.close()
# %%
led_on_off(ser,'B')

# %%
led_on_off(ser,'B')

# %%
def receiving(ser):
    global last_received

    buffer_string = ''
    while True:
        buffer_string = buffer_string + ser.read(ser.inWaiting())
        if '\n' in buffer_string:
            lines = buffer_string.split('\n') # Guaranteed to have at least 2 entries
            last_received = lines[-2]
            #If the Arduino sends lots of empty lines, you'll lose the
            #last filled line, so you could make the above statement conditional
            #like so: if lines[-2]: last_received = lines[-2]
            buffer_string = lines[-1]
# %%
receiving(ser)
# %%
