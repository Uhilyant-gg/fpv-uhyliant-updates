"""Present one contextual startup action without granting execution authority."""
from __future__ import annotations
from typing import Any, Mapping

LABELS={
 'find-camera':'Знайти камеру',
 'restore-camera':'Відновити камеру',
 'connect-camera':'Підключити камеру',
 'show-video':'Показати відео',
}

def startup_action_presentation(startup: Mapping[str,Any] | None)->dict[str,Any]:
 if not isinstance(startup,Mapping):return {'visible':False,'action':None,'label':'','reasonCode':'startup-state-unavailable'}
 action=startup.get('action')
 if action not in LABELS:return {'visible':False,'action':None,'label':'','reasonCode':startup.get('reasonCode') or 'startup-action-unavailable'}
 return {'visible':True,'action':action,'label':LABELS[action],'reasonCode':startup.get('reasonCode') or 'startup-action-available'}
