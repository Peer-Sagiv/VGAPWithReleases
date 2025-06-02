from pulp import *
from typing import List, TYPE_CHECKING

if TYPE_CHECKING:
    from members import Client, Machine

class OPTAlg:
    def __init__(self, machines: List['Machine'], clients: List['Client'], time_interval):
        self._machines = machines
        self._clients:List['Client'] = clients
        self._dimension = len(clients[0].demands)
        self._time_interval = time_interval

    def calc_value(self):
        T = sorted(set(t for c in self._clients for t in range(c.assign_time, c.departure_time, self._time_interval)))
        prob = LpProblem("MultipleKnapsackWithDepartures", LpMaximize)

        x = LpVariable.dicts("x", ((c, s) for c in self._clients for s in self._machines), lowBound=0, upBound=1)
        prob += lpSum(c.value * x[(c, s)] for c in self._clients for s in self._machines)

        for c in self._clients:
            prob += lpSum(x[(c, s)] for s in self._machines) <= 1, f"MachineAssignment_{c}"
        for s in self._machines:
            for d in range(self._dimension):
                for t in T:
                    active_clients = [c for c in self._clients if c.assign_time <= t < c.departure_time]
                    prob += lpSum(c.demands[d] * x[(c, s)]  for c in active_clients) <= s.capacity(d), f"Cap_{s}_{d}_t{t}"
        
        total_value = 0
        prob.solve()
        for client in self._clients:
            for machine in self._machines:
                total_value += client.value * x[(client, machine)].varValue
        return total_value
