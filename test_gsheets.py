import gspread
from google.oauth2.service_account import Credentials

# Имя вашей Google Таблицы
SPREADSHEET_NAME = "BotResponse"

# Области доступа
SCOPES = ['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive']

def main():
    creds = Credentials.from_service_account_file('google-credentials.json', scopes=SCOPES)
    client = gspread.authorize(creds)
    
    try:
        sheet = client.open(SPREADSHEET_NAME).sheet1
        print(f"Успешно подключились к таблице: {SPREADSHEET_NAME}")
        print(f"Название первого листа: {sheet.title}")
    except Exception as e:
        print(f"Ошибка при подключении к таблице: {e}")

if __name__ == "__main__":
    main()
