#!/usr/bin/python
import sys
import time
import os
import ConfigParser
from collections import deque
import subprocess
import shlex
import numpy
import logging
import json

egg_path='/home/epe005/gepan_experiments/helper_scripts/ClusterMetrics/testmat/matplotlib-1.4.2/distribute-0.6.28-py2.6.egg'
egg_path2='/home/epe005/gepan_experiments/helper_scripts/ClusterMetrics/testmat/matplotlib-1.4.2/numpy-1.9.1/dist/numpy-1.9.1-py2.6-linux-x86_64.egg'
sys.path.append(egg_path)
sys.path.append(egg_path2)
from matplotlib import pyplot
from matplotlib import dates
from mpl_toolkits.axes_grid1 import host_subplot
import mpl_toolkits.axisartist as AA
from optparse import OptionParser
from dateutil.tz import *
#import numpy

class Group:
  def __init__(self, metrics_hosts=list(), name="group"):
    self.data = metrics_hosts
    self.name=name

  
class Output:
  def __init__(self, format="text", processes=list(), from_file=None):
    self.input = processes
    self.format = format
    self.graphdata = dict()
    self.from_file = from_file

  def generate(self, groups=None):
    if(len(self.graphdata) < 1):
      if(self.from_file == None):
        self.graphdata = self._getgraph()
      else:
        self.import_file(self.from_file)
    if(self.format == "text"):
      self._gettext()
    elif(self.format == "png"):
      if not groups:
        self._showgraph(self.graphdata)
      else:
        self._showgroupgraph(self.graphdata, groups)

  def _gettext(self):
    for entry in self.input:
      for datapoint in entry.datapoints:
        print datapoint.host.name + " " + datapoint.value

  def _getgraph(self):
    metricLists = dict()
    for entry in self.input:
      #Each entry contains datapoints for one metric, for one host
      if(entry.metric.name not in metricLists):
        metricLists[entry.metric.name] = dict()
      if(entry.host.name not in metricLists[entry.metric.name]):
        metricLists[entry.metric.name][entry.host.name] = (list(), list())
      for datapoint in entry.datapoints:
        try:
          metricLists[entry.metric.name][entry.host.name][0].append(dates.epoch2num(int(datapoint.time.strip(':'))))
          metricLists[entry.metric.name][entry.host.name][1].append(float(datapoint.value))
        except Exception:
          logging.info("Ignored datapoint due to exception: " + str(sys.exc_info()))
          continue
#    self._showgraph(metricLists)
    self.metricLists = metricLists
    return metricLists

  def _showgraph(self, metricLists):
    # For every metric
    for key in metricLists.keys():
      fig = pyplot.figure(figsize=(10,5))
      # For every host
      for keyHost in metricLists[key].keys():
        pyplot.plot_date(metricLists[key][keyHost][0], metricLists[key][keyHost][1], '-', label=keyHost, tz=tzlocal())
      pyplot.ylabel("Metric: " + key)
      pyplot.xlabel("Time")
      pyplot.xticks(rotation='vertical')
      fig.autofmt_xdate()
      pyplot.ticklabel_format()
      pyplot.gca().get_xaxis().get_major_formatter().scaled[1/(24.*60.)] = '%H:%M:%S'
      lgd = pyplot.legend(loc='upper right', bbox_to_anchor=(1.6,0.9))
      pyplot.tight_layout()
      pyplot.subplots_adjust(right=0.6)
      pyplot.savefig("figure-" + key + ".png")
      pyplot.close()

  def _showgroupgraph(self, metricLists, group):
    fig = pyplot.figure(figsize=(10,5))
    axis_dict = dict()
    styles = ['--','-.',':','-']
    #host = host_subplot(111, axes_class=AA.Axes)
    for key in metricLists.keys():
      if(key not in group.data):
        logging.warning(key + " is not in group: " + str(group))
        continue
      if key not in axis_dict.keys():
        if len(axis_dict.keys()) < 1:
          pyplot.axes().set_ylabel("Metric: " + key)
          pyplot.axes().set_ybound(lower=0)
          axis_dict[key] = (styles.pop(), pyplot.axes())
        else:
          newax = pyplot.axes().twinx()
          newax.set_frame_on(True)
          newax.patch.set_visible(False)
          newax.set_ylabel("Metric: " + key)
          newax.set_ybound(lower=0)
          axis_dict[key] = (styles.pop(), newax)
      # For every host
      for keyHost in metricLists[key].keys():
        if keyHost not in group.data:
          logging.warning(keyHost + " is not in group")
          continue
        axis_dict[key][1].plot_date(metricLists[key][keyHost][0], metricLists[key][keyHost][1], axis_dict[key][0], label=keyHost + "-" + key, tz=tzlocal())
    if(len(axis_dict) < 1):
      return
    pyplot.xlabel("Time")
    pyplot.xticks(rotation='vertical')
    fig.autofmt_xdate()
    pyplot.ticklabel_format()
    pyplot.gca().get_xaxis().get_major_formatter().scaled[1/(24.*60.)] = '%H:%M:%S'
   
    legendLines = list()
    legendLabels = list()
    for legends in axis_dict.keys():
      tempLines, tempLabels = axis_dict[legends][1].get_legend_handles_labels()
      legendLines += tempLines
      legendLabels += tempLabels

    lgd = pyplot.legend(legendLines, legendLabels,loc='upper left', bbox_to_anchor=(1.2,0.9))
    pyplot.tight_layout()
    pyplot.subplots_adjust(right=0.6)
    pyplot.savefig("figure-"+ group.name +".png", bbox_extra_artists=[lgd], bbox_inches='tight')
    pyplot.close()

  def export_file(self, file):
    f = open(file, 'w')
    json.dump(self.graphdata, f)
    f.close()

  def import_file(self, file):
    f = open(file, 'r')
    self.graphdata = json.load(f)
    f.close()
      

class Metric:
  def __init__(self, name="", start="end-6000s", end="now"):
    self.name = name
    self.start = start
    self.stop = end

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
    self.command_string = "rrdtool fetch " + rootrrd + host.name + "/" + metric.name + ".rrd AVERAGE -e " + metric.stop + " -s " + metric.start
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
        logging.warning("Was not able to split: " + line)
        continue
      self.datapoints.append(DataPoint(host=self.host, metric=self.metric, time=splitString[0], value=splitString[1]))

  def print_data(self):
    for point in self.datapoints:
      print point.host.name.strip() + " | " + point.metric.strip() + " | " + point.time.strip() + " | " + point.value.strip()

  def get_graph_list(metrics, hosts):
    result = list()
    for point in self.datapoints:
      if point.metric.name in metrics:
        if point.host.name in hosts:
          result.append((point.time, point.value, point.host.name))
    return result

def main(args):
  parser = OptionParser()
  parser.add_option("-s", "--start", dest="start_time", default="now-1d", help="Start time for graph")
  parser.add_option("-e", "--end", dest="end_time", default="now", help="End time for graph")
  parser.add_option("-c", "--config", dest="config_file", default="default.conf", help="Configuration file")
  parser.add_option("-i", "--input", dest="input_file", help="Input file from previous run")
  parser.add_option("-o", "--output", dest="output_file", help="Output file for raw data (to re-analyze later)")

  (options,args) = parser.parse_args()

  timeFile = open('time_data', 'w')

  config = ConfigParser.SafeConfigParser()
  config.read(options.config_file)
  hosts = dict()
  metrics = list()
  groups = list()

  for item, value in config.items("Hosts"):
    hosts[item] = Host(value)

  for item,value in config.items("Metrics"):
    metrics.append(Metric(value, start=options.start_time, end=options.end_time))

  for item,value in config.items("Groups"):
    groups.append(Group(value.split(), item))

  rootrrdpath = config.get("Paths", "root_rrd")

  processes = list()

  command_queue = dict()
  if(not options.input_file):
    for host in hosts.keys():
      for metric in metrics:
        processes.append(Process(host=hosts[host], metric=metric, rootrrd=rootrrdpath))

    for process in processes:
      process.get_data()

  output = Output("png", processes, from_file=options.input_file)
  #output.generate()
  for group in groups:
    print str(group)
    output.generate(group)
  if(options.output_file):
    output.export_file(options.output_file)

if __name__ == "__main__":
    main(sys.argv[1:])
    #cProfile.run('main(sys.argv[1:])', 'profileData')
