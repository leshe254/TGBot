import sys
import telebot
from tokenbot import token
from gsheets import senddata

bot = telebot.TeleBot(token)

# Сеты с отделами и критичностью задач
departments = {"Администрация", "Администрация эл. журнала", "IT отдел", "Завхоз"}
criticals = {"Жизненно-необходимо", "Средняя важность", "В свободное время"}


@bot.message_handler(commands=['start'])
def start_message(message):
    user_nik = str(message.from_user.username)
    # Приветствие собеседника!
    bot.send_message(message.chat.id, f"Здравствуйте, {message.chat.first_name}!")
    bot.send_message(message.chat.id, 'Выберите к кому хотите обратиться', reply_markup=depmarkup)
    bot.register_next_step_handler(message, critical_switch, user_nik)

    # Сценарий на все случаи жизни)))


def critical_switch(message, user_nik):
    dep = str(message.text)
    # Проверка на дурака
    if dep in departments:
        bot.send_message(message.chat.id, 'Укажите приоритетность вашего обращения', reply_markup=critmarkup)
        bot.register_next_step_handler(message, cabinet_input, user_nik, dep)
    else:
        bot.send_message(message.chat.id, 'Выберите из списка!', reply_markup=depmarkup)
        bot.register_next_step_handler(message, critical_switch, user_nik)


def cabinet_input(message, user_nik, dep):
    crit = str(message.text)
    # Проверка на дурака
    if crit in criticals:
        bot.send_message(message.chat.id, 'Укажите кабинет', reply_markup=telebot.types.ReplyKeyboardRemove())
        bot.register_next_step_handler(message, problem, user_nik, dep, crit)
    else:
        bot.send_message(message.chat.id, 'Выберите из списка!', reply_markup=critmarkup)
        bot.register_next_step_handler(message, cabinet_input, user_nik, dep)


def problem(message, user_nik, dep, crit):
    cab = str(message.text)
    # Проверка на дурака
    if cab[0] != '/':
        bot.send_message(message.chat.id, 'Опишите Вашу проблему')
        bot.register_next_step_handler(message, problem_message, user_nik, dep, crit, cab)
    else:
        bot.send_message(message.chat.id, 'Недопустимая команда, попробуйте указать кабинет без "/"')
        bot.register_next_step_handler(message, problem, user_nik, dep, crit)


def problem_message(message, user_nik, dep, crit, cab):
    prob = str(message.text)
    # Проверка на дурака
    if prob[0] != '/':
        bot.send_message(
            message.chat.id,
            'Спасибо за обращение, информация передана! Чтобы зарегистрировать новое обращение - нажмите "/start"',
            reply_markup=startmarkup,
        )
        # Вызываем метод передачи данных в Гугл таблицы
        senddata(user_nik, dep, crit, cab, prob)
    else:
        bot.send_message(message.chat.id, 'Недопустимая команда, попробуйте начать описание не с "/"')
        bot.register_next_step_handler(message, problem_message, user_nik, dep, crit, cab)


if __name__ == '__main__':
    # Проверка на наличие сетов
    if not departments or not criticals:
        sys.exit("Задай сеты кнопок с отделами и важностью!")

    # Создаем клавиатуру для выбора отдела
    depmarkup = telebot.telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
    for department in departments:
        itemtmp = telebot.telebot.types.KeyboardButton(department)
        depmarkup.add(itemtmp)
    # Создаем клавиатуру для выбора критичности
    critmarkup = telebot.telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
    for critical in criticals:
        itemtmp = telebot.telebot.types.KeyboardButton(critical)
        critmarkup.add(itemtmp)
    # Создаем клаву для "/start"
    startmarkup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
    startbtn = telebot.types.KeyboardButton("/start")
    startmarkup.add(startbtn)
    # Запуск бота
    bot.infinity_polling()
