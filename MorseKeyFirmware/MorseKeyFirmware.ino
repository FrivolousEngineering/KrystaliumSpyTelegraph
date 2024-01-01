#define buttonPin 7
#define buzzerPin A2

float dash_duration = 200.0;

long time_start_char;
long time_start_pauze;
boolean button_state;
boolean previous_button_state = false;
String kar = "";

static String letters[] = {
    ".-", "-...", "-.-.", "-..", ".", "..-.", "--.", "....", "..", ".---", "-.-", ".-..", "--", "-.", "---", ".--.", "--.-",
    ".-.", "...", "-", "..-", "...-", ".--", "-..-", "-.--", "--..", "E"
  };

void setup() {
  // put your setup code here, to run once:
  Serial.begin(115200);
  pinMode(buttonPin, INPUT_PULLUP);
  pinMode(buzzerPin, OUTPUT); //Set buzzerPin as output
  analogWrite(buzzerPin, 255);
}

void loop() {

  button_state = !digitalRead(buttonPin);

  if (button_state) 
  {
    if (button_state != previous_button_state) 
    {
      time_start_char = millis();
      decodePauze(time_start_pauze);
    }
    tone(buzzerPin, 4000);
  }
  else 
  {
    if (button_state != previous_button_state) 
    {
      time_start_pauze = millis();
      decode(time_start_char);

    noTone(buzzerPin);
    analogWrite(buzzerPin, 255);
    }
    

    //digitalWrite(BUZZER, LOW);
  }

  if (abs(millis() - time_start_pauze) > dash_duration * 10) 
  {
    decodePauze(time_start_pauze);
  }

  previous_button_state = button_state;
}

void decode(long start_time) 
{
  char teken = '?';
  long press_time = abs(millis() - start_time); 
  float dot_duration = dash_duration / 3.0;

  if (start_time <= 2)
  {
    return; // Ignore this, probably noise.
  }

  if (press_time <= dot_duration) teken = '.';
  else if (press_time > dash_duration) teken = '-';
  else if ((press_time > (dash_duration + dot_duration) / 1.9) && start_time <= dash_duration) teken = '-';
  else teken = '.';

  if (teken == '-') 
  {
    if (press_time > dash_duration) dash_duration++;
    if (press_time < dash_duration) dash_duration--;
  }
  else if (teken == '.') 
  {
    if (press_time > dash_duration / 3.0) dash_duration++;
    if (press_time < dash_duration / 3.0) dash_duration--;
  }
  kar += teken;
  Serial.print(teken);
}

void decodePauze(long start_time) 
{
  if (kar == "") return;

  char teken = '?';
  long time_difference = abs(millis() - start_time);
  if (time_difference > dash_duration - dash_duration / 40) 
  {
    decodeChracter();
    //Serial.print();
  }
  if (time_difference > dash_duration * 2) 
  {
    decodeChracter();
    Serial.println("");
  }
}

void decodeChracter() 
{
  int i = 0;
  while (letters[i] != "E") 
  {
    if (letters[i] == kar) 
    {
      Serial.print((char)('A' + i));
      break;
    }
    i++;
  }
  if (letters[i] == "E")
  {
    Serial.print(kar);
  }
  kar = "";
}
