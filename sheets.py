import gspread
from google.oauth2.service_account import Credentials

def open_sheet():
    creds = Credentials.from_service_account_file(
        "secrets/google_credentials.json",
        scopes=["https://www.googleapis.com/auth/spreadsheets"]
    )
    client = gspread.authorize(creds)
    sheet_id = "1f-xhtzIHwd_gAJXugZBwsiiwo8Cz-rucs2h7Pk74KiQ"
    return client.open_by_key(sheet_id).sheet1

def append_row(row):
    sh = open_sheet()
    sh.append_row(row)
