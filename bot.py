import sys
import telebot
from tokenbot import token
from gsheets import senddata
from datetime import datetime

# Задаем токен для телебота и игнорируем висячие сообщения
bot = telebot.TeleBot(token, skip_pending=True)

# Листы с отделами и критичностью задач
departments = ["Администрация", "Администрация эл. журнала", "IT отдел", "Завхоз"]
criticals = ["Жизненно-необходимо", "Средняя важность", "В свободное время", "Вернуться назад"]
# Параметры, которые передаются дальше
datalist = ['От кого', 'в какой отдел', 'Критичность', 'Кабинет', 'Проблема']
# Режим работы
workdays = {'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sun', 'Sat'}
workhours = ['8', '20']

# ID чатов для пересылки сообщений о новых обращениях
chatids = [
    ["Администрация", 337998259],
    [
        "Администрация эл. журнала",
        "https://docs.google.com/spreadsheets/d/1Fsj8fp93V_R0rLY_xtUeMSKWrqQv5N1Igiy1kTrb9Iw",
    ],
    ["IT отдел", 283476064],
    ["Завхоз", "https://docs.google.com/spreadsheets/d/17ZJ6i08O_Ebg2py6FUHqul2Bp-rjbRxUq41mDrHhpN0"],
]


# Проверка рабочего времени бота
def check_worktime():
    weekday = datetime.now().strftime("%a")
    dayhour = datetime.now().strftime("%H")
    if weekday in workdays and int(dayhour) > int(workhours[0]) and int(dayhour) < int(workhours[1]):
        return True
    else:
        return False


@bot.message_handler(content_types=['text'])
def start_message(message):
    print(message.chat.id)
    if check_worktime():
        if str(message.text) != "/start":
            bot.send_message(
                message.chat.id,
                "Вероятнее всего возникла проблема, попробуйте начать сначала",
                reply_markup=startmarkup,
            )
        else:
            user_nik = str(message.from_user.username)
            # Приветствие собеседника!
            bot.send_message(message.chat.id, f"Здравствуйте, {message.chat.first_name}!")
            bot.send_message(message.chat.id, 'Выберите к кому хотите обратиться', reply_markup=depmarkup)
            bot.register_next_step_handler(message, critical_switch, user_nik)
    else:
        bot.send_message(
            message.chat.id,
            "Заявки принимаются только в рабочее время!\n(Пн-Пт с 8:00 до 20:00)",
            reply_markup=startmarkup,
        )


def critical_switch(message, user_nik):
    if check_worktime():
        dep = str(message.text)
        # Проверка на дурака
        if dep in departments:
            bot.send_message(message.chat.id, 'Укажите приоритетность вашего обращения', reply_markup=critmarkup)
            bot.register_next_step_handler(message, cabinet_input, user_nik, dep)
        else:
            bot.send_message(message.chat.id, 'Выберите из списка!', reply_markup=depmarkup)
            bot.register_next_step_handler(message, critical_switch, user_nik)
    else:
        bot.send_message(
            message.chat.id,
            "Заявки принимаются только в рабочее время!\n(Пн-Пт с 8:00 до 20:00)",
            reply_markup=startmarkup,
        )
        bot.register_next_step_handler(message, start_message)


def cabinet_input(message, user_nik, dep):
    if check_worktime():
        crit = str(message.text)
        # Проверка на дурака
        if crit in criticals:
            if crit == "Вернуться назад":
                bot.send_message(message.chat.id, 'Выберите к кому хотите обратиться', reply_markup=depmarkup)
                bot.register_next_step_handler(message, critical_switch, user_nik)
            else:
                bot.send_message(message.chat.id, 'Укажите кабинет', reply_markup=backmarkup)
                bot.register_next_step_handler(message, problem, user_nik, dep, crit)
        else:
            bot.send_message(message.chat.id, 'Выберите из списка!', reply_markup=critmarkup)
            bot.register_next_step_handler(message, cabinet_input, user_nik, dep)
    else:
        bot.send_message(
            message.chat.id,
            "Заявки принимаются только в рабочее время!\n(Пн-Пт с 8:00 до 20:00)",
            reply_markup=startmarkup,
        )
        bot.register_next_step_handler(message, start_message)


def problem(message, user_nik, dep, crit):
    if check_worktime():
        cab = str(message.text)
        # Проверка на дурака
        if cab[0] != '/':
            if cab == "Вернуться назад":
                bot.send_message(message.chat.id, 'Укажите приоритетность вашего обращения', reply_markup=critmarkup)
                bot.register_next_step_handler(message, cabinet_input, user_nik, dep)
            else:
                bot.send_message(message.chat.id, 'Опишите Вашу проблему')
                bot.register_next_step_handler(message, problem_message, user_nik, dep, crit, cab)
        else:
            bot.send_message(message.chat.id, 'Недопустимая команда, попробуйте указать кабинет без "/"')
            bot.register_next_step_handler(message, problem, user_nik, dep, crit)
    else:
        bot.send_message(
            message.chat.id,
            "Заявки принимаются только в рабочее время!\n(Пн-Пт с 8:00 до 20:00)",
            reply_markup=startmarkup,
        )
        bot.register_next_step_handler(message, start_message)


def problem_message(message, user_nik, dep, crit, cab):
    if check_worktime():
        prob = str(message.text)
        # Проверка на дурака
        if prob[0] != '/':
            if prob == "Вернуться назад":
                bot.send_message(message.chat.id, 'Укажите кабинет', reply_markup=backmarkup)
                bot.register_next_step_handler(message, problem, user_nik, dep, crit)
            else:
                bot.send_message(
                    message.chat.id,
                    'Спасибо за обращение, информация передана! Чтобы зарегистрировать новое обращение - нажмите "/start"',
                    reply_markup=startmarkup,
                )
                # Вызываем метод передачи данных в Гугл таблицы
                senddata(user_nik, dep, crit, cab, prob)

                # Поиск среди чатов и отправка уведомления начальнику отдела
                for i in range(0, len(chatids)):
                    if dep == chatids[i][0]:
                        bot.send_message(
                            chatids[i][1],
                            f"Вам поступило новое обращение от @{user_nik}\n{prob} в {cab}!",
                            reply_markup=startmarkup,
                        )
        else:
            bot.send_message(message.chat.id, 'Недопустимая команда, попробуйте начать описание не с "/"')
            bot.register_next_step_handler(message, problem_message, user_nik, dep, crit, cab)
    else:
        bot.send_message(
            message.chat.id,
            "Заявки принимаются только в рабочее время!\n(Пн-Пт с 8:00 до 20:00)",
            reply_markup=startmarkup,
        )
        bot.register_next_step_handler(message, start_message)


if __name__ == '__main__':
    # Проверка на наличие сетов
    if not departments or not criticals:
        sys.exit("Задай сеты кнопок с отделами и важностью!")

    # Создаем клаву для "/start"
    startmarkup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
    startbtn = telebot.types.KeyboardButton("/start")
    startmarkup.add(startbtn)
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
    # Создаем ккнопку назад
    backmarkup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
    backbtn = telebot.types.KeyboardButton("Вернуться назад")
    backmarkup.add(backbtn)

    # Запуск бота
    bot.infinity_polling()
