import PySimpleGUI as sg
import random
import string
import sqlite3
import ast
from Crypto.Random import get_random_bytes
from Crypto.Protocol.KDF import PBKDF2
from Crypto.Cipher import AES
from passwords import PassStorage

layout = [
    # Блок текста и поля, в которое вводится мастер-ключ
    [sg.Text('Введите мастер-ключ:'), sg.InputText(key='-PASS-', )],

    [
        # Кнопка генерации мастер-ключа
        sg.Button('Сгенерировать мастер-ключ'),
        # Галочка использования в генерации цифр
        sg.Checkbox('Цифры', k='-NUMBER-'),
        # Галочка использования в генерации специальных символов
        sg.Checkbox('Спец. символы', k='-SPEC-'),
        # Галочка использования в генерации разных регистров
        sg.Checkbox('Разные регистры', k='-REGISTER-'),
        sg.Text('Длина мастер-ключа:', size=(16, 1), justification='r',
                pad=(0, 0)),
        # Список выбора длинны генерации мастер-ключа
        sg.Combo(['6', '8', '10', '12', '16'], default_value='12', s=(15, 22),
                 enable_events=True, readonly=True, k='-LENGTH-')
    ],
    # Кнопки шифровки и расшифровки мастер-ключа
    [sg.Button('Зашифровать'), sg.Button('Расшифровать')],
    [sg.Text(key='-TEXT-')],
]

# Придание окну разметки интерфейса
window = sg.Window('Шифрование слова', layout)

while True:
    event, values = window.read()

    # Завершения программы при нажатии на кнопку закрытия окна
    if event == sg.WINDOW_CLOSED:
        break

    elif event == 'Зашифровать':

        # Переменная password равна введённому в поле мастер-ключу
        password = values['-PASS-']
        # Переменная, отвечающая за подключение к базе данных
        conn = sqlite3.connect('password.db')
        # Создание объекта для выполнения операций с базой данных
        cursor = conn.cursor()
        # Функция выполнения SQL запросов
        conn.commit()

        def PassEncrypt(passwrd):
            passwrd = passwrd.encode("utf-8")
            # Генерация соли
            salt = get_random_bytes(32)
            # Занесение соли в базу данных
            cursor.execute(f"UPDATE password SET salt = '{list(salt)}';")
            conn.commit()
            # Генерация ключа на основе мастер-ключа и соли
            key = PBKDF2(passwrd, salt, dkLen=32)
            # Создание объекта и указание режима шифрования Cipher Feedback,
            # Который позволяет работать с данными меньше размера блока шифра
            cipherEncrypt = AES.new(key, AES.MODE_CFB)
            # Шифрование мастер-ключа с использованием объекта
            # cipherEncrypt и запись его в переменную cipheredBytes
            cipheredBytes = cipherEncrypt.encrypt(
                passwrd)
            # Запись зашифрованного мастер-ключа в базу данных
            cursor.execute(f"UPDATE password SET cipheredBytes = "
                           f"'{list(cipheredBytes)}';")
            conn.commit()
            iv = cipherEncrypt.iv
            # Запись iv в базу данных
            cursor.execute(f"UPDATE password SET iv = '{list(iv)}';")
            conn.commit()
            sg.popup("Ваш мастер-ключ успешно зашифрован!")


        def CheckDbExists():
            # Запрос для проверки существования базы данных
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' "
                           "AND name='password'")
            # Извлечение всех результатов запроса из объекта cursor
            tableExists = cursor.fetchall()

            if tableExists:

                dbInit = sg.popup("База данных инициализированна!")

                if dbInit == "OK":

                    # Очистка базы данных
                    cursor.execute("DELETE FROM password;")
                    conn.commit()
                    # заполение базы данных значениями NULL
                    cursor.execute(
                        """
                        INSERT INTO password (
                        salt,
                        iv,
                        cipheredBytes
                        ) 
                        VALUES (NULL, NULL, NULL);
                        """
                    )
                    conn.commit()
                    PassEncrypt(password)
                    return

            table = sg.popup("Создание необходимых таблиц!")

            if table == "OK":

                # Генерация таблицы и полей в ней
                createTable = """
                              CREATE TABLE password (
                              salt TEXT,
                              iv TEXT,
                              cipheredBytes TEXT
                              )
                              """
                cursor.execute(createTable)
                conn.commit()
                cursor.execute(
                    """
                    INSERT INTO password (
                    salt,
                    iv,
                    cipheredBytes
                    )
                    VALUES (NULL, NULL, NULL);
                    """
                )
                conn.commit()
                dbDone = sg.popup("База данных создана и настроена!")

                if dbDone == "OK":
                    CheckDbExists()


        def EmptyPassCheck():
            # Проверка, является ли поле ввода мастер-ключа пустым
            # или наполненным пробелами
            if password.strip() == '':
                newText = 'Вы не ввели мастер-ключ!'
                # Вывод уведомления об отсутствии мастер-ключа
                window['-TEXT-'].update(newText)
            else:
                # Очистка поля уведомления
                window['-TEXT-'].update('')
                CheckDbExists()

        EmptyPassCheck()

    elif event == 'Расшифровать':

        password = values['-PASS-']
        conn = sqlite3.connect('password.db')
        cursor = conn.cursor()
        conn.commit()

        def passDecrypt():
            passwordDecrypt = password.encode('utf-8')
            # Чтение соли из базы данных
            cursor.execute("SELECT salt FROM password;")
            # Запись соли в переменную
            saltDecrypt = bytes(ast.literal_eval(str(cursor.fetchall())[3:-4]))
            # Генерация ключа на основе мастер-ключа и расшифрованной соли
            keyDecrypt = PBKDF2(passwordDecrypt, saltDecrypt, dkLen=32)
            # Чтение iv из базы данных
            cursor.execute("SELECT iv FROM password")
            # Запись iv в переменную
            ivDecrypt = bytes(ast.literal_eval(str(cursor.fetchall())[3:-4]))
            # Чтение зашифрованного мастер-ключа из базы данных
            cursor.execute("SELECT cipheredBytes FROM password")
            # Запись зашифрованного мастер-ключа в переменную
            decryptedBytes = bytes(ast.literal_eval
                                   (str(cursor.fetchall())[3:-4]))
            # Создание объекта на основе расшифрованных ключа и iv
            cipherDecrypt = AES.new(keyDecrypt, AES.MODE_CFB, iv=ivDecrypt)
            # Расшифровка мастер-ключа
            decipheredBytes = cipherDecrypt.decrypt(decryptedBytes)

            # Проверка, сходятся ли расшифрованный мастер-ключ с введённым
            if decipheredBytes == values['-PASS-'].encode('utf-8'):

                login = sg.popup("Мастер-ключ успешно расшифрован")

                if login == "OK":

                    window.close()
                    PassStorage()

            else:

                sg.popup("Ошибка! Скорее всего Вы "
                         "ввели неправильный мастер-ключ!")
            return keyDecrypt

        passDecrypt()

    elif event == 'Сгенерировать мастер-ключ':

        def PassGen():
            # Запись в переменную выбранной длинны мастер-ключа
            passLength = int(values['-LENGTH-'])
            # Лист символов мастер-ключа
            genPass = []

            # Цикл генерации случайных символов
            for i in range(passLength):

                # Добавление в лист мастер-ключа случайных символов
                # латиницы нижнего регистра
                genPass.append(random.choice(string.ascii_lowercase))

                # Проверка, выбран ли параметр цифр
                if values['-NUMBER-']:

                    # Добавление в лист мастер-ключа случайных цифр
                    genPass.append(random.choice(string.digits))

                # Проверка, выбран ли параметр специальных знаков
                if values['-SPEC-']:

                    # Добавление в лист мастер-ключа
                    # случайных специальных знаков
                    genPass.append(random.choice(string.punctuation))

                # Проверка, выбран ли параметр верхнего регистра
                if values['-REGISTER-']:

                    # Добавление в лист мастер-ключа случайного
                    # символа верхнего регистра
                    genPass.append(random.choice(string.ascii_uppercase))

            # Перемешивание символов в случайном порядке в листе мастер-ключа
            random.shuffle(genPass)

            # Вывод сгенерированного мастер-ключа в поле ввода
            window['-PASS-'].update("".join(map(str, genPass))[:passLength])

        PassGen()

window.close()
