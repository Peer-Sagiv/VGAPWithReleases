import random
import json

# A real value can't be negative
UNSATISFIABLE_VALUE = -1337

class Client:
    def __init__(self, assign_time, departure_time, demands, value):
        self.assign_time = assign_time
        self.departure_time = departure_time
        self.demands = demands
        self.value = value

    def value_density(self):
        return self.value / (sum(self.demands) * self.departure_time - self.assign_time)
    
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
        return cls(int(entry["start_time"]), int(entry["end_time"]), [float(d) for d in json.loads(entry["demands"])], int(entry["value"]))

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
