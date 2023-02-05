# command_file = open('C:\\python_tool_development\\isk-tools\\report_output\\views\\extension_number.txt', encoding='utf-8')
command_file = open('C:\\Users\\yumaru51\\PycharmProjects\\django\\report_output\\views\\extension_number.txt', encoding='utf-8')

raw_data = command_file.read()
command_file.close()
# 1行ずつ辞書型にする
lines = raw_data.splitlines()

bot_dict = {}
for line in lines:
    # カンマ区切りの配列にする
    number_list = line.split(',')
    key = number_list[0]
    response = number_list[1]
    bot_dict[key] = response


def extension_number_command(command):
    response = ''
    for key in bot_dict:
        if key in command:
            response = bot_dict[key]
            break
    return response
