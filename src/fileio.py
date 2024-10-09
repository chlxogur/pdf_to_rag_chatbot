import os
from src.config import DATA_PATH

def save_uploaded_files(uploaded_files):
    saved_file_names = []  # 저장된 파일명을 담을 리스트
    text_for_input = ""
    for filename in os.listdir(DATA_PATH):
        if filename.endswith('.pdf'):
            file_path = os.path.join(DATA_PATH, filename)
            os.remove(file_path)
            
    for uploaded_file in uploaded_files:
        # 파일 저장 경로 설정
        save_path = os.path.join(DATA_PATH, uploaded_file.name)
        
        # 파일 저장
        with open(save_path, "wb") as f:
            f.write(uploaded_file.getbuffer())
        
        # 저장된 파일명을 리스트에 추가
        saved_file_names.append(os.path.splitext(uploaded_file.name)[0])
    text_for_input = "\n".join(saved_file_names)
    text_for_input += "\n\n"
    text_for_input += "연결 재무상태표\n연결 손익계산서\n연결 포괄손익계산서"
    with open("input.txt", "w", encoding="UTF-8") as f:
        f.write(text_for_input)

    return saved_file_names  # 파일명 목록 리턴