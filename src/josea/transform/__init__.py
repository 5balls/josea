# Copyright 2024 Florian Pesth
#
# This file is part of JoSea.
#
# JoSea is free software: you can redistribute it and/or modify it under the terms of the GNU Affero General Public License version 3 as published by the Free Software Foundation.
#
# JoSea is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License version 3 along with JoSea. If not, see <https://www.gnu.org/licenses/>. 

import jsonpickle
import json
from os.path import expanduser
import pypandoc

class transform_rule():
  source: str
  target: str
  transform: str
  def __init__(self,source:str=None,target:str=None,transform:str=None):
    self.source = source
    self.target = target
    self.transform = transform

class transform_if_exists_add_rule():
  exists: str
  target: str
  value: str
  def __init__(self,exists:str=None,target:str=None,value:str=None):
    self.exists = exists
    self.target = target
    self.value = value

class transform_if_value_add_rule():
  source: str
  source_value: str
  target: str
  target_value: str
  def __init__(self,source:str=None,source_value:str=None,target:str=None,target_value:str=None):
    self.source = source
    self.source_value = source_value
    self.target = target
    self.target_value = target_value

class transform_config():
  rules: list[transform_rule]
  if_exist_add_rules: list[transform_if_exists_add_rule]
  if_value_add_rules: list[transform_if_value_add_rule]
  def __init__(self,rules:list[transform_rule]=None,if_exist_add_rules:list[transform_if_exists_add_rule]=None,if_value_add_rules:list[transform_if_value_add_rule]=None):
    self.rules = rules
    self.if_exist_add_rules = if_exist_add_rules
    self.if_value_add_rules = if_value_add_rules

class transform():
  config: transform_config
  def __init__(self, filename:str="~/.josea/transformconfig.json", debug:bool=False):
    transformconfig = open(expanduser(filename), "r")
    self.config = jsonpickle.decode(transformconfig.read())
  def apply(self,sourcejson:str):
    # I would prefer to have json like path support in python
    # but couldn't find it, so a slightly convoluted own
    # implementation will have to do
    sourcedata = json.loads(sourcejson)
    targetdata = dict()
    for rule in self.config.rules:
      value = sourcedata
      # Recursively resolve key path if possible:
      keys = rule.source.split("/")[1:]
      if keys:
        for key in keys:
          if value:
            if key.isnumeric():
              value = value[int(key)]
            else:
              value = value.get(key, None)
        if not value:
          continue
      else:
        continue
      if rule.transform:
        if rule.transform == "markdown2html":
          value = value.replace(" •","\n*")
          value = pypandoc.convert_text(value,'html', format='md')
          value = value.replace("<ul>\n<li>","<ul><li>")
          value = value.replace("</li>\n<li>","</li><li>")
          value = value.replace("\n","<br />")
      keys = rule.target.split("/")[1:]
      # Recursively build up dict:
      targetvalue = targetdata
      for key in keys[:-1]:
        targetvalue = targetvalue.setdefault(key, {})
      targetvalue[keys[-1]] = value
    for rule in self.config.if_value_add_rules:
      value = sourcedata
      # Recursively resolve key path if possible:
      keys = rule.source.split("/")[1:]
      if keys:
        for key in keys:
          if value:
            if key.isnumeric():
              value = value[int(key)]
            else:
              value = value.get(key, None)
        if not value:
          continue
      else:
        continue
      if value != rule.source_value:
        continue
      else:
        value = rule.target_value
      keys = rule.target.split("/")[1:]
      # Recursively build up dict:
      targetvalue = targetdata
      for key in keys[:-1]:
        targetvalue = targetvalue.setdefault(key, {})
      targetvalue[keys[-1]] = value
    for rule in self.config.if_exist_add_rules:
      value = targetdata
      # Recursively resolve key path if possible:
      keys = rule.exists.split("/")[1:]
      if keys:
        for key in keys:
          if value:
            if key.isnumeric():
              value = value[int(key)]
            else:
              value = value.get(key, None)
        if not value:
          continue
      else:
        continue
      keys = rule.target.split("/")[1:]
      # Recursively build up dict:
      targetvalue = targetdata
      for key in keys[:-1]:
        targetvalue = targetvalue.setdefault(key, {})
      targetvalue[keys[-1]] = rule.value
    targetdata["original"] = sourcedata
    return json.dumps(targetdata)
