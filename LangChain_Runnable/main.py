from src.support_bot.service import SupportService
from src.support_bot.ui import create_ui


def main() -> None:
    service = SupportService()
    app = create_ui(service)
    app.launch()


if __name__ == "__main__":
    main()
