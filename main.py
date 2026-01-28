import os
from datetime import datetime

import cv2
import telebot
from telebot import types
from ultralytics import YOLO
from PIL import Image
import psycopg2
import datetime

# Подключение к базе данных
conn = psycopg2.connect(dbname='', user='', password='', host='')

# Инициализация бота
bot = telebot.TeleBot('token')


# Функция для сохранения данных работника
def save_worker(worker_name, worker_post, worker_dr, worker_salary):
    cursor = conn.cursor()
    query = "INSERT INTO workers (worker_name, worker_post, worker_dr, worker_salary) VALUES (%s, %s, %s, %s)"
    cursor.execute(query, (worker_name, worker_post, worker_dr, worker_salary))
    conn.commit()
    cursor.close()

def save_violation_id(worker_id, worker_hardhat, worker_safety_vest):
    cursor = conn.cursor()
    current_time = datetime.datetime.now()
    query = "INSERT INTO violations (worker_id, timestamp, helmet_violation, vest_violation) VALUES (%s, %s, %s, %s)"
    cursor.execute(query, (worker_id, current_time, worker_hardhat, worker_safety_vest))
    conn.commit()
    cursor.close()

def save_violation_name(worker_name, worker_hardhat, worker_safety_vest):
    cursor = conn.cursor()
    current_time = datetime.datetime.now()

    # Запрос для получения worker_id
    query = "SELECT worker_id FROM workers WHERE worker_name LIKE %s"
    cursor.execute(query, (worker_name,))
    result = cursor.fetchone()

    if result:
        worker_id = result[0]

        # Запрос для вставки данных о нарушении
        query1 = "INSERT INTO violations (worker_id, timestamp, helmet_violation, vest_violation) VALUES (%s, %s, %s, %s)"
        cursor.execute(query1, (worker_id, current_time, worker_hardhat, worker_safety_vest))

        conn.commit()
    else:
        print("Работник с таким именем не найден.")

    cursor.close()


# Обработчик команды /start
@bot.message_handler(commands=['start'])
def handle_start(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    button_start = types.KeyboardButton("Запустить")
    button_check = types.KeyboardButton("Проверить")
    button_add = types.KeyboardButton("Добавить работника")
    #button_change = types.KeyboardButton("Изменить работника")
    markup.add(button_start, button_check, button_add) #button_change)
    bot.send_message(
        message.from_user.id,
        "Привет! Я бот, который поможет вам выявлять нарушения техники безопасности на производстве. 📸 "
        "Отправьте мне фотографию или видео человека, и я проверю, соблюдает ли он основные правила безопасности: "
        "есть ли у него каска и защитный жилет. "
        "Моя задача — облегчить контроль и помочь поддерживать безопасность на рабочем месте. "
        "Ваши данные защищены, а обработка занимает всего несколько секунд. "
        "Давайте вместе сделаем рабочие места безопаснее! 🦺⛑", reply_markup=markup
    )


# Обработчик текстовых сообщений
@bot.message_handler(content_types=['text'])
def handle_text(message):
    if message.text == "Проверить":
        keyboard = types.InlineKeyboardMarkup()
        key_id = types.InlineKeyboardButton(text='Ввести id работника', callback_data='id')
        key_new_id = types.InlineKeyboardButton(text='Ввести ФИО работника', callback_data='newid')
        keyboard.add(key_id, key_new_id)
        bot.send_message(message.from_user.id, "Выберите: ", reply_markup=keyboard)


    elif message.text == "Запустить":
        bot.send_message(
            message.from_user.id,
            "Привет! Я бот, который поможет вам выявлять нарушения техники безопасности на производстве. 📸 "
            "Отправьте мне фотографию или видео человека, и я проверю, соблюдает ли он основные правила безопасности: "
            "есть ли у него каска и защитный жилет. "
            "Моя задача — облегчить контроль и помочь поддерживать безопасность на рабочем месте. "
            "Ваши данные защищены, а обработка занимает всего несколько секунд. "
            "Давайте вместе сделаем рабочие места безопаснее! 🦺⛑"
        )

    elif message.text == "Добавить работника":
        bot.send_message(message.from_user.id, "Давайте добавим работника в базу данных!")
        msg = bot.send_message(message.chat.id, 'Введите ФИО работника (например, Иванов И.И.):')
        bot.register_next_step_handler(msg, process_worker_name)


# Переменные для хранения данных работника
worker_data = {}
def process_worker_name(message):
    worker_data['name'] = message.text
    msg = bot.send_message(message.chat.id, 'Введите должность работника:')
    bot.register_next_step_handler(msg, process_worker_post)


def process_worker_post(message):
    worker_data['post'] = message.text
    msg = bot.send_message(message.chat.id, 'Введите дату рождения работника (например, 1990-01-01):')
    bot.register_next_step_handler(msg, process_worker_dr)


def process_worker_dr(message):
    worker_data['dr'] = message.text
    msg = bot.send_message(message.chat.id, 'Введите зарплату работника:')
    bot.register_next_step_handler(msg, process_worker_salary)


def process_worker_salary(message):
    worker_data['salary'] = message.text
    # Сохранение данных работника в базе данных
    save_worker(worker_data['name'], worker_data['post'], worker_data['dr'], worker_data['salary'])
    bot.send_message(message.chat.id, "Работник успешно добавлен в базу данных!")



worker_violation = {}
# Обработчик нажатий на онлайн-кнопки
@bot.callback_query_handler(func=lambda call: True)
def callback_worker(call):
    if call.data == "id":
        msg = bot.send_message(call.message.chat.id, 'Отправьте id работника!')
        bot.register_next_step_handler(msg, search_id)
    elif call.data == "newid":
        msg = bot.send_message(call.message.chat.id, 'Введите ФИО работника!')
        bot.register_next_step_handler(msg, search_newid)


def search_id(message):
    worker_violation['worker'] = message.text
    # Сохранение данных работника в базе данных
    bot.send_message(message.chat.id, "Отправьте фото или видео!")

def search_newid(message):
    worker_violation['worker'] = message.text
    # Сохранение данных работника в базе данных
    bot.send_message(message.chat.id, "Отправьте фото или видео!")

# Обработчик отправки фотографий
@bot.message_handler(content_types=['photo'])
def handle_photo(message):
    file_info = bot.get_file(message.photo[-1].file_id)
    downloaded_file = bot.download_file(file_info.file_path)

    # Сохранение изображения
    src = 'safety.jpg'
    with open(src, 'wb') as new_file:
        new_file.write(downloaded_file)

    img = Image.open(src)
    img.save('safety.jpg')

    # Загрузка модели и выполнение предсказания
    model = YOLO('runs/detect/yolov8n_v1_train/weights/best.pt')
    results = model.predict(source=src, save=True, conf=0.5)

    # Определение целевых классов

    detected_classes = [model.names[int(det.cls)] for det in results[0].boxes]
    bot.reply_to(message, f"Фото обрабатывается!")

    if 'Hardhat' in detected_classes:
        bot.reply_to(message, f"Каска обнаружена на изображении.")
        worker_violation['worker_hardhat'] = True
    else:
        bot.reply_to(message, f"Каска не обнаружена на изображении.")
        worker_violation['worker_hardhat'] = False
    if 'Safety Vest' in detected_classes:
        bot.reply_to(message, f"Защитный жилет обнаружен на изображении.")
        worker_violation['worker_safety_vest'] = True
    else:
        bot.reply_to(message, f"Защитный жилет не обнаружен на изображении.")
        worker_violation['worker_safety_vest'] = False

    #проверка введен ли id или ФИО
    if worker_violation['worker'].isdigit()== True:
        save_violation_id(worker_violation['worker'], worker_violation['worker_hardhat'], worker_violation['worker_safety_vest'])
    else:
        save_violation_name(worker_violation['worker'], worker_violation['worker_hardhat'], worker_violation['worker_safety_vest'])

#обработчик видео
@bot.message_handler(content_types=['video'])
def handle_video(message):
    # Получаем информацию о файле видео
    file_info = bot.get_file(message.video.file_id)
    downloaded_file = bot.download_file(file_info.file_path)

    # Задаем путь для сохранения видео
    video_path = 'safety.mp4'
    with open(video_path, 'wb') as new_file:
        new_file.write(downloaded_file)

    bot.reply_to(message, "Видео обрабатывается!")

    # Загружаем модель YOLO (замени на нужный путь)
    model = YOLO('runs/detect/yolov8n_v1_train/weights/best.pt')

    # Открываем видео для покадровой обработки
    cap = cv2.VideoCapture(video_path)

    # Проверка, удалось ли открыть видео
    if not cap.isOpened():
        print("Ошибка при открытии видео.")
        return

    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break  # Конец видео
        # Выполнение предсказания на кадре
        results = model.predict(source=frame, save=True, conf=0.5)
        detected_classes = [model.names[int(det.cls)] for det in results[0].boxes]

    if 'Hardhat' in detected_classes:
        bot.reply_to(message, f"Каска обнаружена на видео.")
        worker_violation['worker_hardhat'] = True
    else:
        bot.reply_to(message, f"Каска не обнаружена на видео.")
        worker_violation['worker_hardhat'] = False
    if 'Safety Vest' in detected_classes:
        bot.reply_to(message, f"Защитный жилет обнаружен на видео.")
        worker_violation['worker_safety_vest'] = True
    else:
        bot.reply_to(message, f"Защитный жилет не обнаружен на видео.")
        worker_violation['worker_safety_vest'] = False

        # проверка введен ли id или ФИО
    if worker_violation['worker'].isdigit() == True:
        save_violation_id(worker_violation['worker'], worker_violation['worker_hardhat'],
                          worker_violation['worker_safety_vest'])
    else:
        save_violation_name(worker_violation['worker'], worker_violation['worker_hardhat'],
                            worker_violation['worker_safety_vest'])

    # Освобождаем ресурсы
    cap.release()
    cv2.destroyAllWindows()
# Запуск бесконечного поллинга
bot.infinity_polling()