import pandas as pd
import os
import glob

# 设置你的输入文件夹路径
input_folder_path = './input/'

# 使用 glob 模块找到所有 '.xlsx' 后缀的文件
xlsx_files = glob.glob(os.path.join(input_folder_path, '*.xlsx'))

# 读取输入 Excel 文件
input_excel_list = xlsx_files
output_excel = "output.xlsx"

language_list = ['en_us']
content = {}

for input_excel in input_excel_list:
    # 读取所有工作表并将其存储在一个字典中，key 为工作表名称，value 为包含数据的 DataFrame
    sheets_dict = pd.read_excel(input_excel, sheet_name=None)

    # 遍历输入 Excel 中的所有工作表
    for sheet_name, data in sheets_dict.items():
        # 获取标题行
        header = data.columns
        lana = header[0]
        lanb = header[1]

        # 将标题行添加到 language_list
        if lana not in language_list:
            language_list.append(lana)
        if lanb not in language_list:
            language_list.append(lanb)

        for index, row in data.iterrows():
            print(f"index: {index} row: {row}")
            a = row[0]
            b = row[1]
            print(f"a: {a} b: {b}")
            if (a not in content.keys()):
                content[a] = {lanb: b}
                continue

            content[a][lanb] = b

print (f"language_list: {language_list} content: {content}")

rows=[]
rows.append(language_list)

for key, value in content.items():
    row = []
    for language in language_list:
        if language == 'en_us':
            row.append(key)
        elif language in value.keys():
            row.append(value[language])
        else:
            row.append("")
    rows.append(row)

print(f"rows: {rows}")

output_data = pd.DataFrame(rows)
# 将输出数据保存到一个新的 Excel 文件中
output_data.to_excel(output_excel, index=False)
