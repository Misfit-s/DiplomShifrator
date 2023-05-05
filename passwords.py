import sqlite3
import PySimpleGUI as sg


def PassStorage():
	data = []
	head = ['Сервис', 'Логин', 'Пароль']

	conn = sqlite3.connect('password.db')
	cursor = conn.cursor()
	conn.commit()

	cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND "
	               "name != 'password'")
	category = cursor.fetchall()

	table = sg.Table(values=data, headings=head, expand_x=True)
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
		event, values = window.read()

		try:
			window['combo'].update(values=category, value=values['combo'])

		except Exception:
			break

		if event == sg.WINDOW_CLOSED:
			break

		elif event == 'Добавить категорию':
			categoryName = sg.popup_get_text('Введите название'
			                                 ' категории').replace(
				'.', '_').replace(' ', '_')

			if categoryName is None:
				pass

			else:

				def categoryAdd():
					category.append(categoryName)
					window['combo'].update(values=category,
					                       value=values['combo'])
					newCategoryIndex = category.index(categoryName)
					combo.update(category[newCategoryIndex])
					createCategoryTable = f"""
										CREATE TABLE {categoryName} (
										id INT,
										service TEXT,
										login TEXT,
										password TEXT
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

		elif event == 'Удалить категорию':

			try:
				selectedCategory = combo.get()
				selectedCategoryIndex = category.index(selectedCategory)

				if selectedCategoryIndex == 0:
					category.pop(selectedCategoryIndex)
					window['combo'].update(values=category,
					                       value=values['combo'])
					combo.update('')
					deleteCategoryTable = f"""DROP TABLE {selectedCategory}"""
					cursor.execute(deleteCategoryTable)
					conn.commit()

				else:
					category.pop(selectedCategoryIndex)
					window['combo'].update(values=category,
					                       value=values['combo'])
					combo.update(category[-1])
					deleteCategoryTable = f"""DROP TABLE {selectedCategory}"""
					cursor.execute(deleteCategoryTable)
					conn.commit()

			except (IndexError, ValueError):
				sg.popup('Ошибка! У вас нет категории для удаления.')

		elif event == 'Добавить данные':

			try:
				dataSelectedCategory = combo.get()[0]

			except IndexError:
				sg.popup('Сначала выберите категорию!')
				window.close()
				PassStorage()

			popupLayout = [
				[sg.Text('Введите данные для добавления.')],
				[sg.Text('Сервис:'), sg.InputText(k='dataService')],
				[sg.Text('Логин'), sg.InputText(k='dataLogin')],
				[sg.Text('Пароль'), sg.InputText(k='dataPass')],
				[sg.Button('Ок'), sg.Button('Закрыть')],
			]

			popup = sg.Window('Добавление сервиса', popupLayout)

			while True:
				event, values = popup.read()

				if event == sg.WINDOW_CLOSED:
					break

				elif event == 'Ок':
					pass

				elif event == 'Закрыть':
					popup.close()

		elif event == 'Выход':
			window.close()
