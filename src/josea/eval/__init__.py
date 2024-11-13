# Copyright 2024 Florian Pesth
#
# This file is part of JoSea.
#
# JoSea is free software: you can redistribute it and/or modify it under the terms of the GNU Affero General Public License version 3 as published by the Free Software Foundation.
#
# JoSea is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License version 3 along with JoSea. If not, see <https://www.gnu.org/licenses/>. 

import jsonpickle
import json
import josea
import requests
from lxml import html, etree
from os.path import expanduser

class eval_config():
  knowhow_positive: list[str]
  knowhow_negative: list[str]
  latitude: float
  longitude: float
  graphhopper_url : str
  motis_url: str
  def __init__(self, knowhow_positive=None, knowhow_negative=None, latitude:float=None, longitude:float=None, graphhopper_url:str=None, motis_url:str=None):
    self.knowhow_positive = knowhow_positive
    self.knowhow_negative = knowhow_negative
    self.latitude = latitude
    self.longitude = longitude
    self.graphhopper_url = graphhopper_url
    self.motis_url = motis_url

def filterfunction(character):
  return character.isalnum() or character.isspace() or character == '#' or character == '+'

class eval():
  def __init__(self, debug:bool=False):
    evalconfig = open(expanduser("~/.josea/evalconfig.json"), "r")
    self.config = jsonpickle.decode(evalconfig.read())
  def knowhow(self,jobid:int):
    db = josea.dbop.db()
    jsonld = db.jsonld(jobid)
    jobdata = json.loads(jsonld)
    xml_title = html.fromstring(jobdata['title'])
    jobdata_plain_title = ''.join(filter(filterfunction, xml_title.text_content())).replace("\n"," ").replace("\t"," ")
    jobdatawords = []
    for jobdataword in jobdata_plain_title.split(" "):
      if jobdataword != '':
        if jobdataword != " ":
          jobdatawords.append(jobdataword.strip().lower())
    xml_description = html.fromstring(jobdata['description'])
    jobdata_plain_description = ''.join(filter(filterfunction, xml_description.text_content())).replace("\n"," ").replace("\t"," ")
    for jobdataword in jobdata_plain_description.split(" "):
      if jobdataword != '':
        if jobdataword != " ":
          jobdatawords.append(jobdataword.strip().lower())
    jobdata_plain_description = " " + " ".join(jobdatawords) + " "
    found_positives = []
    found_negatives = []
    for positive in self.config.knowhow_positive:
      positive_plain = ''.join(filter(filterfunction, positive)).lower() 
      if positive_plain in jobdata_plain_description:
        found_positives.append(positive)
    for negative in self.config.knowhow_negative:
      negative_plain = ''.join(filter(filterfunction, negative)).lower() 
      if negative_plain in jobdata_plain_description:
        found_negatives.append(negative)
    tags_sum = (len(found_negatives)+len(found_positives))
    if tags_sum != 0:
      job_score = len(found_positives)/tags_sum
    else:
      job_score = 1
    db.add_evaldata(jobid,"knowhow_score",json.dumps(job_score))
    db.add_evaldata(jobid,"knowhow_positive",json.dumps(found_positives))
    db.add_evaldata(jobid,"knowhow_negative",json.dumps(found_negatives))
  def distance(self,jobid:int):
    db = josea.dbop.db()
    jsonld = db.jsonld(jobid)
    jobdata = json.loads(jsonld)
    if 'jobLocation' in jobdata:
      latitude_from = None
      longitude_from = None
      if 'geo' in jobdata['jobLocation']:
        latitude_from = jobdata['jobLocation']['geo']['latitude']
        longitude_from = jobdata['jobLocation']['geo']['longitude']
      elif 'address' in jobdata['jobLocation']:
        location = ''
        if 'addressLocality' in jobdata['jobLocation']['address']:
          location += jobdata['jobLocation']['address']['addressLocality']
        if 'streetAddress' in jobdata['jobLocation']['address'] and (jobdata['jobLocation']['address']['addressLocality'] != jobdata['jobLocation']['address']['streetAddress']):
          location = jobdata['jobLocation']['address']['streetAddress'] + " " + location
        url = self.config.motis_url
        response = requests.get(url + '/geocode', params={'text': location.split(", ")[0]})
        routingdata = response.json()
        if routing and len(routing) > 0:
          latitude_from = routingdata[0]['lat']
          longitude_from = routingdata[0]['lon']
        else:
          return

      if latitude_from and longitude_from:
        latitude_to = self.config.latitude
        longitude_to = self.config.longitude
        url = self.config.graphhopper_url + '/route'
        reqdata = dict()
        reqdata["points"] = [[longitude_from, latitude_from],
            [longitude_to, latitude_to]
        ]
        reqdata["profile"] = "car"
        response = requests.post(url, json=reqdata)
        routingdata = response.json()
        if (len(routingdata['paths']) == 1):
          distance_km = routingdata['paths'][0]['distance'] / 1000
          time_minutes = routingdata['paths'][0]['time'] / (1000*60)
          db.add_evaldata(jobid,"distance_car_km",json.dumps(distance_km))
          db.add_evaldata(jobid,"distance_car_minutes",json.dumps(time_minutes))
  def all(self,jobid:int):
    self.knowhow(jobid)
    self.distance(jobid)

