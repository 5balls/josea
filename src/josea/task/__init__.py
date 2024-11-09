# Copyright 2024 Florian Pesth
#
# This file is part of JoSea.
#
# JoSea is free software: you can redistribute it and/or modify it under the terms of the GNU Affero General Public License version 3 as published by the Free Software Foundation.
#
# JoSea is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License version 3 along with JoSea. If not, see <https://www.gnu.org/licenses/>. 

from tasklib import TaskWarrior, Task
import jsonpickle
import json
import datetime
import josea
from os.path import expanduser

class task_config():
  data_location: str
  def __init__(self,data_location:str=None):
    self.data_location = data_location

class task():
  def __init__(self, debug:bool=False):
    taskconfig = open(expanduser("~/.josea/taskconfig.json"), "r")
    self.config = jsonpickle.decode(taskconfig.read())
    self.tw = TaskWarrior(data_location=self.config.data_location)
  def from_jobposting(self,jobid:int):
    db = josea.dbop.db()
    jsonld = db.jsonld(jobid)
    jobdata = json.loads(jsonld)
    title = jobdata['title']
    try:
      dateposted = datetime.datetime.strptime(jobdata['datePosted'], '%Y-%m-%dT%H:%M:%S.%fZ')
    except ValueError:
      try:
        dateposted = datetime.datetime.strptime(jobdata['datePosted'], '%Y-%m-%dT%H:%M:%SZ')
      except ValueError:
        dateposted = datetime.datetime.now()
    validthrough = datetime.datetime.strptime(jobdata['validThrough'], '%Y-%m-%dT%H:%M:%S.%fZ')
    company = jobdata['hiringOrganization']['name']
    city = jobdata['jobLocation']['address']['addressLocality']
    task = Task(self.tw, description = city + ': ' + company + ' - ' + title)
    task['until'] = validthrough
    task['tags'] = ['Jobsuche','Stellenausschreibung']
    task.save()
    self.tw.execute_command([task['id'],"mod","entry:"+dateposted.strftime("%Y-%m-%d %H:%M:%S"),"rc.dateformat:Y-M-D %H:%N:%S","job_dbid:"+str(jobid)])
    # Add more meta information if in db:
    job_score = db.get_evaldata(jobid, "knowhow_score")
    if job_score:
      self.tw.execute_command([task['id'],"mod","job_score:"+str(json.loads(job_score[0]))])
    positive_tags = db.get_evaldata(jobid, "knowhow_positive")
    if positive_tags:
      self.tw.execute_command([task['id'],"mod","job_positive_tags:"+str(json.loads(positive_tags[0]))])
    negative_tags = db.get_evaldata(jobid, "knowhow_negative")
    if negative_tags:
      self.tw.execute_command([task['id'],"mod","job_negative_tags:"+str(json.loads(negative_tags[0]))])



