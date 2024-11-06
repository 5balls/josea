# This file is part of JoSea.
#
# JoSea is free software: you can redistribute it and/or modify it under the terms of the GNU Affero General Public License version 3 as published by the Free Software Foundation.
#
# JoSea is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License version 3 along with JoSea. If not, see <https://www.gnu.org/licenses/>. 

from josea.dbop.dboperations import db_config

import jsonpickle

class db():
  config: db_config
  def __init__(self, debug:bool=False):
    dbconfig = open("dbconfig.json", "r")
    self.config = jsonpickle.decode(dbconfig.read())
    self.connect_or_create_database(self.config.name,debug)
  def __del__(self):
    self.connection.close()

  from josea.dbop.dboperations import connect_or_create_database

  from josea.dbop.dboperations import is_duplicate
  
  from josea.dbop.dboperations import add_jobposting
