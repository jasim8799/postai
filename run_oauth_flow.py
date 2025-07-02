from google_auth_oauthlib.flow import InstalledAppFlow

flow = InstalledAppFlow.from_client_secrets_file(
    "client_secrets.json",
    scopes=["https://www.googleapis.com/auth/youtube.upload"]
)

# Use console flow for headless environment
credentials = flow.run_console()

# Save to file
with open("youtube_token.json", "w") as f:
    f.write(credentials.to_json())
