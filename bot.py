from datetime import datetime
import telebot
from telebot import types
from tokenbot import token

bot=telebot.TeleBot(token)

departments = ["Администрация", "Администрация эл. журнала", "IT отдел", "Завхоз"]
criticals = ["Жизненно-необходимо", "Средняя важность", "В свободное время"]

@bot.message_handler(commands=['start'])
def start_message(message):
    user_first_name = str(message.chat.first_name)
    user_nik = str(message.from_user.username)
    bot.send_message(message.chat.id, f"Здравствуйте, {user_first_name}!") #Приветствие собеседника!
    
    if(len(departments) > 0): #Проверяем количество элементов массива "отделы"
        markup=types.ReplyKeyboardMarkup(resize_keyboard=True)
        for i in range(len(departments)): #Для каждого элемента перечня создаем кнопку
            itemtmp=types.KeyboardButton(departments[i])
            markup.add(itemtmp)
    bot.send_message(message.chat.id,'Выберите к кому хотите обратиться',reply_markup=markup)
    bot.register_next_step_handler(message, critical_switch)
    
    #Сценарий на все случаи жизни)))
def critical_switch(message):
        dep = str(message.text)
        if(dep in departments): #Проверка на дурака
            if(len(criticals) > 0): #Проверяем количество элементов массива "критичность задачи"
                markup=types.ReplyKeyboardMarkup(resize_keyboard=True)
                for i in range(len(criticals)): #Для каждого элемента перечня создаем кнопку
                    itemtmp=types.KeyboardButton(criticals[i])
                    markup.add(itemtmp)
            bot.send_message(message.chat.id,'Укажите приоритетность вашего обращения',reply_markup=markup)
            bot.register_next_step_handler(message, cabinet_input)
        else:
            if(len(departments) > 0): #Проверяем количество элементов массива "отделы"
                markup=types.ReplyKeyboardMarkup(resize_keyboard=True)
                for i in range(len(departments)): #Для каждого элемента перечня создаем кнопку
                    itemtmp=types.KeyboardButton(departments[i])
                    markup.add(itemtmp)
            bot.send_message(message.chat.id,'Выберите из списка!',reply_markup=markup)
            bot.register_next_step_handler(message, critical_switch)
        

def cabinet_input(message):
        crit = str(message.text)
        if(crit in criticals): #Проверка на дурака
            bot.send_message(message.chat.id,'Укажите кабинет', reply_markup=types.ReplyKeyboardRemove())
            bot.register_next_step_handler(message, problem)
        else:
            if(len(criticals) > 0): #Проверяем количество элементов массива "критичность задачи"
                markup=types.ReplyKeyboardMarkup(resize_keyboard=True)
                for i in range(len(criticals)): #Для каждого элемента перечня создаем кнопку
                    itemtmp=types.KeyboardButton(criticals[i])
                    markup.add(itemtmp)
            bot.send_message(message.chat.id,'Выберите из списка!',reply_markup=markup)
            bot.register_next_step_handler(message, cabinet_input)
        
def problem(message):
        cab = str(message.text)
        if(cab[0] != '/'): #Проверка на дурака
            bot.send_message(message.chat.id,'Опишите Вашу проблему')
            bot.register_next_step_handler(message, finish_message)
        else:
            bot.send_message(message.chat.id,'Недопустимая команда, попробуйте указать кабинет без "/"')
            bot.register_next_step_handler(message, problem)
        
def finish_message(message):
        prob = str(message.text)
        if(prob[0] != '/'): #Проверка на дурака
            time = datetime.now().strftime("%a, %d %b %Y %H:%M:%S") #Окончательное время регистрации заявки
            markup=types.ReplyKeyboardMarkup(resize_keyboard=True)
            new_problem=types.KeyboardButton("/start")
            markup.add(new_problem)
            bot.send_message(message.chat.id,'Спасибо за обращение, информация передана! Чтобы зарегистрировать новое обращение - нажмите "/start"',reply_markup=markup)
            #Тут должна быть отправка данных на сервер
        else:
            bot.send_message(message.chat.id,'Недопустимая команда, попробуйте начать описание не с "/"')
            bot.register_next_step_handler(message, finish_message) 

bot.infinity_polling()