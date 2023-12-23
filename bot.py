import os.path
import requests
import config
import json

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
insurances = []
names = {}
encounterRates = {}
newRows = {}
current = 130
praId = 1
praName = "Doe Medical Inc"

def changeMeasure(index):
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


def flipDateFormat(day, flip):
  newDay = ""
  slash = day.split("/")
  if len(slash[1]) == 1:
    slash[1] = "0" + slash[1]

  if flip:
    newDay = slash[2] + "/" + slash[1] + "/" + slash[0]
  else:
    newDay = slash[2] + "/" + slash[0] + "/" + slash[1]

  return newDay

def getPatient(client, id):
  filter = client.get_type('ns1:SinglePatientFilter')
  reqhead = client.get_type('ns1:RequestHeader')
  getpatientreq = client.get_type('ns1:GetPatientReq')

  header_value = reqhead(ClientVersion = "2.0.8684.25480", CustomerKey=config.TEBRA_CUSTOMER_KEY, User=config.TEBRA_USER, Password=config.TEBRA_PASSCODE)
  filter_soap = filter(ExternalID = "1", ExternalVendorID = 1, PatientID = id)

  fullRequest = getpatientreq(RequestHeader = header_value, Filter = filter_soap)

  result = client.service.GetPatient(fullRequest)


  #print(result.Patient.Cases.PatientCaseData[0].InsurancePolicies.PatientInsurancePolicyData[0])

  if result.Patient.Cases.PatientCaseData[0].InsurancePolicies != None:
    
    Insurance = result.Patient.Cases.PatientCaseData[0].InsurancePolicies.PatientInsurancePolicyData[0].CompanyName
    insurances.append(Insurance)
  else:
    insurances.append("None")
 

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

def updateSheet(paramRange, sheet, data, newEntry):
  print(paramRange)
  updateResult = (sheet.values().update(spreadsheetId=config.SAMPLE_SPREADSHEET_ID, range=paramRange, valueInputOption = "USER_ENTERED", body = {"values": [newEntry]})).execute()

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

    indice = 1
    

    for row in cells:
      
      names[row[2]] = changeMeasure(indice)
      encounterRates[row[2]] = 0
      indice += 1
      if indice == 31:
        indice = 1

  except HttpError as err:
    print(err)

  
  #28500
  measures = [130, 155, 181, 286, 47, 493]
  encounterStart = 29540
  newRowIndex = {}
  encounterEnd = 29650

  for id in range(encounterStart, encounterEnd):
    percentage = (id - encounterStart) / (encounterEnd - encounterStart) 
    print(percentage * 100)

    encounter = getEncounters(client, id)

    patientId = encounter.EncounterDetails.EncounterDetailsData[0].PatientID

    if patientId in names:

      patient = getPatient(client, encounter.EncounterDetails.EncounterDetailsData[0].PatientID)
      serviceDate = flipDateFormat(encounter.EncounterDetails.EncounterDetailsData[0].ServiceStartDate.split(" ")[0], False)

      print(encounter.EncounterDetails.EncounterDetailsData[0].ServiceStartDate.split(" ")[0])
      print(serviceDate)

      if patient.Patient.Cases.PatientCaseData[0].InsurancePolicies != None:
        payerName = patient.Patient.Cases.PatientCaseData[0].InsurancePolicies.PatientInsurancePolicyData[0].CompanyName
      else:
        payerName = "None"
      birth = flipDateFormat(patient.Patient.DOB, False)
      code = 99350

      
      measureNumber = names[str(patientId)]

      row = {}
      row = [
        config.PATIENT_360_PROVIDER_NPI, #"ProviderNPI": 
        config.PATIENT_360_PROVIDER_TIN, #"ProviderTIN": 
        patientId, #"PatientID": 
        serviceDate, #"DateOfService": 
        
      ]

      """
      birth, #"PatientBirth": 
        payerName, #"Payer": 
        code, #"EncounterCode": 
        "G8427", #"MeasureCode": 
        0, #"Measure"
      """
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
        row.append("TRUE")
        row.append("FALSE")
        row.append("1123F") 
      elif measureNumber == 493:
        row.append("FALSE")
        row.append("FALSE")
        row.append("FALSE")
        row.append("FALSE")
        row.append("M1168") 

      """
      if measureNumber == 181:
        row['Absence'] = "TRUE"
        row['MeasureCode'] = "G8535"
      elif measureNumber == 155:
        row['Screened'] = "TRUE"
        row['Service'] = "FALSE"
        row['MeasureCode'] = "0518F"
      elif measureNumber == 286:
        # Check if patient has Alzheimers
        row['DiagnosisCode'] = "G30.9"
        row['MeasureCode'] = "G9922" 
      elif measureNumber == 47:
        row['Service'] = "TRUE"
        row['Absence'] = "FALSE"
        row['MeasureCode'] = "1123F"
      """

      if measureNumber in newRows:
        newRows[measureNumber].append(row)
        
      else:
        newRows[measureNumber] = [row]
        newRowIndex[measureNumber] = 2
      
      # Algorithm 
      # Every 5 patient is the same measure. However, if t

      
      
      if patientId in names:
        updateSheet(str(measureNumber) + "!A" + str(newRowIndex[measureNumber]) + ":M", sheet, None, row)
        newRowIndex[measureNumber] += 1
        encounterRates[patientId] = encounterRates[patientId] + 1

      

  print(json.dumps(newRows, indent=4))
  
  

 
  
 
if __name__ == "__main__":
  main()