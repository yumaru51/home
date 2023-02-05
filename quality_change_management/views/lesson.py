
# 変数定義
test_list = [
    ['要素1', '要素2', '', '要素3'],
    ['要素4', '要素5', '', '要素6'],
    ['要素7', '要素8', '', '要素9'],
]
test_list2 = []
# test_dict = {'fubuki': 1, 'shirayuki': 2}

# 挿入
# test_list.append(['要素7', '要素8', '要素9'])
# test_list[4] = 5

# test_dict['hatsuyuki'] = 3
# test_dict['fubuki'] = 5

# 表示
# for i, e in enumerate(test_list):
#     print('要素番号：', i, ', 値：', e, ', 型：', type(e))

for i in test_list:
    # print(i)
    print(i[0])
    print(i[1])
    print(i[3])
    test_list2.append([i[0], i[1], i[3]])
    # for j in i:
    #     print(j)
print(test_list2)


# print(test_dict.items())
# for test_dict in test_dict.items():
#     print(test_dict, test_dict[0], test_dict[1])
    # print(key, test_dict[key])

