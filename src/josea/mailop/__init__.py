# Copyright 2024 Florian Pesth
#
# This file is part of JoSea.
#
# JoSea is free software: you can redistribute it and/or modify it under the terms of the GNU Affero General Public License version 3 as published by the Free Software Foundation.
#
# JoSea is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License version 3 along with JoSea. If not, see <https://www.gnu.org/licenses/>. 

from mailbox import MH,MHMessage
from os import path,getcwd
import jsonpickle
import re
from os.path import expanduser

from josea.mailop.mailboxoperations import mail_rule, mail_config, delete_mail

class mb():
  def __init__(self, mailfile : str, debug:bool=False):
    self.mh = MH(path.dirname(mailfile), create=False)
    self.message = self.mh.get(path.basename(mailfile))
    mailconfigs = open(expanduser("~/.josea/mailconfigs.json"), "r")
    self.configs = jsonpickle.decode(mailconfigs.read())
    self.job_links = list()
    links = self.find_links_in_html_body()
    for config in self.configs:
      config_applies = config.applies(self.message)
      if debug: 
        print("%s: %s" % (config.name, config_applies))
      if config_applies:
        for link in links:
          link_valid = config.linkvalid(link["href"],link["text"],debug)
          if debug: 
            print('"%s..." "%s": %s' % (link["href"][:10], link["text"], link_valid))
          if link_valid:
            link.update(configname = config.name)
            self.job_links.append(link)

  from josea.mailop.mailboxoperations import find_links_in_html_body
