import gspread

#Привязка токена
Sheet_credential = gspread.service_account("tokengoogle.json")

#Двумерный массив с сопоставлением отдела и ссылки на таблицу
sheets = ["administration", "https://docs.google.com/spreadsheets/d/1H00lV5YvAA6wVHLankgA8zp5jHb0ktjMsi9aVrFiJRo"],
["ejournal" , "https://docs.google.com/spreadsheets/d/1Fsj8fp93V_R0rLY_xtUeMSKWrqQv5N1Igiy1kTrb9Iw"],
["it", "https://docs.google.com/spreadsheets/d/14NnC9nyCtADkD81q9RMFJKFfNz3RTo_egr3eO8GUQzk"],
["supmanager", "https://docs.google.com/spreadsheets/d/17ZJ6i08O_Ebg2py6FUHqul2Bp-rjbRxUq41mDrHhpN0"]

#Функция подключения к таблице и записи в неё новых строк
def senddata(department, date, nikname, cabinet, critical, problem):
    for department in sheets[0]:
        spreadsheet = Sheet_credential.open_by_url(sheets[department])
    