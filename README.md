# Amrapali University - Total Quality Inventory Management System (TQM Portal)

[![TQM Quality Goal](https://img.shields.io/badge/Quality%20Goal-Q14%20Improve%20Navigation-0b3d91.svg)](https://student.amrapali.ac.in)
[![Course](https://img.shields.io/badge/Course-BBAT104%20TQM-00a6d6.svg)](https://student.amrapali.ac.in)
[![Compliance](https://img.shields.io/badge/Standard-ISO%209001%20Compliant-16a34a.svg)](https://student.amrapali.ac.in)
[![Status](https://img.shields.io/badge/Status-100%25%20Verified%20(5%2F5%20Targets)-success.svg)](https://student.amrapali.ac.in)

> **Official Student & Course Information**  
> **Student Name:** Ritik Kumar  
> **University Roll No.:** 2520301005  
> **Class Serial No.:** 136  
> **Programme:** Bachelor of Technology in Computer Science & Engineering (B.Tech CSE)  
> **Semester / Section:** 3rd Year, 5th Semester, Section C  
> **Academic Session:** 2026-27  
> **Subject Code & Title:** BBAT104: Fundamental of Total Quality Management  
> **Institution:** Amrapali University / Group of Institutes, Haldwani (Nainital), Uttarakhand  
> **Student Portal Design Alignment:** [student.amrapali.ac.in](https://student.amrapali.ac.in)  
> **Assigned Quality Goal:** **Q14 - Improve Navigation**

---

## 🏛️ Amrapali Student Portal Design Alignment

This project has been transformed from a desktop prototype into an **enterprise-ready, full-stack web application** designed specifically using the branding, layout, color tokens, and navigation paradigms of the official **Amrapali University Student Portal** ([student.amrapali.ac.in](https://student.amrapali.ac.in)):

* **Primary Palette:** Amrapali Deep Royal Navy (`#0b3d91`, hover `#061f4a`)
* **Secondary Accent:** Amrapali Cyan / Bright Blue (`#00a6d6`, hover `#0288d1`)
* **Background & Cards:** Soft tinted institutional canvas (`#f5f9ff`) with crisp white elevated surfaces (`#ffffff`) and subtle blue border accents (`#dbe7f3`)
* **Typography:** Modern Google Fonts (`Roboto`, `Inter`, `JetBrains Mono`)
* **Institutional Masthead:** Official Amrapali University Crest (`amrapali_circle.jpg`) and brand wordmark (`amrapali_logo.png`)
* **Student Metadata Badge:** Live session indicator displaying Ritik Kumar, Roll 2520301005, B.Tech CSE 5th Sem, Sec C, S.No: 136

---

## 🚀 Quick Start Guide

### 1. Prerequisites
Python 3.10+ (Tested on Python 3.14).

### 2. Installation
```bash
# Clone or navigate into the project folder
cd "Inventory_TQM_Q14"

# (Optional) Activate virtual environment
source .venv/bin/activate   # On Mac/Linux
# or .venv\Scripts\activate # On Windows

# Install required dependencies
pip install -r requirements.txt
```

### 3. Launch the Web Application
```bash
python run.py
# Or explicitly:
python web_app.py
```
Then open your web browser and navigate to:
👉 **[http://127.0.0.1:5001/](http://127.0.0.1:5001/)**

### 🔐 Genuine Registered Accounts & Authentication Options

The system implements strict identity and role-based access control. Only genuine registered accounts can sign in (random/unregistered emails are rejected):

| Role | User ID / Login ID | Password | Registered Gmail Address | Access Scope |
|:---|:---|:---|:---|:---|
| 👑 **Administrator** | `admin` | `admin123` | `admin@amrapali.ac.in` | **Full Institutional Access:** Catalog management, Vendor ratings, Lot inspections, FMEA/PDCA, ISO 9001 audit trails. |
| 🎓 **Student Member** | `ritik`<br>*(or `ritikkumarhempur5`)* | `ritik123` | `ritikkumarhempur5@gmail.com`<br>`ritikkumar2520301005@gmail.com` | **Quality Operations Access:** Ritik Kumar (Roll: 2520301005). Stock IN/OUT, Quality inspection dossiers, TQM 7 QC tools, EOQ & ABC calculators. |
| 👤 **Store Member** | `member` | `member123` | `member@amrapali.ac.in` | **Standard Operator Access:** Catalog browsing, inventory movements, and inspection verification. |

#### Two Ways to Log In for Every Registered Account:
1. **Direct Login (ID & Password):** Enter your User ID (or registered Gmail) and Password on the login page.
2. **Google Sign-In ("Continue with Google"):** Click the Google button, enter your registered Gmail address, and authenticate. Unregistered Gmail IDs are rejected to ensure only authorized users access the system.

### 4. Alternative Modes
```bash
# Launch the web portal on a custom port
python run.py --web --port 8080

# Launch the legacy desktop Tkinter GUI
python run.py --gui
```

---

## 📊 Complete Feature Architecture

### 1. Core Inventory Modules
* **TQM Command Dashboard (`/`):** 6 live KPI cards (Active Products, Stock Units, Low Stock Alerts, Verified Suppliers, Total Portfolio Valuation, Quality Pass Rate), visual category doughnut chart, mini Pareto curve, and real-time activity ledger.
* **Product Catalog Master (`/products`):** Full CRUD for inventory items with unique SKU enforcement, reorder thresholds, dynamic stock status badges (Healthy, Low Stock, Out of Stock), live search filter, and CSV export.
* **Stock In / Out Movement Ledger (`/stock`):** Real-time tracking of inward receipts and outward issues with balance validation preventing negative inventory, transaction note logging, and ISO 9001 traceability.
* **Suppliers & Vendor Quality Ratings (`/suppliers`):** Supplier directory with VQR scorecards rating Quality Compliance (%), On-Time Delivery (%), and composite grades (A+, A, B, C).

### 2. TQM 7 QC Tools & Statistical Quality Control (`/tqm`)
* **Tool 1: Live Pareto 80/20 Analysis:** Dual-axis interactive chart (Chart.js) plotting defect frequencies against a cumulative percentage curve with the 80% cutoff line. Identifies the "vital few" root causes versus the "useful many".
* **Tool 2: Ishikawa (Fishbone) 6M Cause-and-Effect:** Interactive 6M taxonomy (Man, Machine, Method, Material, Measurement, Milieu) diagnosing root causes of inventory discrepancies.
* **Tool 3: FMEA & Interactive RPN Risk Calculator:** Failure Mode and Effects Analysis matrix with a real-time slider calculating Risk Priority Numbers ($RPN = \text{Severity} \times \text{Occurrence} \times \text{Detection}$) and dynamic risk badges (Critical $\ge 150$, High $100-149$, Moderate $60-99$, Low $<60$).
* **Tool 4: Deming PDCA Cycle (Kaizen):** Structured 4-phase continuous improvement tracker across Plan, Do, Check, and Act.
* **Tool 5: CTQ Tree & SIPOC Process Map:** Critical-to-Quality hierarchy mapping customer needs to measurable parameters, plus Suppliers-Inputs-Process-Outputs-Customers flow.

### 3. Industry Operations Research & Supply Chain Calculators (`/calculators`)
* **Wilson's Economic Order Quantity (EOQ):**
  $$\text{EOQ} = \sqrt{\frac{2 \times D \times S}{H}}$$
  Calculates optimal order batch size, orders per year, cycle days, annual ordering cost, holding cost, Safety Stock ($SS$), and Reorder Point ($ROP$).
* **ABC Inventory Stratification:** Automatically segments products by invested capital ($Quantity \times Unit Price$) into Class A (top 70%), Class B (next 20%), and Class C (bottom 10%) with control policies.

### 4. Incoming Quality Inspection (GRN QC) (`/inspections`)
* Quality inspection at the Goods Receipt Note stage.
* Logs lot numbers, sample size, defect counts, defect categories, and disposition status (**PASSED**, **QUARANTINE**, **REJECTED**).
* Calculates lot defect rate and tracks Acceptance Quality Limit (AQL) adherence.

### 5. Quality Reports & ISO 9001 Audit Trail (`/reports`)
* Real-time Low-Stock Exception Report with one-click reorder triggers.
* Immutable ISO 9001 Audit Trail capturing User, Action, Subsystem, Details, and Timestamps.
* Application Exception and Error Diagnostic Log.
* Print-optimized layout (`window.print()`) for hardcopy submission.

### 6. Academic Viva & Syllabus Guide (`/viva-guide`)
* Top 8 high-yield viva examination questions and answers.
* W. Edwards Deming's 14 Quality Principles mapped to software engineering.
* Six Sigma DMAIC framework summary.

---

## ⌨️ Quality Goal Q14 Navigation Rubric Compliance

Teacher Quality Goal **Q14 - Improve Navigation** requires five measurable features. All five have been implemented and verified:

| Target ID | Requirement | Implementation in Web App | Status |
|:---|:---|:---|:---:|
| **T1** | **$\le 2$ Clicks Access** | Universal sticky top navbar allows direct 1-click access to all modules from anywhere. | ✅ **PASSED (1-Click)** |
| **T2** | **Universal Breadcrumbs** | Hierarchical clickable breadcrumbs displayed on 100% of pages. | ✅ **PASSED** |
| **T3** | **Top Navigation Bar** | Persistent, responsive Amrapali-branded navbar with active indicators. | ✅ **PASSED** |
| **T4** | **Dedicated Home Button** | Amrapali Crest, wordmark, and dedicated Home link return to dashboard. | ✅ **PASSED** |
| **T5** | **Keyboard Shortcuts** | Full hotkey support (`Alt+H`, `Alt+P`, `Alt+M`, `Alt+S`, `Alt+I`, `Alt+Q`, `Alt+C`, `Alt+R`, `Alt+V`, `F1`). | ✅ **PASSED** |

### Hotkey Accelerator Shortcuts:
* `Alt + H` : Return to Dashboard (Home)
* `Alt + P` : Products Catalog
* `Alt + M` : Stock IN / OUT Movements
* `Alt + S` : Suppliers Directory & VQR
* `Alt + I` : Quality Inspections (GRN)
* `Alt + Q` : TQM 7 QC Tools & Pareto Analysis
* `Alt + C` : Industry Calculators (EOQ & ABC)
* `Alt + R` : Quality Reports & ISO 9001 Audit
* `Alt + V` : Academic Viva & Syllabus Guide
* `F1` or `?` : Open Keyboard Shortcuts Modal
* `Esc` : Dismiss Active Modal

---

## 🧪 Verification & Automated Testing

Run the automated integration test suite:
```bash
python -c "
import tests.test_smoke as t1
import tests.test_web_routes as t2

t1.test_database_schema()
t2.test_web_routes_smoke()
t2.test_q14_navigation_compliance()
t2.test_abc_analysis_calculation()
t2.test_eoq_calculation()
print('All tests passed!')
"
```

---

## 📁 Repository Structure

```
Inventory_TQM_Q14/
├── run.py                 # Primary entry point (Default: Web App; --gui for desktop)
├── web_app.py             # Flask Web Application & REST API
├── main.py                # Legacy Tkinter entry point
├── requirements.txt       # Dependencies (Flask, Pandas, Matplotlib)
├── README.md              # Project documentation & viva guide
├── config/
│   └── settings.py        # Configuration and Q14 quality targets
├── database/
│   ├── db.py              # SQLite connection helper
│   ├── schema.py          # Database schema (Products, Inspections, FMEA, PDCA, Audits)
│   └── compat.py          # Compatibility layer
├── models/
│   ├── product.py         # Product data classes
│   ├── stock_movement.py  # Stock movement structures
│   └── supplier.py        # Supplier structures
├── services/
│   ├── product_service.py   # Product CRUD service
│   ├── inventory_service.py # Stock IN/OUT service
│   ├── supplier_service.py  # Supplier and VQR service
│   ├── report_service.py    # Metrics and audit service
│   └── tqm_service.py       # TQM 7 QC, EOQ, ABC, and FMEA service
├── static/
│   ├── css/
│   │   └── amrapali-theme.css # Amrapali Student Portal design system CSS
│   ├── js/
│   │   └── app.js             # Hotkeys, Chart.js, calculators, modals JS
│   └── img/
│       ├── amrapali_logo.png   # Amrapali brand wordmark
│       └── amrapali_circle.jpg # Amrapali University Crest
├── templates/
│   ├── base.html          # Amrapali portal masthead, nav, breadcrumbs, modal
│   ├── dashboard.html     # KPI tiles, charts, live alerts
│   ├── products.html      # Product master catalog & modals
│   ├── stock.html         # Stock IN/OUT ledger & validation
│   ├── suppliers.html     # Supplier cards & VQR scores
│   ├── inspections.html   # GRN QC lot inspections
│   ├── tqm.html           # 7 QC Tools (Pareto, Fishbone, FMEA, PDCA, CTQ)
│   ├── calculators.html   # Wilson EOQ & Pareto ABC stratification
│   ├── reports.html       # Low-stock dossier & ISO 9001 audit
│   └── viva_guide.html    # Academic viva & Deming principles
├── artifacts/             # Course artefacts (FMEA CSV, Defect Log CSV, PDCA CSV, Diagrams)
├── docs/                  # Project report & SRS documentation
└── tests/
    ├── test_smoke.py      # Database schema smoke test
    └── test_web_routes.py # Full web route and algorithm tests
```

---

## 🎓 Academic Submission Note
Submitted in partial fulfillment of the requirements for **B.Tech CSE 5th Semester** in **Fundamental of Total Quality Management (BBAT104)** at **Amrapali University, Haldwani**, Academic Session 2026-27.
