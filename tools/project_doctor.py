#!/usr/bin/env python3
"""Machine-readable repository readiness entry point for humans, CI and coding agents."""
import json
import subprocess
import sys
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
CANONICAL=("PRODUCT_UX.md","PROJECT_STATE.md","DEVELOPMENT_GUIDE.md","HARDWARE_E2E.md","DELIVERY_ROADMAP.md","AUTONOMOUS_DEVELOPMENT.md")

def emit(status,area,stage,reason,summary,checks,next_milestone=None,exit_code=1):
 payload={"schemaVersion":1,"status":status,"area":area,"stage":stage,"reasonCode":reason,"summary":summary,"checks":checks,"nextMilestone":next_milestone}
 print(json.dumps(payload,ensure_ascii=False,separators=(',',':')))
 return exit_code

def run(name,cmd,cwd=None):
 try:
  result=subprocess.run(cmd,cwd=cwd or ROOT,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True,timeout=300)
 except Exception as exc:return {"name":name,"ok":False,"detail":type(exc).__name__}
 tail="\n".join(result.stdout.splitlines()[-12:])
 return {"name":name,"ok":result.returncode==0,"detail":tail[-3000:]}

def main():
 checks=[]
 missing=[name for name in CANONICAL if not (ROOT/name).is_file()]
 checks.append({"name":"canonical-files","ok":not missing,"detail":"missing: "+", ".join(missing) if missing else "present"})
 if missing:return emit("BLOCKED","repository","canonical-state","canonical-files-missing","Canonical project files are incomplete",checks)
 checks.append(run("compile",[sys.executable,"-m","compileall","-q","-f","src","tools"]))
 if not checks[-1]["ok"]:return emit("BLOCKED","repository","compile","compile-failed","Python source compilation failed",checks)
 checks.append(run("app-tests",[sys.executable,"-m","unittest","discover","-s",".","-p","test_*.py"],ROOT/"src"/"app"))
 if not checks[-1]["ok"]:return emit("BLOCKED","application","tests","app-tests-failed","Application tests failed",checks)
 checks.append(run("tool-tests",[sys.executable,"-m","unittest","discover","-s",".","-p","test_*.py"],ROOT/"tools"))
 if not checks[-1]["ok"]:return emit("BLOCKED","tooling","tests","tool-tests-failed","Tool tests failed",checks)
 return emit("READY","repository","validation","ready","Repository software validation passed",checks,"E1",0)

if __name__=="__main__":raise SystemExit(main())
