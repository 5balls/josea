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
import subprocess
import requests

class coverletter_section():
  keywords: list[str]
  text: str
  sectionid: str
  def __init__(self,keywords:str=None,text:str=None,sectionid:str=None):
    self.keywords = keywords
    self.text = text
    self.sectionid = sectionid

class application_config():
  outputpath : str
  coverletter_m4file : str
  coverletter_sections : list[coverletter_section]
  motis_url: str
  def __init__(self, outputpath:str=None, coverletter_m4file:str=None, coverletter_sections:list[coverletter_section]=None,motis_url:str=None):
    self.outputpath = outputpath
    self.coverletter_m4file = coverletter_m4file
    self.coverletter_sections = coverletter_sections
    self.motis_url = motis_url

class application():
  def __init__(self, debug:bool=False):
    reportconfig = open(expanduser("~/.josea/applicationconfig.json"),"r")
    self.config = jsonpickle.decode(reportconfig.read())
  def draft_coverletter(self,positive_keywords:list[str]):
    sections = dict()
    alternative_sections = dict()
    matching_texts = dict()
    covered_keywords = list()
    for coverlettersection in self.config.coverletter_sections:
      number_of_matches = 0
      matching_keywords = list()
      for keyword in coverlettersection.keywords:
        for positive_keyword in positive_keywords:
          if keyword == positive_keyword:
            number_of_matches = number_of_matches + 1
            matching_keywords.append(keyword)
            covered_keywords.append(keyword)
      # A section is better if it contains more matching keywords:
      for matching_keyword in matching_keywords:
        if matching_keyword in sections:
          sectionid, matches = sections[matching_keyword]
          if matches >= number_of_matches:
            if matching_keyword in alternative_sections:
              alternative_sections[matching_keyword].append((coverlettersection.sectionid, number_of_matches))
            else:
              alternative_sections[matching_keyword] = [(coverlettersection.sectionid, number_of_matches)]
            matching_texts[coverlettersection.sectionid] = coverlettersection.text
            continue
        # If we are going to overwrite a previous entry we want to save
        # it in the alternative sections (We don't have to add it to
        # matching_texts, because we did already)
        if matching_keyword in sections:
          sectionid, matches = sections[matching_keyword]
          if matching_keyword in alternative_sections:
            alternative_sections[matching_keyword].append(sections[matching_keyword])
          else:
            alternative_sections[matching_keyword] = [sections[matching_keyword]]
        sections[matching_keyword] = (coverlettersection.sectionid, number_of_matches)
        matching_texts[coverlettersection.sectionid] = coverlettersection.text
    outputsections = dict()
    for keyword, section in sections.items():
      sectionid = section[0]
      number_of_matches = section[1]
      if sectionid in outputsections:
        comment, text = outputsections[sectionid]
        comment = comment + ', "' + keyword + '"'
        outputsections[sectionid] = (comment,text)
      else:
        if number_of_matches == 1:
          outputsections[sectionid] = ('% "' + sectionid + '" ' + str(number_of_matches) + ' match: "' + keyword + '"',matching_texts[sectionid])
        else:
          outputsections[sectionid] = ('% "'  + sectionid + '" ' + str(number_of_matches) + ' matches: "' + keyword + '"',matching_texts[sectionid])
    for keyword, alternative_sections_keyword in alternative_sections.items():
      for section in alternative_sections_keyword:
        sectionid = section[0]
        number_of_matches = section[1]
        if sectionid in outputsections:
          comment, text = outputsections[sectionid]
          comment = comment + ', "' + keyword + '"'
          outputsections[sectionid] = (comment,text)
        else:
          if number_of_matches == 1:
            outputsections[sectionid] = ('% Alternative "' + sectionid + '" ' + str(number_of_matches) + ' match: "' + keyword + '"',matching_texts[sectionid])
          else:
            outputsections[sectionid] = ('% Alternative "' + sectionid + '" ' + str(number_of_matches) + ' matches: "' + keyword + '"',matching_texts[sectionid])
    outputtext = ""
    for keyword in positive_keywords:
      if keyword not in covered_keywords:
        if outputtext:
          outputtext += ', "' + keyword + '"'
        else:
          outputtext = '% Uncovered keywords: "' + keyword + '"'
    if outputtext:
      outputtext += '\n'
    for sectionid, outputsection in outputsections.items():
      outputtext += outputsection[0] + '\n'
      outputtext += outputsection[1] + '\n\n'
    return outputtext
  def write(self,jobid):
    db = josea.dbop.db()
    jsonld = db.jsonld(jobid)
    jobdata = json.loads(jsonld)
    job_positive_tags_json_string = db.get_evaldata(jobid, "knowhow_positive")
    positive_keywords = list()
    if job_positive_tags_json_string:
      positive_keywords = json.loads(job_positive_tags_json_string[0])
      coverletter_text = self.draft_coverletter(positive_keywords)
    else:
      coverletter_text = "`errprint(__program__:__file__:__line__`: fatal error: No positive keywords for coverletter!')m4exit(`1')"
    try:
      jobdescription = jobdata['title']
    except KeyError:
      jobdescription = "% Could not get job description from meta data!"
    try:
      company_name = jobdata['hiringOrganization']['name'].replace("&","\&")
    except KeyError:
      company_name = "% Could not get the company name from meta data!"
    try:
      company_adress = jobdata['jobLocation']['address']['streetAddress']
    except KeyError:
      company_adress = "% Could not get Street Address from meta data!"
    try:
      company_plz = jobdata['jobLocation']['address']['postalCode']
    except KeyError:
      company_plz = "% Could not get postal code from meta data!"
    try:
      company_city = jobdata['jobLocation']['address']['addressLocality']
    except KeyError:
      company_city = "% Could not get city from meta data!"
    try:
      m4process = subprocess.run(["m4",
          '-Djobdescription='+jobdescription,
          '-Dcompany_name='+company_name,
          '-Dcompany_adress='+company_adress,
          '-Dcompany_plz='+company_plz,
          '-Dcompany_city='+company_city,
          '-Dcoverletter_text='+coverletter_text,
          '-Dpositive_keywords='+', '.join(positive_keywords),
          expanduser(self.config.coverletter_m4file)],
          check=True,
          capture_output=True)
    except subprocess.CalledProcessError as error:
      print("Could not execute m4!")
      return False
    job_company_filename = ''.join(x for x in jobdata['hiringOrganization']['name'].title() if not x.isspace() and x.isalpha())
    job_title_filename =  ''.join(x for x in jobdata['title'].title() if not x.isspace() and x.isalpha())
    bewerbungsfilename = expanduser(self.config.outputpath)+"/Bewerbung"+job_company_filename+".tex"
    with open(bewerbungsfilename, "wb") as bewerbungsfile:
      bewerbungsfile.write(m4process.stdout)
    return True



