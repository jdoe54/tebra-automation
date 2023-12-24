# tebra-automation

Created in December 17th.

This script will add patient information to be used for importing into the website Patient360, a MIPS CMS Qualified Registry. 

First, it uses the Google API to connect to a spreadsheet. A config file is used to store private information.

CONFIG VARIABLES:
- TEBRA_PASSCODE is the password of the Tebra account that can access your practice.
- TEBRA_USER is the username of the Tebra account. This account must be a Systems Administrator in the practice portal.
- TEBRA_CUSTOMER_KEY is a special key given in the Kareo/Tebra portal. You can access this by going to Help -> Get Customer Key
- PATIENT_360_USER is the username of the Patient360 account.
- PATIENT_360_PASSCODE is the password of the Patient360 account.
- PATIENT_360_PROVIDER_TIN is the provider's taxpayer identification number. It is found on Patient360's Provider page.
- PATIENT_360_PROVIDER_NPI is the provider's national providers information. It is found on Patient360's Provider page.
- RANGE_NAME is for the first spreadsheet sheet, which has a list of all patient's names that you will import.
- SPREADSHEET_ID is the ID in the Google Sheets link address. EX: spreadsheets/d/[ID]/edit

After collecting each patient present on the Google Spreadsheet, it will then start collecting their information and tracking
when they encountered the provider. The encounter detail is taken and put into a new Sheet for each measure.

