import ConfigParser
import subprocess
import shlex
from Queue import Queue, Empty
from threading import Thread
import time

class iostat_output:
  def __init__(self):
    self.cpulines = list()
    self.devlines = list()
    self.fslines = list()
    self.mode = 0

  def get_metric(self, name):
    print self.cpulines
    if name == "iowait":
      for line in self.cpulines:
        linesplit = line.split()
        print line
        if len(linesplit) > 3:
          print linesplit[3]
          return linesplit[3].strip()
      
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

  descriptors = [d1]

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
  while still_data:
    try:
      current_line = host_queue.get_nowait()
      if(not current_object.add_line(current_line)):
        current_object = iostat_output()
      current_object.add_line(current_line)
    except Empty:
      still_data = False

  current_object.get_metric(name)

  return float(current_object.get_metric(name))


#This code is for debugging and unit testing
if __name__ == '__main__':
    metric_init({})
    for d in descriptors:
        time.sleep(5)
        v = d['call_back'](d['name'])
        print 'value for %s is %f' % (d['name'],  v)
    metric_cleanup()


