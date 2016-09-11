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

def main():
    lp = updateLittlePresents()
    polling_interval_in_minutes = 5
    number_of_loops = 0
    loop_interval_in_seconds = 30

    while(1):
        print('Looping: %s' % (number_of_loops))
        # This loop runs forever
        # It should check for updates to the sheet every 5 min (288 / day)
        # and check if there's anything to print every 1 minute (for accuracy)
        checkForDeliveries(lp)
        number_of_loops += 1

        if number_of_loops * (loop_interval_in_seconds / 60.0) >= polling_interval_in_minutes:
            print('Time to update')
            number_of_loops = 0
            lp = updateLittlePresents()

        time.sleep(loop_interval_in_seconds)

def checkForDeliveries(all_lps):
    print('Checking deliveries')
    # Get date in format found in google sheet
    now = datetime.datetime.now()

    current_day_string = now.strftime("%m/%d/%y")
    current_hour = int(now.strftime("%H"))
    am_pm = "pm" if current_hour >= 12 else "am"
    current_hour = `current_hour-12` if current_hour > 12 else `current_hour`
    current_minute = now.strftime("%M")
    current_time_string = "%s:%s %s" % (current_hour, current_minute, am_pm)

    # Get hour and minute string to compare with google sheet
    # current_hour =
    # current_minute
    for present in all_lps:
        delivery_day = present[0]
        delivery_time = present[1]
        message = present[2]

        if delivery_day == current_day_string and delivery_time == current_time_string:
            print('Printing a message!')
            print(message)
        else:
            print('Not a match')

def updateLittlePresents():
    """Shows basic usage of the Sheets API.

    Creates a Sheets API service object and prints the names and majors of
    students in a sample spreadsheet:
    https://docs.google.com/spreadsheets/d/1BxiMVs0XRA5nFMdKvBdBZjgmUUqptlbs74OgvE2upms/edit
    """

    print('Updating little presents')
    credentials = get_credentials()
    http = credentials.authorize(httplib2.Http())
    discoveryUrl = ('https://sheets.googleapis.com/$discovery/rest?'
                    'version=v4')
    service = discovery.build('sheets', 'v4', http=http,
                              discoveryServiceUrl=discoveryUrl)

    spreadsheetId = '1ivUi_2nw3gHs-9d1xL-sdOnaaAousjIgE8a4Bw9B2sI'
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


if __name__ == '__main__':
    main()
