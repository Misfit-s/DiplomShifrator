import PySimpleGUI as sg
import random
import string
import sqlite3
import ast
from Crypto.Random import get_random_bytes
from Crypto.Protocol.KDF import PBKDF2
from Crypto.Cipher import AES

# Разметка интерфейса
layout = [
    # Блок текста и поля, в которое вводится мастер-ключ
    [sg.Text('Введите мастер-ключ:'), sg.InputText(key='-PASS-', )],
    # Кнопка генерации мастер-ключа и галочка использования в генерации цифр
    [sg.Button('Сгенерировать мастер-ключ'), sg.Checkbox('Цифры', k='-NUMBER-'),
     # Галочка использования в генерации специальных символов
     # и галочка использования в генерации разных регистров
     sg.Checkbox('Спец. символы', k='-SPEC-'), sg.Checkbox('Разные регистры',
                                                           k='-REGISTER-'),
     sg.Text('Длина мастер-ключа:', size=(16, 1), justification='r',
             pad=(0, 0)),
     # Список выбора длинны генерации мастер-ключа
     sg.Combo(['6', '8', '10', '12', '16'], default_value='12', s=(15, 22),
              enable_events=True, readonly=True, k='-LENGTH-')],
    # Кнопки шифровки и расшифровки мастер-ключа
    [sg.Button('Зашифровать'), sg.Button('Расшифровать')],
    [sg.Text(key='-TEXT-')]
]

# Придание окну разметки интерфейса
window = sg.Window('Шифрование слова', layout)

while True:
    event, values = window.read()

    # Указание завершения программы при нажатии на кнопку закрытия окна
    if event == sg.WINDOW_CLOSED:
        break

    elif event == 'Зашифровать':

        # Переменная password будет равна введённому в поле мастер-ключу
        password = values['-PASS-']
        # Переменная, отвечающая за подключение к базе данных
        conn = sqlite3.connect('password.db')
        # Создание объекта для выполнения операций с базой данных
        cursor = conn.cursor()
        conn.commit()  # Функция выполнения SQL запросов

        # Функция шифрования мастер-ключа
        def PassEncrypt(passwrd):
            # Кодирование мастер-ключа в кодировку utf-8
            passwrd = passwrd.encode("utf-8")
            # Генерация соли
            salt = get_random_bytes(32)
            cursor.execute(f"UPDATE password SET salt = '{list(salt)}';")
            # Занесение соли в базу данных
            conn.commit()
            # Генерация ключа на основе мастер-ключа и соли
            key = PBKDF2(passwrd, salt, dkLen=32)
            # Создание объекта и указание режима шифрования Cipher Feedback,
            # Который позволяет работать с данными меньше размера блока шифра.
            cipher_encrypt = AES.new(key, AES.MODE_CFB)
            # Шифрование мастер-ключа с использованием объекта
            # cipher_encrypt и запись его в переменную ciphered_bytes
            ciphered_bytes = cipher_encrypt.encrypt(
                passwrd)
            cursor.execute(f"UPDATE password SET ciphered_bytes = "
                           f"'{list(ciphered_bytes)}';")
            # Запись зашифрованного мастер-ключа в базу данных
            conn.commit()
            # Запись iv в переменную
            iv = cipher_encrypt.iv
            cursor.execute(f"UPDATE password SET iv = '{list(iv)}';")
            # Запись iv в базу данных
            conn.commit()
            # Показ сообщения об успешности шифрования мастер-ключа
            sg.popup("Ваш мастер-ключ успешно зашифрован!")

        # Функция проверки существования базы данных
        def CheckDbExists():
            # Указание запроса для проверки существования базы данных
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' "
                           "AND name='password'")
            # Извлечение всех результатов запроса из объекта cursor
            table_exists = cursor.fetchall()

            if table_exists:
                dbInit = sg.popup("База данных инициализированна!")
                if dbInit == "OK":

                    cursor.execute("DELETE FROM password;")
                    # Очистка базы данных
                    conn.commit()
                    cursor.execute("""INSERT INTO password (
                                   salt,
                                   iv,
                                   ciphered_bytes) 
                                   VALUES (NULL, NULL, NULL);""")
                    # заполение базы данных значениями NULL
                    conn.commit()
                    # Вызов функции шифрования пароля
                    PassEncrypt(password)
                    return

            table = sg.popup("Создание необходимых таблиц!", )
            if table == "OK":

                # Генерация таблицы и полей в ней
                createTable = """CREATE TABLE password ( 
                              salt TEXT,
                              iv TEXT,
                              ciphered_bytes TEXT)"""
                cursor.execute(createTable)
                # Указание и выполнение запроса на генерацию таблицы и полей
                conn.commit()
                cursor.execute("""INSERT INTO password (
                               salt,
                               iv,
                               ciphered_bytes)
                               VALUES (NULL, NULL, NULL);""")
                conn.commit()
                dbDone = sg.popup("База данных создана и настроена!")
                if dbDone == "OK":

                    # Вызов функции проверки существования базы данных
                    CheckDbExists()

        # Проверка на пустое поле ввода мастер-ключа
        def EmptyPassCheck():
            # Проверка, является ли поле ввода мастер-ключа пустым
            # или наполненным пробелами
            if password.strip() == '':
                new_text = 'Вы не ввели мастер-ключ!'
                # Вывод уведомления об отсутствии мастер-ключа
                window['-TEXT-'].update(new_text)
            else:
                # Очистка поля уведомления
                window['-TEXT-'].update('')
                # Вызов функции проверки сушествования базы данных
                CheckDbExists()

        # Вызов функции проверки на пустое поле ввода мастер-ключа
        EmptyPassCheck()

    elif event == 'Расшифровать':

        password = values['-PASS-']
        conn = sqlite3.connect('password.db')
        cursor = conn.cursor()
        conn.commit()

        # Функция расшифровки мастер-ключа
        def passDecrypt():
            passwordDecrypt = password.encode('utf-8')
            cursor.execute("SELECT salt FROM password;")
            # Чтение соли из базы данных и запись в переменную
            saltDecrypt = bytes(ast.literal_eval(str(cursor.fetchall())[3:-4]))
            # Генерация ключа на основе мастер-ключа и расшифрованной соли
            keyDecrypt = PBKDF2(passwordDecrypt, saltDecrypt, dkLen=32)
            cursor.execute("SELECT iv FROM password")
            # Чтение iv из базы данных и запись в переменную
            ivDecrypt = bytes(ast.literal_eval(str(cursor.fetchall())[3:-4]))
            cursor.execute("SELECT ciphered_bytes FROM password")
            # Чтение зашифрованного мастер-ключа из базы данных
            # и запись в переменную
            DecryptedBytes = bytes(ast.literal_eval
                                   (str(cursor.fetchall())[3:-4]))
            # Создание объекта на основе расшифрованных ключа и iv
            cipher_decrypt = AES.new(keyDecrypt, AES.MODE_CFB, iv=ivDecrypt)
            # Расшифровка мастер-ключа
            deciphered_bytes = cipher_decrypt.decrypt(DecryptedBytes)

            # Проверка, сходятся ли расшифрованный мастер-ключ с введённым
            if deciphered_bytes == values['-PASS-'].encode('utf-8'):

                sg.popup("Мастер-ключ успешно расшифрован")

            else:

                sg.popup("Ошибка! Скорее всего Вы "
                         "ввели неправильный мастер-ключ!")

        # Вызов функции расшифровки мастер-ключа
        passDecrypt()

    elif event == 'Сгенерировать мастер-ключ':

        # Функция генерации мастер-ключа
        def PassGen():
            # Запись в переменную выбранной длинны мастер-ключа
            pass_length = int(values['-LENGTH-'])
            # Лист символов мастер-ключа
            GenPass = []

            # Цикл генерации случайных символов
            for i in range(pass_length):

                # Добавление в лист мастер-ключа случайных символов
                # латиницы нижнего регистра
                GenPass.append(random.choice(string.ascii_lowercase))

                # Проверка, выбран ли параметр цифр
                if values['-NUMBER-']:

                    # Добавление в лист мастер-ключа случайных цифр
                    GenPass.append(random.choice(string.digits))

                # Проверка, выбран ли параметр специальных знаков
                if values['-SPEC-']:

                    # Добавление в лист мастер-ключа
                    # случайных специальных знаков
                    GenPass.append(random.choice(string.punctuation))

                # Проверка, выбран ли параметр верхнего регистра
                if values['-REGISTER-']:

                    # Добавление в лист мастер-ключа случайного
                    # символа верхнего регистра
                    GenPass.append(random.choice(string.ascii_uppercase))

            # Перемешивание символов в случайном порядке в листе мастер-ключа
            random.shuffle(GenPass)

            # Вывод сгенерированного мастер-ключа в поле ввода
            window['-PASS-'].update("".join(map(str, GenPass))[:pass_length])

        # Вызов функции генерации мастер-ключа
        PassGen()

window.close()
