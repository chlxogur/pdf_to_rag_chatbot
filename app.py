import streamlit as st
import os
from src.makeresponse import make_response
from src.managedb import load_db, make_db
from src.fileio import save_uploaded_files
from src.maketable import make_table
from src.config import DATA_PATH
import uuid
import shutil
import time

default_file_names = ["연결 재무상태표.xlsx", "연결 손익계산서.xlsx", "연결 포괄손익계산서.xlsx"]
SESSION_TIMEOUT = 600   # 10분이 지나면 세션종료
OLD_FOLDER_LIFETIME = 60 * 6   # 변경된지 6시간이 지나면 폴더 삭제

col = list()
def update_db(session_id = "initial"):
    make_table(session_id)
    st.session_state.messages = []
    st.session_state.db = make_db(session_id)
    
def cleanup_session():
    current_time = time.time()
    if 'last_access' in st.session_state:
        last_access = st.session_state['last_access']
        if current_time - last_access > SESSION_TIMEOUT:
            # 타임아웃이 지나면 DB 파일 삭제
            if os.path.exists(os.path.join(DATA_PATH, st.session_state.session_id)):
                shutil.rmtree(os.path.join(DATA_PATH, st.session_state.session_id))
                st.write("세션 타임아웃으로 인해 DB 파일이 삭제되었습니다.")
                st.session_state.clear()  # 세션 상태 초기화

def cleanup_old_folders():
    current_time = time.time()
    for folder_name in os.listdir(DATA_PATH):
        last_modified = os.path.getmtime(os.path.join(DATA_PATH, folder_name))
        if folder_name != "initial" and current_time - last_modified > OLD_FOLDER_LIFETIME:
            shutil.rmtree(os.path.join(DATA_PATH, folder_name))
                
cleanup_session()
cleanup_old_folders()

st.title("표를 아는 챗봇")

if "session_id" not in st.session_state:
    session_id = str(uuid.uuid4())
    if session_id in os.listdir(DATA_PATH):
        shutil.rmtree(os.path.join(DATA_PATH, session_id))
    shutil.copytree(os.path.join(DATA_PATH, "initial"), os.path.join(DATA_PATH, session_id))
    st.session_state.session_id = session_id
    st.session_state.messages = []
    st.session_state.db = load_db(st.session_state.session_id)
    st.session_state.file_names = [default_file_names]
    st.session_state.file_db_matched = True
    st.session_state.last_access = time.time()

uploaded_files = st.file_uploader("PDF 파일 업로드", type="pdf", accept_multiple_files=True)

if uploaded_files:
    # 파일명을 출력
    file_names = save_uploaded_files(uploaded_files, st.session_state.session_id)
    if st.session_state.file_names != file_names:
        st.session_state.file_names = file_names
        st.session_state.file_db_matched = False

if st.button("DB 새로고침"):
    update_db(st.session_state.session_id)
    st.session_state.file_db_matched = True
    st.session_state.last_access = time.time()

col[0:2] = st.columns(3)
    
for idx, file_name in enumerate(default_file_names):
    file_path = os.path.join(DATA_PATH, st.session_state.session_id, "output", file_name)
    with col[idx]:
        if os.path.exists(file_path) and st.session_state.file_db_matched == True:
            # 파일명 추출
            file_name = os.path.basename(file_path)

            # 파일을 다운로드할 수 있는 버튼 제공
            with open(file_path, 'rb') as file:
                st.download_button(
                    label=f"{file_name}",
                    data=file,
                    file_name=file_name,
                    mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
                )
                
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])
        
if prompt := st.chat_input("입력"):
    st.chat_message("user").markdown(prompt)
    st.session_state.messages.append({"role": "user", "content": prompt})
    
    response = make_response(st.session_state.db, prompt)
    with st.chat_message("assistant"):
        st.markdown(response)
    st.session_state.messages.append({"role": "assistant", "content": response})
    st.session_state.last_access = time.time()