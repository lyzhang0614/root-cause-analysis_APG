import igraph as ig
import numpy as np
import pandas as pd
import os
import time
import random
import math



def generate(data_dict, params_dict, save_path):
    try:
        nodes = data_dict.get('apg_nodes')
        edges = data_dict.get('apg_edges')
        alerts = data_dict.get('alerts')
    except Exception:
        raise RuntimeError('数据为空或异常！')
    try:
        approach = params_dict.get('approach')
    except Exception:
        raise RuntimeError('选择一种故障定位方法！')
    try:
        my_rca = RCA(nodes=nodes,
                     edges=edges,
                     alerts=alerts,
                     approach=approach,
                     rou=params_dict.get('rou', 0.5),

                     walkers=params_dict.get('walkers', 50),
                     p=params_dict.get('p', 0.2),
                     z=params_dict.get('z', 5))
    except ValueError:
        raise RuntimeError('数据量不足！')
    my_rca.save(save_path)


class RCA():

    def __init__(self, nodes=None, edges=None, alerts=None, approach='state_iteration', rou=0.5, walkers=50, p=0.2,
                 z=5):
        self._rou = rou
        self._walkers = walkers
        self._p = p
        self._z = z
        self._approach = approach
        self._apg = ig.Graph(directed=True)
        self._random_walk_graph = ig.Graph(directed=True)
        if nodes is not None and edges is not None and alerts is not None:
            self.rca(nodes, edges, alerts)

    def rca(self, nodes, edges, alerts):
        """构建故障传播图，基于相似度计算转移概率矩阵，进行随机游走/状态迭代，输出根因列表"""
        self._get_apg(nodes, edges)
        begin = time.clock()
        self._get_transfer_matrix()
        if self._approach == 'random_walk':
            self._random_walk(alerts)
        if self._approach == 'state_iteration':
            self._state_iteration_v2(alerts)
        if self._approach == 'DBR':
            self._DBR(alerts)
        if self._approach == 'random_selection':
            self._random_selection()
        if self._approach == 'TBAC':
            self._TBAC(alerts)
        end = time.clock()
        self._runtime = end - begin
        print(self._approach, ':', end - begin)

    def _get_apg(self, nodes, edges):
        """
            返回故障传播图，及边相似度信息。
            :param nodes: 应用/主机/服务器节点信息
            :param edges: 应用之间的调用关系（必要），应用和主机之间的部署关系（可选），主机和服务器之间的从属关系（可选），关系的相似度
            :return: 故障传播图（带有相似度）
        """
        # node:
        self._nodes = list(nodes['node'])
        self._n = len(self._nodes)
        self._apg.add_vertices(self._nodes)
        # edge, similarity:
        self._apg_edges = list(zip(edges['node1'], edges['node2']))
        self._edge_similarities = dict(zip(self._apg_edges, list(edges['similarity'])))
        self._apg.add_edges(self._apg_edges)

    def __app_p_stay(self, node, neighbors):
        """
            返回特定节点的停留概率。
            :param node: 当前节点
            :param neighbors: 当前节点的所有邻居节点
            :return: 当前节点的停留概率
        """
        x_to = []
        x_from = []
        for neighbor in neighbors:
            if (node, neighbor) in self._apg_edges:
                if (neighbor, node) not in self._apg_edges:
                    x_from.append(self._edge_similarities[node, neighbor])  # 'from' the app node
            if (neighbor, node) in self._apg_edges:
                x_to.append(self._edge_similarities[neighbor, node])  # 'to' the app node
        p = 0
        if len(x_to) > 0 and len(x_from) > 0:
            p = max(max(x_to) - max(x_from), 0)
        if len(x_to) > 0 and len(x_from) == 0:  # no child nodes
            p = max(x_to)
        return p

    def _get_transfer_matrix(self):
        """
            返回故障传播图的归一化后的转移概率矩阵。
        """
        t_matrix = np.zeros((self._n, self._n))
        t_matrix_df = pd.DataFrame(t_matrix, columns=self._nodes, index=self._nodes)
        self._random_walk_graph.add_vertices(self._nodes)
        for node in self._nodes:
            # self-edges:
            neighbors = [self._nodes[nei] for nei in set(self._apg.neighbors(vertex=node))]
            if 'app' in node:
                t_matrix_df.loc[node, node] = self.__app_p_stay(node, neighbors)
            if 'host' in node or 'sv' in node:
                p = max([self._edge_similarities[node, nei] for nei in neighbors])
                t_matrix_df.loc[node, node] = p
            self._random_walk_graph.add_edge(node, node)
        for edge in self._apg_edges:
            node_i = edge[0]
            node_j = edge[1]
            # forward-edges:
            t_matrix_df.loc[edge] = self._edge_similarities[edge]
            self._random_walk_graph.add_edge(node_i, node_j)
            # backward-edges:
            if (node_j, node_i) not in self._apg_edges:
                t_matrix_df.loc[node_j, node_i] = self._edge_similarities[edge] * self._rou
                self._random_walk_graph.add_edge(node_j, node_i)
        # normalize:
        t_matrix = t_matrix_df.values
        for i in range(0, self._n):
            t_matrix[i] = [t_matrix[i][j] / sum(t_matrix[i]) for j in range(0, self._n)]
        self._t_matrix = pd.DataFrame(t_matrix, columns=self._nodes, index=self._nodes)

    def _random_walk(self, alerts):
        """
            由告警节点出发，分配walker，随机游走，基于首次停留投票机制，输出根因列表。
            :param alerts: 告警节点列表
            :return: 根因列表（节点，停留次数）
        """
        alert_nodes = alerts['alert_node']
        self.node_stops = dict(zip(self._nodes, np.zeros(self._n)))
        for start_node in alert_nodes:
            for i in range(0, self._walkers):
                self.__random_walk(start_node)
        self.root_cause_list = sorted(self.node_stops.items(), key=lambda x: x[1], reverse=True)

    def __random_walk(self, from_node):
        """
            返回由特定节点出发，一次随机游走，所有节点的停留次数（叠加后）。
            :param from_node: 出发节点
            :return: 所有节点的停留次数（节点，停留次数）
        """
        pre_node = ''
        while pre_node != from_node:
            neighbors = set(self._random_walk_graph.neighbors(vertex=from_node))
            probabilities = [self._t_matrix.loc[from_node, self._nodes[neighbor]] for neighbor in neighbors]
            target = np.random.choice(list(neighbors), p=probabilities)
            pre_node = from_node
            from_node = self._nodes[target]
        self.node_stops[from_node] += 1

    def _state_iteration_v1(self, alerts):
        """
            根据告警列表初始化状态向量，状态迭代，输出根因列表。
            :param alerts: 告警节点列表
            :return: 根因列表（节点，概率）
        """
        steps = self._apg.diameter()
        alert_nodes = list(alerts['alert_node'])
        state_vector = []
        for node in self._nodes:
            if node in alert_nodes:
                state_vector.append(1)
            else:
                state_vector.append(0)
        sv0 = [state_vector[j] / sum(state_vector) for j in range(0, self._n)]
        sv_list = []
        for i in range(0, steps):
            b = np.power(self._t_matrix.values, i)
            sv = np.dot(np.array(sv0), b)
            sv_list.append(sv)
        p = sum(sv_list) / steps
        nodes_p = dict(zip(self._nodes, p))
        self.root_cause_list = sorted(nodes_p.items(), key=lambda x: x[1], reverse=True)

    def _state_iteration_v2(self, alerts):
        """
            根据告警列表初始化状态向量，状态迭代，输出根因列表。
            :param alerts: 告警节点列表
            :return: 根因列表（节点，概率）
        """
        alert_nodes = list(alerts['alert_node'])
        state_vector = []
        for node in self._nodes:
            if node in alert_nodes:
                state_vector.append(1)
            else:
                state_vector.append(0)
        sv0 = [state_vector[j] / sum(state_vector) for j in range(0, self._n)]
        pre = np.array(sv0)
        while (True):
            p = np.dot(np.array(pre), self._t_matrix.values)
            flag = 1
            for i in range(len(p)):
                if p[i] != pre[i]:
                    flag = 0
                    break
            if flag == 1:
                break
            pre = p
        nodes_p = dict(zip(self._nodes, p))
        self.root_cause_list = sorted(nodes_p.items(), key=lambda x: x[1], reverse=True)

    def _DBR(self, alerts):
        """
            对于每个组件c，它都形成一个传播图，其中节点是可以从c到达的一组异常组件。
            RCA问题可以转化为选择最佳传播图。
            传播图的等级由从源实体到所有其他异常实体的最小总距离确定。
            :param alerts: 告警节点列表
            :return: 根因列表（节点，最短路径长度总和）
        """
        alert_nodes = list(alerts['alert_node'])
        scores = []
        for c in self._nodes:
            # 构建子图：从c可达，异常：
            sum_path_len = 0
            for a in alert_nodes:
                path = self._apg.get_shortest_paths(c, a)[0]
                t = len(path)
                if t != 0:  # 可达
                    sum_path_len += t - 1
            scores.append(sum_path_len)
        nodes_s = dict(zip(self._nodes, scores))
        self.root_cause_list = sorted(nodes_s.items(), key=lambda x: x[1], reverse=False)

    def _random_selection(self):
        """
            由直接发布所有节点的随机排列（random permutations），输出根因列表。
            :return: 根因列表（节点，）
        """
        rs = self._nodes
        random.shuffle(rs)
        t = np.zeros(len(self._nodes))
        nodes_rs = dict(zip(rs, t))
        self.root_cause_list = sorted(nodes_rs.items(), key=lambda x: x[1], reverse=False)

    def _TBAC(self, alerts):
        """
            根据告警列表(异常分数：0.5异常，-0.5正常)，计算异常等级，输出根因列表。
            :param alerts: 告警节点列表
            :return: 根因列表（节点，异常等级）
        """
        # 每个节点，及其对应的异常分数：
        ano_scores = []
        alert_nodes = list(alerts['alert_node'])
        for node in self._nodes:
            if node in alert_nodes:
                ano_scores.append(0.5)
            else:
                ano_scores.append(-0.5)
        node_anoScores = dict(zip(self._nodes, ano_scores))
        # warshall算法计算传递闭包矩阵：
        mtx = self.__adj_matrix()
        self.__warshall(mtx)
        # 每个节点，及其对应的异常等级：
        all_s = []
        for i, node in enumerate(self._nodes):
            # 找到该节点的传递闭包
            col = mtx[:, i]
            ins = [self._nodes[k] for k in [j for j, e in enumerate(col) if e == 1]]
            row = mtx[i, :]
            outs = [self._nodes[k] for k in [j for j, e in enumerate(row) if e == 1]]
            tran_nodes = set(ins + outs)
            x = set(ins).intersection(set(outs))
            # 计算与每个“邻”节点之间的最短路径距离->权重
            ws = []
            for t in tran_nodes:
                if t in x:
                    path1 = self._apg.get_shortest_paths(t, node)[0]
                    path2 = self._apg.get_shortest_paths(node, t)[0]
                    l = min(len(path1), len(path2))
                else:
                    if t in ins:
                        path = self._apg.get_shortest_paths(t, node)[0]
                    else:
                        path = self._apg.get_shortest_paths(node, t)[0]
                    l = len(path)
                w = 0
                if l != 1:
                    w = 1 / math.pow((l - 1), self._z)
                ws.append(w)
            # 计算aggregated异常分数：
            s = self.__aggregation(ws, tran_nodes, node_anoScores, self._p)
            all_s.append(s)

        # 计算每个节点的异常等级：
        rs = []
        for i, node in enumerate(self._nodes):
            s = all_s[i]
            # 计算in节点集合的集合异常分数：
            col = mtx[:, i]
            ins = [self._nodes[k] for k in [j for j, e in enumerate(col) if e == 1]]
            in_ws = []
            for i_node in ins:
                path = self._apg.get_shortest_paths(i_node, node)[0]
                w = 0
                if len(path) != 1:
                    w = 1 / math.pow((len(path) - 1), self._z)
                in_ws.append(w)
            s_in = self.__aggregation(in_ws, ins, node_anoScores, 1)
            # 计算out节点集合中的集合异常分数最大值：
            row = mtx[i, :]
            outs = [j for j, e in enumerate(row) if e == 1]
            all_s_out = [all_s[k] for k in outs]
            s_out = max(all_s_out)
            # 计算异常等级：
            if s_in > s and s_out <= s:
                r = 0.5 * (s + 1)
            elif s_in <= s and s_out > s:
                r = 0.5 * (s - 1)
            else:
                r = s
            rs.append(r)

        # 根据异常等级排序输出根因列表：
        nodes_tbac = dict(zip(self._nodes, rs))
        self.root_cause_list = sorted(nodes_tbac.items(), key=lambda x: x[1], reverse=True)

    def __adj_matrix(self):
        self._apg.write_adjacency(f='am.txt')  # 邻接矩阵
        A = np.zeros((self._n, self._n), dtype=float)
        f = open('am.txt')
        lines = f.readlines()
        A_row = 0
        for line in lines:
            list = line.strip('\n').split(' ')
            A[A_row:] = list
            A_row += 1
        return A

    def __warshall(self, A):
        for i in range(0, self._n):
            for j in range(0, self._n):
                if A[j, i]:
                    for k in range(0, self._n):
                        A[j, k] = (A[j, k] or A[i, k])

    def __gama(self, a, q):
        t = math.pow(abs(a), q)
        if a < 0:
            t = t * (-1)
        return t

    def __aggregation(self, ws, tran_nodes, node_anoScores, p):
        sum_w = sum(ws)
        sum_2 = 0
        for i, t in enumerate(tran_nodes):
            s = node_anoScores.get(t)
            sum_2 += ws[i] * self.__gama(s, p)
        S = self.__gama(sum_2 / sum_w, 1 / p)
        return S

    def save(self, directory='.'):
        """保存根因列表（节点，分数/概率）"""
        s = '-' + str(self._walkers) if self._approach == 'random_walk' else ''
        model_id = self._approach + '-' + str(self._rou) + s
        path = os.path.join(directory, model_id)
        if not os.path.isdir(path):
            os.makedirs(path)
        files = os.listdir(path)
        # try to keep the newest 2 model files
        if len(files) > 0:
            os.remove(os.path.join(path, min(files)))

        t = str(pd.Timestamp('now').strftime('%Y%m%d_%H%M%S'))
        full_path1 = os.path.join(directory, model_id, t + '.csv')
        pd.DataFrame(self.root_cause_list, columns=['root_cause', 'score']).to_csv(full_path1)
        full_path2 = os.path.join(directory, model_id, t + '_rt.txt')
        with open(full_path2, "w") as f:
            f.write(str(self._runtime))
