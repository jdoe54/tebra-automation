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



# If modifying these scopes, delete the file token.json.
SCOPES = ["https://www.googleapis.com/auth/spreadsheets.readonly"]

# The ID and range of a sample spreadsheet.

WSDL = "https://webservice.kareo.com/services/soap/2.1/KareoServices.svc?wsdl"
insurances = []
names = {}
encounterRates = {}
praId = 1
praName = "Doe Medical Inc"

def getPatient(client, id):
  filter = client.get_type('ns1:SinglePatientFilter')
  reqhead = client.get_type('ns1:RequestHeader')
  getpatientreq = client.get_type('ns1:GetPatientReq')

  header_value = reqhead(ClientVersion = "2.0.8684.25480", CustomerKey=config.TEBRA_CUSTOMER_KEY, User=config.TEBRA_USER, Password=config.TEBRA_PASSCODE)
  filter_soap = filter(ExternalID = "1", ExternalVendorID = 1, PatientID = id)

  fullRequest = getpatientreq(RequestHeader = header_value, Filter = filter_soap)

  result = client.service.GetPatient(fullRequest)

  Insurance = result.Patient.Cases.PatientCaseData[0].InsurancePolicies.PatientInsurancePolicyData[0].CompanyName
  insurances.append(Insurance)
  return result

def getEncounters(client, id):
  details = client.get_type("ns1:GetEncounterDetailsReq")
  reqhead = client.get_type('ns1:RequestHeader')
  filter = client.get_type("ns1:EncounterDetailsFilter")
  practice = client.get_type("ns1:EncounterDetailsPractice")

  header_value = reqhead(ClientVersion = "2.0.8684.25480", CustomerKey=config.TEBRA_CUSTOMER_KEY, User=config.TEBRA_USER, Password=config.TEBRA_PASSCODE)
  practice_value = practice(PracticeID = praId, PracticeName = praName)
  filter_value = filter(EncounterID = id, Practice = practice_value)
  details_value = details(RequestHeader = header_value, Filter = filter_value)

  result = client.service.GetEncounterDetails(details_value)

  return result 

def main():
  """Shows basic usage of the Sheets API.
  Prints values from a sample spreadsheet.
  """
  client = Client(wsdl=WSDL)

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

    for row in cells:
      names[row[2]] = row[3]
      encounterRates[row[2]] = 0

    

  except HttpError as err:
    print(err)

  try:
    #28500
    encounterStart = 29600
    encounterEnd = 29650

    for id in range(encounterStart, encounterEnd):
      result = getEncounters(client, id)

      PatientId = result.EncounterDetails.EncounterDetailsData[0].PatientID
      if PatientId in names:
        
        encounterRates[PatientId] = encounterRates[PatientId] + 1
    
    print(encounterRates)
    
  
  except Exception as err:
    print(err)

 
  
 
if __name__ == "__main__":
  main()