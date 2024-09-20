import streamlit as st
from src.makeresponse import make_response
from src.managedb import load_db

st.title("표를 아는 챗봇")

if "messages" not in st.session_state:
    st.session_state.messages = []
    st.session_state.db = load_db()

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