from datetime import datetime
import telebot
from telebot import types
from tokenbot import token

bot=telebot.TeleBot(token)

@bot.message_handler(commands=['start'])
def start_message(message):
    time = int(datetime.now().strftime("%H"))
    user_first_name = str(message.chat.first_name)
    user_nik = str(message.from_user.username)
    #Приветствие собеседника!
    
    if(time > 18 & time < 24):
        bot.send_message(message.chat.id, f"Добрый вечер, {user_first_name}!")
    elif(time > 12 & time < 18):
        bot.send_message(message.chat.id, f"Добрый день, {user_first_name}!")
    elif(time > 6 & time < 12):
        bot.send_message(message.chat.id, f"Доброе утро, {user_first_name}!")
    elif(time > 0 & time < 6):
        bot.send_message(message.chat.id, f"Доброй ночи, {user_first_name}!")
    
    markup=types.ReplyKeyboardMarkup(resize_keyboard=True)
    item1=types.KeyboardButton("Администрация")
    item2=types.KeyboardButton("Администрация эл. журнала")
    item3=types.KeyboardButton("IT отдел")
    item4=types.KeyboardButton("Завхоз")
    markup.add(item1)
    markup.add(item2)
    markup.add(item3)
    markup.add(item4)
    bot.send_message(message.chat.id,'Выберите к кому хотите обратиться',reply_markup=markup)
    bot.register_next_step_handler(message, critical_switch);
    
    #Сценарий на все случаи жизни)))
def critical_switch(message):
        dep = str(message.text)
        markup=types.ReplyKeyboardMarkup(resize_keyboard=True)
        crit1=types.KeyboardButton("Жизненно-необходимо")
        crit2=types.KeyboardButton("Средняя важность")
        crit3=types.KeyboardButton("В свободное время")
        markup.add(crit1)
        markup.add(crit2)
        markup.add(crit3)
        bot.send_message(message.chat.id,'Укажите приоритетность вашего обращения',reply_markup=markup)
        bot.register_next_step_handler(message, cabinet_input);

def cabinet_input(message):
        bot.send_message(message.chat.id,'Введите номер кабинета', reply_markup=types.ReplyKeyboardRemove())
        bot.register_next_step_handler(message, problem);
        
def problem(message):
        bot.send_message(message.chat.id,'Опишите Вашу проблему')
        bot.register_next_step_handler(message, finish_message);
        
def finish_message(message):
        markup=types.ReplyKeyboardMarkup(resize_keyboard=True)
        new_problem=types.KeyboardButton("/start")
        markup.add(new_problem)
        bot.send_message(message.chat.id,'Спасибо за обращение, информация передана! Чтобы зарегистрировать новое обращение - нажмите "/start"',reply_markup=markup)
        #Тут должна быть отправка данных на сервер
bot.infinity_polling()