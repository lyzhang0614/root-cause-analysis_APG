import os
import pandas as pd
from root_cause import generate


scenario = 'simulation14'
names = ['apg_nodes', 'apg_edges', 'alerts']
data_dict = dict()
for k in names:
    df = pd.read_csv(os.path.join('data_apg', scenario, k + '.csv'))
    data_dict[k] = df


approaches = ['random_walk', 'state_iteration', 'DBR', 'random_selection', 'TBAC']
# generate(data_dict=data_dict, params_dict=dict(approach=approaches[0], rou=0.5, walkers=50),
#          save_path=os.path.join('demo', scenario, approaches[0]))
# generate(data_dict=data_dict, params_dict=dict(approach=approaches[1], rou=0.5),
#          save_path=os.path.join('demo', scenario, approaches[1]))
# generate(data_dict=data_dict, params_dict=dict(approach=approaches[2]),
#          save_path=os.path.join('demo', scenario, approaches[2]))
# generate(data_dict=data_dict, params_dict=dict(approach=approaches[3]),
#          save_path=os.path.join('demo', scenario, approaches[3]))
generate(data_dict=data_dict, params_dict=dict(approach=approaches[4], p=0.2, z=5),
         save_path=os.path.join('demo', scenario, approaches[4]))
