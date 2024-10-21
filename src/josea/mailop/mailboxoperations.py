# This file is part of JoSea.
#
# JoSea is free software: you can redistribute it and/or modify it under the terms of the GNU Affero General Public License version 3 as published by the Free Software Foundation.
#
# JoSea is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License version 3 along with JoSea. If not, see <https://www.gnu.org/licenses/>. 


import email
from lxml import html, etree
from email.policy import default

def find_links_in_html_body(self):
  # Get html part of email, convert it to valid xml and try to get all links in
  # plaintext. Return as (possible empty) array.
  email_message = email.message_from_bytes(self.message.as_bytes(), policy=default)
  body = email_message.get_body(('html', 'text')).get_content()
  xmltree = html.fromstring(body)
  links = dict()
  for link in xmltree.iter('a'):
    linktext = link.text
    for childlink in link:
      if childlink.tag == "span":
        linktext = childlink.text
    if linktext:
      if (linktext in links) and str(link.get("href")) != links[linktext]:
        pass
      else:
        links[linktext] = link.get("href") 
  return links
