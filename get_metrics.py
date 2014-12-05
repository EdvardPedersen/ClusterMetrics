#!/usr/bin/python
import sys
import time
import os
import ConfigParser
from collections import deque
import subprocess
import shlex

class Metric:
  def __init__(self, name=""):
    self.name = name
    self.start = "0"
    self.stop = "now"

class Host:
  def __init__(self,name=""):
    self.name = name

class DataPoint:
  def __init__(self, host=None, metric=None, time="0", value="0"):
    self.host = host
    self.metric = metric
    self.time = time
    self.value = value

class Process:
  def __init__(self, host=None, metric=None, rootrrd=""):
    self.host=host
    self.metric=metric
    self.datapoints = list()
    self.command_string = "rrdtool fetch " + rootrrd + host.name + "/" + metric + ".rrd AVERAGE -e now -s end-60s"
    self.host_process = subprocess.Popen( shlex.split(self.command_string) ,stdout=subprocess.PIPE)

  def get_data(self):
    hosts, herr = self.host_process.communicate()
    self.resultstring = str(hosts)
    splitLines = self.resultstring.split("\n")
    for line in splitLines:
      if len(line.strip()) < 1:
        continue
      splitString = line.split(" ",1)
      if len(splitString) != 2:
        print("Was not able to split: " + line)
        continue
      self.datapoints.append(DataPoint(host=self.host, metric=self.metric, time=splitString[0], value=splitString[1]))

  def print_data(self):
    for point in self.datapoints:
      print point.host.name.strip() + " | " + point.metric.strip() + " | " + point.time.strip() + " | " + point.value.strip()

def main(args):
  timeFile = open('time_data', 'w')

  config = ConfigParser.ConfigParser()
  config.read("default.conf")
  hosts = dict()
  metrics = list()

  for item, value in config.items("Hosts"):
    hosts[item] = Host(value + ".local")

  for item,value in config.items("Metrics"):
    metrics.append(value)

  rootrrdpath = config.get("Paths", "root_rrd")

  processes = list()

  command_queue = dict()

  for host in hosts.keys():
    for metric in metrics:
      processes.append(Process(host=hosts[host], metric=metric, rootrrd=rootrrdpath))

  for process in processes:
    process.get_data()
    process.print_data()

if __name__ == "__main__":
    main(sys.argv[1:])
    #cProfile.run('main(sys.argv[1:])', 'profileData')
