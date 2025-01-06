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
from os.path import expanduser
from lxml import html, etree
import pypandoc
import subprocess
import datetime

class report_config():
  path : str
  reportpath : str
  applicant: str
  def __init__(self, path:str=None, reportpath:str=None, applicant:str=None):
    self.path = path
    self.reportpath = reportpath
    self.applicant = applicant

class report():
  def __init__(self, debug:bool=False):
    reportconfig = open(expanduser("~/.josea/reportconfig.json"),"r")
    self.config = jsonpickle.decode(reportconfig.read())
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
    jsonld = db.jsonld(jobid)
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

    if "url" in jobdata:
      rst_description += self.title("Link von Stellenbörse",1)
      rst_description += "\n" + jobdata['url'] + "\n\n"

    job_positive_tags = []
    job_negative_tags = []
    rst_description += self.title("Automatisierte Bewertung",1)
    if "datePosted" in jobdata:
      rst_description += ":Veröffentlichungsdatum:\n "+jobdata['datePosted']+"\n\n"
    distance_json = db.get_evaldata(jobid,"distance_car_km")
    if distance_json:
      rst_description += ":Fahrtdistanz:\n  "+str(json.loads(distance_json[0]))+"km\n\n"
    time_json = db.get_evaldata(jobid,"distance_car_minutes")
    if time_json:
      rst_description += ":Fahrtzeit:\n  "+str(json.loads(time_json[0]))+"min\n\n"
    job_score = db.get_evaldata(jobid,"knowhow_score")
    if job_score:
      rst_description += ":Kenntnisse:\n  "+str(json.loads(job_score[0]))+"\n\n"
    job_positive_tags_json_string = db.get_evaldata(jobid, "knowhow_positive")
    if job_positive_tags_json_string:
      job_positive_tags = json.loads(job_positive_tags_json_string[0])
      if job_positive_tags:
        rst_description += ":Positiv:\n"
        for positive_tag in job_positive_tags:
          rst_description += "  "+positive_tag+"\n"
        rst_description += "\n"
    job_negative_tags_json_string = db.get_evaldata(jobid, "knowhow_negative")
    if job_negative_tags_json_string:
      job_negative_tags = json.loads(job_negative_tags_json_string[0])
      if job_negative_tags:
        rst_description += ":Negativ:\n"
        for negative_tag in job_negative_tags:
          rst_description += "  "+negative_tag+"\n"
        rst_description += "\n"
    notes = db.get_notes(jobid)
    if notes:
        rst_description += self.title("Eigene Notizen",1)
        for note in notes:
          rst_description += ":"+note[0]+":\n"
          rst_description += " "+note[1]+"\n\n"
    rst_description += self.title("Veröffentlichte Beschreibung",1)
    rst_description += pypandoc.convert_text(etree.tostring(xml_description),'rst', format='html')
    rst_description += "\n"
    rst_description += self.title("JSON-LD (ohne description)",1)
    rst_description += ".. code-block:: javascript\n\n   "
    json_short = jobdata
    json_short.pop('description')
    if "original" in json_short:
      if "jobdetail" in json_short["original"]:
        if "stellenangebotsBeschreibung" in json_short["original"]["jobdetail"]:
          json_short["original"]["jobdetail"].pop("stellenangebotsBeschreibung")
    rst_description += "   ".join(json.dumps(json_short, indent=4).splitlines(True))
    rst_description += "\n\n"
    stellenfilename = expanduser(self.config.path)+"/Stelle"+job_company_filename+'_' + job_title_filename + ".pdf"
    try:
      with open(stellenfilename, "wb") as stellenfile:
        m4process = subprocess.run(["rst2pdf","-s","/home/flo/bin/json2stelle.yaml"], input=rst_description.encode("utf8"), stdout=stellenfile)
    except subprocess.CalledProcessError as error:
      print("Could not execute rst2pdf!")
      return False
    return True
  def view(self,jobid:int):
    db = josea.dbop.db()
    jsonld = db.jsonld(jobid)
    jobdata = json.loads(jsonld)
    xml_description = html.fromstring(jobdata['description'])
    job_company_filename = ''.join(x for x in jobdata['hiringOrganization']['name'].title() if not x.isspace() and x.isalpha())
    job_title_filename =  ''.join(x for x in jobdata['title'].title() if not x.isspace() and x.isalpha())
    stellenfilename = expanduser(self.config.path)+"/Stelle"+job_company_filename+'_' + job_title_filename + ".pdf"
    try:
      subprocess.run(["evince",stellenfilename])
    except subprocess.CalledProcessError as error:
      return False
    return True
  def weekly(self):
    today = datetime.datetime.today()
    cal = today.isocalendar()
    year = cal.year
    if(cal.weekday == 7):
      week = cal.week
      firstweekday = today - datetime.timedelta(days=cal.weekday-1)
      firstweekday = datetime.datetime.combine(firstweekday,datetime.time.min)
      lastweekday = firstweekday + datetime.timedelta(days=6)
    else:
      week = cal.week - 1
      firstweekday = today - datetime.timedelta(days=cal.weekday-1+7)
      firstweekday = datetime.datetime.combine(firstweekday,datetime.time.min)
      lastweekday = firstweekday + datetime.timedelta(days=6)
      lastweekday = datetime.datetime.combine(lastweekday,datetime.time.max)
      if(week<1):
        week = 1
    rst_description = self.title('Bewerbungen ' + self.config.applicant + ' KW ' + str(week) + ' / ' + str(year))
    db = josea.dbop.db()
    stati = db.get_stati_for_daterange(firstweekday,lastweekday)
    statidescriptions = dict()

    rst_applications = self.title('Bewerbungen',1)
    rst_applications += '.. csv-table::\n   :header: "Firma", "Ort", "Jobbeschreibung", "Beworben am"\n\n '
    rst_discarded = self.title('Verworfene Stellenausschreibungen',1)
    rst_discarded += '.. csv-table::\n   :header: "Firma", "Ort", "Jobbeschreibung", "Verworfen am", "Notizen"\n\n '
    last_application = 0
    for status in stati:
      jobid = status[0]
      statusid = status[1]
      time = datetime.datetime.strptime(status[2],"%Y-%m-%d %H:%M:%S")
      if not (statusid in statidescriptions):
        statidescriptions[statusid] = db.get_status_name(statusid)[0]
      jsonld = db.jsonld(jobid)
      jobdata = json.loads(jsonld)
      if statidescriptions[statusid] == 'applied':
        if jobid != last_application:
          rst_applications += '   "' + jobdata['hiringOrganization']['name'] + '", "' +jobdata['jobLocation']['address']['addressLocality'] + '", "' + jobdata['title'] + '", "' + time.strftime('%d.%m.%Y %H:%M') + '"\n'
          last_application = jobid
      elif statidescriptions[statusid] == 'discarded':
          notes = db.get_notes(jobid)
          discarded_notes = ''
          if notes:
            for note in notes:
              discarded_notes += note[1]+ ", "
            discarded_notes = discarded_notes[:-2]
          rst_discarded += '   "' + jobdata['hiringOrganization']['name'] + '", "' +jobdata['jobLocation']['address']['addressLocality'] + '", "' + jobdata['title'] + '", "' + time.strftime('%d.%m.%Y') + '", "' + discarded_notes + '"\n'
      else:
        pass
        #print(jobdata['hiringOrganization']['name'],jobdata['title'],statidescriptions[statusid],status[2])
    rst_description += rst_applications + "\n"
    rst_description += rst_discarded + "\n"
    weeklyreportfilename = expanduser(self.config.reportpath)+"/Bewerbungen_" +self.config.applicant.replace(" ","_") + "_KW"+str(week).zfill(2) + "_" + str(year) + ".pdf"
    try:
      with open(weeklyreportfilename, "wb") as weeklyreportfile:
        m4process = subprocess.run(["rst2pdf","-s","/home/flo/bin/json2stelle.yaml"], input=rst_description.encode("utf8"), stdout=weeklyreportfile)
    except subprocess.CalledProcessError as error:
      print("Could not execute rst2pdf!")
      return False
    return True

  def view_weekly(self):
    today = datetime.datetime.today()
    cal = today.isocalendar()
    year = cal.year
    if(cal.weekday == 7):
      week = cal.week
      firstweekday = today - datetime.timedelta(days=cal.weekday-1)
      firstweekday = datetime.datetime.combine(firstweekday,datetime.time.min)
      lastweekday = firstweekday + datetime.timedelta(days=6)
    else:
      week = cal.week - 1
      firstweekday = today - datetime.timedelta(days=cal.weekday-1+7)
      firstweekday = datetime.datetime.combine(firstweekday,datetime.time.min)
      lastweekday = firstweekday + datetime.timedelta(days=6)
      lastweekday = datetime.datetime.combine(lastweekday,datetime.time.max)
      if(week<1):
        week = 1
    weeklyreportfilename = expanduser(self.config.reportpath)+"/Bewerbungen_" +self.config.applicant.replace(" ","_") + "_KW"+str(week).zfill(2) + "_" + str(year) + ".pdf"
    try:
      subprocess.run(["evince",weeklyreportfilename])
    except subprocess.CalledProcessError as error:
      return False
    return True
