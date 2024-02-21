from datetime import datetime
import telebot
from telebot import types
from tokenbot import token

bot=telebot.TeleBot(token)

departments = ["Администрация", "Администрация эл. журнала", "IT отдел", "Завхоз"]
criticals = ["Жизненно-необходимо", "Средняя важность", "В свободное время"]

@bot.message_handler(commands=['start'])
def start_message(message):
    #Никнейм, будет использоваться позже
    user_nik = str(message.from_user.username)
    #Приветствие собеседника!
    bot.send_message(message.chat.id, f"Здравствуйте, {str(message.chat.first_name)}!") 
    #Проверяем количество элементов массива "отделы"
    if(len(departments) > 0): 
        markup=types.ReplyKeyboardMarkup(resize_keyboard=True)
        #Для каждого элемента перечня создаем кнопку
        for department in departments: 
            itemtmp=types.KeyboardButton(department)
            markup.add(itemtmp)
    bot.send_message(message.chat.id,'Выберите к кому хотите обратиться',reply_markup=markup)
    bot.register_next_step_handler(message, critical_switch)
    
#Сценарий на все случаи жизни
def critical_switch(message):
        dep = str(message.text)
        #Проверка на дурака
        if(dep in departments): 
            #Проверяем количество элементов массива "критичность задачи"
            if(len(criticals) > 0): 
                markup=types.ReplyKeyboardMarkup(resize_keyboard=True)
                #Для каждого элемента перечня создаем кнопку
                for critical in criticals: 
                    itemtmp=types.KeyboardButton(critical)
                    markup.add(itemtmp)
            bot.send_message(message.chat.id,'Укажите приоритетность вашего обращения',reply_markup=markup)
            bot.register_next_step_handler(message, cabinet_input)
        else:
            #Проверяем количество элементов массива "отделы"
            if(len(departments) > 0): 
                markup=types.ReplyKeyboardMarkup(resize_keyboard=True)
                #Для каждого элемента перечня создаем кнопку
                for department in departments: 
                    itemtmp=types.KeyboardButton(departments)
                    markup.add(itemtmp)
            bot.send_message(message.chat.id,'Выберите из списка!',reply_markup=markup)
            bot.register_next_step_handler(message, critical_switch)
        

def cabinet_input(message):
        crit = str(message.text)
        #Проверка на дурака
        if(crit in criticals): 
            bot.send_message(message.chat.id,'Укажите кабинет', reply_markup=types.ReplyKeyboardRemove())
            bot.register_next_step_handler(message, problem)
        else:
            #Проверяем количество элементов массива "критичность задачи"
            if(len(criticals) > 0): 
                markup=types.ReplyKeyboardMarkup(resize_keyboard=True)
                #Для каждого элемента перечня создаем кнопку
                for critical in criticals: 
                    itemtmp=types.KeyboardButton(critical)
                    markup.add(itemtmp)
            bot.send_message(message.chat.id,'Выберите из списка!',reply_markup=markup)
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
            markup=types.ReplyKeyboardMarkup(resize_keyboard=True)
            new_problem=types.KeyboardButton("/start")
            markup.add(new_problem)
            bot.send_message(message.chat.id,'Спасибо за обращение, информация передана! Чтобы зарегистрировать новое обращение - нажмите "/start"',reply_markup=markup)
            #Тут должна быть отправка данных на сервер
        else:
            bot.send_message(message.chat.id,'Недопустимая команда, попробуйте начать описание не с "/"')
            bot.register_next_step_handler(message, finish_message) 

bot.infinity_polling()