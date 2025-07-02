from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
import os

scopes = ["https://www.googleapis.com/auth/youtube.force-ssl"]

flow = InstalledAppFlow.from_client_secrets_file(
    "client_secret.json",
    scopes=scopes,
)

# OPTION 1 (console):
# creds = flow.run_console()

# OPTION 2 (browser popup):
creds = flow.run_local_server(port=0)

with open("token.json", "w") as token:
    token.write(creds.to_json())

print("✅ New token.json saved!")
