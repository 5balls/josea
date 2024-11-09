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
  if ("evaldatatypes",) not in tables:
    self.connection.execute("""
        CREATE TABLE evaldatatypes(
          id INTEGER PRIMARY KEY,
          description TEXT NOT NULL
          )""")
    self.connection.commit()
  if ("evaldata",) not in tables:
    self.connection.execute("""
        CREATE TABLE evaldata(
          id INTEGER PRIMARY KEY,
          job INTEGER NOT NULL,
          type INTEGER NOT NULL,
          data TEXT NOT NULL,
          FOREIGN KEY (job) references joboffers(id),
          FOREIGN KEY (type) references evaldatatypes(id)
          )""")
    self.connection.commit()
  if ("notes",) not in tables:
    self.connection.execute("""
        CREATE TABLE notes(
          id INTEGER PRIMARY KEY,
          job INTEGER NOT NULL,
          time DATETIME DEFAULT CURRENT_TIMESTAMP NOT NULL,
          note TEXT NOT NULL,
          FOREIGN KEY (job) references joboffers(id)
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
  return jobid

def jsonld(self,jobid:int):
  result = self.connection.execute("SELECT jsonld FROM joboffers WHERE id=?",(jobid,))
  jsonld = result.fetchone()
  return jsonld[0]

def add_evaldata(self,jobid:int,description:str,data:str):
  result = self.connection.execute("SELECT id from evaldatatypes WHERE description=?",(description,))
  evaldatatypeid = result.fetchone()
  if not evaldatatypeid:
    cursor = self.connection.cursor()
    cursor.execute("INSERT INTO evaldatatypes (description) values (?)",(description,))
    self.connection.commit()
    evaldatatypeid = (cursor.lastrowid,)
  self.connection.execute("INSERT INTO evaldata (job,type,data) values (?,?,?)",(jobid,evaldatatypeid[0],data))
  self.connection.commit()

def get_evaldata(self,jobid:int,description:str):
  result = self.connection.execute("SELECT id from evaldatatypes WHERE description=?",(description,))
  evaldatatypeid = result.fetchone()
  if not evaldatatypeid:
    return None
  result = self.connection.execute("SELECT data FROM evaldata WHERE job=? AND type=?",(jobid,evaldatatypeid[0]))
  data = result.fetchone()
  if not data:
    return None
  else:
    return data

def add_note(self,jobid:int,note:str):
  self.connection.execute("INSERT INTO notes (job,note) values (?,?)",(jobid,note))
  self.connection.commit()

def get_notes(self,jobid:int):
  result = self.connection.execute("SELECT time,note FROM notes WHERE job=?",(jobid,))
  return result.fetchall()

def discard_job(self,jobid:int):
  self.add_note(jobid,"Jobangebot verworfen")
  result = self.connection.execute("SELECT id FROM statuses WHERE name=?",("discarded",))
  statusid = result.fetchone()
  self.connection.execute("INSERT INTO history (joboffer,status) values (?,?)",(jobid,statusid[0]))
  self.connection.commit()
  obsolete_messageids = []
  result = self.connection.execute("SELECT message FROM messagejobdependencies WHERE containedjob=?",(jobid,))
  messages_containing_job = result.fetchall()
  for message_containing_job in messages_containing_job:
    result = self.connection.execute("SELECT containedjob FROM messagejobdependencies WHERE message=?",message_containing_job)
    jobs = result.fetchall()
    currentmailid_obsolete = True
    for job in jobs:
      result = self.connection.execute("SELECT status FROM history WHERE joboffer=?",job)
      last_status = result.fetchall()[-1][0]
      if last_status != statusid[0]:
        currentmailid_obsolete = False
        break
    if currentmailid_obsolete:
      result = self.connection.execute("SELECT messageid FROM messageids WHERE id=?",message_containing_job)
      obsolete_messageids.append(result.fetchone()[0])
  return obsolete_messageids

      
