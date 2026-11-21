import time,uuid
from collections import deque
from copy import deepcopy

VALID_LEVELS={'info','warning','error'}
class DiagnosticEvents:
 def __init__(self,limit=100,clock=None):
  self._items=deque(maxlen=max(1,min(int(limit),1000)));self._clock=clock or time.time
 def record(self,component,level,message,correlation_id=None,detail=None):
  component=(component or '').strip();level=(level or '').strip().lower();message=(message or '').strip()
  if not component or level not in VALID_LEVELS or not message:return False
  self._items.append({'timestamp':int(self._clock()),'correlationId':correlation_id or uuid.uuid4().hex,'component':component,'level':level,'message':message,'detail':deepcopy(detail) if detail is not None else None});return True
 def snapshot(self):return deepcopy(list(self._items))
 def correlated(self,correlation_id,component=None):
  cid=str(correlation_id or '').strip();component=str(component or '').strip()
  if not cid:return []
  return deepcopy([x for x in self._items if x.get('correlationId')==cid and (not component or x.get('component')==component)])
 def clear(self):self._items.clear()
