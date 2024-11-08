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
import josea
import json

class report_config():
  path : str
  def __init__(self, path:str=None):
    self.path = path

class report():
  def __init__(self, debug:bool=False):
    reportconfig = open("~/.josea/reportconfig.json","r")
    self.config = jsonpickle.decode(reportconfig)
  def title(self,text,level=0):
    levelchar = dict()
    levelchar[0] = "="
    levelchar[1] = "-"
    levelchar[2] = "."
    titletext = text + "\n"
    titletext += levelchar[level] * len(text) + "\n\n"
    return titletext
  def pdf(self,jobid:int):
    db = josea.dbop.db()
    jsonld = db.jsonld()
    jobdata = json.loads(jsonld)
    xml_description = html.fromstring(jobdata['description'])
    job_company_filename = ''.join(x for x in jobdata['hiringOrganization']['name'].title() if not x.isspace() and x.isalpha())
    job_title_filename =  ''.join(x for x in jobdata['title'].title() if not x.isspace() and x.isalpha())
    rst_description = self.title(jobdata['title'])
    rst_description += ".. contents:: Inhaltsverzeichnis\n   :depth: 4\n\n"
    rst_description += self.title("Kontaktdaten",1)
    rst_description += "| " + jobdata['hiringOrganization']['name'] + "\n"
    if 'streetAddress' in jobdata['jobLocation']['address']:
      rst_description += "| " + jobdata['jobLocation']['address']['streetAddress'] + "\n"
    if 'postalCode' in jobdata['jobLocation']['address']:
      rst_description += "| " + jobdata['jobLocation']['address']['postalCode'] + " " + jobdata['jobLocation']['address']['addressLocality'] + "\n\n"
    else:
      rst_description += "| " + jobdata['jobLocation']['address']['addressLocality'] + "\n\n"

    job_positive_tags = []
    job_negative_tags = []
    rst_description += self.title("Automatisierte Bewertung",1)
    distance_json = db.get_evaldata(jobid,"distance_car_km")
    if distance_json:
      rst_description += ":Fahrtdistanz:\n  "+str(json.loads(distance_json))+"km\n\n"
    time_json = db.get_evaldata(jobid,"distance_car_minutes")
    if time_json:
      rst_description += ":Fahrtzeit:\n  "+str(json.loads(time_json))+"min\n\n"
    job_score = db.get_evaldata(jobid,"knowhow_score")
    if job_score:
      rst_description += ":Kenntnisse:\n  "+str(json.loads(job_score))+"\n\n"
    job_positive_tags_json_string = db.get_evaldata(jobid, "knowhow_positive")
    if job_positive_tags_json_string:
      job_positive_tags = json.loads(job_positive_tags_json_string)
      if job_positive_tags:
        rst_description += ":Positiv:\n"
        for positive_tag in job_positive_tags:
          rst_description += "  "+positive_tag+"\n"
        rst_description += "\n"
    job_negative_tags_json_string = db.get_evaldata(jobid, "knowhow_negative")
    if job_negative_tags_json_string:
      job_negative_tags = json.loads(job_negative_tags_json_string)
      if job_negative_tags:
        rst_description += ":Negativ:\n"
        for negative_tag in job_negative_tags:
          rst_description += "  "+negative_tag+"\n"
        rst_description += "\n"
    rst_description += self.title("Veröffentlichte Beschreibung",1)
    rst_description += pypandoc.convert_text(etree.tostring(xml_description),'rst', format='html')
    rst_description += "\n"
    rst_description += self.title("JSON-LD (ohne description)",1)
    rst_description += ".. code-block:: javascript\n\n   "
    json_short = jobdata
    json_short.pop('description')
    rst_description += "   ".join(json.dumps(json_short, indent=4).splitlines(True))
    rst_description += "\n\n"
    stellenfilename = self.config.path+"/Stelle"+job_company_filename+'_' + job_title_filename + ".pdf"
    try:
      with open(stellenfilename, "wb") as stellenfile:
        m4process = subprocess.run(["rst2pdf","-s","/home/flo/bin/json2stelle.yaml"], input=rst_description.encode("utf8"), stdout=stellenfile)
    except subprocess.CalledProcessError as error:
      print("Could not execute rst2pdf!")
      return False
    return True

