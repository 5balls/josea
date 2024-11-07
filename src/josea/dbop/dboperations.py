# Copyright 2024 Florian Pesth
#
# This file is part of JoSea.
#
# JoSea is free software: you can redistribute it and/or modify it under the terms of the GNU Affero General Public License version 3 as published by the Free Software Foundation.
#
# JoSea is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License version 3 along with JoSea. If not, see <https://www.gnu.org/licenses/>. 

import sqlite3
import json

class db_config():
  name : str
  def __init__(self,name:str=None):
    self.name = name

def connect_or_create_database(self,name:str,debug:bool=False):
  self.connection = sqlite3.connect(name) 
  result = self.connection.execute("SELECT name from sqlite_master")
  self.connection.commit()
  tables = result.fetchall()
  if debug:
    print("Tables: %s" % tables)
  if ("statuses",) not in tables:
    if debug:
      print("Create table statuses...")
    self.connection.execute("""
        CREATE TABLE statuses(
          id INTEGER PRIMARY KEY,
          name TEXT NOT NULL
          )""")
    self.connection.commit()
    if debug:
      print("Insert rows in table statuses...")
    data = [("new",),("applied",),("discarded",),("waitforanswer",),("noanswer",),("rejected",)]
    self.connection.executemany("INSERT INTO statuses (name) values (?)", data)
    self.connection.commit()
  if ("joboffers",) not in tables:
    if debug:
      print("Create table joboffers...")
    self.connection.execute("""
        CREATE TABLE joboffers(
          id INTEGER PRIMARY KEY,
          company TEXT NOT NULL,
          description TEXT NOT NULL,
          jsonld TEXT NOT NULL
          )""")
    self.connection.commit()
  if ("history",) not in tables:
    if debug:
      print("Create table history...")
    self.connection.execute("""
        CREATE TABLE history(
          id INTEGER PRIMARY KEY,
          joboffer INTEGER NOT NULL,
          status INTEGER NOT NULL,
          time DATETIME DEFAULT CURRENT_TIMESTAMP NOT NULL,
          FOREIGN KEY (status) references statuses(id),
          FOREIGN KEY (joboffer) references joboffers(id)
          )""")
    self.connection.commit()
  if ("messageids",) not in tables:
    self.connection.execute("""
        CREATE TABLE messageids(
          id INTEGER PRIMARY KEY,
          messageid TEXT NOT NULL
          )""")
    self.connection.commit()
  if ("messagejobdependencies",) not in tables:
    self.connection.execute("""
        CREATE TABLE messagejobdependencies(
          id INTEGER PRIMARY KEY,
          message INTEGER NOT NULL,
          containedjob INTEGER NOT NULL,
          FOREIGN KEY (message) references messageids(id),
          FOREIGN KEY (containedjob) references joboffers(id)
        )""")
    self.connection.commit()

def is_duplicate(self,jsonld:str):
  jobdata = json.loads(jsonld)
  company = jobdata["hiringOrganization"]["name"]
  description = jobdata["title"]
  result = self.connection.execute("SELECT id FROM joboffers WHERE company=? and description=?",(company,description))
  ids = result.fetchall()
  if not ids:
    return False
  return True

def add_jobposting(self,jsonld:str,message=None):
  jobdata = json.loads(jsonld)
  company = jobdata["hiringOrganization"]["name"]
  description = jobdata["title"]
  cursor = self.connection.cursor()
  cursor.execute("INSERT INTO joboffers (company,description,jsonld) values (?,?,?)",(company,description,jsonld))
  self.connection.commit()
  jobid = cursor.lastrowid
  result = self.connection.execute("SELECT id FROM statuses WHERE name=?",("new",))
  statusid = result.fetchone()
  self.connection.execute("INSERT INTO history (joboffer,status) values (?,?)",(jobid,statusid[0]))
  self.connection.commit()
  if message:
    result = self.connection.execute("SELECT id FROM messageids WHERE messageid=?",(message['message-id'],))
    messageidid = result.fetchone()
    if not messageidid:
      cursor = self.connection.cursor()
      cursor.execute("INSERT INTO messageids (messageid) values (?)",(message['message-id'],))
      self.connection.commit()
      messageidid = (cursor.lastrowid,)
    result = self.connection.execute("SELECT id FROM messagejobdependencies WHERE message=? AND containedjob=?",(messageidid[0],jobid))
    depid = result.fetchone()
    if not depid:
      self.connection.execute("INSERT INTO messagejobdependencies (message,containedjob) values (?,?)",(messageidid[0],jobid))
      self.connection.commit()
