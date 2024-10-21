# This file is part of JoSea.
#
# JoSea is free software: you can redistribute it and/or modify it under the terms of the GNU Affero General Public License version 3 as published by the Free Software Foundation.
#
# JoSea is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License version 3 along with JoSea. If not, see <https://www.gnu.org/licenses/>. 

from mailbox import MH
from os import path,getcwd
import jsonpickle

class mail_config():
  name : str
  def __init__(self, name=""):
    self.name = name

class mb():
  def __init__(self, mailfile : str):
    self.mh = MH(path.dirname(mailfile), create=False)
    self.message = self.mh.get(path.basename(mailfile))
    self.mail_config = mail_config()
    mailconfigs = open("mailconfigs.json", "r")
    self.config = jsonpickle.decode(mailconfigs.read())
    print(self.config)
    print(jsonpickle.encode(self.config))

  from josea.mailop.mailboxoperations import find_links_in_html_body
