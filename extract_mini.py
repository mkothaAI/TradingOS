import pdfplumber, os, json, re

def extract(path):
  d={"titles":[],"concepts":[],"rules":[],"formulas":[],"psych":[],"risk":[],"err":[]}
  try:
    if not os.path.exists(path): return {"err":["Not found"]}
    with pdfplumber.open(path) as pdf:
      txt = ""
      for p in pdf.pages[:20]: 
        t=p.extract_text()
        if t: txt+=t+"\n"
    lines = [l.strip() for l in txt.split("\n") if l.strip()]
    for l in lines:
      if re.match(r"^Chapter \d+", l): d["titles"].append(l)
      if any(k in l for k in ["Rule","Must","Should"]) and len(d["rules"])<5: d["rules"].append(l)
      if any(k in l for k in ["Risk","Loss","Margin"]) and len(d["risk"])<5: d["risk"].append(l)
      if any(k in l for k in ["=","+","*"]) and any(c.isdigit() for c in l) and len(d["formulas"])<5: d["formulas"].append(l)
      if len(l)>30 and l[0].isupper() and len(d["concepts"])<10: d["concepts"].append(l)
    for k in d: d[k]=list(set(d[k]))
  except Exception as e: d["err"].append(str(e))
  return d

base="trading_os_v1/source/Varsity"
mods=[
("1 Introduction to Stock Markets","Module 1_Introduction to Stock Markets.pdf"),
("2 Technical Analysis","Module 2_Technical Analysis.pdf"),
("3 Fundamental Analysis","Module 3_Fundamental Analysis.pdf"),
("4 Futures Trading","Module 4_Futures Trading.pdf"),
("5 Options Theory for Professional Trading","Module 5_Options-Theory-for-Professional-Trading.pdf"),
("6 Option Strategies","Module 6_Option Strategies.pdf"),
("7 Markets and Taxation","Module 7_Markets & Taxation.pdf"),
("8 Currency  Commodity Futures","Module 8_Currency and Commodity Futures.pdf"),
("9 Risk Management and Trading Psychology","Module 9_Risk Management & Trading Psychology.pdf"),
("10 Trading Systems","Module 10_Trading Systems.pdf"),
("11 Personal Finance Part 1","Module11_Personal-Finance.pdf"),
("13 Financial Modelling","Module 13.pdf"),
("14 PERSONAL FINANCE - INSURANCE","Module 14_Personal Finance Insurance.pdf")]

for name, file in mods:
  res = extract(os.path.join(base, name, file))
  print(f"--- {name} ---")
  print(json.dumps(res))
