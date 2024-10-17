from src.pdfparsing import extract_table_with_won_unit, table_to_dic
from src.fileio import read_text_file
from collections import deque
from langchain_core.documents import Document
from langchain_community.vectorstores import FAISS
from langchain_openai import OpenAIEmbeddings
import numpy as np
from src.config import DATA_PATH, COLLECTION_NAME
import os

def make_db(session_id = "initial"):
    df = {}
    file_names, desired_table_name_list, target_year = read_text_file(session_id)
    for file_name in file_names:
        df[file_name] = extract_table_with_won_unit(file_name, desired_table_name_list, session_id)
        
    data_dic = table_to_dic(df, target_year)

    markdown_docs = []
    for table_name in data_dic.keys():
        
        dfsearch_stack = deque()
        dfsearch_stack.append((data_dic[table_name], []))
        while dfsearch_stack:
            current_dic, ancestors = dfsearch_stack.pop()
            for key, value in reversed(current_dic.items()):
                current_path = ancestors + [key]
                if isinstance(value, dict) and key != "Value":
                    dfsearch_stack.append((value, current_path))
                else:
                    for key_of_company, value_of_company in value.items():
                        if key_of_company != "sum" and key_of_company != "average":
                            header_number = 1
                            metadata = {}
                            page_content = ""
                            for path_node in current_path[:-2]:                                 # 과목명을 다중컬럼으로 입력
                                metadata.update({f"Header {header_number}" : path_node})
                                header_number += 1
                            page_content = page_content + f"Title : {current_path[-2]}, "
                            metadata.update({"Company" : key_of_company})
                            for key_of_cell, value_of_cell in value_of_company.items():
                                if np.isnan(value_of_cell):
                                    value_of_cell = "-"
                                page_content = page_content + f"{key_of_cell}년 : {value_of_cell}, "
                            document = Document(page_content=page_content[:-2], metadata=metadata)
                            markdown_docs.append(document)
                            
    text_embedding_model = OpenAIEmbeddings()
    db = FAISS.from_documents(documents = markdown_docs, embedding = text_embedding_model)
    db.save_local(folder_path=os.path.join(DATA_PATH, session_id, "output", "faissdb"), index_name=COLLECTION_NAME)

    return db

def load_db(session_id = "initial"):
    try:
        db = FAISS.load_local(
            folder_path=os.path.join(DATA_PATH, session_id, "output", "faissdb"),
            index_name=COLLECTION_NAME,
            embeddings=OpenAIEmbeddings(),
            allow_dangerous_deserialization=True
            )
    except RuntimeError:            # DB가 없으면 새로 만듦.
        db = make_db(session_id)
    return db