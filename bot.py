from datetime import datetime
import telebot
from tokenbot import token

bot=telebot.TeleBot(token)

#Сеты с отделами и критичностью задач
departments = ["Администрация", "Администрация эл. журнала", "IT отдел", "Завхоз"]
criticals = ["Жизненно-необходимо", "Средняя важность", "В свободное время"]


if __name__ == '__main__':
    #Проверка на наличие сетов
    if(len(departments) == True & len(criticals) == True):
        #Создаем клавиатуру для выбора отдела
        depmarkup=types.ReplyKeyboardMarkup(resize_keyboard=True)
        for department in departments: 
            itemtmp=types.KeyboardButton(department)
            depmarkup.add(itemtmp)
        #Создаем клавиатуру для выбора критичности
        critmarkup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        for critical in criticals: 
                itemtmp=types.KeyboardButton(critical)
                critmarkup.add(itemtmp)
        #Создаем клаву для "/start"
        startmarkup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        startbtn=types.KeyboardButton("/start")
        startmarkup.add(startbtn)
        #Запуск бота
        bot.infinity_polling()
    else:
         print("Задай сеты кнопок с отделами и важностью!")
         exit(1)


@bot.message_handler(commands=['start'])
def start_message(message):
    user_nik = str(message.from_user.username)
    #Приветствие собеседника!
    bot.send_message(message.chat.id, f"Здравствуйте, {str(message.chat.first_name)}!") 
    bot.send_message(message.chat.id,'Выберите к кому хотите обратиться',reply_markup=depmarkup)
    bot.register_next_step_handler(message, critical_switch)
    
    #Сценарий на все случаи жизни)))
def critical_switch(message):
        dep = str(message.text)
        #Проверка на дурака
        if(dep in departments): 
            bot.send_message(message.chat.id,'Укажите приоритетность вашего обращения',reply_markup=critmarkup)
            bot.register_next_step_handler(message, cabinet_input)
        else:
            bot.send_message(message.chat.id,'Выберите из списка!',reply_markup=depmarkup)
            bot.register_next_step_handler(message, critical_switch)
        

def cabinet_input(message):
        crit = str(message.text)
        #Проверка на дурака
        if(crit in criticals): 
            bot.send_message(message.chat.id,'Укажите кабинет', reply_markup=types.ReplyKeyboardRemove())
            bot.register_next_step_handler(message, problem)
        else:
            bot.send_message(message.chat.id,'Выберите из списка!',reply_markup=critmarkup)
            bot.register_next_step_handler(message, cabinet_input)
        
def problem(message):
        cab = str(message.text)
        #Проверка на дурака
        if(cab[0] != '/'): 
            bot.send_message(message.chat.id,'Опишите Вашу проблему')
            bot.register_next_step_handler(message, finish_message)
        else:
            bot.send_message(message.chat.id,'Недопустимая команда, попробуйте указать кабинет без "/"')
            bot.register_next_step_handler(message, problem)
        
def finish_message(message):
        prob = str(message.text)
        #Проверка на дурака
        if(prob[0] != '/'): 
            #Окончательное время регистрации заявки
            time = datetime.now().strftime("%a, %d %b %Y %H:%M:%S") 
            bot.send_message(message.chat.id,'Спасибо за обращение, информация передана! Чтобы зарегистрировать новое обращение - нажмите "/start"',reply_markup=startmarkup)
            #Тут должна быть отправка данных на сервер
        else:
            bot.send_message(message.chat.id,'Недопустимая команда, попробуйте начать описание не с "/"')
            bot.register_next_step_handler(message, finish_message)