import os
from src.config import DATA_PATH

# input.txt에서 원하는 pdf랑 원하는 표 이름 받아오기
def read_text_file(session_id = "initial"):
    with open(os.path.join(DATA_PATH, session_id, "input.txt"), 'r', encoding='utf-8') as file:
        # 파일 전체 내용을 읽어서 '\n\n'으로 분리
        content = file.read().strip().split('\n\n')

        # 첫 번째 부분은 파일명, 두 번째 부분은 항목명으로 처리
        file_names = content[0].split('\n')
        items = content[1].split('\n')
        if len(content) > 2:
            years = content[2].split('\n')
        else:
            years = False
        
        return file_names, items, years
    
def save_uploaded_files(uploaded_files, session_id = "initial"):
    saved_file_names = []  # 저장된 파일명을 담을 리스트
    text_for_input = ""
    for filename in os.listdir(os.path.join(DATA_PATH, session_id)):
        if filename.endswith('.pdf'):
            file_path = os.path.join(DATA_PATH, session_id, filename)
            os.remove(file_path)
            
    for uploaded_file in uploaded_files:
        # 파일 저장 경로 설정
        save_path = os.path.join(DATA_PATH, session_id, uploaded_file.name)
        
        # 파일 저장
        with open(save_path, "wb") as f:
            f.write(uploaded_file.getbuffer())
        
        # 저장된 파일명을 리스트에 추가
        saved_file_names.append(os.path.splitext(uploaded_file.name)[0])
    text_for_input = "\n".join(saved_file_names)
    text_for_input += "\n\n"
    text_for_input += "연결 재무상태표\n연결 손익계산서\n연결 포괄손익계산서"
    with open(os.path.join(DATA_PATH, session_id, "input.txt"), "w", encoding="UTF-8") as f:
        f.write(text_for_input)

    return saved_file_names  # 파일명 목록 리턴