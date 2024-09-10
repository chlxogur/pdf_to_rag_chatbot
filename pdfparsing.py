import tabula
from pypdf import PdfReader
import re
import pandas as pd
import numpy as np
import json

# 목차에서 검색해서 지금 챕터의 인덱스와 다음 챕터의 이름, 인덱스를 리턴, 못 찾았으면 -1을 리턴
def title_to_page_index(reader, chapter_title):
    length_of_table_of_contents = get_first_page_index(reader)          # 목차의 길이
    for idx in range(length_of_table_of_contents):                      # 목차 페이지를 보면서
        page = reader.pages[idx]
        table_of_contents = page.extract_text()                         # 텍스트 추출
        start_index = table_of_contents.find(chapter_title)             # 원하는 챕터가 있는지 확인
        if start_index != -1:                                           # 있으면
            end_of_line = table_of_contents[start_index:].find("\n") + start_index      # 끝라인 찾고
            page_index = int(table_of_contents[start_index:end_of_line].split(". ")[-1]) + length_of_table_of_contents - 1      # 0부터 시작하는 인덱스니까 -1을 넣어줌
            r = re.compile(r"[.][ ]?[^.]+[ ]?[.]{3}")                   # 목차에 나오는 . (제목) ... 이런 구조를 찾기 위한 정규표현식
            match = r.search(table_of_contents[end_of_line+1:]).span()  # 다음 줄에서 정규표현식에 맞는 부분이 있는지 확인
            chapter_title_of_next_chapter = table_of_contents[match[0]+(end_of_line+1):match[1]+(end_of_line+1)].strip(" .")    # 다음 챕터의 이름 추출
            end_of_next_line = table_of_contents[end_of_line+1:].find("\n") + (end_of_line+1)                                   # 다음 챕터의 끝라인 찾고
            page_index_of_next_chapter = int(table_of_contents[end_of_line+1:end_of_next_line].split(". ")[-1]) + length_of_table_of_contents - 1   # 다음 챕터의 페이지 번호 추출
            result = {                              # 구조화시킴
                "chapter_title" : chapter_title,
                "page_index": page_index,
                "chapter_title_of_next_chapter" : chapter_title_of_next_chapter,
                "page_index_of_next_chapter" : page_index_of_next_chapter
            }
            return result
    return -1

# 첫 페이지의 페이지 인덱스를 리턴
def get_first_page_index(reader):
    for idx, page in enumerate(reader.pages):
        text = page.extract_text()
        if text.rfind("Page 1") != -1:
            return idx

# 챕터의 텍스트를 리턴
def get_text_of_chapter(reader, chapter_title):
    number_of_pages = len(reader.pages)
    page_info = title_to_page_index(reader, chapter_title)
    if page_info == -1:
        return -1
    # 여유롭게 앞에 한장 뒤에 한장씩 더 추출, 목차에 보니까 앞뒤로 한장정도씩 잘못 나온 경우가 있음
    start_page = page_info["page_index"] - 1 if page_info["page_index"] > 0 else page_info["page_index"]            # 혹시 첫 페이지일수 있으니 조건 설정
    end_page = page_info["page_index_of_next_chapter"] + 1 if page_info["page_index_of_next_chapter"] < (number_of_pages - 1) else page_info["page_index_of_next_chapter"]  # 마지막 페이지를 넘어가지 않도록 조건 지정
    text = ""
    for page_number in range(start_page, end_page + 1):
        page = reader.pages[page_number]
        text = "".join([text, page.extract_text()])     # 이어붙이기
    r = re.compile(f"(?<!\. ){page_info['chapter_title']}")     # 앞에 .이랑 공백이 없는 경우를 제외한건데, pypdf로 뽑아보니 이런 형식이 순서가 바뀌어 나와서 조건을 설정했다.
    start = r.search(text).start()
    r = re.compile(f"(?<!\. ){page_info['chapter_title_of_next_chapter']}") # 다음 챕터의 제목은 어디있나 확인
    end = r.search(text).start()
    return text[start:end]

# input.txt에서 원하는 pdf랑 원하는 표 이름 받아오기
def read_text_file():
    with open("input.txt", 'r', encoding='utf-8') as file:
        # 첫 번째 줄을 읽어서 숫자를 파싱
        first_line = file.readline().strip()
        num_files, num_items = map(int, first_line.split())
        
        file.readline()

        # 파일명을 읽음
        file_names = []
        for i in range(num_files):
            file_name = file.readline().strip()
            file_names.append(file_name)
            
        file.readline()

        # 항목명을 읽음
        items = []
        for i in range(num_items):
            item = file.readline().strip()
            items.append(item)

        return file_names, items
    
def extract_table(file_name, desired_table_name_list):
    if ".pdf" not in file_name:
        file_name = file_name + ".pdf"

    reader = PdfReader(f"data/{file_name}")

    table_text_dic = {}             # key에 테이블 이름, value에 텍스트 쭉
    for name in desired_table_name_list:
        table_text_dic.update({name : get_text_of_chapter(reader, name)})
        
    table_range = []
    for table_name in desired_table_name_list:
        this_table_range = title_to_page_index(reader, table_name)
        if this_table_range != -1:
            table_range.extend([i for i in range(this_table_range["page_index"], this_table_range["page_index_of_next_chapter"] + 1)])
    desired_page_index = list(set(table_range))
    desired_page_number = [i + 1 for i in desired_page_index]       # 주의 : 다음 챕터의 시작 페이지까지 나옴

    tabula_result_dfs = tabula.read_pdf(
        f"data/{file_name}",
        pages=desired_page_number,
        stream=True,
        lattice=True
    )

    dfs = {}
    for idx in range(len(tabula_result_dfs)):           # 나눠진 테이블을 병합
        for key in table_text_dic:
            if table_text_dic[key] == -1:
                dfs[key] = -1
                continue
            nextline_removed_text = table_text_dic[key].replace("\n", "\r")
            if tabula_result_dfs[idx].iloc[:, 0].apply(lambda x : False if pd.isna(x) else x in nextline_removed_text).sum() == tabula_result_dfs[idx].shape[0]:
                if dfs.get(key) is None:
                    dfs[key] = tabula_result_dfs[idx]
                else:
                    if dfs[key].columns is not tabula_result_dfs[idx]:
                        temp_df = pd.DataFrame(tabula_result_dfs[idx].columns, index = dfs[key].columns).T     # 내용이 컬럼으로 들어가 있는 부분을 추출
                        dfs[key] = pd.concat([dfs[key], temp_df], ignore_index=True)
                        tabula_result_dfs[idx].columns = dfs[key].columns
                    dfs[key] = pd.concat([dfs[key], tabula_result_dfs[idx]], ignore_index=True)
                    break
                
    for key in dfs:
        text = table_text_dic[key]
        parents = []
        level = 0
        new_column = ["과목"]
        if isinstance(dfs[key], pd.DataFrame):
            for column in dfs[key].columns[1:]:         # 제 몇 기 이렇게 나오는 컬럼을 년도로 통일
                r = re.compile(rf"\n{column}.*[0-9]{{4}}[.][0-9]{{2}}[.][0-9]{{2}}.*\n")
                new_column.append(r.search(text).group()[-14:-10])
            dfs[key].columns = new_column
            dfs[key].iloc[:, 1:] = dfs[key].iloc[:, 1:].replace({'\(': '-', '\)': '', ',': ''}, regex=True)
            
            for idx, row in dfs[key].iterrows():        # 내용 다듬기
                row["과목"] = row["과목"].replace("\r", "\n")
                
                r = re.compile(f"\\n[ ]?\\u3000*{re.escape(row['과목'])}[^가-힣]*\\n")  # 됐다 ㅠㅠ
                r_searched = r.search(text)
                current_row_text = r_searched.group()
                next_cursor = r_searched.end()

                name_start = current_row_text.find(row["과목"])
                current_level = current_row_text[:name_start].count("\u3000")
                row["과목"] = row["과목"].replace("\n", "")     # 이제 \n을 없애고
                dfs[key].iloc[idx, 1:] = dfs[key].iloc[idx, 1:].apply(pd.to_numeric, errors='coerce')
                
                r = re.compile("\(단위[ ]?:[ ]?원\)")
                matched = r.search(row["과목"])
                if matched:
                    dfs[key].iloc[idx, 1:] = dfs[key].iloc[idx, 1:].apply(pd.to_numeric, errors='coerce') / 1000000         # 단위가 원단위면 100만으로 나눠서 단위를 통일
                    row["과목"] = row["과목"].replace(matched.group(), "").strip()                                          # (단위 : 원) 삭제
                r = re.compile("\(주[ ]?[1-9].*\)")
                matched = r.search(row["과목"])
                if matched:
                    row["과목"] = row["과목"].replace(matched.group(), "").strip()                                          # (주11) 이런거 삭제
                if current_level == level:
                    try:
                        parents.pop()
                    except IndexError:
                        pass
                    parents.append(row["과목"])
                elif current_level > level:
                    for i in range(level + 1, current_level + 1):           # 의미가 없는 반복문이긴 한데.. 예외가 있을 수 있으니 > 부등호+반복문으로 처리함
                        parents.append(row["과목"])
                    level = current_level
                else:
                    for i in range(current_level, level + 1):
                        try:
                            parents.pop()
                        except IndexError:
                            pass
                    parents.append(row["과목"])
                    level = current_level
                dfs[key].loc[idx, "과목"] = "_".join(parents)
                text = text[next_cursor - 1:]           # 바로 앞에 줄바꿈 문자까지 포함하려고 -1 추가
    return dfs
"""
def process_financial_statements_by_statement(df):
    result = {}
    statements = []
    companies = df.keys()
    for company in companies:
        statements.extend(df[company].keys())
    statements = list(set(statements))
    
    for statement in statements:
        for cols in [[0, 1], [0, 2], [0, 3]]:
            temp_frames = []
            valid_companies = []
            
            for company in companies:
                if company.find(".") != -1:             # 확장자 부분 자르기
                    company = company[:company.find(".")]
                company_name = company.lower()
                
                # 데이터프레임이 -1 이면 무시
                if company_name in df and statement in df[company_name]:
                    if isinstance(df[company_name][statement], pd.DataFrame):
                        temp = df[company_name][statement].iloc[:, cols].T
                        temp.columns = temp.iloc[0, :]
                        temp = temp.drop(temp.index[0])
                        
                        temp_frames.append(temp)
                        company = company.capitalize()      # 맨 앞글자만 대문자로
                        valid_companies.append(company)
            
            if temp_frames:
                combined_result = pd.concat(temp_frames, keys=valid_companies)
                combined_result.index = valid_companies
                
                total = combined_result.sum(min_count=1)
                combined_result.loc["Sum"] = total
                
                avg = combined_result.iloc[:-1].mean()      # 합계까지 더해 평균을 더하는 문제 방지
                combined_result.loc["Avg"] = avg
                combined_result = combined_result.replace(np.nan, "-")
                combined_result = combined_result.sort_index(axis=1, ascending=True)

                year = temp_frames[0].index[0]
                
                if year not in result:
                    result[year] = {}
                
                result[year][statement] = combined_result
    
    return result


def table_to_json(df):
    result = {}
    for year in df:
        df_of_this_year = df[year]
        for title in df_of_this_year:
            column_list = df[year][title].columns
            for column in column_list:
                value = df[year][title][column]
                ancestors = [year] + column.split("_")
                current = result
                for key in ancestors:
                    if key not in current:
                        current[key] = {}
                    current = current[key]
                current["Value"] = dict(value)
    return result

def table_to_json_2(df):
    result = {}
    for year in df:
        df_of_this_year = df[year]
        for title in df_of_this_year:
            column_list = df[year][title].columns
            for column in column_list:
                key_count = 0
                value = df[year][title][column]
                splitted_column = column.split("_")
                column_name = splitted_column[-1] + "_" + str(key_count)
                ancestors = splitted_column[:-1]
                while result.get(column_name) != None:
                    key_count += 1
                    column_name = splitted_column[-1] + "_" + str(key_count)
                result[column_name] = {}
                result[column_name]["Year"] = year
                result[column_name]["Value"] = dict(value)
                result[column_name]["Ancestors"] = ancestors
    return result
"""
"""
    테이블을 column_name 기준으로 오름차순 정렬해서 최대한 옆 문서에 나오도록
    자연어로 나열해보자. 예) 삼성전자의 2023년 자산의 유동자산의 미수금은 --이다 이렇게
"""
def table_to_text(df):
    pass



"""    
df_csv = process_financial_statements_by_statement(df, file_names, desired_table_name_list)

with pd.ExcelWriter("data/output/2023.xlsx") as writer:
    df_csv["2023"]["연결 재무상태표"].to_excel(writer, sheet_name = "연결 재무상태표")
    df_csv["2023"]["연결 손익계산서"].to_excel(writer, sheet_name = "연결 손익계산서")
    df_csv["2023"]["연결 포괄손익계산서"].to_excel(writer, sheet_name = "연결 포괄손익계산서")
    
with open("data/output/사업계획서자손2.json", "w", encoding="UTF-8") as json_file:
    json.dump(table_to_json_2(df_csv), json_file, indent=4, ensure_ascii=False)
"""