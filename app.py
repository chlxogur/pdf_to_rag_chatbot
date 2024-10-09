import streamlit as st
import os
from src.makeresponse import make_response
from src.managedb import load_db, make_db
from src.fileio import save_uploaded_files
from src.maketable import make_table
from src.config import OUTPUT_PATH

def update_db():
    make_table()
    st.session_state.messages = []
    st.session_state.db = make_db()
    file_paths = [
        os.path.join(OUTPUT_PATH, "연결 재무상태표.xlsx"),
        os.path.join(OUTPUT_PATH, "연결 손익계산서.xlsx"),
        os.path.join(OUTPUT_PATH, "연결 포괄손익계산서.xlsx")
    ]
    for file_path in file_paths:
        if os.path.exists(file_path):
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
        else:
            st.write(f"File {file_path} does not exist.")

st.title("표를 아는 챗봇")

if "messages" not in st.session_state:
    st.session_state.messages = []
    st.session_state.db = load_db()

uploaded_files = st.file_uploader("PDF 파일 업로드", type="pdf", accept_multiple_files=True)

if uploaded_files:
    # 파일명을 출력
    file_names = save_uploaded_files(uploaded_files)

if st.button("DB 새로고침"):
    update_db()

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