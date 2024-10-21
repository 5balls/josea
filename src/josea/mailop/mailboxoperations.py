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

