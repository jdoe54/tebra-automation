import os.path
import requests
import config

# Google Sheet Imports
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# Zeep / Tebra Imports
from zeep import Client
from zeep import xsd

# Suds
#from suds.client import Client

from requests import Session
from requests.auth import HTTPBasicAuth
from zeep.transports import Transport




# If modifying these scopes, delete the file token.json.
SCOPES = ["https://www.googleapis.com/auth/spreadsheets.readonly"]

# The ID and range of a sample spreadsheet.

WSDL = "https://webservice.kareo.com/services/soap/2.1/KareoServices.svc?wsdl"


def main():
  """Shows basic usage of the Sheets API.
  Prints values from a sample spreadsheet.
  """
  creds = None
  # The file token.json stores the user's access and refresh tokens, and is
  # created automatically when the authorization flow completes for the first
  # time.
  if os.path.exists("token.json"):
    creds = Credentials.from_authorized_user_file("token.json", SCOPES)
  # If there are no (valid) credentials available, let the user log in.
  if not creds or not creds.valid:
    if creds and creds.expired and creds.refresh_token:
      creds.refresh(Request())
    else:
      flow = InstalledAppFlow.from_client_secrets_file(
          "credentials.json", SCOPES
      )
      creds = flow.run_local_server(port=0)
    # Save the credentials for the next run
    with open("token.json", "w") as token:
      token.write(creds.to_json())

  try:
    service = build("sheets", "v4", credentials=creds)

    # Call the Sheets API
    sheet = service.spreadsheets()
    result = (
        sheet.values()
        .get(spreadsheetId=config.SAMPLE_SPREADSHEET_ID, range=config.SAMPLE_RANGE_NAME)
        .execute()
    )
    cells = result.get("values", [])

    if not cells:
      print("No data found.")
      return

    # Now, get the Tebra SOAP API through the Customer Key
      

  except HttpError as err:
    print(err)

  try:
    url = "https://jsonplaceholder.typicode.com/posts/1"

    # A GET request to the API
    response = requests.get(url)

    # Print the response
    response_json = response.json()
    print(response_json)

  except HttpError as err:
    print(err)
  
  client = Client(wsdl=WSDL)
    
  filter = client.get_type('ns1:SinglePatientFilter')
  reqhead = client.get_type('ns1:RequestHeader')
  getpatientreq = client.get_type('ns1:GetPatientReq')

  header_value = reqhead(ClientVersion = "2.0.8684.25480", CustomerKey=config.TEBRA_CUSTOMER_KEY, User=config.TEBRA_USER, Password=config.TEBRA_PASSCODE)
  filter_soap = filter(ExternalID = "1", ExternalVendorID = 1, PatientID = 2746)

  fullRequest = getpatientreq(RequestHeader = header_value, Filter = filter_soap)

  result = client.service.GetPatient(fullRequest)


 
  
 
if __name__ == "__main__":
  main()