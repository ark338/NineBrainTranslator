import pandas as pd
import os
import glob
from easy_gpt_utils import embedding, vector_database
import itertools
import time
import logging
import sys

class PrintHandler(logging.StreamHandler):
    def emit(self, record):
        print(self.format(record))

formatter = logging.Formatter('%(asctime)s [%(levelname)s] [%(name)s] [%(funcName)s:%(lineno)d] - %(message)s')
console_handler = PrintHandler(sys.stdout)
console_handler.setFormatter(formatter)
logger = logging.getLogger()
logger.setLevel(logging.INFO)
#logger.setLevel(logging.DEBUG)
logger.addHandler(console_handler)

def summary_golssary_from_excel(save_output=True):
    # 设置你的输入文件夹路径
    input_folder_path = './input/'

    # 使用 glob 模块找到所有 '.xlsx' 后缀的文件
    xlsx_files = glob.glob(os.path.join(input_folder_path, '*.xlsx'))

    # 读取输入 Excel 文件
    input_excel_list = xlsx_files
    #input_excel_list = ['input.xlsx']  // for test

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
                logger.debug(f"index: {index} row: {row}")
                a = row[0]
                b = row[1]
                logger.debug(f"a: {a} b: {b}")
                if (a not in content.keys()):
                    content[a] = {'en_us': a, lanb: b}
                    continue

                content[a][lanb] = b

    logger.debug (f"language_list: {language_list} content: {content}")


    if save_output:
        rows=[]
        rows.append(language_list)

        for key, value in content.items():
            row = []
            for language in language_list:
                if language in value.keys():
                    row.append(value[language])
                else:
                    row.append("")
            rows.append(row)

        logger.debug(f"rows: {rows}")

        output_excel = "output.xlsx"
        output_data = pd.DataFrame(rows)
        # 将输出数据保存到一个新的 Excel 文件中
        output_data.to_excel(output_excel, index=False)

    return content

# add glossaies to pinecone
def add_glossary_to_pinecone(content):
    # use azure api instead of openai
    embedding_instance = embedding.Embedding(
        model="model-text-embedding-ada-002", 
        api_type="azure", 
        api_base = "https://ninebot-rd-openai-1.openai.azure.com/",
        api_version = "2022-12-01"
    )
    pinecone_instance = vector_database.Pinecone(index = 'segway-knowledge-base', environment='asia-southeast1-gcp')

    delete_all = True
    if delete_all:
        pinecone_instance.delete(namespace = vector_database.NamesSpaces.Glossary.value, deleteAll=True)

    items = []
    counter = 0
    for key, value in content.items():
    #for key, value in itertools.islice(content.items() ,100):
        for try_counter in range(3):
            try:
                embe = embedding_instance.get_raw_embedding(str(value))
                break
            except Exception as e:
                logger.error (f"get_raw_embedding error: {e}")
                time.sleep(1)
                continue
                # TODO: buggy here, need to fix

        meta = vector_database.create_meta(category='glossary', content=str(value))
        item = vector_database.create_item(vector=embe, metadata=meta)
        items.append(item)

        logger.info (f"progress:{counter}/{len(content.items())}")

        # flow control: embedding model has RPM limit of 3000
        counter += 1
        chunk_size = 100
        if counter % chunk_size == 0 and counter > 1:
            logger.debug (f"items: {items}")
            pinecone_instance.upsert(namespace = vector_database.NamesSpaces.Glossary.value, items = items)
            items = []
            logger.info (f"upsert {chunk_size} to pinecone...")
            

    logger.debug (f"items: {items}")
    pinecone_instance.upsert(namespace = vector_database.NamesSpaces.Glossary.value, items = items)
    logger.info (f"upsert rest to pinecone...")
    embe = embedding_instance.get_raw_embedding("segway test")
    logger.debug ("upsert success")

    ret = pinecone_instance.query_meta(namespace=vector_database.NamesSpaces.Glossary.value, vector=embe, top_k=30)
    logger.debug (f"ret: {ret}")



content = summary_golssary_from_excel(False)
add_glossary_to_pinecone(content)
