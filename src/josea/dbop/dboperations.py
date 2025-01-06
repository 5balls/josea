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
from os.path import expanduser

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
  if "hiringOrganization" not in jobdata:
    print("Could not find \"hiringOrganization!\" in jsonld!")
    print(jsonld)
    return False
  company = jobdata["hiringOrganization"]["name"]
  if "title" not in jobdata:
    print("Could not find \"title!\" in jsonld!")
    print(jsonld)
    return False
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
  jsonld = result.fetchall()
  if jsonld:
    return jsonld[-1][0]
  else:
    return "{}"

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
  data = result.fetchall()
  if not data:
    return None
  else:
    return data[-1]

def get_max_evaldata(self,description:str):
  result = self.connection.execute("SELECT id from evaldatatypes WHERE description=?",(description,))
  evaldatatypeid = result.fetchone()
  if not evaldatatypeid:
    return None
  result = self.connection.execute("SELECT max(CAST(data AS FLOAT)) FROM evaldata WHERE type=?",evaldatatypeid)
  data = result.fetchone()
  if not data:
    return None
  else:
    return float(data[0])

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

def set_status(self,jobid:int,status:str):
  result = self.connection.execute("SELECT id FROM statuses WHERE name=?",(status,))
  statusid = result.fetchone()
  self.connection.execute("INSERT INTO history (joboffer,status) values (?,?)",(jobid,statusid[0]))
  self.connection.commit()

def set_status_with_date(self,jobid:int,status:str,date:str):
  result = self.connection.execute("SELECT id FROM statuses WHERE name=?",(status,))
  statusid = result.fetchone()
  self.connection.execute("INSERT INTO history (joboffer,status,time) values (?,?,?)",(jobid,statusid[0],date))
  self.connection.commit()

def get_history_ids(self,jobid:int):
  result = self.connection.execute("SELECT id FROM history WHERE joboffer=?",(jobid,))
  return result.fetchall()

def get_last_history_id(self,jobid:int):
  history_ids = self.get_history_ids(jobid)
  if history_ids:
    return history_ids[-1]
  else:
    return None

def get_history_time(self,historyid:int):
  result = self.connection.execute("SELECT time FROM history WHERE id=?",(historyid,))
  return result.fetchone()

def get_history_status(self,historyid:int):
  result = self.connection.execute("SELECT status FROM history WHERE id=?",(historyid,))
  return result.fetchone()

def apply_job(self,jobid:int):
  self.add_note(jobid,"Auf Stelle beworben")
  self.set_status(jobid,"applied")

def rejection_received(self,jobid:int):
  self.add_note(jobid,"Absage erhalten")
  self.set_status(jobid,"rejected")

def construct_filename(self,jobid:int,ending:str,path:str=''):
  jsonld = self.jsonld(jobid)
  jobdata = json.loads(jsonld)
  if 'hiringOrganization' not in jobdata:
    return False, ''
  if 'name' not in jobdata['hiringOrganization']:
    return False, ''
  if 'title' not in jobdata:
    return False, ''
  job_company_filename = ''.join(x for x in jobdata['hiringOrganization']['name'].title() if not x.isspace() and x.isalpha())
  job_title_filename =  ''.join(x for x in jobdata['title'].title() if not x.isspace() and x.isalpha())
  return True, expanduser(path) + job_company_filename+'_' + job_title_filename + '.' + ending

def get_stati_for_daterange(self,firstdatetime,seconddatetime):
  result = self.connection.execute("SELECT joboffer,status,time FROM history WHERE time>=? AND time<=?",(firstdatetime,seconddatetime))
  return result.fetchall()

def get_status_name(self,statusid:int):
  result = self.connection.execute("SELECT name FROM statuses WHERE id=?",(statusid,))
  return result.fetchone()

def get_jobid_by_string(self,searchstring:str):
  result = self.connection.execute("SELECT id FROM joboffers WHERE (lower(company) LIKE '%' || lower(?) || '%') OR (lower(description) LIKE '%' || lower(?) || '%') OR (lower(jsonld) LIKE '%' || lower(?) || '%')",(searchstring,searchstring,searchstring))
  return result.fetchall()
  
