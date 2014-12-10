import ConfigParser
import subprocess
import shlex
from Queue import Queue, Empty
from threading import Thread
import time

class iostat_output:
  def __init__(self, prev_object=None):
    self.cpulines = list()
    self.devlines = list()
    self.fslines = list()
    self.mode = 0
    self.prevInstances = 0
    self.prevVal = dict()
    self.vals = dict()
    if(prev_object):
      self.prevInstances = prev_object.prevInstances + 1
      for item in prev_object.prevVal.keys():
        self.vals[item] = prev_object.prevVal[item]

  def get_metric(self, name):
    return self.vals[name] / self.prevInstances

  def get_metrics(self):
    self._get_iowait()
    self._get_diskread()
    self._get_diskwrite()

  def _get_iowait(self):
    for line in self.cpulines:
      linesplit = line.split()
      if len(linesplit) > 3:
        if not self.vals.has_key("iowait"):
          self.vals['iowait'] = 0.0
        self.vals["iowait"] += float(linesplit[3].strip())

  def _get_diskread(self):
    for line in self.devlines:
      linesplit = line.split()
      if len(linesplit) > 5:
        if not self.vals.has_key('diskread'):
          self.vals['diskread'] = 0.0
        self.vals['diskread'] += float(linesplit[5].strip())

  def _get_diskwrite(self):
    for line in self.devlines:
      linesplit = line.split()
      if len(linesplit) > 6:
        if not self.vals.has_key('diskwrite'):
          self.vals['diskwrite'] = 0.0
        self.vals['diskwrite'] += float(linesplit[6].strip())

  def add_line(self, line):
    if line.startswith('avg-cpu'):
      if(self.mode > 1):
        return False
      self.mode = 1 
    elif line.startswith('Device'):
      self.mode = 2
    elif line.startswith('Filesystem'):
      self.mode = 3
    elif self.mode == 1:
      self.cpulines.append(line)
    elif self.mode == 2:
      self.devlines.append(line)
    elif self.mode == 3:
      self.fslines.append(line)
    return True

def queue_host(input, queue):
  for line in iter(input.readline, b''):
    queue.put(line)

def metric_init(params):
  global host_queue, descriptors, current_object, host_process

  d1 = {'name': 'iowait',
        'call_back': iowait_handler,
        'time_max': 90,
        'value_type': 'float',
        'units': '%',
        'slope': 'both',
        'format': '%f',
        'description': 'IOwait',
        'groups': 'health'}

  d2 = {'name': 'diskread',
        'call_back': iowait_handler,
        'time_max': 90,
        'value_type': 'float',
        'units': 'MiB/s',
        'slope': 'both',
        'format': '%f',
        'description': 'MiB read per second',
        'groups': 'health'}

  d3 = {'name': 'diskwrite',
        'call_back': iowait_handler,
        'time_max': 90,
        'value_type': 'float',
        'units': 'MiB/s',
        'slope': 'both',
        'format': '%f',
        'description': 'MiB write per second',
        'groups': 'health'}

  descriptors = [d1,d2,d3]

  host_process = subprocess.Popen(shlex.split("iostat -x -m -d -c -n 1"), stdout=subprocess.PIPE)
  host_queue = Queue()
  host_thread = Thread(target=queue_host, args=(host_process.stdout, host_queue))
  host_thread.daemon = True
  host_thread.start()

  current_object = iostat_output()

  return descriptors

def metric_cleanup():
    '''Clean up the metric module.'''
    host_process.terminate()
    host_process.kill()
    pass

def iowait_handler(name):
  global current_object
  still_data = True
  num_entries = 0
  current_data = 0.0
  while still_data:
    try:
      current_line = host_queue.get_nowait()
      if(not current_object.add_line(current_line)):
        current_object.get_metrics()
        current_object = iostat_output(current_object)
      current_object.add_line(current_line)
    except Empty:
      still_data = False
  current_object.get_metrics()
  return float(current_object.get_metric(name))


#This code is for debugging and unit testing
if __name__ == '__main__':
    metric_init({})
    time.sleep(3)
    for d in descriptors:
        v = d['call_back'](d['name'])
        print 'value for %s is %f' % (d['name'],  v)
    metric_cleanup()


