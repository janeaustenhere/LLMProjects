"""Gradio entry point for the Hopscotch support assistant."""

from src.ui import create_app


if __name__ == "__main__":
    create_app().launch()
