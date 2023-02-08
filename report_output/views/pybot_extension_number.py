command_file = open('C:\\Users\\y-kawauchi\\python_tool_development\\home\\report_output\\views\\extension_number.txt', encoding='utf-8')  # 会社
# command_file = open('C:\\Users\\yumaru51\\PycharmProjects\\home\\report_output\\views\\extension_number.txt', encoding='utf-8')  # 自宅

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
