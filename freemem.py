import ConfigParser
import subprocess
import shlex
import time

def metric_init(params):
  global descriptors

  d1 = {'name': 'freemem',
        'call_back': freemem_handler,
        'time_max': 90,
        'value_type': 'uint',
        'units': 'MiB',
        'slope': 'both',
        'format': '%u',
        'description': 'Free memory',
        'groups': 'health'}

  descriptors = [d1]

  return descriptors

def metric_cleanup():
    pass

def freemem_handler(name):
  process = subprocess.Popen(shlex.split("free -m"), stdout=subprocess.PIPE)
  results, err = process.communicate()

  memline = results.split('\n')[2].split()

  return int(memline[3])


#This code is for debugging and unit testing
if __name__ == '__main__':
    metric_init({})
    for d in descriptors:
        time.sleep(5)
        v = d['call_back'](d['name'])
        print 'value for %s is %u' % (d['name'],  v)
    metric_cleanup()


