from .pybot_extension_number import extension_number_command
from .pybot_application_forms import application_forms_command
from .pybot_heisei import heisei_command
from .pybot_len import len_command
from .pybot_eto import eto_command
from .pybot_random import choice_command, dice_command
from .pybot_datetime import today_command, now_command, weekday_command


# command_file = open('C:\\python_tool_development\\isk-tools\\report_output\\views\\pybot.txt', encoding='utf-8')
command_file = open('C:\\Users\\yumaru51\\PycharmProjects\\django\\report_output\\views\\pybot.txt', encoding='utf-8')
# command_file = open('./yumarusystem/pybot.txt', encoding='utf-8')
raw_data = command_file.read()
command_file.close()
# 1行ずつ辞書型にする
lines = raw_data.splitlines()

bot_dict = {}
for line in lines:
	# カンマ区切りの配列にする
	word_list = line.split(',')
	key = word_list[0]
	response = word_list[1]
	bot_dict[key] = response


def pybot(command):
	response = ''
	try:
		for key in bot_dict:
			if key in command:
				response = bot_dict[key]
				break

		if '内線' in command:
			response = extension_number_command(command)
		if '申請書' in command:
			response = application_forms_command(command)
		if '平成' in command:
			response = heisei_command(command)
		if '長さ' in command:
			response = len_command(command)
		if '干支' in command:
			response = eto_command(command)
		if '選ぶ' in command:
			response = choice_command(command)
		if 'さいころ' in command:
			response = dice_command()
		if '今日' in command:
			response = today_command()
		if '現在' in command:
			response = now_command()
		if '曜日' in command:
			response = weekday_command(command)

		if not response:
			response = '何ヲ言ッテルカ、ワカラナイ'
		return response

	except Exception as e:
		print('予期セヌ　エラーガ　発生シマシタ')
		print('* 種類：', type(e))
		print('* 内容：', e)
