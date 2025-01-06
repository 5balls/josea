# Copyright 2024 Florian Pesth
#
# This file is part of JoSea.
#
# JoSea is free software: you can redistribute it and/or modify it under the terms of the GNU Affero General Public License version 3 as published by the Free Software Foundation.
#
# JoSea is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License version 3 along with JoSea. If not, see <https://www.gnu.org/licenses/>. 

from josea.dbop.dboperations import db_config
from os.path import expanduser

import jsonpickle

class db():
  config: db_config
  def __init__(self, debug:bool=False):
    dbconfig = open(expanduser("~/.josea/dbconfig.json"), "r")
    self.config = jsonpickle.decode(dbconfig.read())
    self.connect_or_create_database(expanduser(self.config.name),debug)
  def __del__(self):
    self.connection.close()

  from josea.dbop.dboperations import connect_or_create_database

  from josea.dbop.dboperations import is_duplicate
  
  from josea.dbop.dboperations import add_jobposting

  from josea.dbop.dboperations import jsonld

  from josea.dbop.dboperations import add_evaldata
  
  from josea.dbop.dboperations import get_evaldata
  
  from josea.dbop.dboperations import get_max_evaldata

  from josea.dbop.dboperations import add_note

  from josea.dbop.dboperations import get_notes

  from josea.dbop.dboperations import discard_job
  
  from josea.dbop.dboperations import apply_job

  from josea.dbop.dboperations import construct_filename

  from josea.dbop.dboperations import get_stati_for_daterange
  
  from josea.dbop.dboperations import get_status_name
