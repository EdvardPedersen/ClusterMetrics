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

Extras
=========
iostat_script.py and iowait.pyconf are scripts to add iostat information to ganglia

TODO
===========
* Implement output in different formats
* Integrate with ganglia XML output to enhance parsing

