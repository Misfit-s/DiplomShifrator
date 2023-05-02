import PySimpleGUI as sg


def Main():

	data = []
	head = ['Сервис', 'Логин', 'Пароль']
	category = []

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

		if event == sg.WINDOW_CLOSED:
			break

		elif event == 'Добавить категорию':
			categoryName = sg.popup_get_text('Введите название категории')
			category.append(categoryName)
			window['combo'].update(values=category, value=values['combo'])
			combo.update(category)

		elif event == 'Выход':
			window.close()
