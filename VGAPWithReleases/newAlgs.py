
import random
from typing import List, TYPE_CHECKING
from pulp import *

if TYPE_CHECKING:
    from members import Machine, Client

class VGAPWD:
    def __init__(self, history_set, machines: List['Machine'], clients: List['Client'], alpha = 0.5):
        self._history_set = history_set
        self._machines = machines
        self._clients: List['Client'] = clients
        self._num_demands = len(clients)
        self._value = 0
        self._dimension = len(clients[0].demands)
        self._alpha = alpha
        self._max_time_request = self._calc_max_time_request()
        
    def _calc_max_time_request(self):
        return max([c.departure_time - c.assign_time for c in self._clients])
  
    def step(self, client):
        history_set: List['Client'] = random.sample(self._history_set, self._num_demands - 1) + [client]
        for s in self._machines:
            s.flush(client)
        prob = LpProblem("MultipleKnapsackWithDepartures", LpMaximize)

        x = LpVariable.dicts("x", ((c, s) for c in history_set for s in self._machines), lowBound=0, upBound=1)
        prob += lpSum(c.value * x[(c, s)] for c in history_set for s in self._machines)

        for c in history_set:
            prob += lpSum(x[(c, s)] for s in self._machines) <= 1
        for s in self._machines:
            for d in range(self._dimension):
                prob += lpSum(c.demands[d] * ((c.departure_time - c.assign_time) / self._max_time_request) * x[(c, s)] for c in history_set) <= s.capacity(d) * self._alpha
        
        prob.solve()
        probs = [(s, x[(client, s)].varValue) for s in self._machines]
        total = sum(p for _, p in probs) if probs else 0
        if total == 0:
            print(f"Customer {client} is unassigned")
            assigned_machine = None
        else:
            normalized = [(s, p / total) for s, p in probs]
            slots, weights = zip(*normalized)
            assigned_machine = random.choices(slots, weights=weights)[0]
            print(f"Customer {client} assigned to {assigned_machine} by randomized rounding")
        
        if assigned_machine and assigned_machine.check_feasible(client):
            self._value += client.value
            assigned_machine.assign(client)
    
    def calc_value(self):
        for m in self._machines:
            m.clear()
        self._clients.sort(key=lambda c:c.assign_time)
        for i, c in enumerate(self._clients):
            self.step(c)
            self._history_set.append(c)
            print(f"Finished round {i}")
        return self._value


class VMKPSD(VGAPWD):
    def step(self, client):
        history_set: List['Client'] = random.sample(self._history_set, self._num_demands - 1) + [client]
        for s in self._machines:
            s.flush(client)
        prob = LpProblem("VectorMultipleKnapsackWithDepartures", LpMaximize)

        x = LpVariable.dicts("y", ((c) for c in history_set), lowBound=0, upBound=1)
        prob += lpSum(c.value * x[(c)] for c in history_set)

        for d in range(self._dimension):
            prob += lpSum(c.demands[d] * ((c.departure_time - c.assign_time) / self._max_time_request) * x[(c)] for c in history_set) <= len(self._machines) * self._alpha
        
        prob.solve()
        probability = x[(client)].varValue
        if probability < random.random():
            print(f"Customer {client} is unassigned")
            return
        for s in self._machines:
            if s.check_feasible(client):
                s.assign(client)
                self._value += client.value
                print(f"Customer {client} assigned to {s} by randomized rounding")
                return
        print(f"Customer {client} is unassigned due to no free machines")
