# Copyright 2024 Florian Pesth
#
# This file is part of JoSea.
#
# JoSea is free software: you can redistribute it and/or modify it under the terms of the GNU Affero General Public License version 3 as published by the Free Software Foundation.
#
# JoSea is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License version 3 along with JoSea. If not, see <https://www.gnu.org/licenses/>. 

import urllib.request
from lxml import html
import jsonpickle

from josea.webop.weboperations import get_all_links_from_xmlstr, get_all_links_from_webpage, link_rule, webpage_action, webpage_config, webpage_rule, webpage_action_enum

class webpage():
  url : dict
  page : str
  configs: list[webpage_config]
  def __init__(self, url:dict, message=None, debug:bool=False):
    self.url = url
    request = urllib.request.urlopen(url["href"])
    self.page = request.read().decode("utf-8")

    webpageconfigs = open("webpageconfigs.json", "r")
    self.configs = jsonpickle.decode(webpageconfigs.read())
    for config in self.configs:
      config_applies = config.applies(self.url, self.page, debug)
      if debug:
        print("%s: %s" % (config.name, config_applies))
      if config_applies:
        config.execute_actions(self.page, message)
      
