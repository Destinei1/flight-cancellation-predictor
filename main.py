from ingestion.flight_api import get_flight_summary, get_flight_history
from ingestion.weather_api import get_weather_for_route
from storage.database import save_flight_history, save_flight_summary, save_weather_for_route


def run_ingestion() -> None:
    print("=== Starting daily ingestion ===\n")

    history = get_flight_history()
    save_flight_history(history)

    summary = get_flight_summary()
    save_flight_summary(summary)

    route = get_weather_for_route()
    save_weather_for_route(route)

    print("\n=== Ingestion complete ===")


if __name__ == "__main__":
    run_ingestion()
