"""Define a probabilistic model for an air traffic network."""

import pyro
import pyro.distributions as dist

from bayes_air.network import NetworkState
from bayes_air.types import QueueEntry


def air_traffic_network_model(
    states: NetworkState, T: float = 24.0, delta_t: float = 0.1
):
    """
    Simulate the behavior of an air traffic network.

    Args:
        states: the starting states of the simulation (will run an independent
            simulation from each start state). All states must include the same
            airports.
        T: the duration of the simulation, in hours
        delta_t: the time resolution of the simulation, in hours
    """
    # Define parameters used by the simulation
    runway_use_time_std_dev = 1.0 / 60  # 1 minute
    travel_time_variation = 0.05  # 5% variation in travel time
    turnaround_time_variation = 0.05  # 5% variation in turnaround time

    # Sample latent variables for airports
    airport_codes = states[0].airports.keys()
    airport_turnaround_times = {
        code: pyro.sample(f"{code}_mean_turnaround_time", dist.Normal(0.75, 0.25))
        for code in airport_codes
    }
    airport_service_times = {
        code: pyro.sample(f"{code}_mean_service_time", dist.Normal(9.0 / 60, 3.0 / 60))
        for code in airport_codes
    }
    travel_times = {
        (origin, destination): pyro.sample(
            f"travel_time_{origin}_{destination}", dist.Normal(1.0, 0.25)
        )
        for origin in airport_codes
        for destination in airport_codes
        if origin != destination
    }

    # Simulate for each state
    output_states = []
    for ind in pyro.plate("days", len(states)):
        state = states[ind]

        # Assign the latent variables to the airports
        for airport in state.airports.values():
            airport.mean_service_time = airport_service_times[airport.code]
            airport.runway_use_time_std_dev = runway_use_time_std_dev
            airport.mean_turnaround_time = airport_turnaround_times[airport.code]
            airport.turnaround_time_std_dev = (
                turnaround_time_variation * airport.mean_turnaround_time
            )

        # Simulate the movement of aircraft within the system for a fixed period of time
        t = 0.0
        for _ in pyro.markov(range(int(T // delta_t))):
            # Update the current time
            t += delta_t

            # All parked aircraft that are ready to turnaround get serviced
            for airport in state.airports.values():
                airport.update_available_aircraft(t)

            # All flights that are able to depart get moved to the runway queue at their
            # origin airport
            ready_to_depart_flights, ready_times = state.pop_ready_to_depart_flights(t)
            for flight, ready_time in zip(ready_to_depart_flights, ready_times):
                queue_entry = QueueEntry(flight=flight, queue_start_time=ready_time)
                state.airports[flight.origin].runway_queue.append(queue_entry)

            # All flights that are using the runway get serviced
            for airport in state.airports.values():
                departed_flights, landing_flights = airport.update_runway_queue(t)

                # Departing flights get added to the in-transit list, while landed flights
                # get added to the completed list
                state.add_in_transit_flights(
                    departed_flights, travel_times, travel_time_variation
                )
                state.add_completed_flights(landing_flights)

            # All flights that are in transit get moved to the runway queue at their
            # destination airport, if enough time has elapsed
            state.update_in_transit_flights(t)

        # Once we're done, return the state (this will include the actual arrival/departure
        # times for each aircraft)
        output_states.append(state)

    return output_states
