import PySimpleGUI as sg
import random
import string
import sqlite3
import ast
from Crypto.Random import get_random_bytes
from Crypto.Protocol.KDF import PBKDF2
from Crypto.Cipher import AES

layout = [
    [sg.Text('Введите мастер-ключ:'), sg.InputText(key='-PASS-')],
    [sg.Button('Сгенерировать мастер-ключ'), sg.Checkbox('Цифры', k='-NUMBER-'),
    sg.Checkbox('Спец. символы', k='-SPEC-'), sg.Checkbox('Разные регистры', k='-REGISTER-'),
    sg.Text('Длина мастер-ключа:', size=(16, 1), justification='r',pad=(0,0)),
    sg.Combo(['6','8','10','12','16'], default_value='12', s=(15,22), enable_events=True, readonly=True, k='-LENGTH-')],
    [sg.Button('Зашифровать'), sg.Button('Расшифровать')],
    [sg.Text(key='-TEXT-')]
]

window = sg.Window('Шифрование слова', layout)

while True:
    event, values = window.read()
    
    if event == sg.WINDOW_CLOSED:
        break
    
    elif event == 'Зашифровать':
        password = values['-PASS-']
        
        conn = sqlite3.connect('password.db')
        cursor = conn.cursor()
        conn.commit()
                
        def PassEncrypt(password):
            password = password.encode("utf-8")
            salt = get_random_bytes(32)
            cursor.execute(f"UPDATE password SET salt = '{list(salt)}';"); conn.commit()
            key = PBKDF2(password, salt, dkLen=32)
            cipher_encrypt = AES.new(key, AES.MODE_CFB)
            ciphered_bytes = cipher_encrypt.encrypt(password)
            cursor.execute(f"UPDATE password SET ciphered_bytes = '{list(ciphered_bytes)}';"); conn.commit()
            iv = cipher_encrypt.iv
            cursor.execute(f"UPDATE password SET iv = '{list(iv)}';"); conn.commit()
            sg.popup("Ваш мастер-ключ успешно зашифрован!")
        
        def check_db_exists():
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='password'")
            table_exists = cursor.fetchall()
            
            if table_exists:
                dbInit = sg.popup("База данных инициализированна!")
                if dbInit == "OK":
                    cursor.execute("DELETE FROM password;"); conn.commit()
                    cursor.execute("INSERT INTO password (salt, iv, ciphered_bytes) VALUES (NULL, NULL, NULL);"); conn.commit()
                    PassEncrypt(password)
                    return
            
            table = sg.popup("Создание необходимых таблиц!",)
            if table == "OK":
                createTable = """CREATE TABLE password (
                              salt TEXT,
                              iv TEXT,
                              ciphered_bytes TEXT)"""
                cursor.execute(createTable); conn.commit()
                cursor.execute("INSERT INTO password (salt, iv, ciphered_bytes) VALUES (NULL, NULL, NULL);"); conn.commit()
                dbDone = sg.popup("База данных создана и настроена!")
                if dbDone == "OK":
                    check_db_exists()

        def EmptyPassCheck():
            if password.strip() == '':
                new_text = 'Вы не ввели мастер-ключ!'
                window['-TEXT-'].update(new_text)
            else:
                window['-TEXT-'].update('')
                check_db_exists()

                
        EmptyPassCheck()
        
    elif event == 'Расшифровать':
        password = values['-PASS-']
        conn = sqlite3.connect('password.db')
        cursor = conn.cursor()
        conn.commit()
        
        def passDecrypt():
            passwordDecrypt = password.encode('utf-8')
            cursor.execute("SELECT salt FROM password;"); saltDecrypt = bytes(ast.literal_eval(str(cursor.fetchall())[3:-4]))
            keyDecrypt = PBKDF2(passwordDecrypt, saltDecrypt, dkLen=32)
            cursor.execute("SELECT iv FROM password"); ivDecrypt = bytes(ast.literal_eval(str(cursor.fetchall())[3:-4]))
            cursor.execute("SELECT ciphered_bytes FROM password"); DecryptedBytes = bytes(ast.literal_eval(str(cursor.fetchall())[3:-4]))
            cipher_decrypt = AES.new(keyDecrypt, AES.MODE_CFB, iv=ivDecrypt)
            deciphered_bytes = cipher_decrypt.decrypt(DecryptedBytes)
            decrypted_data = deciphered_bytes#.decode('utf-8')
            if decrypted_data == values['-PASS-'].encode('utf-8'):
                sg.popup("Мастер-ключ успешно расшифрован")
            else:
                sg.popup("Ошибка! Скорее всего Вы ввели неправильный мастер-ключ!")
            
        passDecrypt()
        
    elif event == 'Сгенерировать мастер-ключ':
        
        def PassGen():
            pass_length = int(values['-LENGTH-'])
            pswd = []
            
            for i in range(pass_length):
                pswd.append(random.choice(string.ascii_lowercase))
                if values['-NUMBER-']:
                    pswd.append(random.choice(string.digits))
                if values['-SPEC-']:
                    pswd.append(random.choice(string.punctuation))
                if values['-REGISTER-']:
                    pswd.append(random.choice(string.ascii_uppercase))
                    
            random.shuffle(pswd)
            
            window['-PASS-'].update("".join(map(str,pswd))[:pass_length])
            
        PassGen()

window.close()
