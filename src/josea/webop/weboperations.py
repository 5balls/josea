# Copyright 2024 Florian Pesth
#
# This file is part of JoSea.
#
# JoSea is free software: you can redistribute it and/or modify it under the terms of the GNU Affero General Public License version 3 as published by the Free Software Foundation.
#
# JoSea is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License version 3 along with JoSea. If not, see <https://www.gnu.org/licenses/>. 

import re
from enum import Enum
from lxml import html
import json
import josea
import time

class link_rule():
  href_contains : str
  href_pattern : re.Pattern
  text_contains : str
  text_pattern : re.Pattern
  def __init__(self, href_contains:str = None, href_pattern:str = None, text_contains:str = None, text_pattern:str = None):
    self.href_contains = href_contains
    self.href_pattern = href_pattern
    self.text_contains = text_contains
    self.text_pattern = text_pattern
    self.repairpatterns()
  def repairpatterns(self):
    if self.href_pattern:
      if isinstance(self.href_pattern, str):
        self.href_pattern = re.compile(self.href_pattern)
    if self.text_pattern:
      if isinstance(self.text_pattern, str):
        self.text_pattern = re.compile(self.text_pattern)
  def applies(self, href:str = None, text:str = None, debug:bool=False):
    self.repairpatterns()
    href_applies = None
    if href and self.href_pattern:
      if self.href_pattern.search(href):
        if debug:
          print('href "%s" matches pattern' % href)
        href_applies = True
      else:
        if debug:
          print('href "%s" does not match pattern' % href)
        href_applies = False
    if href and self.href_contains:
      href_applies = self.href_contains in href
      if debug:
        print('href "%s" contained in "%s": %s' % (self.href_contains, href, href_applies))
    text_applies = None
    if text and self.text_pattern:
      if self.text_pattern.search(text):
        if debug:
          print('text "%s" matches pattern' % text)
        text_applies = True
      else:
        if debug:
           print('text "%s" does not match pattern' % text)
        text_applies = False
    if text and self.text_contains:
      text_applies = self.text_contains in text
      if debug:
        print('text "%s" contained in "%s": %s' % (self.text_contains, text, text_applies))
    if debug:
      print('→ href_applies: %s, text_applies: %s' % (href_applies,text_applies))
      print('→ href: %s, text: %s' % (href,text))
    if href is not None and ((self.href_contains is not None) or (self.href_pattern is not None)):
      if text is not None and ((self.text_contains is not None) or (self.text_pattern is not None)):
        return href_applies and text_applies
      else:
        return href_applies
    else:
      if text is not None:
        return text_applies
    return False

# We need this outside of the webpage class because
# we would get cross dependencies otherwise
def get_all_links_from_xmlstr(page:str):
  xml = html.fromstring(page)
  links = list()
  for link in xml.iter('a'):
    linktext = "".join(link.itertext())
    l_link = {"href": link.get("href"), "text": linktext}
    links.append(l_link) 
  return links

def get_all_links_from_webpage(url:dict):
  request = urllib.request.urlopen(url)
  time.sleep(15)
  page = request.read().decode("utf-8")
  return get_all_links_from_xmlstr(page)

class webpage_action_enum(Enum):
  FOLLOW_LINK = 1
  DOWNLOAD_JSONLD = 2
  INSERT_DB = 3
  CREATE_TASK = 4
  EVALUATE_JOB = 5
  DOWNLOAD_JSON_AND_TRANSFORM_TO_JSONLD = 6

class webpage_action():
  action: webpage_action_enum
  linkrule: link_rule
  transform_configfile: str
  data = ''
  retval = False
  error: str
  def __init__(self, action:webpage_action_enum, linkrule:link_rule = None, transform_configfile:str = None):
    self.action = action
    self.linkrule = linkrule
    self.error = ''
    self.transform_configfile = transform_configfile
  def execute(self, message=None):
    match self.action:
      case webpage_action_enum.FOLLOW_LINK:
        # Downloads webpage and puts webpage content into data
        links = get_all_links_from_xmlstr(self.data)
        for link in links:
           if self.linkrule.applies(link['href'],link['text']):
             request = urllib.request.urlopen(url)
             time.sleep(15)
             webpage_action.data = request.read().decode("utf-8")
             return self.set_retval(True)
        self.error = "No link rule applied!"
        return self.set_retval(False)
      case webpage_action_enum.DOWNLOAD_JSONLD:
        # Downloads jsonld and puts the json string into data
        xmltreewebpage = html.fromstring(self.data)
        for script in xmltreewebpage.iter("script"):
          if(script.get("type") == "application/ld+json"):
            webpage_action.data = script.text
            return self.set_retval(True)
        self.error = "Could not get correct script section!"
        return self.set_retval(False)
      case webpage_action_enum.DOWNLOAD_JSON_AND_TRANSFORM_TO_JSONLD:
        # Downloads json and transform to jsonld
        xmltreewebpage = html.fromstring(self.data)
        for script in xmltreewebpage.iter("script"):
          if(script.get("type") == "application/json" and script.get("id") == "ng-state"):
            transform = josea.transform.transform(self.transform_configfile)
            retval, data = transform.apply(script.text)
            if retval:
              webpage_action.data = data
              return self.set_retval(True)
            else:
              self.error = "Jobposting seems to be gone"
              return self.set_retval(False)
        self.error = "Could not get correct script section!"
        return self.set_retval(False)
      case webpage_action_enum.INSERT_DB:
        # Inserts jsonld into database and puts database id for it in data
        db = josea.dbop.db()
        if db.is_duplicate(self.data):
          self.error = "Jobposting is duplicate of one in database!"
          return self.set_retval(False)
        webpage_action.data = db.add_jobposting(self.data, message)
        return self.set_retval(True)
      case webpage_action_enum.EVALUATE_JOB:
        # Queries db for jobid and evaluate job
        evalobj = josea.eval.eval()
        evalobj.all(self.data)
        return self.set_retval(True)
      case webpage_action_enum.CREATE_TASK:
        # Queries db for jobid and creates task from it
        task = josea.task.task()
        task.from_jobposting(self.data)
        return self.set_retval(True)
      case _:
        return self.set_retval(False)
  def set_retval(self,val:bool):
    webpage_action.retval = val
    return val

class webpage_rule():
  url_contains: str
  url_pattern: re.Pattern
  xpath: str
  xpath_text_contains: str
  xpath_text_pattern: re.Pattern
  negate: bool
  def __init__(self, url_contains:str=None, url_pattern:str=None, xpath:str=None, xpath_text_contains:str=None, xpath_text_pattern:str=None, negate:bool=False):
    self.url_contains = url_contains
    self.url_pattern = url_pattern
    self.xpath = xpath
    self.xpath_text_contains = xpath_text_contains
    self.xpath_text_pattern = xpath_text_pattern
    self.negate = negate
    self.repairpatterns()
  def repairpatterns(self):
    if self.url_pattern:
      if isinstance(self.url_pattern, str):
        self.url_pattern = re.compile(self.url_pattern)
    if self.xpath_text_pattern:
      if isinstance(self.xpath_text_pattern, str):
        self.xpath_text_pattern = re.compile(self.xpath_text_pattern)
  def applies(self, url:str, xml:str, debug:bool=False):
    if debug:
      print("Test rule, url=%s, xml=%s" % (url,xml[:100]))
    self.repairpatterns()
    xmltree = html.fromstring(xml)
    if self.url_contains:
      return self.logic(self.url_contains in url['href'])
    if self.url_pattern:
      if self.url_pattern.search(url['href']):
        return self.logic(True)
      else:
        return self.logic(False)
    if self.xpath:
      for matched_xpath in xmltree.findall(self.xpath):
        xpath_text = "".join(matched_xpath.itertext())
        if self.xpath_text_contains:
          if self.xpath_text_contains in xpath_text:
            return self.logic(True)
        if self.xpath_text_pattern:
          if self.xpath_text_pattern.search(xpath_text):
            return self.logic(True)
          else:
            return self.logic(False)
    return self.logic(False)
  def logic(self, value:bool):
    if self.negate:
      return not value
    else:
      return value

class webpage_config:
  name : str
  rules: list[webpage_rule]
  actions: list[webpage_action]
  def __init__(self, name:str=None, rules:list[webpage_rule]=None, actions:list[webpage_action]=None):
    self.name=name
    self.rules = rules
    self.actions = actions
  def applies(self, url:str, xml:str,debug:bool=False):
    for rule in self.rules:
      if not rule.applies(url,xml,debug):
        return False
    return True
  def execute_actions(self, xml:str, message=None):
    webpage_action.data = xml
    for action in self.actions:
      retval = action.execute(message)
      if not retval:
        print("Could not execute action \"%s\" for config \"%s\"! Errormessage was \"%s\"" % (action.action,self.name,action.error))
        break

