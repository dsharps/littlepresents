from __future__ import print_function
import httplib2
import os
import time
import datetime
import threading

from apiclient import discovery
import oauth2client
from oauth2client import client
from oauth2client import tools

import RPi.GPIO as GPIO
import subprocess, time, Image, socket
from Adafruit_Thermal import *

try:
    import argparse
    flags = argparse.ArgumentParser(parents=[tools.argparser]).parse_args()
except ImportError:
    flags = None

# If modifying these scopes, delete your previously saved credentials
# at ~/.credentials/sheets.googleapis.com-python-quickstart.json
SCOPES = 'https://www.googleapis.com/auth/spreadsheets.readonly'
CLIENT_SECRET_FILE = '../credentials/client_secret.json'
APPLICATION_NAME = 'Google Sheets API Python Quickstart'

ledPin                  = 18
buttonPin               = 23
holdTime                = 2     # Duration for button hold (shutdown)
tapTime                 = 0.01  # Debounce time for button taps
nextDeliveryInterval    = 0.0   # Time of next recurring delivery operation
nextUpdateInterval      = 0.0 # Time of next recurring update operation
dailyFlag               = False # Set after daily trigger occurs
lastId                  = '1'   # State information passed to/from interval script
printer                 = Adafruit_Thermal("/dev/ttyAMA0", 19200, timeout=5)
lp_list_for_maggie      = []
lp_list_for_dave        = []

# Called when button is briefly tapped.  Invokes time/temperature script.
def tap():
  pass
  #GPIO.output(ledPin, GPIO.HIGH)  # LED on while working
  #subprocess.call(["python", "timetemp.py"])
  #GPIO.output(ledPin, GPIO.LOW)


# Called when button is held down.  Prints image, invokes shutdown process.
def hold():
  GPIO.output(ledPin, GPIO.HIGH)
  printer.printImage(Image.open('gfx/goodbye.png'), True)
  printer.feed(3)
  subprocess.call("sync")
  subprocess.call(["shutdown", "-h", "now"])
  GPIO.output(ledPin, GPIO.LOW)


# Called at periodic intervals (30 seconds by default).
# Invokes twitter script.
def interval():
  pass
  #GPIO.output(ledPin, GPIO.HIGH)
  #p = subprocess.Popen(["python", "twitter.py", str(lastId)],
  #  stdout=subprocess.PIPE)
  #GPIO.output(ledPin, GPIO.LOW)
  #return p.communicate()[0] # Script pipes back lastId, returned to main


# Called once per day (6:30am by default).
# Invokes weather forecast and sudoku-gfx scripts.
def daily():
  pass
  #GPIO.output(ledPin, GPIO.HIGH)
  #subprocess.call(["python", "forecast.py"])
  #subprocess.call(["python", "sudoku-gfx.py"])
  #GPIO.output(ledPin, GPIO.LOW)


# Initialization

# Use Broadcom pin numbers (not Raspberry Pi pin numbers) for GPIO
GPIO.setmode(GPIO.BCM)

# Enable LED and button (w/pull-up on latter)
GPIO.setup(ledPin, GPIO.OUT)
GPIO.setup(buttonPin, GPIO.IN, pull_up_down=GPIO.PUD_UP)

# LED on while working
GPIO.output(ledPin, GPIO.HIGH)

# Processor load is heavy at startup; wait a moment to avoid
# stalling during greeting.
time.sleep(3)

# Show IP address (if network is available)
try:
	s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
	s.connect(('8.8.8.8', 0))
	printer.print('My IP address is ' + s.getsockname()[0])
	printer.feed(3)
except:
	printer.boldOn()
	printer.println('Network is unreachable.')
	printer.boldOff()
	printer.print('Connect display and keyboard\n'
	  'for network troubleshooting.')
	printer.feed(3)
	exit(0)

# Print greeting image
printer.printImage(Image.open('gfx/hello.png'), True)
printer.feed(3)
GPIO.output(ledPin, GPIO.LOW)

# Poll initial button state and time
prevButtonState = GPIO.input(buttonPin)
prevTime        = time.time()
tapEnable       = False
holdEnable      = False

def get_credentials():
    """Gets valid user credentials from storage.

    If nothing has been stored, or if the stored credentials are invalid,
    the OAuth2 flow is completed to obtain the new credentials.

    Returns:
        Credentials, the obtained credential.
    """
    home_dir = os.path.expanduser('~')
    credential_dir = os.path.join(home_dir, '.credentials')
    if not os.path.exists(credential_dir):
        os.makedirs(credential_dir)
    credential_path = os.path.join(credential_dir,
                                   'sheets.googleapis.com-python-quickstart.json')

    store = oauth2client.file.Storage(credential_path)
    credentials = store.get()
    if not credentials or credentials.invalid:
        flow = client.flow_from_clientsecrets(CLIENT_SECRET_FILE, SCOPES)
        flow.params['access_type'] = 'offline'
        flow.user_agent = APPLICATION_NAME
        if flags:
            credentials = tools.run_flow(flow, store, flags)
        else: # Needed only for compatibility with Python 2.6
            credentials = tools.run(flow, store)
        print('Storing credentials to ' + credential_path)
    return credentials

def checkForDeliveries(lp_list, addressee):
    #print('Checking deliveries')
    # Get date in format found in google sheet
    now = datetime.datetime.now()

    current_day_string = now.strftime("%m/%d/%y")
    current_hour = int(now.strftime("%H"))
    am_pm = "pm" if current_hour >= 12 else "am"
    current_hour = `current_hour-12` if current_hour > 12 else `current_hour`
    current_minute = now.strftime("%M")
    current_time_string = "%s:%s %s" % (current_hour, current_minute, am_pm)
    print('Checking deliveries for %s, it\'s %s, %s' % (addressee, current_day_string, current_time_string))
    print('LP found: %s' % (len(lp_list)))
    # Get date in format found in google sheet
    
    # Get hour and minute string to compare with google sheet
    # current_hour =
    # current_minute
    for present in lp_list:
        delivery_day = present[0]
        delivery_time = present[1]
        message = present[2]

        if delivery_day == current_day_string and delivery_time == current_time_string:
            GPIO.output(ledPin, GPIO.HIGH)
            
            print('Printing a message!')
            print(message)
            printer.feed(2)
            printer.boldOn()
            printer.println('For %s' % (addressee))
            printer.boldOff()
            printer.println('%s - %s' % (delivery_day, delivery_time))
            printer.feed(1)
            printer.print(message)
            printer.feed(2)
            printer.justify('C')
            printer.println('~ ~ ~ ~ ~')
            printer.justify('L')
            printer.feed(2)
            GPIO.output(ledPin, GPIO.LOW)
        else:
            print('Not a match')

def updateLittlePresents(sheetId, addressee):
    """Shows basic usage of the Sheets API.

    Creates a Sheets API service object and prints the names and majors of
    students in a sample spreadsheet:
    https://docs.google.com/spreadsheets/d/1BxiMVs0XRA5nFMdKvBdBZjgmUUqptlbs74OgvE2upms/edit
    """

    print('Updating little presents for %s' % (addressee))
    credentials = get_credentials()
    http = credentials.authorize(httplib2.Http())
    discoveryUrl = ('https://sheets.googleapis.com/$discovery/rest?'
                    'version=v4')
    service = discovery.build('sheets', 'v4', http=http,
                              discoveryServiceUrl=discoveryUrl)

    #spreadsheetId = '1ivUi_2nw3gHs-9d1xL-sdOnaaAousjIgE8a4Bw9B2sI'
    spreadsheetId = sheetId
    rangeName = 'Sheet1!A1:C11'
    result = service.spreadsheets().values().get(
        spreadsheetId=spreadsheetId, range=rangeName).execute()
    values = result.get('values', [])

    if not values:
        print('No data found.')
    else:
        # print(values)
        print('Little Presents: (%s)' % (len(values)))
        for row in values:
            # Print columns A and E, which correspond to indices 0 and 4.
            print('Delivery date: %s, Delivery time: %s, Message: %s' % (row[0], row[1], row[2]))
        return values


# Main loop
while(True):
  #print("Looping")
  # Poll current button state and time
  buttonState = GPIO.input(buttonPin)
  t           = time.time()

  # Has button state changed?
  if buttonState != prevButtonState:
    prevButtonState = buttonState   # Yes, save new state/time
    prevTime        = t
  else:                             # Button state unchanged
    if (t - prevTime) >= holdTime:  # Button held more than 'holdTime'?
      # Yes it has.  Is the hold action as-yet untriggered?
      if holdEnable == True:        # Yep!
        hold()                      # Perform hold action (usu. shutdown)
        holdEnable = False          # 1 shot...don't repeat hold action
        tapEnable  = False          # Don't do tap action on release
    elif (t - prevTime) >= tapTime: # Not holdTime.  tapTime elapsed?
      # Yes.  Debounced press or release...
      if buttonState == True:       # Button released?
        if tapEnable == True:       # Ignore if prior hold()
          tap()                     # Tap triggered (button released)
          tapEnable  = False        # Disable tap and hold
          holdEnable = False
      else:                         # Button pressed
        tapEnable  = True           # Enable tap and hold actions
        holdEnable = True

  # LED blinks while idle, for a brief interval every 2 seconds.
  # Pin 18 is PWM-capable and a "sleep throb" would be nice, but
  # the PWM-related library is a hassle for average users to install
  # right now.  Might return to this later when it's more accessible.
  if ((int(t) & 1) == 0) and ((t - int(t)) < 0.15):
    GPIO.output(ledPin, GPIO.HIGH)
  else:
    GPIO.output(ledPin, GPIO.LOW)

  # Once per day (currently set for 6:30am local time, or when script
  # is first run, if after 6:30am), run forecast and sudoku scripts.
  l = time.localtime()
  if (60 * l.tm_hour + l.tm_min) > (60 * 6 + 30):
    if dailyFlag == False:
      #daily()
      dailyFlag = True
  else:
    dailyFlag = False  # Reset daily trigger

  # Every 30 seconds, run Twitter scripts.  'lastId' is passed around
  # to preserve state between invocations.  Probably simpler to do an
  # import thing.
  if t > nextDeliveryInterval:
    nextDeliveryInterval = t + 60.0
    checkForDeliveries(lp_list_for_maggie, "Maggie")
    checkForDeliveries(lp_list_for_dave,   "Dave")

  if t > nextUpdateInterval:
    nextUpdateInterval = t + 300.0
    lp_list_for_maggie = updateLittlePresents('1ivUi_2nw3gHs-9d1xL-sdOnaaAousjIgE8a4Bw9B2sI', "Maggie")
    lp_list_for_dave   = updateLittlePresents('1HD0N7c02u4xXcoQAbaY5po3iDeKYiManfVSzsuUU7Ss', "Dave")
