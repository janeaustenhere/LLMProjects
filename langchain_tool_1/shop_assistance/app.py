from __future__ import annotations

from typing import Any
from uuid import uuid4

import streamlit as st

from shop_assistance.application.container import ApplicationContainer
from shop_assistance.config.config import get_settings
from shop_assistance.client.shop_api_client import (
    AuthenticationError,
)


def initialize_session() -> None:
    if "container" not in st.session_state:
        settings = get_settings()
        st.session_state.container = ApplicationContainer.build(settings)

    if "thread_id" not in st.session_state:
        st.session_state.thread_id = str(uuid4())

    if "messages" not in st.session_state:
        st.session_state.messages = []

    if "authenticated_email" not in st.session_state:
        st.session_state.authenticated_email = None


def reset_conversation() -> None:
    settings = get_settings()

    old_container: ApplicationContainer = st.session_state.container
    old_container.api_client.close()

    st.session_state.container = ApplicationContainer.build(settings)
    st.session_state.thread_id = str(uuid4())
    st.session_state.messages = []
    st.session_state.authenticated_email = None


def render_login() -> None:
    st.subheader("Sign in")

    with st.form("login_form"):
        email = st.text_input(
            "Email",
            placeholder="customer@example.com",
        )
        submitted = st.form_submit_button(
            "Sign in",
            type="primary",
        )

    if submitted:
        try:
            container: ApplicationContainer = st.session_state.container
            container.api_client.sign_in(email)
            st.session_state.authenticated_email = email.strip().lower()
            st.success("Signed in successfully.")
            st.rerun()
        except AuthenticationError as exc:
            st.error(str(exc))


def render_sidebar() -> None:
    with st.sidebar:
        st.header("Session")

        if st.session_state.authenticated_email:
            st.write(
                f"Signed in as `{st.session_state.authenticated_email}`"
            )

        if st.button("New conversation", use_container_width=True):
            reset_conversation()
            st.rerun()

        st.caption(
            "The assistant can inspect your cart and orders and can "
            "cancel an explicitly selected order item."
        )


def render_history() -> None:
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

            activities = message.get("tool_activities", [])
            if activities:
                with st.expander("Tool activity"):
                    for activity in activities:
                        st.markdown(f"**{activity['tool_name']}**")
                        render_tool_output(activity["output"])


def render_tool_output(output: Any) -> None:
    if isinstance(output, (dict, list)):
        st.json(output)
    else:
        st.code(str(output), language=None)


def handle_prompt(prompt: str) -> None:
    st.session_state.messages.append(
        {
            "role": "user",
            "content": prompt,
        }
    )

    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        try:
            with st.spinner("Working on your request..."):
                container: ApplicationContainer = (
                    st.session_state.container
                )
                reply = container.agent.chat(
                    message=prompt,
                    thread_id=st.session_state.thread_id,
                )

            st.markdown(reply.content)

            serialized_activities = [
                {
                    "tool_name": activity.tool_name,
                    "output": activity.output,
                }
                for activity in reply.tool_activities
            ]

            if serialized_activities:
                with st.expander("Tool activity"):
                    for activity in serialized_activities:
                        st.markdown(
                            f"**{activity['tool_name']}**"
                        )
                        render_tool_output(activity["output"])

            st.session_state.messages.append(
                {
                    "role": "assistant",
                    "content": reply.content,
                    "tool_activities": serialized_activities,
                }
            )

        except Exception as exc:
            error_message = (
                "I couldn't complete that request. "
                f"Details: {exc}"
            )
            st.error(error_message)
            st.session_state.messages.append(
                {
                    "role": "assistant",
                    "content": error_message,
                }
            )


def main() -> None:
    st.set_page_config(
        page_title="Shop Assistant",
        page_icon="🛍️",
        layout="centered",
    )

    initialize_session()
    render_sidebar()

    st.title("🛍️ Shop Assistant")
    st.caption(
        "Ask about your cart or orders, or request an item cancellation."
    )

    if not st.session_state.authenticated_email:
        render_login()
        return

    render_history()

    prompt = st.chat_input(
        "Ask about your cart or orders..."
    )

    if prompt:
        handle_prompt(prompt)


if __name__ == "__main__":
    main()