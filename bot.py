import sys
import time
from pathlib import Path
from datetime import datetime
from requests.exceptions import RequestException
from threading import Thread
import telebot
import numpy as np
from tokenbot import token
from gsheets import senddata

# Задаем токен для телебота и игнорируем висячие сообщения
bot = telebot.TeleBot(token, skip_pending=True)

# Листы с отделами и критичностью задач
departments = ["Администрация", "Администрация эл. журнала", "IT отдел", "Завхоз"]
# Режим работы
workdays = {'Mon', 'Tue', 'Wed', 'Thu', 'Fri'}
workhours = [8, 20]

# ID чатов для пересылки сообщений о новых обращениях
chatids = {
    "Администрация": 337998259,
    "Администрация эл. журнала": 362796634,
    "IT отдел": 283476064,
    "Завхоз": 5162642969,
}

# Словарь с номерами телефонов
phonesfile = Path("phones.npy")
phonedict = {}
# Словарь с очередью уведомлений
notificationfile = Path("notif.npy")
notificationqueue = {}


# Проверка рабочего времени бота
def check_worktime():
    time = datetime.now()
    weekday = time.strftime("%a")
    dayhour = time.hour
    if weekday in workdays and dayhour >= workhours[0] and dayhour < workhours[1]:
        return True


# Проверка начала рабочего времени (Для уведомлений)
def check_startwork():
    time = datetime.now()
    if time.hour == workhours[0] and time.minute == 0:
        return True


def tray():
    # Бесконечный цикл
    while True:
        # Сейчас самое начало рабочего дня (до минуты)
        if check_worktime() and check_startwork():
            # Отправляем всю очередь сообщений
            notify()
            time.sleep(60)
        else:
            time.sleep(30)


# Метод для отправки скопившихся уведомлений за момент, когда было не рабочее время (Вторичный процесс)
def notify():
    print("Проверка очереди уведомлений...")
    # Пытаемся загрузить сохранённую очередь обращений, если таковая есть
    if notificationfile.exists():
        notificationqueue = np.load(notificationfile, allow_pickle='TRUE').item()
        # Есть хоть одно обращение в очереди
        if len(notificationqueue) != 0:
            print(f"Очередь обращений загружена! {len(notificationqueue)} обращение(ий).")
            # Отправляем количество новых обращений по отделам
            for i in notificationqueue:
                if not notificationqueue.get(i) is None:
                    count = notificationqueue.get(i)
                    bot.send_message(
                        chatids.get(i),
                        f"Количество новых обращений в Ваш отдел в нерабочее время: {count}!",
                        reply_markup=startmarkup,
                    )
                else:
                    print("Обращений за вечер не было!")
            # Очищаем очередь обращений
            notificationqueue = {}
            np.save(notificationfile, notificationqueue)
    # Файлик с обращениями не создан
    else:
        print("Обращений за вечер не было!")


# Регистрация в очередь нового обращения
def newnotif(dep):
    # Окончательное время регистрации заявки
    time = datetime.now().strftime("%d %b %Y, %H:%M")
    # Добавляем новое уведомление в соответсвии с отделом
    if notificationqueue.get(dep) is None:
        notificationqueue[dep] = 1
    else:
        notificationqueue[dep] += 1
    print(f"{time}: Новое обращение добавлено в очередь!")
    np.save(notificationfile, notificationqueue)


@bot.message_handler(content_types=['text'])
def start_message(message):
    for i in chatids:
        if chatids.get(i) == message.chat.id:
            startmarkup = quickanswerboard
            break
    # Перехват id чата для отправки уведомлений начальнику отдела
    # print(message.chat.id)
    # Если не пришла команда начать и пользователь без имени не поделился контактом
    if (str(message.text) != "/start") and (message.contact is None) and str(message.text) != "Ответить":
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
    # Реагирование на ответ
    elif str(message.text) == "Ответить":
        bot.send_message(message.chat.id, 'Введите id для ответа!', reply_markup=backmarkup)
        bot.register_next_step_handler(message, id_answer)
    # Если пользователь прислал сообщение текстом
    else:
        user_nik = str(message.from_user.username)
        if user_nik == 'None':
            if message.contact is None:
                # print("Пишет аккаунт без username")
                if phonedict.get(message.chat.id) is None:
                    bot.send_message(
                        message.chat.id,
                        "Оставьте Ваш номер чтобы мы смогли связаться с Вами.",
                        reply_markup=phoneboard,
                    )
                    bot.register_next_step_handler(message, start_message)
                else:
                    user_nik = phonedict.get(message.chat.id)
                    bot.send_message(message.chat.id, f"Здравствуйте, {message.chat.first_name}!")
                    bot.send_message(message.chat.id, f'Твой номер "{user_nik}" ?', reply_markup=answerboard)
                    bot.register_next_step_handler(message, checknumber, user_nik)
            # Пользователь поделился контактом с нами
            else:
                user_nik = f"+{message.contact.phone_number}"
                # Приветствие собеседника!
                bot.send_message(message.chat.id, f"Здравствуйте, {message.chat.first_name}!")
                # Записываем номер в словарь и сохраняем
                bot.send_message(message.chat.id, "Мы записали Ваш номер!")
                phonedict[message.chat.id] = user_nik
                print(f"Добавлен новый номер телефона для {message.chat.id}: {user_nik}!")
                np.save(phonesfile, phonedict)
                bot.send_message(message.chat.id, "Выберите к кому хотите обратиться", reply_markup=depmarkup)
                bot.register_next_step_handler(message, cabinet_input, user_nik)
        else:
            # Приветствие собеседника!
            bot.send_message(message.chat.id, f"Здравствуйте, {message.chat.first_name}!")
            bot.send_message(message.chat.id, "Выберите к кому хотите обратиться", reply_markup=depmarkup)
            bot.register_next_step_handler(message, cabinet_input, user_nik)


# Проверка номера
def checknumber(message, user_nik):
    answer = str(message.text)
    # Если пользователь прислал медиа-контент
    if answer == "None":
        bot.send_message(
            message.chat.id,
            'Мы пока не научили бота обрабатывать заявки с медиа-контентом =(\nПопробуйте ответить "Да" или "Нет"...',
            reply_markup=answerboard,
        )
        bot.register_next_step_handler(message, checknumber, user_nik)
    # Если пользователь подтвердил свой номер телефона
    elif answer == "Да":
        bot.send_message(message.chat.id, "Выберите к кому хотите обратиться", reply_markup=depmarkup)
        bot.register_next_step_handler(message, cabinet_input, user_nik)
    # Если пользователь пишет, что номер ошибочный
    elif answer == "Нет":
        bot.send_message(message.chat.id, "Поделитесь Вашим номером!", reply_markup=phoneboard)
        bot.register_next_step_handler(message, newnumber)
    # Если пользователь написал что-то текстом
    else:
        bot.send_message(message.chat.id, 'Попробуйте ответить "Да" или "Нет"', reply_markup=answerboard)
        bot.register_next_step_handler(message, checknumber, user_nik)


# Сохранение нового номера
def newnumber(message):
    # Если пользователь прислал новый номер телефона
    if not message.contact is None:
        # Записываем номер в словарь и сохраняем
        bot.send_message(message.chat.id, "Ваш новый номер записан!")
        user_nik = f"+{message.contact.phone_number}"
        phonedict[message.chat.id] = user_nik
        print(f"Изменён номер телефона для {message.chat.id}: {user_nik}!")
        np.save(phonesfile, phonedict)
        # Возвращаемся к выбору отдела
        bot.send_message(message.chat.id, "Выберите к кому хотите обратиться", reply_markup=depmarkup)
        bot.register_next_step_handler(message, cabinet_input, user_nik)
    # Во всех других случая просим его снова поделиться номером
    else:
        bot.send_message(message.chat.id, 'Требуется нажать кнопку "Поделиться номером"!', reply_markup=phoneboard)
        bot.register_next_step_handler(message, newnumber)

# Сбор данных для ответа
def id_answer(message):
    ansid = str(message.text)
    # Пользователь нажал ответить и прислал id чата
    if ansid != "Вернуться назад":
        bot.send_message(message.chat.id, 'Введите ответ для обращения!', reply_markup=backmarkup)
        bot.register_next_step_handler(message, send_answer, ansid)
    # Пользователь выбрал ответить, но нажал кнопку назад
    else:
        bot.send_message(message.chat.id, 'Вы можете прислать ответ пользователю позже!', reply_markup=backmarkup)
        bot.register_next_step_handler(message, start_message)

# Ответ на обращение
def send_answer(message, ansid):
    anstext = str(message.text)
    # Пользватель нажал ответить, прислал id и ввел текст
    if anstext != "Вернуться назад":
        # Отправляем сообщение собеседнику
        bot.send_message(ansid, f'Вам поступил ответ на Ваше обращение:\n{anstext}', reply_markup=startmarkup)
        bot.send_message(message.chat.id, 'Ответ на обращение отправлен!', reply_markup=startmarkup)
        bot.register_next_step_handler(message, start_message)
    # Пользователь нажал ответить, прислал id и потом нажал назад, возвращаем его на ввод id
    else:
        bot.send_message(message.chat.id, 'Напишите "Ответить" если хотите ответить на обращение!', reply_markup=startmarkup)
        bot.register_next_step_handler(message, start_message)


def cabinet_input(message, user_nik):
    dep = str(message.text)
    # Проверка на дурака
    if dep in departments:
        bot.send_message(message.chat.id, "Укажите кабинет", reply_markup=backmarkup)
        bot.register_next_step_handler(message, problem, user_nik, dep)
    else:
        bot.send_message(message.chat.id, "Выберите из списка!", reply_markup=depmarkup)
        bot.register_next_step_handler(message, cabinet_input, user_nik)


def problem(message, user_nik, dep):
    cab = str(message.text)
    # Проверка на дурака
    if cab[0] != '/':
        # Проверка на наличие медиа-контента
        if cab == "None":
            bot.send_message(
                message.chat.id,
                "Мы пока не научили бота обрабатывать заявки с медиа-контентом =(\nПопробуйте указать кабинет текстом...",
            )
            bot.register_next_step_handler(message, problem, user_nik, dep)
        # Если пользователь решил вернуться назад
        elif cab == "Вернуться назад":
            bot.send_message(message.chat.id, "Выберите к кому хотите обратиться", reply_markup=depmarkup)
            bot.register_next_step_handler(message, cabinet_input, user_nik)
        # Если всё норм
        else:
            bot.send_message(message.chat.id, "Опишите Вашу проблему", reply_markup=backmarkup)
            bot.register_next_step_handler(message, problem_message, user_nik, dep, cab)
    # Если пользователь прислал команду
    else:
        bot.send_message(message.chat.id, 'Недопустимая команда, попробуйте указать кабинет без "/"')
        bot.register_next_step_handler(message, problem, user_nik, dep)

def problem_message(message, user_nik, dep, cab):
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
            bot.register_next_step_handler(message, problem_message, user_nik, dep, cab)
        # Если пользователь вместо проблемы - нажал назад
        elif prob == "Вернуться назад":
            bot.send_message(message.chat.id, "Укажите кабинет", reply_markup=backmarkup)
            bot.register_next_step_handler(message, problem, user_nik, dep)
        # Если проблема соответствует проблеме (не команда, не вернуться назад и не медиа-контент)
        else:
            # Делаем, чтобы в гугл таблице была ссылка для связи на ТГ
            if user_nik[0] != '+':
                tgurl = "https://t.me/" + user_nik
                senddata(tgurl, dep, cab, prob)
            # Если человек обращается с номером телефона
            else:
                # Вызываем метод передачи данных в Гугл таблицы
                senddata(user_nik, dep, cab, prob)
            if check_worktime():
                bot.send_message(
                    message.chat.id,
                    'Спасибо за обращение, информация передана!\nЧтобы зарегистрировать новое обращение - нажмите "/start"',
                    reply_markup=startmarkup,
                )
                # Поиск среди чатов и отправка уведомления начальнику отдела
                if user_nik[0] == '+':
                    bot.send_message(
                        chatids.get(dep),
                        f'Вам поступило новое обращение от {user_nik}\n{prob} в {cab}!\nДля ответа нажмите "Ответить"\n(id для ответа: {message.chat.id})',
                    )
                else:
                    bot.send_message(
                        chatids.get(dep),
                        f'Вам поступило новое обращение от @{user_nik}\n{prob} в {cab}!\nДля ответа нажмите "Ответить"\n(id для ответа: {message.chat.id})',
                    )
            # Не рабочее время (Заявки ставятся в очередь)
            else:
                newnotif(dep)
                bot.send_message(
                    message.chat.id,
                    'Спасибо за обращение!\nС Вами свяжутся в рабочее время!\nЧтобы зарегистрировать новое обращение - нажмите "/start"',
                    reply_markup=startmarkup,
                )

    # Пользователь прислал команду вместо описания проблемы
    else:
        bot.send_message(message.chat.id, 'Недопустимая команда, попробуйте начать описание не с "/"')
        bot.register_next_step_handler(message, problem_message, user_nik, dep, cab)


if __name__ == '__main__':
    # Проверка на наличие листов
    if not departments:
        sys.exit("Необходимо задать листы кнопок с отделами и важностью!")

    # Пытаемся загрузить сохранённые телефоны из книги номеров при запуске бота, если таковое есть
    if phonesfile.exists():
        phonedict = np.load(phonesfile, allow_pickle='TRUE').item()
        print(f"Телефонная книга с сохранёнными номерами успешно загружена! {len(phonedict)} номер(ов).")
    else:
        print("Телефонная книга с сохранёнными номерами пустая!")
    # Создаем клаву для "/start"
    startmarkup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
    startbtn = telebot.types.KeyboardButton("/start")
    startmarkup.add(startbtn)

    # Создаем клавиатуру для выбора отдела
    depmarkup = telebot.telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
    for department in departments:
        itemtmp = telebot.telebot.types.KeyboardButton(department)
        depmarkup.add(itemtmp)

    # Создаем ккнопку назад
    backmarkup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
    backbtn = telebot.types.KeyboardButton("Вернуться назад")
    backmarkup.add(backbtn)

    # Кнопка отправки номера
    phoneboard = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
    ph_button = telebot.types.KeyboardButton(text="Поделиться номером", request_contact=True)
    phoneboard.add(ph_button)

    # Кнопки "Да" или "Нет"
    answerboard = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
    yes_button = telebot.types.KeyboardButton("Да")
    no_button = telebot.types.KeyboardButton("Нет")
    answerboard.add(yes_button)
    answerboard.add(no_button)

    # Кнопки старт и "Ответить"
    quickanswerboard = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
    ansbtn = telebot.types.KeyboardButton("Ответить")
    quickanswerboard.add(startbtn)
    quickanswerboard.add(ansbtn)

    # В случае если бот не работал или по какой-то причине не были отправлены уведомления в начале рабочего дня
    if check_worktime():
        notify()

    # Демон висящих заявок
    t = Thread(target=tray, daemon=True)
    t.start()

    # Запуск бота
    bot.infinity_polling(none_stop=True, timeout=90, long_polling_timeout=5)
