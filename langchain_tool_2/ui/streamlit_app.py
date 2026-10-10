import os
from http.client import responses

import httpx
import streamlit as st

BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8090").rstrip("/")

st.set_page_config(page_title="Hopscotch Chat", page_icon="🛍️")

st.title("Hopscotch Chat")
st.session_state.setdefault("login", None)
st.session_state.setdefault("messages", [])

def post(path: str, **kwargs) -> dict:
    response = httpx.post(f"{BACKEND_URL}{path}", timeout=180, **kwargs)
    response.raise_for_status()
    return response.json()

if st.session_state.login is None:
    with st.form("login_form"):
        email = st.text_input("Email")
        submitted = st.form_submit_button("sign in")
    if submitted:
        try:
            st.session_state.login = post("/api/v1/auth/login",
                                          json={"email": email})
            st.rerun()
        except httpx.HTTPStatusError as err:
            st.error(f"sign-in failed: {err}")
    st.stop()

login = st.session_state.login
st.caption(f"Signed in as {login['customer']['email']}")
token = login["access_token"]
headers = {"Authorization": f"Bearer {token}"}

if st.button("sign out"):
    try:
        httpx.delete(f"{BACKEND_URL}/api/v1/chat/history", headers=headers, timeout=180)
    finally:
        st.session_state.login = None
        st.session_state.messages = []
        st.rerun()

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

if query := st.chat_input("Ask about your cart or orders"):
    st.session_state.messages.append({"role": "user", "content": query})
    with st.chat_message("user"):
        st.markdown(query)
    with st.chat_message("assistant"):
        try:
            with st.spinner("Thinking..."):
                answer = post("/api/v1/chat", headers=headers,
                              json={"query": query})["answer"]
            st.markdown(answer)
            st.session_state.messages.append({"role": "assistant", "content": answer})
        except httpx.HTTPStatusError as err:
            st.error(f"sign-in failed: {err}")

