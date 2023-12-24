import os.path
import config
import json
import time

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
SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]

# The ID and range of a sample spreadsheet.

WSDL = "https://webservice.kareo.com/services/soap/2.1/KareoServices.svc?wsdl"

names = {}
encounterRates = {}
newRows = {}
PRACTICE_ID = 1
PRACTICE_NAME = "Doe Medical Inc"

def convertPayerName(name):
  # Function converts given name into acceptable name used for imports.

  if name == "UnitedHealthCare":
    return "United"
  elif name == "Medicare - California - Northern Region":
    return "Medicare Part B FFS"
  elif name == "Blue Cross - California (Anthem)":
    return "AnthemWellPoint"
  else:
    return "Other"

def changeMeasure(index):
  # Function provides a measure number based on the patient's number in the order of the first spreadsheet.

  if (index < 6):
    return 130
  elif (index < 11):
    return 155
  elif (index < 16):
    return 181
  elif (index < 21):
    return 286
  elif (index < 26):
    return 47
  else:
    return 493


def flipDateFormat(day):
  # Changes the date from MM/DD/YYYY to YYYY/MM/DD.
  
  newDay = ""
  slash = day.split("/")
  if len(slash[1]) == 1:
    slash[1] = "0" + slash[1]

  newDay = slash[2] + "/" + slash[0] + "/" + slash[1]

  return newDay

def getPatient(client, id):
  """
  # Provides the patient information using Kareo SOAP API.

  Args: 
    client: The WSDL client object passed.
    id: Patient ID.

  Returns:
    Patient info.
  """

  filter = client.get_type('ns1:SinglePatientFilter')
  reqhead = client.get_type('ns1:RequestHeader')
  getpatientreq = client.get_type('ns1:GetPatientReq')

  header_value = reqhead(ClientVersion = "2.0.8684.25480", CustomerKey=config.TEBRA_CUSTOMER_KEY, User=config.TEBRA_USER, Password=config.TEBRA_PASSCODE)
  filter_soap = filter(ExternalID = "1", ExternalVendorID = 1, PatientID = id)

  fullRequest = getpatientreq(RequestHeader = header_value, Filter = filter_soap)

  result = client.service.GetPatient(fullRequest)
 
  return result

def getEncounters(client, id):
  """
  # Provides encounter information from practice ID, name, and encounter ID.

  Args: 
    client: The WSDL client object passed.
    id: Encounter ID.

  Returns:
    Encounter details.
  """

  details = client.get_type("ns1:GetEncounterDetailsReq")
  reqhead = client.get_type('ns1:RequestHeader')
  filter = client.get_type("ns1:EncounterDetailsFilter")
  practice = client.get_type("ns1:EncounterDetailsPractice")

  header_value = reqhead(ClientVersion = "2.0.8684.25480", CustomerKey=config.TEBRA_CUSTOMER_KEY, User=config.TEBRA_USER, Password=config.TEBRA_PASSCODE)
  practice_value = practice(PracticeID = PRACTICE_ID, PracticeName = PRACTICE_NAME)
  filter_value = filter(EncounterID = id, Practice = practice_value)
  details_value = details(RequestHeader = header_value, Filter = filter_value)

  result = client.service.GetEncounterDetails(details_value)

  return result 

def updateSheet(paramRange, sheet, newEntry):
  # Enters new encounter details into the Google Spreadsheet, sheet can change based on param. newEntry is the encounter details.

  updateResult = (sheet.values().update(spreadsheetId=config.SPREADSHEET_ID, range=paramRange, valueInputOption = "USER_ENTERED", body = {"values": [newEntry]})).execute()
  return updateResult

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
        .get(spreadsheetId=config.SPREADSHEET_ID, range=config.RANGE_NAME)
        .execute()
    )
    cells = result.get("values", [])
    
    if not cells:
      print("No data found.")
      return

    indice = 1
    for row in cells:
      names[row[2]] = changeMeasure(indice)
      encounterRates[row[2]] = 0
      indice += 1
      if indice == 31:
        indice = 1

  except HttpError as err:
    print(err)

  
  # July dates start at 28500
  encounterStart = 28500
  encounterEnd = 29657
  newRowIndex = {}

  for id in range(encounterStart, encounterEnd):
 
    # This will create a row for a sheet in the spreadsheet.
    # Percentage is how many encounters have been parsed through.

    percentage = (id - encounterStart) / (encounterEnd - encounterStart) 
    print("Completion: " + str(percentage * 100) + "%")

    encounter = getEncounters(client, id)
    patientId = encounter.EncounterDetails.EncounterDetailsData[0].PatientID

    if patientId in names:

      time.sleep(0.5)
      patient = getPatient(client, encounter.EncounterDetails.EncounterDetailsData[0].PatientID)
      serviceDate = flipDateFormat(encounter.EncounterDetails.EncounterDetailsData[0].ServiceStartDate.split(" ")[0])

      if patient.Patient.Cases.PatientCaseData[0].InsurancePolicies != None:
        payerName = patient.Patient.Cases.PatientCaseData[0].InsurancePolicies.PatientInsurancePolicyData[0].CompanyName
        payerName = convertPayerName(payerName)
      else:
        payerName = "Other"
      
      birth = flipDateFormat(patient.Patient.DOB)
      code = 99350

      measureNumber = names[str(patientId)]

      row = {}
      row = [
        config.PATIENT_360_PROVIDER_NPI, 
        config.PATIENT_360_PROVIDER_TIN, 
        patientId,
        serviceDate, 
      ]

      # for 286, no birthday
      if measureNumber != 286:
        row.append(birth)

      row.append(payerName)

      # Encounter Code for 130, 155, 181, 47, 
      # 286 gets diagnosis code, 493 gets reporting criteria

      if measureNumber == 286:
        row.append("G30.9")
      elif measureNumber == 493:
        row.append("1")
        
      row.append(code)

      # Last
      if measureNumber == 130:
        row.append("G8427")
      elif measureNumber == 155:
        row.append("TRUE")
        row.append("FALSE")
        row.append("0518F")
      elif measureNumber == 181:
        row.append("TRUE")
        row.append("G8535")
      elif measureNumber == 286:
        row.append("G9922")
      elif measureNumber == 47:
        row.append("FALSE")
        row.append("TRUE")
        row.append("1123F") 
      elif measureNumber == 493:
        row.append("FALSE")
        row.append("FALSE")
        row.append("FALSE")
        row.append("FALSE")
        row.append("M1168") 

      if measureNumber in newRows:
        newRows[measureNumber].append(row)
      else:
        newRows[measureNumber] = [row]
        newRowIndex[measureNumber] = 2
      
      if patientId in names:
        updateSheet(str(measureNumber) + "!A" + str(newRowIndex[measureNumber]) + ":M", sheet, row)
        newRowIndex[measureNumber] += 1
        encounterRates[patientId] = encounterRates[patientId] + 1
  
 
if __name__ == "__main__":
  main()