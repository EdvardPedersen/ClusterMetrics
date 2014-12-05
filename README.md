ClusterMetrics
==============

A simple tool for parsing rrdtool fetch information

Requirements
=============

Python 2.6+
rrdtool

Usage
============
* First run config_metrics.py
* Modify the default.conf file to match your setup, and the metrics you want to use
* Run get_metrics.py

TODO
===========
* Allow user to specify time frame
* Implement output in different formats
* Integrate with ganglia XML output to enhance parsing
