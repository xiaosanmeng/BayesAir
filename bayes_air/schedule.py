"""Define methods for working with schedules."""
import pandas as pd

from bayes_air.types import Airport, Flight


# Parse the provided data into our custom data structures
def parse_flight(schedule_row: tuple) -> Flight:
    """
    Parse a row of the schedule into an Flight object.

    Args:
        schedule_row: a tuple of the following items
            - flight_number
            - origin_airport
            - destination_airport
            - scheduled_departure_time
            - scheduled_arrival_time
            - actual_departure_time
            - actual_arrival_time
    """
    (
        flight_number,
        origin_airport,
        destination_airport,
        scheduled_departure_time,
        scheduled_arrival_time,
        actual_departure_time,
        actual_arrival_time,
    ) = schedule_row

    return Flight(
        flight_number=flight_number,
        origin=origin_airport,
        destination=destination_airport,
        scheduled_departure_time=scheduled_departure_time,
        scheduled_arrival_time=scheduled_arrival_time,
        actual_departure_time=actual_departure_time,
        actual_arrival_time=actual_arrival_time,
    )


def parse_schedule(schedule_df: pd.DataFrame) -> tuple[list[Flight], list[Flight]]:
    """Parse a pandas dataframe for a schedule into a list of pending flights.

    Args:
        schedule_df: A pandas dataframe with the following columns:
            flight_number: The flight number
            origin_airport: The airport code of the origin airport
            destination_airport: The airport code of the destination airport
            scheduled_departure_time: The scheduled departure time
            scheduled_arrival_time: The scheduled arrival time
            actual_departure_time: The actual departure time
            actual_arrival_time: The actual arrival time

    Returns:
        a list of flights, and
        a list of airports
    """
    # Get a list of flights
    flights = [parse_flight(row) for row in schedule_df.itertuples(index=False)]

    # Get a list of unique airport codes from the origin and destination columns
    airport_codes = pd.concat(
        [schedule_df["origin_airport"], schedule_df["destination_airport"]]
    ).unique()
    # Create an airport object for each airport code
    airports = [Airport(code) for code in airport_codes]

    return flights, airports
