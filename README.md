# root-cause-analysis_APG

With development of Internet technology, IT systems are becoming more and more complex, in which there are two main relationships among system components: service call relationship, and deployment configuration relationship. Once anomalies occur in some local system components, it is easy to spread, leading to a large number of concurrent alarms. Hence, it is important to quickly and precisely locate root causes. In this paper, for root cause analysis of concurrent alarms in IT systems, based on collected configuration information, metrics data, alarm data, etc., we first construct an anomaly propagation graph, and then propose two optional sub-algorithms: random walk and state iteration, to simulate and track anomaly propagation process. Simulation experiments demonstrate high effectiveness and efficiency of our method, which also supports root cause localization with multiple call chains, and is robust to alarms with false positives and false negatives. The proposed method pays more attention to system characteristics and have low dependence on experience knowledge of IT operators.

Initial Requirements:

You need to manually install the following:

(1) Python 3.6

The python modules you need to install and import are:

(2) igraph

(3) numpy

(4) pandas

(5) os

The encoding unicode is: (6) UTF-8.

Description of code files：

(7) demo.py: to input scenario data, select an algorithm and specify parameters.

(8) root_cause.py: implementation of two algorithms, and output a list of root causes.

