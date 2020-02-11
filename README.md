# root-cause-analysis_APG

With the development of Internet technology, IT systems are getting more and more complex, in which there are two main relationships among system components: service call relationship and deployment configuration relationship. Once a local anomaly occurs in the system, it tends to spread, triggering emergent and dense concurrent alarms. Hence, it is important to quickly and precisely locate the root cause of concurrent alarms. In this paper, we first construct an anomaly propagation graph using collected system data. Then, based on the graph, we propose two optional algorithms: random walk and state iteration, to track anomaly propagation process and locate the root cause. Simulation experiments demonstrate that our proposed method can localize root causes correctly and rapidly for scenarios with complex call chains and resource competition, and is robust to alarm error. The proposed method pays more attention to system characteristics and depends little on experience knowledge of IT operators.

Initial Requirements:

You need to manually install the following:

(1) Python 3.6

The python modules you need to install and import are:

(2) igraph

(3) numpy

(4) pandas

(5) os

The encoding unicode is: (6) UTF-8.

Description of Code Files：

(1) demo.py: to input scenario data, select an algorithm and specify parameters.

(2) root_cause.py: implementation of two algorithms, and output a list of root causes.

