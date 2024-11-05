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
      print('href_applies: %s, text_applies %s' % (href_applies,text_applies))
    if href_applies is not None:
      if text_applies is not None:
        return href_applies and text_applies
      else:
        return href_applies
    else:
      if text_applies is not None:
        return text_applies
    return False

# We need this outside of the webpage class because
# we would get cross dependencies otherwise
def get_all_links_from_xmlstr(xml:str):
  xml = html.fromstring(page)
  links = list()
  for link in xml.iter('a'):
    linktext = "".join(link.itertext())
    l_link = {"href": link.get("href"), "text": linktext}
    links.append(l_link) 
  return links

def get_all_links_from_webpage(url:dict):
  request = urllib.request.urlopen(url)
  page = request.read().decode("utf-8")
  return get_all_links_from_xmlstr(page)

class webpage_action_enum(Enum):
  FOLLOW_LINK = 1
  DOWNLOAD_JSONLD = 2

class webpage_action():
  action: webpage_action_enum
  linkrule: link_rule
  data = ''
  def __init__(self, action:webpage_action_enum, linkrule:link_rule = None):
    self.action = action
    self.linkrule = linkrule
  def execute(self):
    match action:
      case webpage_action_enum.FOLLOW_LINK:
        links = get_all_links_from_xmlstr(self.data)
        for link in links:
           if linkrule.applies(link['href'],link['text']):
             request = urllib.request.urlopen(url)
             webpage_action.data = request.read().decode("utf-8")
             return True
        return False
      case webpage_action_enum.DOWNLOAD_JSONLD:
        xmltreewebpage = html.fromstring(self.data)
        for script in xmltreewebpage.iter("script"):
          if(script.get("type") == "application/ld+json"):
            webpage_action.data = json.loads(script.text)
            return True
      case _:
        return False

class webpage_rule():
  url_contains: str
  url_pattern: re.Pattern
  xpath: str
  xpath_text_contains: str
  xpath_text_pattern: re.Pattern
  actions: list[webpage_action]
  negate: bool
  def __init__(self, url_contains:str=None, url_pattern:str=None, xpath:str=None, xpath_text_contains:str=None, xpath_text_pattern:str=None, actions:list[webpage_action]=None, negate:bool=False):
    self.url_contains = url_contains
    self.url_pattern = url_pattern
    self.xpath = xpath
    self.xpath_text_contains = xpath_text_contains
    self.xpath_text_pattern = xpath_text_pattern
    self.actions = actions
    self.negate = negate
  def repairpatterns(self):
    if self.url_pattern:
      if isinstance(self.url_pattern, str):
        self.url_pattern = re.compile(self.url_pattern)
    if self.xpath_text_pattern:
      if isinstance(self.xpath_text_pattern, str):
        self.xpath_text_pattern = re.compile(self.xpath_text_pattern)
  def applies(self, url:str, xml:str):
    xmltree = html.fromstring(xml)
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
  def execute_actions(self, xml:str):
    webpage_action.data = xml
    for action in self.actions:
      action.execute()

class webpage_config:
  name : str
  rules: list[webpage_rule]
  def __init__(self, name:str=None, rules:list[webpage_rule]=None):
    self.name=name
    self.rules = rules
  def applies(self, url:str, xml:str):
    for rule in self.rules:
      if not rule.applies(url,xml):
        return False
    return True
