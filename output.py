# ㄹㅇ 걍 껍데기 상태

import streamlit as st

st.title("표를 아는 챗봇")


# Initialize chat history
if "messages" not in st.session_state:
    st.session_state.messages = []

# Display chat messages from history on app rerun
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])
        
# React to user input
if prompt := st.chat_input("입력"):
    # Display user message in chat message container
    st.chat_message("user").markdown(prompt)
    # Add user message to chat history
    st.session_state.messages.append({"role": "user", "content": prompt})
    if prompt[0] == "한":
        response = "한국전력공사의 당기 유동자산은 29,536,215백만원 입니다."
    elif prompt[0] == "삼":
        response = "삼성전자, 한국전력공사, 현대자동차의 당기 재고자산의 합계는 177,901,835백만원 입니다."
    else:
        response = "죄송합니다. 제공된 자료에서는 해당 질문에 대한 답변을 찾을 수 없습니다."
    #response = f"Echo: {prompt}"
    # Display assistant response in chat message container
    with st.chat_message("assistant"):
        st.markdown(response)
    # Add assistant response to chat history
    st.session_state.messages.append({"role": "assistant", "content": response})