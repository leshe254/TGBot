import sys
import telebot
import time
from tokenbot import token
from gsheets import senddata
from datetime import datetime
from requests.exceptions import RequestException

# Задаем токен для телебота и игнорируем висячие сообщения
bot = telebot.TeleBot(token, skip_pending=True)

# Листы с отделами и критичностью задач
departments = ["Администрация", "Администрация эл. журнала", "IT отдел", "Завхоз"]
criticals = ["Жизненно-необходимо", "Средняя важность", "В свободное время", "Вернуться назад"]
# Параметры, которые передаются дальше
datalist = ['От кого', 'в какой отдел', 'Критичность', 'Кабинет', 'Проблема']
# Режим работы
workdays = {'Mon', 'Tue', 'Wed', 'Thu', 'Fri'}
workhours = ['8', '20']

# ID чатов для пересылки сообщений о новых обращениях
chatids = {
    "Администрация": 337998259,
    "Администрация эл. журнала": 362796634,
    "IT отдел": 283476064,
    "Завхоз": 5162642969,
}


# Проверка рабочего времени бота
def check_worktime():
    time = datetime.now()
    weekday = time.strftime("%a")
    dayhour = time.strftime("%H")
    if weekday in workdays and int(dayhour) > int(workhours[0]) and int(dayhour) < int(workhours[1]):
        return True
    else:
        return False


@bot.message_handler(content_types=['text'])
def start_message(message):
    # Перехват id чата для отправки уведомлений начальнику отдела
    print(message.chat.id)
    # Если сейчас рабочее время
    if check_worktime():
        # Если не пришла команда начать и пользователь без имени не поделился контактом
        if (str(message.text) != "/start") and (message.contact is None):
            # Если пользователь решил ввести текстом свой номер телдефона
            if str(message.text).isdigit() or (str(message.text))[0] == '+':
                bot.send_message(
                    message.chat.id,
                    "Номер вводить нет необходимости\nНажмите кнопку ниже",
                    reply_markup=phoneboard,
                )
            # Если бот перезапускался или другире проблемы - возвращаем его на старт
            else:
                bot.send_message(
                    message.chat.id,
                    "Похоже Вас долого не было\nНеобходимо повторно заполнить заявку",
                    reply_markup=startmarkup,
                )
            bot.register_next_step_handler(message, start_message)
        # Если пользователь прислал сообщение текстом
        else:
            user_nik = str(message.from_user.username)
            if user_nik == 'None':
                if message.contact is None:
                    # print("Пишет аккаунт без username")
                    bot.send_message(
                        message.chat.id,
                        "Оставьте Ваш номер чтобы мы смогли связаться с Вами.",
                        reply_markup=phoneboard,
                    )
                    bot.register_next_step_handler(message, start_message)
                else:
                    user_nik = "+" + str(message.contact.phone_number)
                    # Приветствие собеседника!
                    bot.send_message(message.chat.id, f"Здравствуйте, {message.chat.first_name}!")
                    bot.send_message(message.chat.id, "Выберите к кому хотите обратиться", reply_markup=depmarkup)
                    bot.register_next_step_handler(message, critical_switch, user_nik)
            else:
                # Приветствие собеседника!
                bot.send_message(message.chat.id, f"Здравствуйте, {message.chat.first_name}!")
                bot.send_message(message.chat.id, "Выберите к кому хотите обратиться", reply_markup=depmarkup)
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
            bot.send_message(message.chat.id, "Укажите приоритетность вашего обращения", reply_markup=critmarkup)
            bot.register_next_step_handler(message, cabinet_input, user_nik, dep)
        else:
            bot.send_message(message.chat.id, "Выберите из списка!", reply_markup=depmarkup)
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
                bot.send_message(message.chat.id, "Выберите к кому хотите обратиться", reply_markup=depmarkup)
                bot.register_next_step_handler(message, critical_switch, user_nik)
            else:
                bot.send_message(message.chat.id, "Укажите кабинет", reply_markup=backmarkup)
                bot.register_next_step_handler(message, problem, user_nik, dep, crit)
        else:
            bot.send_message(message.chat.id, "Выберите из списка!", reply_markup=critmarkup)
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
            # Проверка на наличие медиа-контента
            if cab == "None":
                bot.send_message(
                    message.chat.id,
                    "Мы пока не научили бота обрабатывать заявки с медиа-контентом =(\nПопробуйте указать кабинет текстом...",
                )
                bot.register_next_step_handler(message, problem, user_nik, dep, crit)
            elif cab == "Вернуться назад":
                bot.send_message(message.chat.id, 'Укажите приоритетность вашего обращения', reply_markup=critmarkup)
                bot.register_next_step_handler(message, cabinet_input, user_nik, dep)
            else:
                bot.send_message(message.chat.id, "Опишите Вашу проблему")
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
            # Проверка на наличие медиа-контента
            if prob == "None":
                bot.send_message(
                    message.chat.id,
                    "Мы пока не научили бота обрабатывать заявки с медиа-контентом =(\nПопробуйте описать проблему текстом...",
                    reply_markup=backmarkup,
                )
                bot.register_next_step_handler(message, problem_message, user_nik, dep, crit, cab)
            elif prob == "Вернуться назад":
                bot.send_message(message.chat.id, "Укажите кабинет", reply_markup=backmarkup)
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
                if chatids.get(dep) != None:
                    if user_nik[0] == '+':
                        bot.send_message(
                            chatids.get(dep),
                            f"Вам поступило новое обращение от {user_nik}\n{prob} в {cab}!",
                            reply_markup=startmarkup,
                        )
                    else:
                        bot.send_message(
                            chatids.get(dep),
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
    # Проверка на наличие листов
    if not departments or not criticals:
        sys.exit("Необходимо задать листы кнопок с отделами и важностью!")

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
    # Кнопка отправки номера
    phoneboard = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
    ph_button = telebot.types.KeyboardButton(text="Поделиться номером", request_contact=True)
    phoneboard.add(ph_button)

    # Запуск бота
    while True:
        try:
            bot.infinity_polling(timeout=90, long_polling_timeout=5)
        except RequestException:
            print("Разрыв коннекта до телеграмма...")
            time.sleep(15)
            print("Переподключение...")
