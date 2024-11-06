# Copyright 2024 Florian Pesth
#
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

from josea.webop import link_rule

class mail_rule():
  mailkey : str
  contains : str
  pattern : re.Pattern
  negate : bool
  def __init__(self, mailkey:str = None, contains:str = None, pattern:str = None, negate:bool = False):
    self.mailkey = mailkey
    self.contains = contains
    self.pattern = pattern
    self.negate = negate
    repairpatterns()
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
  def linkvalid(self, href:str=None, text:str=None, debug:bool=False):
    for link in self.validlinks:
      if(link.applies(href,text,debug)):
        return True
    return False


def find_links_in_html_body(self):
  # Get html part of email, convert it to valid xml and try to get all links in
  # plaintext. Return as (possible empty) array.
  links = list()
  email_message = email.message_from_bytes(self.message.as_bytes(), policy=email.policy.default)
  body = email_message.get_body(('html', 'text'))
  if not body:
    return links
  content = body.get_content()
  xmltree = html.fromstring(content)
  for link in xmltree.iter('a'):
    linktext = "".join(link.itertext())
    links.append({"href": link.get("href"), "text": linktext}) 
  return links

