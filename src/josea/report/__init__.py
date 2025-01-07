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
  def weekly(self, firstday:str=None):
    if not firstday:
      today = datetime.datetime.today()
    else:
      today = datetime.datetime.strptime(firstday,"%Y-%m-%d")
    cal = today.isocalendar()
    year = cal.year
    if(cal.weekday == 7):
      week = cal.week
      firstweekday = today - datetime.timedelta(days=cal.weekday-1)
      firstweekday = datetime.datetime.combine(firstweekday,datetime.time.min)
      lastweekday = firstweekday + datetime.timedelta(days=6)
      lastweekday = datetime.datetime.combine(lastweekday,datetime.time.max)
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
    rst_rejected = self.title('Abgelehnt',1)
    rst_rejected += '.. csv-table::\n   :header: "Firma", "Ort", "Jobbeschreibung", "Abgelehnt am"\n\n '
    last_application = 0
    for status in stati:
      jobid = status[0]
      if not jobid:
        continue
      statusid = status[1]
      time = datetime.datetime.strptime(status[2],"%Y-%m-%d %H:%M:%S")
      if not (statusid in statidescriptions):
        statidescriptions[statusid] = db.get_status_name(statusid)[0]
      jsonld = db.jsonld(jobid)
      jobdata = json.loads(jsonld)
      statustext = statidescriptions[statusid]
      if statustext == 'applied' or statustext == 'waitforanswer' or statustext == 'noanswer' or statustext == 'applicationsend':
        if jobid != last_application:
          rst_applications += '   "' + jobdata['hiringOrganization']['name'] + '", "' +jobdata['jobLocation']['address']['addressLocality'] + '", "' + jobdata['title'] + '", "' + time.strftime('%d.%m.%Y %H:%M') + '"\n'
          last_application = jobid
      elif statustext == 'discarded':
          notes = db.get_notes(jobid)
          discarded_notes = ''
          if notes:
            for note in notes:
              discarded_notes += note[1]+ ", "
            discarded_notes = discarded_notes[:-2]
          company_name = '?'
          if 'hiringOrganization' in jobdata:
            if 'name' in jobdata['hiringOrganization']:
              company_name = jobdata['hiringOrganization']['name']
          job_location = '?'
          if 'jobLocation' in jobdata:
            if 'address' in jobdata['jobLocation']:
              if 'addressLocality' in jobdata['jobLocation']['address']:
                job_location = jobdata['jobLocation']['address']['addressLocality']
          job_title = '?'
          if 'title' in jobdata:
            job_title = jobdata['title']
          #rst_discarded += '   "' + company_name + ' (' + str(jobid)+ ')", "' + job_location + '", "' + job_title + '", "' + time.strftime('%d.%m.%Y') + '", "' + discarded_notes + '"\n'
          rst_discarded += '   "' + company_name + '", "' + job_location + '", "' + job_title + '", "' + time.strftime('%d.%m.%Y') + '", "' + discarded_notes + '"\n'
      elif statustext == 'rejected':
          rst_rejected += '   "' + jobdata['hiringOrganization']['name'] + '", "' +jobdata['jobLocation']['address']['addressLocality'] + '", "' + jobdata['title'] + '", "' + time.strftime('%d.%m.%Y') + '"\n'
      else:
        pass
        #print(jobdata['hiringOrganization']['name'],jobdata['title'],statidescriptions[statusid],status[2])
    rst_description += rst_applications + "\n"
    rst_description += rst_discarded + "\n"
    rst_description += rst_rejected + "\n"
    weeklyreportfilename = expanduser(self.config.reportpath)+"/Bewerbungen_" +self.config.applicant.replace(" ","_") + "_KW"+str(week).zfill(2) + "_" + str(year) + ".pdf"
    try:
      with open(weeklyreportfilename, "wb") as weeklyreportfile:
        m4process = subprocess.run(["rst2pdf","-s","/home/flo/bin/json2stelle.yaml"], input=rst_description.encode("utf8"), stdout=weeklyreportfile)
    except subprocess.CalledProcessError as error:
      print("Could not execute rst2pdf!")
      return False
    return True
  def view_weekly(self,firstday=None):
    if not firstday:
      today = datetime.datetime.today()
    else:
      today = datetime.datetime.strptime(firstday,"%Y-%m-%d")
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
  def open_appliations(self):
    rst_description = self.title('Offene Bewerbungen ' + self.config.applicant)
    db = josea.dbop.db()
    stati = db.get_last_stati()
    statidescriptions = dict()

    rst_applications = self.title('Offen',1)
    rst_applications += '.. csv-table::\n   :header: "DB id", "Firma", "Jobbeschreibung", "Status"\n   :widths: 10, 30, 30, 30\n\n '
    rst_rejected = self.title('Abgelehnt',1)
    rst_rejected += '.. csv-table::\n   :header: "DB id", "Firma", "Ort", "Jobbeschreibung", "Status"\n\n '
    for status in stati:
      jobid = status[1]
      if not jobid:
        continue
      statusid = status[2]
      time = datetime.datetime.strptime(status[3],"%Y-%m-%d %H:%M:%S")
      if not (statusid in statidescriptions):
        statidescriptions[statusid] = db.get_status_name(statusid)[0]
      jsonld = db.jsonld(jobid)
      jobdata = json.loads(jsonld)
      notes = db.get_notes(jobid)
      rst_notes = ''
      if notes:
          for note in notes:
            rst_notes += "| " + note[0] + "\n   | " + note[1] + "\n   "
      rst_notes += "\n   "
      statustext = statidescriptions[statusid]
      match statustext:
        case 'applied':
          statusinfo = 'Bewerbung wird gerade vorbereitet'
        case 'applicationsend':
          statusinfo = 'Bewerbung wurde verschickt, noch keine Eingangsbestätigung!'
        case 'waitforanswer':
          statusinfo = 'Eingangsbestätigung erhalten, warte auf Entscheidung'
        case 'rejected':
          statusinfo = 'Bewerbung abgelehnt'
        case _:
          statusinfo = statustext
      if statustext == 'applied' or statustext == 'waitforanswer' or statustext == 'noanswer' or statustext == 'applicationsend':
        rst_applications += '   "' + str(jobid) + '", "' + jobdata['hiringOrganization']['name'] + ' (' +jobdata['jobLocation']['address']['addressLocality'] + ')", "' + jobdata['title'] + '", "' + rst_notes + time.strftime('%d.%m.%Y %H:%M') + ' **' + statusinfo + '**"\n'
      elif statustext == 'rejected':
        rst_rejected += '   "' + str(jobid) + '", "' + jobdata['hiringOrganization']['name'] + '", "' +jobdata['jobLocation']['address']['addressLocality'] + '", "' + jobdata['title'] + '", "' + time.strftime('%d.%m.%Y %H:%M') + ' **' + statusinfo + '**"\n'
      else:
        pass
        #print(jobdata['hiringOrganization']['name'],jobdata['title'],statidescriptions[statusid],status[2])
    rst_description += rst_applications + "\n"
    rst_description += rst_rejected + "\n"
    openreportfilename = expanduser(self.config.reportpath)+"/Offene_Bewerbungen_" +self.config.applicant.replace(" ","_") + ".pdf"
    try:
      with open(openreportfilename, "wb") as openreportfile:
        m4process = subprocess.run(["rst2pdf","-s","/home/flo/bin/json2stelle.yaml"], input=rst_description.encode("utf8"), stdout=openreportfile)
    except subprocess.CalledProcessError as error:
      print("Could not execute rst2pdf!")
      return False
    return True
  def view_open_applications(self):
    openreportfilename = expanduser(self.config.reportpath)+"/Offene_Bewerbungen_" +self.config.applicant.replace(" ","_") + ".pdf"
    try:
      subprocess.run(["evince",openreportfilename])
    except subprocess.CalledProcessError as error:
      return False
    return True

