#include <FastLED.h>


#define NUM_LEDS 7
#define DATA_PIN 6

#define FRAMES_PER_SECOND 25

 
// The LED can be in only one of these states at any given time
#define BRIGHT                          0
#define UP                              1
#define DOWN                            2
#define DIM                             3
#define BRIGHT_HOLD                     4
#define DIM_HOLD                        5


// Percent chance the LED will suddenly fall to minimum brightness
#define FLICKER_BOTTOM_PERCENT          10
// Absolute minimum of the flickering
#define FLICKER_ABSOLUTE_MIN_INTENSITY  32
// Minimum intensity during "normal" flickering (not a dramatic change)
#define FLICKER_MIN_INTENSITY           128
// Maximum intensity of the flickering
#define FLICKER_MAX_INTENSITY           255


// Decreasing brightness will take place over a number of milliseconds in this range
#define DOWN_MIN_MSECS                  20
#define DOWN_MAX_MSECS                  250
// Increasing brightness will take place over a number of milliseconds in this range
#define UP_MIN_MSECS                    20
#define UP_MAX_MSECS                    250
// Percent chance the color will hold unchanged after brightening
#define BRIGHT_HOLD_PERCENT             20
// When holding after brightening, hold for a number of milliseconds in this range
#define BRIGHT_HOLD_MIN_MSECS           0
#define BRIGHT_HOLD_MAX_MSECS           100
// Percent chance the color will hold unchanged after dimming
#define DIM_HOLD_PERCENT                5
// When holding after dimming, hold for a number of milliseconds in this range
#define DIM_HOLD_MIN_MSECS              0
#define DIM_HOLD_MAX_MSECS              50

#define MINVAL(A,B)             (((A) < (B)) ? (A) : (B))
#define MAXVAL(A,B)             (((A) > (B)) ? (A) : (B))


#define COOLING  55 
#define SPARKING 20

CRGB leds[NUM_LEDS];

int active_led = -1;


byte state;
unsigned long flicker_msecs;
unsigned long flicker_start;
byte index_start;
byte index_end;

CRGBPalette16 currentPalette;


DEFINE_GRADIENT_PALETTE( gradient ) {
0, 0, 0, 255, // blue
240, 15, 0, 255, //slightly purple
255, 30, 0, 255 //slightly purple
};


const byte numChars = 32;
char receivedChars[numChars];

// variables to hold the parsed data
char command_type_sent[numChars] = {0};
int command_value = 0;
float floatFromPC = 0.0;

boolean newData = false;

void setup() { 
  FastLED.addLeds<WS2812, DATA_PIN, GRB>(leds, NUM_LEDS).setCorrection(TypicalLEDStrip);
  FastLED.clear(); 
  currentPalette = gradient;
  Serial.begin(115200);
}


void loop() { 
  recvWithStartEndMarkers();
  if (newData == true) {
    parseData();
    newData = false;
  }
  
  random16_add_entropy( random());
  FastLED.clear();
  handleLedFlickerBrightness(); 
  handleFlickerColor();
  

  FastLED.show(); // display this frame
  FastLED.delay(1000 / FRAMES_PER_SECOND);
}

void recvWithStartEndMarkers() {
  static byte ndx = 0;
  char rc;

  while (Serial.available() > 0 && newData == false) 
  {
    rc = Serial.read();

    if(rc != '\r' && rc != '\n') // Endline indicates end of command
    {
      receivedChars[ndx] = rc;
      ndx++;
      if (ndx >= numChars) 
      {
        ndx = numChars - 1;
      }
    }
    else 
    {
      receivedChars[ndx] = '\0'; // terminate the string
      ndx = 0;
      newData = true;
    } 
  }
}


void parseData() {      // split the data into its parts
  char * strtokIndx; // this is used by strtok() as an index

  strtokIndx = strtok(receivedChars, " ");      // Get the command type

  String command(strtokIndx);

  strtokIndx = strtok(NULL, " "); // this continues where the previous call left off
  command_value = atoi(strtokIndx);     // convert this part to an integer

  if(command == "light")
  {
    Serial.print("Setting active light to: ");
    Serial.println(command_value);
    active_led = command_value;
  }

}

void handleFlickerColor()
{
  if(active_led == -1)
  {
    return; // do nothing
  }

  static byte heat;
  // "cool down a little"
  heat = qsub8( heat,  random8(0, ((COOLING * 10)) + 2));
  byte colorindex = scale8( heat, 248);

  if ( random8() < SPARKING ) {
    heat = qadd8( heat, random8(160, 255) );
  }

  leds[active_led] = ColorFromPalette( currentPalette, colorindex);
  
}


void setFlickerState(byte new_state)
{
  state = new_state;
}


void setFlickerIntensity(byte intensity)
{
  intensity = MAXVAL(MINVAL(intensity, FLICKER_MAX_INTENSITY), FLICKER_ABSOLUTE_MIN_INTENSITY);

  FastLED.setBrightness(intensity);
}

void handleLedFlickerBrightness()
{
  unsigned long current_time = millis();; 
  switch (state)
  {
    case BRIGHT:
    {   
      //Serial.println("Bright"); 
      flicker_msecs = random(DOWN_MAX_MSECS - DOWN_MIN_MSECS) + DOWN_MIN_MSECS;
      flicker_start = current_time;
      index_start = index_end;
      if (index_start > FLICKER_ABSOLUTE_MIN_INTENSITY && random(100) < FLICKER_BOTTOM_PERCENT)
      {
        index_end = random(index_start - FLICKER_ABSOLUTE_MIN_INTENSITY) + FLICKER_ABSOLUTE_MIN_INTENSITY;
      } else {
        index_end = random(index_start- FLICKER_MIN_INTENSITY) + FLICKER_MIN_INTENSITY;
      }
 
      setFlickerState(DOWN);
      break;  
    }  
    case DIM:
    {
      //Serial.println("Dim");
      flicker_msecs = random(UP_MAX_MSECS - UP_MIN_MSECS) + UP_MIN_MSECS;
      flicker_start = current_time;
      index_start = index_end;
      index_end = random(FLICKER_MAX_INTENSITY - index_start) + FLICKER_MIN_INTENSITY;
      setFlickerState(UP);
      break;
    }
    case BRIGHT_HOLD:  
    case DIM_HOLD:
    {
      //Serial.println("DIM Hold");
      if (current_time >= (flicker_start + flicker_msecs))
      {
        setFlickerState(state == BRIGHT_HOLD ? BRIGHT : DIM); 
      }
      break;
    }
    case UP:
    case DOWN:
    {
      //  Serial.println("Down");
      if (current_time < (flicker_start + flicker_msecs)) {
        setFlickerIntensity(index_start + ((index_end - index_start) * (((current_time - flicker_start) * 1.0) / flicker_msecs)));
      } else {
        setFlickerIntensity(index_end);
 
        if (state == DOWN)
        {
          if (random(100) < DIM_HOLD_PERCENT)
          {
            flicker_start = current_time;
            flicker_msecs = random(DIM_HOLD_MAX_MSECS - DIM_HOLD_MIN_MSECS) + DIM_HOLD_MIN_MSECS;
            setFlickerState(DIM_HOLD);
          } else {
            setFlickerState(DIM);
          } 
        } else {
          if (random(100) < BRIGHT_HOLD_PERCENT)
          {
            flicker_start = current_time;
            flicker_msecs = random(BRIGHT_HOLD_MAX_MSECS - BRIGHT_HOLD_MIN_MSECS) + BRIGHT_HOLD_MIN_MSECS;
            setFlickerState(BRIGHT_HOLD);
          } else {
            setFlickerState(BRIGHT);
          }
        }
      }
      break;
    }
  }
}
