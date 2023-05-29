import sqlite3
import pyperclip
import PySimpleGUI as sg
from Crypto.Cipher import AES
from Crypto.Protocol.KDF import PBKDF2
from Crypto.Random import get_random_bytes


def PassStorage():
	data = []
	head = ['Сервис', 'Логин', 'Пароль']

	conn = sqlite3.connect('password.db')
	cursor = conn.cursor()
	conn.commit()

	cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND "
	               "name != 'password'")
	category = cursor.fetchall()

	table = sg.Table(values=data, headings=head, expand_x=True, k='data',
	                 enable_events=True, enable_click_events=True,
	                 selected_row_colors='red on yellow')
	combo = sg.Combo(category, enable_events=True,
	                 readonly=True, k='combo', expand_x=True, size=25)

	layout = [
		[sg.Text('Ваши пароли', justification='center', expand_x=True)],
		[sg.Column([[sg.Text('Категории:'), combo]],
		           element_justification='c')],
		[sg.Button('Добавить категорию'), sg.Button('Удалить категорию')],
		[sg.Column([[table]], element_justification='c', expand_x=True)],
		[sg.Column([[sg.Button('Добавить данные'),
		             sg.Button('Удалить данные')]],
		           element_justification='c', expand_x=True)],
	]

	window = sg.Window('Пароли', layout)

	while True:
		e, v = window.read()

		defaultCategory = v['combo']

		# TODO: расшифровка данных из БД и вывод в table, а так же пофиксить
		# TODO: баги и переделать авторизацию

		try:
			window['combo'].update(values=category, value=v['combo'])
			window['data'].update(values=data)

		except Exception:
			break

		if e == sg.WINDOW_CLOSED:
			break

		elif e == 'Добавить категорию':
			categoryName = sg.popup_get_text('Введите название'
			                                 ' категории').replace(
				'.', '_').replace(' ', '_')

			if categoryName is None:
				pass

			else:

				def categoryAdd():
					category.append(categoryName)
					window['combo'].update(values=category,
					                       value=v['combo'])
					newCategoryIndex = category.index(categoryName)
					combo.update(category[newCategoryIndex])
					createCategoryTable = f"""
										CREATE TABLE {categoryName} (
										id INTEGER PRIMARY KEY AUTOINCREMENT,
										service_salt TEXT,
										service_iv TEXT,
										service_cipheredBytes TEXT,
										login_salt TEXT,
										login_iv TEXT,
										login_cipheredBytes TEXT,
										pass_salt TEXT,
										pass_iv TEXT,
										pass_cipheredBytes TEXT
										)
										"""
					cursor.execute(createCategoryTable)
					conn.commit()

				try:
					categoryAdd()

				except sqlite3.OperationalError:
					popup = sg.popup('У Вас уже есть категория '
					                 'с таким названием!')
					if popup == 'OK':
						PassStorage()

		elif e == 'Удалить категорию':

			try:
				selectedCategory = combo.get()
				selectedCategoryIndex = category.index(selectedCategory)

				if selectedCategoryIndex == 0:
					category.pop(selectedCategoryIndex)
					window['combo'].update(values=category,
					                       value=v['combo'])
					combo.update('')
					deleteCategoryTable = f"""DROP TABLE {selectedCategory}"""
					cursor.execute(deleteCategoryTable)
					conn.commit()

				else:
					category.pop(selectedCategoryIndex)
					window['combo'].update(values=category,
					                       value=v['combo'])
					combo.update(category[-1])
					deleteCategoryTable = f"""DROP TABLE {selectedCategory}"""
					cursor.execute(deleteCategoryTable)
					conn.commit()

			except (IndexError, ValueError):
				sg.popup('Ошибка! У вас нет категории для удаления.')

		elif e == 'Добавить данные':

			try:
				combo.get()[0]

			except IndexError:
				sg.popup('Сначала выберите категорию!')
				window.close()
				PassStorage()

			dataService = sg.InputText(k='dataService', size=20)
			dataLogin = sg.InputText(k='dataLogin', size=20)
			dataPass = sg.InputText(k='dataPass', size=20)

			popupLayout = [
				[sg.Text('Введите данные для добавления.')],
				[sg.Column(
					[[sg.Text('Сервис:', size=6), dataService],
					 [sg.Text('Логин:', size=6), dataLogin],
					 [sg.Text('Пароль:', size=6), dataPass],
					 [sg.Button('Ок'), sg.Button('Закрыть')]],
					element_justification='c')],
			]

			popup = sg.Window('Добавление сервиса', popupLayout)

			while True:
				event, values = popup.read()

				if event == sg.WINDOW_CLOSED:
					break

				elif event == 'Ок':

					popupDataService = values['dataService']
					popupDataLogin = values['dataLogin']
					popupDataPass = values['dataPass']
					windowCategorySelected = (v['combo'])

					def dataEncrypt(data_service, data_login, data_pass):
						dataServiceEncrypt = data_service.encode("utf-8")
						dataLoginEncrypt = data_login.encode("utf-8")
						dataPassEncrypt = data_pass.encode("utf-8")

						dataServiceSalt = get_random_bytes(32)
						dataLoginSalt = get_random_bytes(32)
						dataPassSalt = get_random_bytes(32)

						dataServiceKey = PBKDF2(dataServiceEncrypt,
						                        dataServiceSalt, dkLen=32)
						dataLoginKey = PBKDF2(dataLoginEncrypt,
						                      dataLoginSalt, dkLen=32)
						dataPassKey = PBKDF2(dataPassEncrypt,
						                     dataPassSalt, dkLen=32)

						cipherEncryptDataService = AES.new(dataServiceKey,
						                                   AES.MODE_CFB)
						cipherEncryptDataLogin = AES.new(dataLoginKey,
						                                 AES.MODE_CFB)
						cipherEncryptDataPass = AES.new(dataPassKey,
						                                AES.MODE_CFB)

						cipheredBytesDataService = cipherEncryptDataService. \
							encrypt(dataServiceEncrypt)
						cipheredBytesDataLogin = cipherEncryptDataLogin. \
							encrypt(dataLoginEncrypt)
						cipheredBytesDataPass = cipherEncryptDataPass. \
							encrypt(dataPassEncrypt)

						ivDataService = cipherEncryptDataService.iv
						ivDataLogin = cipherEncryptDataLogin.iv
						ivDataPass = cipherEncryptDataPass.iv

						cursor.execute(f"INSERT INTO "
						               f"{windowCategorySelected[0]} "
						               f"(service_salt, login_salt,"
						               f" pass_salt, service_cipheredBytes, "
						               f"login_cipheredBytes, "
						               f"pass_cipheredBytes,"
						               f" service_iv, login_iv, "
						               f"pass_iv) VALUES "
						               f"('{list(dataServiceSalt)}', "
						               f"'{list(dataLoginSalt)}', "
						               f"'{list(dataPassSalt)}',"
						               f"'{list(cipheredBytesDataService)}',"
						               f"'{list(cipheredBytesDataLogin)}',"
						               f"'{list(cipheredBytesDataPass)}',"
						               f"'{list(ivDataService)}', "
						               f"'{list(ivDataLogin)}', "
						               f"'{list(ivDataPass)}')")
						conn.commit()

					dataEncrypt(popupDataService,
					            popupDataLogin, popupDataPass)

					popup.close()


		elif isinstance(e, tuple) and e[:2] == ('data', '+CLICKED+'):
			row, col = position = e[2]
			if None not in position and row >= 0:
				text = data[row][col]
				pyperclip.copy(text)
				sg.popup('Данные успешно помещены в буфер обмена!',
				         auto_close=True, auto_close_duration=1)

		elif e == 'Выход':
			window.close()
