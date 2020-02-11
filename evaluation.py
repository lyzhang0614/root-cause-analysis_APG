import os
import pandas as pd
import matplotlib.pyplot as plt

approaches = ['random_walk', 'state_iteration', 'DBR', 'random_selection', 'TBAC']
rou = 0.5

"""1.计算平均精度均值 MAP"""


def hit_num(true_rc, predict_rc):
    n = 0
    for p_rc in predict_rc:
        if p_rc in true_rc:
            n += 1
    return n


def cal_ap(k, scenarios, true_rc, approach):
    ap = 0.0
    for i, t_rc in zip(scenarios, true_rc):
        scenario = 'simulation' + str(i)
        s = '-' + str(200) if approach == 'random_walk' else ''
        model_id = approach + '-' + str(rou) + s
        path = os.path.join('demo', scenario, approach, model_id)
        files = os.listdir(path)
        full_path = os.path.join(path, files[-2])
        df = pd.read_csv(full_path)
        root_cause_list = df['root_cause']
        temp = hit_num(t_rc, root_cause_list[:k]) / min([k, len(t_rc)])
        ap += temp
    ap = ap / len(scenarios)
    return ap


def cal_map(apg_nodes_num, scenarios, true_rc, approach):
    m_ap = 0
    for k in range(1, apg_nodes_num + 1):
        m_ap += cal_ap(k, scenarios, true_rc, approach)
    m_ap = m_ap / apg_nodes_num
    return m_ap


"""2.计算输出根因列表的运行时间"""


def cal_runtime(scenarios, approach):
    m_rt = 0.0
    for i in scenarios:
        scenario = 'simulation' + str(i)
        s = '-' + str(200) if approach == 'random_walk' else ''
        model_id = approach + '-' + str(rou) + s
        path = os.path.join('demo', scenario, approach, model_id)
        files = os.listdir(path)
        full_path = os.path.join(path, files[-1])
        with open(full_path, 'r') as f:
            rt = f.read()
        temp = float(rt)
        m_rt += temp
    m_rt = m_rt / len(scenarios)
    return m_rt


""" 3.计算误报率（得到根因列表后，故障排查耗时） AFP, MEP"""


def cal_n(true_rc, node, sorted_rc):
    n = 0
    if node in true_rc:
        for node_j in sorted_rc:
            if node_j not in true_rc:
                n += 1
    return n


def cal_fp(scenarios, true_rc, approach):
    afp = 0.0
    mfp = 0.0
    for i, t_rc in zip(scenarios, true_rc):
        scenario = 'simulation' + str(i)
        s = '-' + str(200) if approach == 'random_walk' else ''
        model_id = approach + '-' + str(rou) + s
        path = os.path.join('demo', scenario, approach, model_id)
        files = os.listdir(path)
        full_path = os.path.join(path, files[-2])
        df = pd.read_csv(full_path)
        sorted_nodes = list(df['root_cause'])
        n_list = []
        for i, node in enumerate(sorted_nodes):
            n_list.append(cal_n(t_rc, node, sorted_nodes[:i + 1]))
        temp = sum(n_list) / len(t_rc)
        # print(temp)
        afp += temp
        mfp += max(n_list)
    afp = afp / len(scenarios)
    mfp = mfp / len(scenarios)
    return afp, mfp


"""4.画算个柱状图：Scenarios 10-14, MAP and AFP, alarm error"""


def plot_alarm_error(value_rw, value_si, s):
    plt.figure(figsize=(12, 6))
    names = ['Scenario %d' % x for x in range(10, 15)]
    x = range(5)

    plt.scatter(x, value_rw, label='Random Walk', marker='o', s=1000)
    plt.scatter(x, value_si, label='State Iteration', marker='^', s=1000)
    plt.plot(x, value_rw, linewidth=10)
    plt.plot(x, value_si, linewidth=10)

    plt.xticks(x, names, fontsize=35, rotation=5)
    if s == 'MAP':
        plt.ylim(0, 1.05)
    plt.yticks(fontsize=35)
    plt.ylabel(s, fontsize=35)
    plt.legend(fontsize=35)
    plt.show()


# 输入场景、图规模、真实根因列表
scenario_types = [[1, 2, 3, 4], [5], [6], [7, 8, 9], [10, 11, 12, 13, 14]]
apg_nums = [18, 18, 20, 19, 26]
true_rcs = [[['app5'], ['host4'], ['sv2'], ['sv2', 'app5', 'host3', 'host4', 'host5']],
            [['app8']],
            [['app8']],
            [['app9'], ['host4', 'sv2'], ['host4', 'app9', 'sv2', 'host9']],
            [['host4', 'app9', 'sv2', 'host9'], ['host4', 'app9', 'sv2', 'host9'], ['host4', 'app9', 'sv2', 'host9'],
             ['host4', 'app9', 'sv2', 'host9'], ['host4', 'app9', 'sv2', 'host9']]]
# scenario_types = [[10, 11, 12, 13, 14]]
# apg_nums = [26]
# true_rcs = [[['host4', 'app9', 'sv2', 'host9'], ['host4', 'app9', 'sv2', 'host9'], ['host4', 'app9', 'sv2', 'host9'],
#              ['host4', 'app9', 'sv2', 'host9'], ['host4', 'app9', 'sv2', 'host9']]]
# scenario_types = [[10], [11], [12], [13], [14]]
# apg_nums = [26, 26, 26, 26, 26]
# true_rcs = [[['host4', 'app9', 'sv2', 'host9']], [['host4', 'app9', 'sv2', 'host9']],
#             [['host4', 'app9', 'sv2', 'host9']],
#             [['host4', 'app9', 'sv2', 'host9']], [['host4', 'app9', 'sv2', 'host9']]]

# 计算评估指标
for apg_num, scenarios, true_rc in zip(apg_nums, scenario_types, true_rcs):
    print('scenarios:', scenarios)
    print('size:', apg_num)
    for approach in approaches:
        m_ap = cal_map(apg_num, scenarios, true_rc, approach)
        print(approach, ':', m_ap)

for scenarios in scenario_types:
    print('scenarios:', scenarios)
    for approach in approaches:
        m_rt = cal_runtime(scenarios, approach)
        print(approach, ':', m_rt)

for apg_num, scenarios, true_rc in zip(apg_nums, scenario_types, true_rcs):
    print('scenarios:', scenarios)
    for approach in approaches:
        afp, mfp = cal_fp(scenarios, true_rc, approach)
        print(approach, ':')
        print('AFP:', afp)
        print('MFP:', mfp)

'''rw_map = [0.99, 0.96, 0.97, 0.95, 0.92]  # random walk
si_map = [0.81, 0.81, 0.81, 0.81, 0.81]  # state iteration
rw_afp = [0.25, 0.75, 0.75, 1.25, 1.75]
si_afp = [4.50, 4.50, 4.50, 4.50, 4.50]
plot_alarm_error(rw_map, si_map, 'MAP')
plot_alarm_error(rw_afp, si_afp, 'AFP')'''
