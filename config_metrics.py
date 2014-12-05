import ConfigParser
import subprocess

config = ConfigParser.SafeConfigParser()

host_process = subprocess.Popen('ganglia', stdout=subprocess.PIPE)
hosts, herr = host_process.communicate()
hoststring = str(hosts)

config.add_section('Hosts')
hostnum = 1
for host in hoststring.split("\n"):
  if(len(host.strip()) > 1):
    config.set('Hosts', 'host' + str(hostnum), host.strip())
    hostnum += 1

config.add_section('Paths')
config.set('Paths', 'root_rrd', '/var/lib/ganglia/rrds/ice2/')

config.add_section('Metrics')
config.set('Metrics', 'metric1', 'cpu_idle')


with open('default.conf', 'wb') as configf:
  config.write(configf)
