#!/usr/bin/env python
#
#       PyEWPlot_Client.py
#       
#       Copyright 2019 Francisco Hernandez <FJHernandez89@gmail.com>
#       
#       This program is free software; you can redistribute it and/or modify
#       it under the terms of the GNU General Public License as published by
#       the Free Software Foundation; either version 2 of the License, or
#       (at your option) any later version.
#       
#       This program is distributed in the hope that it will be useful,
#       but WITHOUT ANY WARRANTY; without even the implied warranty of
#       MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#       GNU General Public License for more details.
#       
#       You should have received a copy of the GNU General Public License
#       along with this program; if not, write to the Free Software
#       Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston,
#       MA 02110-1301, USA.
#       
#       
import configparser, argparse, json, urllib.request, requests
from flask import Flask, render_template, Response, stream_with_context

DEBUG = False

# Lets get the parameter file
Config = configparser.ConfigParser()
parser = argparse.ArgumentParser(description='This is a Flask client for PyEWPlot')
parser.add_argument('-f', action="store", dest="ConfFile",   default="EWPlot.conf", type=str)
results = parser.parse_args()

Config.read(results.ConfFile)

Servers = json.loads(Config.get("PlotServers","ip"))
port = Config.get("PlotServers","port")

Channels = {}
for server in Servers:
  url = 'http://' + server + ':' + port + '/menu/'
  if DEBUG:
    print(url)
  with urllib.request.urlopen(url) as myurl:
    data = json.loads(myurl.read().decode())
    if DEBUG:
      print(server,data)
    for chan in data:
      feed_url = 'http://' + server + ':' + port + '/graph_feed/' + chan
      Channels[chan] = feed_url

if DEBUG:
  print(Channels)
  print(Channels.keys())


# Start the web server
app = Flask(__name__,static_url_path = "/tmp", static_folder = "tmp")

@app.route('/')
def index():
  stations = list(Channels.keys())
  stations.sort()
  individualsta = []
  for station in stations:
    thissta = station.split('.')[0]
    individualsta.append(thissta)
  matching = set(individualsta)
  matching = sorted(matching)
  return render_template('index.html', results=stations, results2 = matching)
  
# Station Graph stream page
@app.route('/Station/<Stat>')
def STAgraph(Stat):
  stations = list(Channels.keys())
  stations.sort()
  matching = [s for s in stations if Stat in s]
  matching.sort()
  if not matching:
    Status = "Incorrect Station or Station not ready"
    exts = False
  else:
    Status = "Graphs for Station: " + Stat
    exts = True
  return render_template('station.html', exist = exts, value=Status, stations=matching)

# SCNL Graph stream page
@app.route('/SCNL/<Stat>')
def SCNLgraph(Stat):
  stations = list(Channels.keys())
  if Stat in stations:
    Status = "Graph for Station/Component: " + Stat
    exts = True
  else: 
    Status = "Incorrect Station or Station not ready"
    exts = False
  return render_template('graph.html', exist = exts, value=Status, station=Stat)

# SCNL Graph stream page
@app.route('/stream/<Stat>')
def graph_feed(Stat):
  stations = list(Channels.keys())
  if Stat in stations:
    Status = "Graph for Station/Component: " + Stat
    req = requests.get(Channels[Stat], stream = True)
    exts = True
    return Response(stream_with_context(req.iter_content()), content_type = req.headers['content-type'])
  else: 
    Status = "Incorrect Station or Station not ready"
    exts = False
    return Response("Error", mimetype='text/html', status=500)

# Main program start
if __name__ == '__main__':
  try:
    app.run(host=Config.get('Server','IP'), port=Config.get('Server','PORT'), debug=DEBUG)
  except KeyboardInterrupt:
    print("\nSTATUS: Stopping, you hit ctl+C. ")
