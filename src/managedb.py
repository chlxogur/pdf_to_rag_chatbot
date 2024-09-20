from src.pdfparsing import read_text_file, extract_table_with_won_unit, table_to_dic
from collections import deque
from langchain_core.documents import Document
from langchain_chroma import Chroma
from langchain_openai import OpenAIEmbeddings
import numpy as np
from src.config import OUTPUT_PATH, COLLECTION_NAME

def make_db():
    df = {}
    file_names, desired_table_name_list, target_year = read_text_file()
    for file_name in file_names:
        df[file_name] = extract_table_with_won_unit(file_name, desired_table_name_list)
        
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

    db = Chroma.from_documents(
        markdown_docs,
        text_embedding_model,
        collection_name = COLLECTION_NAME,
        persist_directory = OUTPUT_PATH + "chromadb",
        collection_metadata = {"hnsw:space":"cosine"}       # 이거 뭘까 공부할 필요가 있음
    )
    return db

def load_db():
    # 임베딩 함수를 load_db() 안에 집어넣으면 해결될지도...
    text_embedding_model = OpenAIEmbeddings()
    vectorstore = Chroma(embedding_function=text_embedding_model, persist_directory= "data/output/" + "chromadb")
    client = vectorstore._client
    collections = client.list_collections()
    target_collection_name = COLLECTION_NAME
    collection_exists = any(collection.name == target_collection_name for collection in collections)
    if collection_exists:
        db = Chroma(
            collection_name="saup_markdown",
            persist_directory= OUTPUT_PATH + "chromadb",
            embedding_function=text_embedding_model
        )
    else:
        db = make_db()
    return db