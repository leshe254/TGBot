import gspread

#Привязка токена
Sheet_credential = gspread.service_account("tokengoogle.json")

#Функция подключения к таблице и записи в неё новых строк
def senddata(department, date, nikname, cabinet, critical, problem):
    spreadsheet = Sheet_credential.open_by_url("https://docs.google.com/spreadsheets/d/1H00lV5YvAA6wVHLankgA8zp5jHb0ktjMsi9aVrFiJRo")
    