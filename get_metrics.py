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
    print self.command_string
    self.host_process = subprocess.Popen( shlex.split(self.command_string) ,stdout=subprocess.PIPE)

  def get_data(self):
    hosts, herr = self.host_process.communicate()
    self.resultstring = str(hosts)
#    print self.resultstring
    splitLines = self.resultstring.split("\n")
    #print splitLines
    for line in splitLines:
      #print line
      if len(line.strip()) < 1:
        continue
      splitString = line.split(" ",1)
      if len(splitString) != 2:
        print("Was not able to split: " + line)
        continue
      self.datapoints.append(DataPoint(host=self.host, metric=self.metric, time=splitString[0], value=splitString[1]))
      #print splitString[0]

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

def add_metric(metric_name, command_queue):
  command_queue[metric_name] = ("rrdtool fetch /var/lib/ganglia/rrds/ice2/compute-0-0.local/cpu_idle.rrd AVERAGE -s end-2d -e now")
  
def execute(command_queue, timeFile, version):
  totalTimeStart = time.time()
  for line in command_queue:
    print "Executing command: " + line
    startTime = time.time()
    if (call(line, shell=True) != 0):
      print "Line " + line + " crashed, aborting..."
      exit(1)
    else:
      elapsedTime = time.time() - startTime
      print "Completed in " + str(elapsedTime) + " seconds."
      timeFile.write(version + " \nLine: " + line + " \nTime: " + str(elapsedTime) +"\n")
      timeFile.flush()
      os.fsync(timeFile)
    totalTimeEnd = time.time()
    timeFile.write(version + " total " + str(totalTimeEnd-totalTimeStart) + "\n\n\n")
    timeFile.flush()
    os.fsync(timeFile)

if __name__ == "__main__":
    main(sys.argv[1:])
    #cProfile.run('main(sys.argv[1:])', 'profileData')
