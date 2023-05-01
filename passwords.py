import PySimpleGUI as sg


def Main():

	data = []
	head = ['Сервис', 'Логин', 'Пароль']

	table = sg.Table(values=data, headings=head, expand_x=True)
	combo = sg.Combo(values=('value', 'value2'), enable_events=True,
	                 readonly=True, k='combo', expand_x=True)

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

		elif event == 'Добавить вкладку':
			pass

		elif event == 'Выход':

			window.close()
