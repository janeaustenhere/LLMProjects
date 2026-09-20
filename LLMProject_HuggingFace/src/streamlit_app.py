from http.client import responses

import streamlit as st
from llm_chat.chatservice import ChatService

st.set_page_config(
    page_title="Hugging Face Chatbot",
    page_icon="🤖"
)

st.title("Hugging Face Chatbot")
st.caption("Ask questions using a hugging face chatbot")

@st.cache_resource
def get_chat_service() -> ChatService:
    return ChatService()

chat_service = get_chat_service()

if "message" not in st.session_state:
    st.session_state.message = []

with st.sidebar:
    if st.button("Clear Conversation"):
        st.session_state.message = []
        st.rerun()
#Redisplay all saved messages whenever Streamlit rerun the script.

for message in st.session_state.message:
    with st.chat_message(message["role"]):
        st.markdown(message["content"], unsafe_allow_html=True)

if prompt := st.chat_input("Ask a question"):
    with st.chat_message("user"):
        st.markdown(prompt, unsafe_allow_html=True)

    previous_message = st.session_state.message

    with st.chat_message("assistant"):
        with st.spinner("thinking...."):
            try:
                response = chat_service.reply(prompt,previous_message)
                st.markdown(response, unsafe_allow_html=True)
            except Exception as e:
                st.error(f"Could not get response from assistant: {e}")
                response = None

    st.session_state.message.append({"role":"user", "content":prompt})

    if response:
        st.session_state.message.append({"role":"assistant", "content":response})



