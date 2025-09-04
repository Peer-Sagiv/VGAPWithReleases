import random
import json
from collections.abc import Sequence


# A real value can't be negative
UNSATISFIABLE_VALUE = -1337

class Client:
    def __init__(self, assign_time, departure_time, demands, value):
        self.assign_time = assign_time
        self.departure_time = departure_time
        self.demands = demands
        self.value = value

    @property
    def is_satisfible(self):
        return self.value != UNSATISFIABLE_VALUE

    @classmethod
    def from_json_entry(cls, entry):
        return cls(entry["start_time"], entry["end_time"], [entry["cpus"], entry["memory"]], entry["value"])

    @classmethod
    def from_csv_entry(cls, entry, random_demands=False):
        if random_demands:
            return cls(int(entry["start_time"]), int(entry["end_time"]), [random.uniform(0.01, 0.5), random.uniform(0.01, 0.5)], float(entry["value"]))
        return cls(int(entry["start_time"]), int(entry["end_time"]), [float(entry["max_cpus"]), float(entry["max_memory"])], float(entry["value"]))

    @classmethod
    def from_presaved_entry(cls, entry):
        return cls(int(entry["start_time"]), int(entry["end_time"]), [float(d) for d in json.loads(entry["demands"])], float(entry["value"]))

    @classmethod
    def from_azure_entry(cls, entry):
        return cls(int(entry["start_time"]), int(entry["end_time"]), [float(entry["core"]), float(entry["memory"]), float(entry["ssd"]), float(entry["nic"])], float(entry["value"]))

    @classmethod
    def unsatisfiable_client(cls, dimensions):
        return cls(0, 1, [100 for _ in range(dimensions)], UNSATISFIABLE_VALUE)

    def to_dict(self):
        return {
            "start_time": self.assign_time,
            "end_time": self.departure_time,
            "demands": self.demands,
            "value": self.value
        }

class Machine:
    def __init__(self, capacities):
        self._capacities = capacities
        self._clients = []

    def clear(self):
        self._clients = []

    def dimensions(self):
        return len(self._capacities)

    def capacity(self, d):
        return self._capacities[d]

    def assign(self, client):
        self._clients += [client]

    def _calc_cur_capacities(self):
        curr_capacities = self._capacities.copy()
        for c in self._clients:
            for i in range(len(curr_capacities)):
                curr_capacities[i] -= c.demands[i]
        return curr_capacities

    def check_feasible(self, client):
        for i, cap in enumerate(self._calc_cur_capacities()):
            if client.demands[i] > cap:
                return False
        return True

    def calc_residue(self, client):
        residue = None
        for i, capacity in enumerate(self._calc_cur_capacities()):
            if residue is None:
                residue = capacity - client.demands[i]
            else:
                residue = min(residue, capacity - client.demands[i])
        return residue

    def flush(self, client):
        self._clients = [c for c in self._clients if c.departure_time > client.assign_time]

class TimeWindow(Sequence):
    def __init__(self, clients_list, start_time, end_time, unit_size):
        self._clients_list = clients_list
        self._start_time = start_time
        self._end_time = end_time
        self.unit_size = unit_size
        self.length = int((end_time - start_time) // unit_size)

    def __getitem__(self, index):
        return self._clients_list[index]

    def __setitem__(self, index, value):
        self._clients_list[index] = value

    def __len__(self):
        return len(self._clients_list)

    def __iter__(self):
        return iter(self._clients_list)

    def __repr__(self):
        return repr(self._clients_list)

    def __iadd__(self, other):
        if isinstance(other, list):
            self._clients_list.extend(other)
            return self
        elif isinstance(other, TimeWindow):
            self._clients_list.extend(other._clients_list)
            return self
        else:
            raise TypeError(f"Cannot add type {type(other)} to History")

    def sort(self, *args, **kwargs):
        self._clients_list.sort(*args, **kwargs)


    def get_latest_from_window(self, required_time):
        """
        Returns a tuple:
          - First element: a TimeWindow object for the latest window
          - Second element: a TimeWindow object for the remaining earlier part
        """
        history_interval_time = required_time * self.unit_size
        window_start = self._end_time - history_interval_time

        latest = [client for client in self._clients_list if client.assign_time >= window_start]
        earlier = [client for client in self._clients_list if client.assign_time < window_start]

        latest_window = TimeWindow(latest, window_start, self._end_time, unit_size=self.unit_size)
        remaining_window = TimeWindow(earlier, self._start_time, window_start, unit_size=self.unit_size)

        return latest_window, remaining_window


    def get_random_window(self, required_time):
        history_interval_time = required_time * self.unit_size


        max_query_interval = self._end_time - history_interval_time
        current_query_time = random.randint(0, max_query_interval) * self.unit_size + self._start_time

        start = current_query_time
        end = start + history_interval_time
        return TimeWindow([client for client in self._clients_list if start <= client.assign_time < end], start, end, unit_size=self.unit_size)

    def iter_windows(self, k):
        """
        Yield TimeWindow objects of length k * unit_size sliding through the full time window.
        """
        window = k * self.unit_size
        t = self._start_time
        while t + window <= self._end_time:
            start = t
            end = t + window
            curr_window = TimeWindow(
                [client for client in self._clients_list if start <= client.assign_time < end],
                start,
                end,
                unit_size=self.unit_size
            )
            yield curr_window
            t += window


    def iter_windows_reverse(self, k):
        """
        Yield TimeWindow objects of length k * unit_size sliding backwards from end_time to start_time.
        """
        window = k * self.unit_size
        t = self._end_time
        while t - window >= self._start_time:
            start = t - window
            end = t
            curr_window = TimeWindow(
                [client for client in self._clients_list if start <= client.assign_time < end],
                start,
                end,
                unit_size=self.unit_size
            )
            yield curr_window
            t -= window


    def get_random_window_pair(self, required_time):
        history_interval_time = required_time * self.unit_size

        max_query_interval = self._end_time - history_interval_time * 2
        current_query_time = random.randint(0, max_query_interval) * self.unit_size + self._start_time
        first_start = current_query_time
        first_end = first_start + history_interval_time
        second_start = first_end
        second_end = first_end + history_interval_time
        window1 = TimeWindow([client for client in self._clients_list if first_start <= client.assign_time < first_end], first_start, first_end, unit_size=self.unit_size)
        window2 = TimeWindow([client for client in self._clients_list if second_start <= client.assign_time < second_end], second_start, second_end, unit_size=self.unit_size)

        return window1, window2


    def iter_window_pairs(self, k, step=None):
        """
        Yield (TimeWindow, TimeWindow) pairs with windows of length k * self.unit_size.
        """
        window = k * self.unit_size
        real_step = window
        if step:
            real_step = step * self.unit_size

        t = self._start_time
        while t + 2 * window <= self._end_time:
            first_start = t
            first_end = t + window
            second_start = first_end
            second_end = first_end + window

            window1 = TimeWindow(
                [client for client in self._clients_list if first_start <= client.assign_time < first_end],
                first_start,
                first_end,
                unit_size=self.unit_size
            )
            window2 = TimeWindow(
                [client for client in self._clients_list if second_start <= client.assign_time < second_end],
                second_start,
                second_end,
                unit_size=self.unit_size
            )
            yield window1, window2
            t += real_step


    def get_max_total_demand(self):
        """
        Compute the maximum total demand over time in each resource dimension.
        Returns:
            A tuple of floats representing the peak concurrent demand per resource dimension observed.
        """
        if not self._clients_list:
            return tuple()

        events = []
        for client in self._clients_list:
            events.append((client.assign_time, 'start', client))
            events.append((client.departure_time, 'end', client))

        # Sort events; for same time, 'end' events before 'start' events
        events.sort(key=lambda x: (x[0], 0 if x[1] == 'end' else 1))

        num_dims = len(self._clients_list[0].demands)
        current_demand = [0.0] * num_dims
        max_demand = [0.0] * num_dims

        for _, event_type, client in events:
            demands = client.demands
            if event_type == 'end':
                for i in range(num_dims):
                    current_demand[i] -= demands[i]
            else:  # 'start'
                for i in range(num_dims):
                    current_demand[i] += demands[i]
            for i in range(num_dims):
                if current_demand[i] > max_demand[i]:
                    max_demand[i] = current_demand[i]

        return tuple(max_demand)

    def get_sum_total_demand(self):
        """
        Compute the sum of total demand (demand * duration) over all clients in each resource dimension.
        Returns:
            A tuple of floats representing the total resource consumption per dimension.
        """
        if not self._clients_list:
            return tuple()

        num_dims = len(self._clients_list[0].demands)
        sum_demand = [0.0] * num_dims

        for client in self._clients_list:
            duration = (client.departure_time - client.assign_time) // self.unit_size
            if duration <= 0:
                continue
            for i in range(num_dims):
                sum_demand[i] += client.demands[i] * duration

        return tuple(sum_demand)

    def get_avg_demand(self):
        return [demand / (2 * self.length) for demand in self.get_sum_total_demand()]
