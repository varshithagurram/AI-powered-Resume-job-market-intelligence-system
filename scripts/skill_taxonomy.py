"""
skill_taxonomy.py

Shared skill taxonomy used by both clean_data.py (job postings) and
parse_resume.py (resumes), so skills are extracted identically from both
sides and are directly comparable in the matching engine.

Canonical skill name -> list of regex patterns that indicate it.
Extend this as new skills show up in real scraped/API data.
"""

SKILL_TAXONOMY = {
    # --- Data & analytics ---
    "SQL": [r"\bsql\b"],
    "Python": [r"\bpython\b"],
    "Excel": [r"\bexcel\b"],
    "Tableau": [r"\btableau\b"],
    "Power BI": [r"\bpower\s*bi\b"],
    "Statistics": [r"\bstatistic(s)?\b", r"\bstats\b"],
    "A/B Testing": [r"\ba/?b\s*testing\b"],
    "Machine Learning": [r"\bmachine\s*learning\b", r"\bml\b"],
    "DAX": [r"\bdax\b"],
    "R": [r"\br programming\b", r"\br\b(?=.*(statist|analy))"],
    "Deep Learning": [r"\bdeep\s*learning\b"],
    "NLP": [r"\bnlp\b", r"\bnatural language processing\b"],
    "Spark": [r"\bspark\b"],
    "Data Visualization": [r"\bdata visuali[sz]ation\b"],
    "ETL": [r"\betl\b"],

    # --- Cloud & infra ---
    "AWS": [r"\baws\b"],
    "Azure": [r"\bazure\b"],
    "GCP": [r"\bgcp\b", r"\bgoogle cloud\b"],
    "Docker": [r"\bdocker\b"],
    "Kubernetes": [r"\bkubernetes\b", r"\bk8s\b"],
    "CI/CD": [r"\bci/?cd\b", r"\bcontinuous integration\b"],
    "Terraform": [r"\bterraform\b"],
    "Linux": [r"\blinux\b"],

    # --- Software engineering languages/frameworks ---
    "Java": [r"\bjava\b(?!script)"],
    "JavaScript": [r"\bjavascript\b", r"\bjs\b(?=.*(react|node|frontend|framework))"],
    "TypeScript": [r"\btypescript\b"],
    "C++": [r"\bc\+\+\b"],
    "C#": [r"\bc#\b"],
    "Go": [r"\bgolang\b", r"\bgo programming\b"],
    "React": [r"\breact(\.js)?\b(?!\s*native)"],
    "Node.js": [r"\bnode(\.js)?\b"],
    "Angular": [r"\bangular\b"],
    "Vue.js": [r"\bvue(\.js)?\b"],
    "REST APIs": [r"\brest(ful)?\s*api(s)?\b"],
    "GraphQL": [r"\bgraphql\b"],
    "Spring Boot": [r"\bspring\s*boot\b"],
    "Django": [r"\bdjango\b"],
    "Flask": [r"\bflask\b"],
    "MongoDB": [r"\bmongodb\b"],
    "Git": [r"\bgit\b(?!hub|lab)"],

    # --- Product / design ---
    "Product Management": [r"\bproduct\s*management\b"],
    "Agile/Scrum": [r"\bagile\b", r"\bscrum\b"],
    "Figma": [r"\bfigma\b"],
    "UI/UX Design": [r"\bui/?ux\b", r"\buser experience\b", r"\buser interface design\b"],
    "Wireframing": [r"\bwirefram(e|ing)\b"],

    # --- Finance / accounting ---
    "Financial Modeling": [r"\bfinancial model(l)?ing\b"],
    "Forecasting": [r"\bforecast(ing)?\b"],
    "Budgeting": [r"\bbudget(ing)?\b"],
    "Accounting": [r"\baccounting\b"],
    "VBA": [r"\bvba\b"],
    "Financial Analysis": [r"\bfinancial analysis\b"],
    "GAAP": [r"\bgaap\b"],
    "Bloomberg Terminal": [r"\bbloomberg\b"],
    "Risk Management": [r"\brisk management\b"],
    "Variance Analysis": [r"\bvariance analysis\b"],
    "Financial Reporting": [r"\bfinancial reporting\b"],

    # --- QA / testing ---
    "Test Automation": [r"\btest automation\b", r"\bautomated testing\b"],
    "Selenium": [r"\bselenium\b"],
    "Manual Testing": [r"\bmanual testing\b"],

    # --- Marketing ---
    "SEO": [r"\bseo\b", r"\bsearch engine optimi[sz]ation\b"],
    "SEM": [r"\bsem\b", r"\bsearch engine marketing\b"],
    "Google Analytics": [r"\bgoogle analytics\b"],
    "Content Marketing": [r"\bcontent marketing\b"],
    "Email Marketing": [r"\bemail marketing\b"],
    "Social Media Marketing": [r"\bsocial media marketing\b"],
    "PPC/Paid Ads": [r"\bppc\b", r"\bpaid ads\b", r"\bpaid advertising\b", r"\bgoogle ads\b"],
    "HubSpot": [r"\bhubspot\b"],
    "Salesforce": [r"\bsalesforce\b"],
    "CRM": [r"\bcrm\b"],
    "Brand Strategy": [r"\bbrand strategy\b"],

    # --- Sales ---
    "Negotiation": [r"\bnegotiation\b"],
    "Lead Generation": [r"\blead generation\b"],
    "Cold Calling": [r"\bcold call(ing)?\b"],
    "Sales Pipeline Management": [r"\bsales pipeline\b", r"\bpipeline management\b"],

    # --- HR ---
    "Recruitment": [r"\brecruit(ment|ing)?\b"],
    "Talent Acquisition": [r"\btalent acquisition\b"],
    "Onboarding": [r"\bonboarding\b"],
    "HRIS": [r"\bhris\b"],
    "Employee Relations": [r"\bemployee relations\b"],
    "Performance Management": [r"\bperformance management\b"],
    "Payroll": [r"\bpayroll\b"],

    # --- Operations / supply chain ---
    "Supply Chain Management": [r"\bsupply chain\b"],
    "Inventory Management": [r"\binventory management\b"],
    "Logistics": [r"\blogistics\b"],
    "Process Improvement": [r"\bprocess improvement\b"],
    "Six Sigma": [r"\bsix sigma\b"],
    "Vendor Management": [r"\bvendor management\b"],

    # --- Project management ---
    "Project Management": [r"\bproject management\b"],
    "PMP": [r"\bpmp\b"],
    "Jira": [r"\bjira\b"],
    "Gantt Charts": [r"\bgantt\b"],
    "Risk Assessment": [r"\brisk assessment\b"],

    # --- Cybersecurity ---
    "Cybersecurity": [r"\bcyber\s*security\b", r"\binformation security\b"],
    "Network Security": [r"\bnetwork security\b"],
    "Penetration Testing": [r"\bpenetration testing\b", r"\bpen testing\b"],
    "Firewall": [r"\bfirewall\b"],
    "SIEM": [r"\bsiem\b"],

    # --- Mobile development ---
    "Swift": [r"\bswift\b"],
    "Kotlin": [r"\bkotlin\b"],
    "React Native": [r"\breact native\b"],
    "Flutter": [r"\bflutter\b"],
    "Android Development": [r"\bandroid development\b", r"\bandroid sdk\b"],
    "iOS Development": [r"\bios development\b"],

    # --- Networking / IT support ---
    "Networking": [r"\bnetworking\b", r"\btcp/?ip\b"],
    "CCNA": [r"\bccna\b"],
    "IT Support": [r"\bit support\b", r"\bhelp\s*desk\b"],

    # --- Soft / general ---
    "Communication": [r"\bcommunication\b"],
    "Leadership": [r"\bleadership\b"],
    "Stakeholder Management": [r"\bstakeholder management\b"],
}


def extract_skills(text: str) -> list[str]:
    """Find canonical skill names mentioned in a block of text."""
    if not isinstance(text, str):
        return []
    text_lower = text.lower()
    found = []
    for skill, patterns in SKILL_TAXONOMY.items():
        for pattern in patterns:
            import re
            if re.search(pattern, text_lower):
                found.append(skill)
                break
    return sorted(found)
