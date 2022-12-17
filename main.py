import simpy
import random
import pandas as pd
from datetime import datetime


class Globals:
    number_of_simulations = 1
    number_of_agents = 3
    # time being simulated in sec -> number or None
    run_number = None
    # number of calls to receive if run number set to None
    call_list = 10
    # arrival interval parameters
    a_h = 18
    a_l = 10
    a_m = 13.5
    # am clearance duration parameters
    d_h = 10
    d_l = 0
    d_m = 3
    # patience parameters
    p_h = 11
    p_l = 4
    # talk time parameters
    t_h = 90
    t_l = 20
    # clerical time parameters
    c_h = 10
    c_l = 5
    results = pd.DataFrame(columns=['run', 'call_no', 'capacity', 'arrival_time', 'wait_time', 'if_dropped',
                                    'wait_before_drop', 'talk_time', 'clerical_time'])


class CallCenter:
    def __init__(self, i, n):
        self.env = simpy.Environment()
        self.duration = 0
        self.name = 0
        self.capacity = n
        self.agent = simpy.Resource(self.env, capacity=self.capacity)
        self.i = i

    def inbound_line(self):
        while self.name < Globals.call_list if Globals.call_list else 1:
            self.name += 1
            call = IncomingCall(self.name)
            interval = call.interval
            self.env.process(self.accepting_call(call))
            yield self.env.timeout(interval)

    def accepting_call(self, call):
        diction = {'run': [self.i + 1], 'call_no': [call.name], 'capacity': [self.capacity]}
        arrival_time = self.env.now
        diction['arrival_time'] = [arrival_time]
        print(f'call # {call.name} came at {self.env.now}')
        with self.agent.request() as req:
            yield req | self.env.timeout(call.patience)
            if req.triggered:
                wait_time = self.env.now - arrival_time
                diction['wait_time'] = [wait_time]
                print(f'call # {call.name} was waiting for {wait_time} sec')
                talk_time = random.uniform(Globals.t_l, Globals.t_h)
                diction['talk_time'] = [talk_time]
                yield self.env.timeout(talk_time)
                clerical_time = random.uniform(Globals.c_l, Globals.c_h)
                diction['clerical_time'] = [clerical_time]
                yield self.env.timeout(clerical_time)
                print(f'call # {call.name} has been finished at {self.env.now}')
            else:
                print(f'call # {self.name} left at {self.env.now} after waiting {self.env.now - arrival_time} sec')
                diction['if_dropped'] = [1]
                diction['wait_before_drop'] = [self.env.now - arrival_time]
        Globals.results = pd.concat([Globals.results, pd.DataFrame.from_dict(diction)], ignore_index=True)

    def run(self):
        self.env.process(self.inbound_line())
        self.env.run(until=Globals.run_number)


class IncomingCall:
    def __init__(self, name):
        self.name = name
        self.patience = random.uniform(Globals.p_l, Globals.p_h)
        self.interval = random.triangular(high=Globals.a_h, low=Globals.a_l, mode=Globals.a_m)


start = datetime.now()
for n in range(1, 100):
    for simulation in range(Globals.number_of_simulations):
        call_center = CallCenter(simulation, n)
        call_center.run()
    if Globals.results[(Globals.results['run'] == simulation) &
                       (Globals.results['capacity'] == n)]['wait_time'].mean() < 4:
        break
finish = datetime.now()
Globals.results.to_csv(f'simulation_log.csv', index=False)
print(f'simulation completed and took {finish - start} ')
