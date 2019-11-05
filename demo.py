import os
import pandas as pd
from root_cause import generate

scenario = 'simulation1'
names = ['apg_nodes', 'apg_edges', 'alerts']
data_dict = dict()
for k in names:
    df = pd.read_csv(os.path.join('data_apg', scenario, k + '.csv'))
    data_dict[k] = df

approaches = ['random_walk', 'state_iteration']
generate(data_dict=data_dict, params_dict=dict(approach=approaches[0], rou=0.5, walkers=200),
         save_path=os.path.join('demo', scenario, approaches[0]))
generate(data_dict=data_dict, params_dict=dict(approach=approaches[1], rou=0.5),
         save_path=os.path.join('demo', scenario, approaches[1]))
