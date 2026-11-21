import time,uuid
from collections import deque

VALID_LEVELS={'info','warning','error'}
class DiagnosticEvents:
 def __init__(self,limit=100,clock=None):
  self._items=deque(maxlen=max(1,min(int(limit),1000)));self._clock=clock or time.time
 def record(self,component,level,message,correlation_id=None,detail=None):
  component=(component or '').strip();level=(level or '').strip().lower();message=(message or '').strip()
  if not component or level not in VALID_LEVELS or not message:return False
  self._items.append({'timestamp':int(self._clock()),'correlationId':correlation_id or uuid.uuid4().hex,'component':component,'level':level,'message':message,'detail':detail if detail is not None else None});return True
 def snapshot(self):return list(self._items)
 def clear(self):self._items.clear()
