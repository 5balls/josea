# This file is part of JoSea.
#
# JoSea is free software: you can redistribute it and/or modify it under the terms of the GNU Affero General Public License version 3 as published by the Free Software Foundation.
#
# JoSea is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License version 3 along with JoSea. If not, see <https://www.gnu.org/licenses/>. 


import email
from lxml import html
from mailbox import MHMessage
import re

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
  def applies(self, href:str = None, text:str = None):
    self.repairpatterns()
    href_applies = None
    if href and self.href_pattern:
      if self.href_pattern.search(href):
        href_applies = True
      else:
        href_applies = False
    if href and self.href_contains:
      href_applies = self.href_contains in href
    text_applies = None
    if text and self.text_pattern:
      if self.text_pattern.search(text):
        text_applies = True
      else:
        text_applies = False
    if text and self.text_contains:
      text_applies = self.text_contains in text
    return href_applies and text_applies

class mail_rule():
  mailkey : str
  contains : str
  pattern : re.Pattern
  negate : bool
  def __init__(self, mailkey:str = None, contains:str = None, pattern:str = None, negate:bool = False):
    self.mailkey = mailkey
    self.contains = contains
    self.pattern = pattern
    if pattern:
      self.pattern = re.compile(pattern)
    self.negate = negate
  def repairpatterns(self):
    if self.pattern:
      if isinstance(self.pattern, str):
        self.pattern = re.compile(self.pattern)
  def applies(self, message:MHMessage):
    self.repairpatterns()
    if not self.mailkey:
      return self.logic(False)
    if self.contains:
      return self.logic(self.contains in message[self.mailkey])
    if self.pattern:
      if self.pattern.search(message[self.mailkey]):
        return self.logic(True)
      else:
        return self.logic(False)
    return False
  def logic(self, value:bool):
    if self.negate:
      return not value
    else:
      return value

class mail_config():
  name : str
  rules : list
  validlinks : list
  def __init__(self, name:str=None, rules:list=None, validlinks:list=None):
    self.name = name
    self.rules = rules
    self.validlinks = validlinks
  def applies(self, message:MHMessage):
    allrulesmatch = True
    for rule in self.rules:
      if not rule.applies(message):
        allrulesmatch = False
    return allrulesmatch
  def linkvalid(self, href:str=None, text:str=None):
    for link in self.validlinks:
      if(link.applies(href,text)):
        return True
    return False


def find_links_in_html_body(self):
  # Get html part of email, convert it to valid xml and try to get all links in
  # plaintext. Return as (possible empty) array.
  email_message = email.message_from_bytes(self.message.as_bytes(), policy=email.policy.default)
  body = email_message.get_body(('html', 'text')).get_content()
  xmltree = html.fromstring(body)
  links = list()
  for link in xmltree.iter('a'):
    linktext = "".join(link.itertext())
    links.append({"href": link.get("href"), "text": linktext}) 
  return links

