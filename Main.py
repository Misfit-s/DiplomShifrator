import PySimpleGUI as sg
import random
import string
import sqlite3
import ast
from Crypto.Random import get_random_bytes
from Crypto.Protocol.KDF import PBKDF2
from Crypto.Cipher import AES

layout = [ # Разметка интерфейса
    [sg.Text('Введите мастер-ключ:'), sg.InputText(key='-PASS-', )], # Блок текста и поля, в которое вводится мастер-ключ
    [sg.Button('Сгенерировать мастер-ключ'), sg.Checkbox('Цифры', k='-NUMBER-'), # Кнопка генерации мастер-ключа и галочка использования в генерации цифр
    sg.Checkbox('Спец. символы', k='-SPEC-'), sg.Checkbox('Разные регистры', k='-REGISTER-'), # Галочка использования в генерации специальных символов и галочка использования в генерации разных регистров
    sg.Text('Длина мастер-ключа:', size=(16, 1), justification='r',pad=(0,0)), 
    sg.Combo(['6','8','10','12','16'], default_value='12', s=(15,22), enable_events=True, readonly=True, k='-LENGTH-')], # Список выбора длинны генерации мастер-ключа
    [sg.Button('Зашифровать'), sg.Button('Расшифровать')], # Кнопки шифровки и расшифровки мастер-ключа
    [sg.Text(key='-TEXT-')] 
]

window = sg.Window('Шифрование слова', layout) # Придание окну разметки интерфейса

while True:
    event, values = window.read()
        
    if event == sg.WINDOW_CLOSED: # Указание завершения программы при нажатии на кнопку закрытия окна
        break
    
    elif event == 'Зашифровать':
        
        password = values['-PASS-'] # Переменная password будет равна введённому в поле мастер-ключу
        conn = sqlite3.connect('password.db') # Переменная, отвечающая за подключение к базе данных
        cursor = conn.cursor() # Создание объекта для выполнения операций с базой данных
        conn.commit() # Функция выполнения SQL запросов
                
        def PassEncrypt(password): # Функция шифрования мастер-ключа
            password = password.encode("utf-8") # Кодирование мастер-ключа в кодировку utf-8
            salt = get_random_bytes(32) # Генерация соли
            cursor.execute(f"UPDATE password SET salt = '{list(salt)}';"); conn.commit() # Занесение соли в базу данных
            key = PBKDF2(password, salt, dkLen=32) # Генерация ключа на основе мастер-ключа и соли
            cipher_encrypt = AES.new(key, AES.MODE_CFB) # Создание объекта и указание режима шифрования Cipher Feedback, который позволяет работать с данными меньше размера блока шифра.
            ciphered_bytes = cipher_encrypt.encrypt(password) # Шифрование мастер-ключа с использованием объекта cipher_encrypt и запись его в переменную ciphered_bytes
            cursor.execute(f"UPDATE password SET ciphered_bytes = '{list(ciphered_bytes)}';"); conn.commit() # Запись зашифрованного мастер-ключа в базу данных
            iv = cipher_encrypt.iv # Запись iv в переменную 
            cursor.execute(f"UPDATE password SET iv = '{list(iv)}';"); conn.commit() # Запись iv в базу данных
            sg.popup("Ваш мастер-ключ успешно зашифрован!") # Показ сообщения об успешности шифрования мастер-ключа
        
        def CheckDbExists(): # Функция проверки существования базы данных
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='password'") # Указание запроса для проверки существования базы данных
            table_exists = cursor.fetchall() # Извлечение всех результатов запроса из объекта cursor
            
            if table_exists: 
                dbInit = sg.popup("База данных инициализированна!") 
                if dbInit == "OK": 
                    cursor.execute("DELETE FROM password;"); conn.commit() # Очистка базы данных
                    cursor.execute("INSERT INTO password (salt, iv, ciphered_bytes) VALUES (NULL, NULL, NULL);"); conn.commit() # заполение базы данных значениями NULL
                    PassEncrypt(password) # Вызов функции шифрования пароля
                    return 
            
            table = sg.popup("Создание необходимых таблиц!",) 
            if table == "OK": 
                createTable = """CREATE TABLE password ( 
                              salt TEXT,
                              iv TEXT,
                              ciphered_bytes TEXT)""" # Генерация таблицы и полей в ней
                cursor.execute(createTable); conn.commit() # Указание и выполнение запроса на генерацию таблицы и полей
                cursor.execute("INSERT INTO password (salt, iv, ciphered_bytes) VALUES (NULL, NULL, NULL);"); conn.commit()
                dbDone = sg.popup("База данных создана и настроена!")
                if dbDone == "OK":
                    CheckDbExists() # Вызов функции проверки существования базы данных

        def EmptyPassCheck(): # Проверка на пустое поле ввода мастер-ключа
            if password.strip() == '': # Проверка, является ли поле ввода мастер-ключа пустым или наполненным пробелами 
                new_text = 'Вы не ввели мастер-ключ!' 
                window['-TEXT-'].update(new_text) # Вывод уведомления об отсутствии мастер-ключа
            else: 
                window['-TEXT-'].update('') # Очистка поля уведомления
                CheckDbExists() # Вызов функции проверки сушествования базы данных

                
        EmptyPassCheck() # Вызов функции проверки на пустое поле ввода мастер-ключа
        
    elif event == 'Расшифровать':
        
        password = values['-PASS-']
        conn = sqlite3.connect('password.db')
        cursor = conn.cursor()
        conn.commit()
        
        def passDecrypt(): # Функция расшифровки мастер-ключа
            passwordDecrypt = password.encode('utf-8') 
            cursor.execute("SELECT salt FROM password;"); saltDecrypt = bytes(ast.literal_eval(str(cursor.fetchall())[3:-4])) # Чтение соли из базы данных и запись в переменную
            keyDecrypt = PBKDF2(passwordDecrypt, saltDecrypt, dkLen=32) # Генерация ключа на основе мастер-ключа и расшифрованной соли
            cursor.execute("SELECT iv FROM password"); ivDecrypt = bytes(ast.literal_eval(str(cursor.fetchall())[3:-4])) # Чтение iv из базы данных и запись в переменную
            cursor.execute("SELECT ciphered_bytes FROM password"); DecryptedBytes = bytes(ast.literal_eval(str(cursor.fetchall())[3:-4])) # Чтение зашифрованного мастер-ключа из базы данных и запись в переменную
            cipher_decrypt = AES.new(keyDecrypt, AES.MODE_CFB, iv=ivDecrypt) # Создание объекта на основе расшифрованных ключа и iv
            deciphered_bytes = cipher_decrypt.decrypt(DecryptedBytes) # Расшифровка мастер-ключа
            if deciphered_bytes == values['-PASS-'].encode('utf-8'): # Проверка, сходятся ли расшифрованный мастер-ключ с введённым
                sg.popup("Мастер-ключ успешно расшифрован") 
            else:
                sg.popup("Ошибка! Скорее всего Вы ввели неправильный мастер-ключ!") 
            
        passDecrypt() # Вызов функции расшифровки мастер-ключа
        
    elif event == 'Сгенерировать мастер-ключ':
        
        def PassGen(): # Функция генерации мастер-ключа
            pass_length = int(values['-LENGTH-']) # Запись в переменную выбранной длинны мастер-ключа
            pswd = [] # Лист символов мастер-ключа
            
            for i in range(pass_length): # Цикл генерации случайных символов
                pswd.append(random.choice(string.ascii_lowercase)) # Добавление в лист мастер-ключа случайных символов латиницы нижнего регистра
                if values['-NUMBER-']: # Проверка, выбран ли параметр цифр
                    pswd.append(random.choice(string.digits)) # Добавление в лист мастер-ключа случайных цифр
                if values['-SPEC-']: # Проверка, выбран ли параметр специальных знаков
                    pswd.append(random.choice(string.punctuation)) # Добавление в лист мастер-ключа случайных специальных знаков
                if values['-REGISTER-']: # Проверка, выбран ли параметр верхнего регистра
                    pswd.append(random.choice(string.ascii_uppercase)) # Добавление в лист мастер-ключа случайного символа верхнего регистра
                    
            random.shuffle(pswd) # Перемешивание символов в случайном порядке в листе мастер-ключа
            
            window['-PASS-'].update("".join(map(str,pswd))[:pass_length]) # Вывод сгенерированного мастер-ключа в поле ввода
            
        PassGen() # Вызов функции генерации мастер-ключа

window.close()
