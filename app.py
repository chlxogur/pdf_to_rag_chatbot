import streamlit as st
import os
import uuid
import shutil
import time
from src.makeresponse import make_response
from src.managedb import load_db, make_db
from src.fileio import read_text_file, save_uploaded_files
from src.maketable import make_table
from src.config import DATA_PATH

OLD_FOLDER_LIFETIME = 60 * 60 * 6       # 변경된지 6시간이 지나면 폴더 삭제

col = list()
def update_db(session_id = "initial"):
    make_table(session_id)
    st.session_state.messages = []
    st.session_state.db = make_db(session_id)
    
def cleanup_old_folders():
    current_time = time.time()
    for folder_name in os.listdir(DATA_PATH):
        last_modified = os.path.getmtime(os.path.join(DATA_PATH, folder_name))
        if folder_name != "initial" and current_time - last_modified > OLD_FOLDER_LIFETIME:
            shutil.rmtree(os.path.join(DATA_PATH, folder_name))
                
cleanup_old_folders()

st.title("표를 아는 챗봇")

if "session_id" not in st.session_state:
    file_names, items, _  = read_text_file("initial")
    session_id = str(uuid.uuid4())
    if session_id in os.listdir(DATA_PATH):
        shutil.rmtree(os.path.join(DATA_PATH, session_id))
    shutil.copytree(os.path.join(DATA_PATH, "initial"), os.path.join(DATA_PATH, session_id))
    os.mkdir(os.path.join(DATA_PATH, session_id, "dummy"))
    os.rmdir(os.path.join(DATA_PATH, session_id, "dummy"))
    st.session_state.session_id = session_id
    st.session_state.messages = []
    st.session_state.db = load_db(st.session_state.session_id)
    st.session_state.file_names = list(map(lambda x: x + ".pdf", file_names))
    st.session_state.item_names = items
    st.session_state.file_db_matched = True

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

col[0:2] = st.columns(3)
    
for idx, item_name in enumerate(st.session_state.item_names):
    if not os.path.splitext(item_name)[1]:
        item_name_with_xlsx = item_name + ".xlsx"
    item_path = os.path.join(DATA_PATH, st.session_state.session_id, "output", item_name_with_xlsx)
    with col[idx]:
        if os.path.exists(item_path) and st.session_state.file_db_matched == True:
            # 파일명 추출
            file_name = os.path.basename(item_path)

            # 파일을 다운로드할 수 있는 버튼 제공
            with open(item_path, 'rb') as file:
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