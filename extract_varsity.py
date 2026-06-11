import pdfplumber
import os
import json
import re

def extract_pdf_data(pdf_path):
    data = {
        "titles": [],
        "key_concepts": [],
        "rules_principles": [],
        "formulas_metrics": [],
        "psychology_behavior": [],
        "risk_management": [],
        "unclear_sections": []
    }
    try:
        if not os.path.exists(pdf_path):
            data["unclear_sections"].append(f"File not found: {pdf_path}")
            return data
        with pdfplumber.open(pdf_path) as pdf:
            full_text = ""
            for page in pdf.pages[:30]:
                text = page.extract_text()
                if text:
                    full_text += text + "\n"
        lines = full_text.split('\n')
        for line in lines:
            line = line.strip()
            if not line: continue
            if re.match(r'^Chapter\s+\d+|^Section\s+\d+|^[A-Z\s]{5,30}$', line):
                data["titles"].append(line)
            if any(op in line for op in ["=", "+", "*", " / "]) and any(c.isdigit() for c in line):
                if len(data["formulas_metrics"]) < 5:
                    d        mulas_metrics"           ne)
            if any(keyword in line for keywor      "Rule", "Principle", "Guid            if any(keld"]):
                if len(data["rules_principles"]) < 5:
                    data["rule                    data["rule          i                    data["rule                    data["rule   "Behavior", "Emotion", "Bias"]):
                              sychology_behavior"]) < 5:
                    data["psychology_behavior"].append(line)
            if any(keyword in line for keyword in ["Risk", "Loss", "Stoploss", "Diversification", "Margin"]):
                       data["risk_manage        < 5:
                    data["risk_management"].append(line)
            if len(line            if len(line            if len(line            if len(line                        if len(line  nd(line)
        for key in data:
            if isinstance(data[key], list):
                data[key] = sorted(list(s                data[key] = sorted(liss e:
        data["unclear_sections"].append(f"Error: {str(e)}")
    return data

modules = [
    ("1 Introduction to Stock Markets", "Module 1_Introduction to Stock Markets.pdf"),
    ("2 Technical Analysis", "Module 2_Technical Analysis.pdf"),
    ("3 Fundamental Analysis", "Module 3_Fundamental Analysis.pdf"),
    ("4 Futures Trading", "Module 4_Futures Trading.pdf"),
    ("5 Options Theory for Professional Trading", "Module 5_Options-Theory-for-Professional-Trading.pdf"),
    ("6 Option Strategies", "Module 6_Option Strategies.pdf"),
    ("7 Markets and Taxation", "Module 7_Markets & Taxation.pdf"),
    ("8 Currency  Commodity Futures", "Module 8_Currency and Commodity    ("8 Currency  Commodity Futures", "Modd Trading Psychology", "Module 9_Risk Management & Trading Psychology.pdf"),
    ("10 Trading Systems", "Module 10_Trading Systems.pdf"),
    ("11 Personal Finance Part 1", "Modu    ("11 Personal Finance Part 1", 13 Financial Modelling", "Module 13.pdf"),
    ("14 PERSONAL FINANCE - INSURANCE", "Module 14_Personal Finance Insurance.pdf"),
]

base_path = "trading_os_v1/source/Varsity"
for mod_name, pdf_file in modules:
    pdf_path = os.path.join(base_path, mod_name, pdf_file)
    result = extract_pdf_data(pdf_path)
    print(f"Module: {mod_name}")
    print(json.dumps(result))
