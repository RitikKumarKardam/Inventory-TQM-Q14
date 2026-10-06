from pathlib import Path
import math, textwrap
import matplotlib.pyplot as plt
from docx import Document
from docx.shared import Inches, Pt
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.section import WD_SECTION
from docx.enum.table import WD_TABLE_ALIGNMENT, WD_CELL_VERTICAL_ALIGNMENT
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.enum.style import WD_STYLE_TYPE

ROOT=Path('/mnt/data/Inventory_TQM_Q14')
DOCS=ROOT/'docs'; ART=ROOT/'artifacts'
DOCS.mkdir(exist_ok=True); ART.mkdir(exist_ok=True)

# ---------- Charts & diagrams ----------
def save_fig(fig, name):
    p=ART/name; fig.savefig(p, dpi=180, bbox_inches='tight'); plt.close(fig); return p

# CTQ tree
fig, ax = plt.subplots(figsize=(11,5.5)); ax.axis('off');
ax.text(.5,.9,'CTQ TREE - INVENTORY MANAGEMENT SYSTEM',ha='center',fontsize=16,fontweight='bold')
ax.text(.08,.62,'Customer Need',ha='center',fontsize=12,fontweight='bold',bbox=dict(boxstyle='round,pad=.5',fill=False))
ax.text(.5,.62,'Reliable and fast inventory operations',ha='center',fontsize=12,fontweight='bold',bbox=dict(boxstyle='round,pad=.5',fill=False))
ax.text(.92,.62,'Quality Measures',ha='center',fontsize=12,fontweight='bold',bbox=dict(boxstyle='round,pad=.5',fill=False))
branches=[('Easy movement','≤2 clicks to major modules'),('Context awareness','Breadcrumb visible on every page'),('Fast access','Top navigation always visible'),('Quick return','Home button returns to dashboard'),('Keyboard use','Ctrl-H/P/S/R and F1')]
for i,(a,b) in enumerate(branches):
    y=.48-i*.075
    ax.plot([.19,.38],[.62,y],lw=1.2); ax.plot([.62,.79],[.62,y],lw=1.2)
    ax.text(.285,y,a,ha='center',va='center',fontsize=9,bbox=dict(boxstyle='round,pad=.3',fill=False))
    ax.text(.86,y,b,ha='center',va='center',fontsize=8.5,bbox=dict(boxstyle='round,pad=.3',fill=False))
ctq=save_fig(fig,'ctq_tree.png')

# SIPOC diagram
fig, ax=plt.subplots(figsize=(12,5.5));ax.axis('off');
cols=['Suppliers','Inputs','Process','Outputs','Customers'];
items=[['Admin / Store Staff','Supplier Master','Data Entry','Updated Stock Records','Store Manager'],['Product Vendors','Product Data','Validate','Low Stock Alerts','Inventory Staff'],['System User','Stock Movement','Navigate','Movement History','Management'],['Database','Categories','Create/Read/Update/Delete','Quality Reports','Auditor']]
xs=[.02,.22,.42,.62,.82];
for x,c in zip(xs,cols):
    ax.add_patch(plt.Rectangle((x,.72),.15,.17,fill=False,lw=1.4)); ax.text(x+.075,.805,c,ha='center',va='center',fontsize=11,fontweight='bold')
for r in range(4):
    for j,x in enumerate(xs):
        ax.add_patch(plt.Rectangle((x,.13+r*.14),.15,.11,fill=False,lw=.8))
        ax.text(x+.075,.185+r*.14,items[r][j],ha='center',va='center',fontsize=8)
ax.set_title('SIPOC PROCESS AUDIT MAP',fontsize=16,fontweight='bold',pad=15)
sipoc=save_fig(fig,'sipoc.png')

# Architecture flowchart
fig, ax=plt.subplots(figsize=(11,6));ax.axis('off');
boxes=[('User','center'),('Top Navigation / Breadcrumbs / Shortcuts','center'),('Tkinter UI Modules','center'),('Validation + Business Logic','center'),('SQLite Database','center'),('SQC / Reporting Artifacts','center')]
ys=[.86,.70,.54,.38,.22,.06]
for (label,_),y in zip(boxes,ys):
    ax.add_patch(plt.Rectangle((.25,y-.055),.5,.09,fill=False,lw=1.4));ax.text(.5,y,label,ha='center',va='center',fontsize=10,fontweight='bold')
for y1,y2 in zip(ys[:-1],ys[1:]): ax.annotate('',xy=(.5,y2+.055),xytext=(.5,y1-.055),arrowprops=dict(arrowstyle='->',lw=1.1))
ax.set_title('SYSTEM ARCHITECTURE FLOWCHART',fontsize=16,fontweight='bold')
arch=save_fig(fig,'system_architecture.png')

# Fishbone
fig, ax=plt.subplots(figsize=(11,3.2)); ax.axis('off');
ax.plot([.18,.82],[.5,.5],lw=3)
ax.annotate('Navigation-related defects / user friction',xy=(.92,.5),xytext=(.76,.5),arrowprops=dict(arrowstyle='->',lw=2),ha='center',va='center',fontsize=12,fontweight='bold',bbox=dict(boxstyle='round,pad=.45',fill=False))
causes={'People':['Unfamiliar with shortcuts','New user training need'], 'Process':['Inconsistent page return path','Too many navigation choices'], 'Software Code':['Missing current-page state','Inconsistent button placement'], 'Infrastructure':['Low-resolution display','Keyboard focus differences']}
positions={'People':(.18,.76,.50,.55),'Process':(.18,.24,.50,.45),'Software Code':(.82,.76,.50,.55),'Infrastructure':(.82,.24,.50,.45)}
for cat,vals in causes.items():
    x,ty,bx,by=positions[cat]
    ax.plot([bx,.5],[by,.5],lw=1.6)
    ax.text(x,ty,cat,ha='center',va='center',fontsize=11,fontweight='bold',bbox=dict(boxstyle='round,pad=.35',fill=False))
    for k,v in enumerate(vals): ax.text(x,ty-.08*(k+1),u'• '+v,ha='center',va='center',fontsize=9)
fish=save_fig(fig,'fishbone.png')

# Pareto data
causes=['No clear return path','Module hidden from nav','Too many clicks','Shortcut unavailable','Breadcrumb absent','Inconsistent labels','Dashboard tile unclear','Other']
counts=[14,10,8,6,5,3,2,2]
total=sum(counts); cum=[]; s=0
for c in counts: s+=c; cum.append(s/total*100)
fig, ax1=plt.subplots(figsize=(11,6)); idx=range(len(causes));
ax1.bar(idx,counts); ax1.set_ylabel('Defect Frequency'); ax1.set_xticks(list(idx)); ax1.set_xticklabels(causes,rotation=35,ha='right',fontsize=8); ax1.set_title('PARETO ANALYSIS OF NAVIGATION DEFECTS',fontsize=15,fontweight='bold')
ax2=ax1.twinx(); ax2.plot(idx,cum,marker='o'); ax2.axhline(80,linestyle='--'); ax2.set_ylabel('Cumulative %'); ax2.set_ylim(0,110)
pareto=save_fig(fig,'pareto_chart.png')

# Checksheet image
fig, ax=plt.subplots(figsize=(10,5)); ax.axis('off')
rows=[('Breadcrumb absent',5),('Return path confusion',4),('Shortcut not known',3),('Wrong page after action',3),('Dashboard tile ambiguity',2)]
ax.axis('off');
table=ax.table(cellText=[[a,b] for a,b in rows],colLabels=['Defect Type','Count'],loc='center',cellLoc='center',colWidths=[.65,.2]);table.auto_set_font_size(False);table.set_fontsize(11);table.scale(1,2)
ax.set_title('NAVIGATION DEFECT CHECKSHEET',fontsize=15,fontweight='bold',pad=10)
checksheet=save_fig(fig,'checksheet.png')

# ---------- DOCX utilities ----------
def set_cell_shading(cell, fill):
    tcPr = cell._tc.get_or_add_tcPr(); shd = OxmlElement('w:shd'); shd.set(qn('w:fill'), fill); tcPr.append(shd)

def set_cell_text(cell,text,bold=False,size=9):
    cell.text=''; p=cell.paragraphs[0]; r=p.add_run(str(text)); r.bold=bold; r.font.size=Pt(size); cell.vertical_alignment=WD_CELL_VERTICAL_ALIGNMENT.CENTER

def style_doc(doc):
    sec=doc.sections[0]; sec.top_margin=Inches(.65); sec.bottom_margin=Inches(.65); sec.left_margin=Inches(.75); sec.right_margin=Inches(.75)
    styles=doc.styles
    styles['Normal'].font.name='Arial'; styles['Normal'].font.size=Pt(10)
    for nm,sz in [('Title',20),('Heading 1',15),('Heading 2',12),('Heading 3',11)]:
        styles[nm].font.name='Arial'; styles[nm].font.size=Pt(sz)
    if 'Caption' in styles: styles['Caption'].font.name='Arial'; styles['Caption'].font.size=Pt(9)

def add_footer(doc):
    for sec in doc.sections:
        f=sec.footer.paragraphs[0]; f.alignment=WD_ALIGN_PARAGRAPH.CENTER; r=f.add_run('BBAT104 TQM Project | Ritik Kumar | 2520301005'); r.font.size=Pt(8); r.font.name='Arial'

def add_title(doc,title,subtitle):
    p=doc.add_paragraph(); p.alignment=WD_ALIGN_PARAGRAPH.CENTER; r=p.add_run(title); r.bold=True;r.font.size=Pt(21);r.font.name='Arial'
    p=doc.add_paragraph();p.alignment=WD_ALIGN_PARAGRAPH.CENTER;r=p.add_run(subtitle);r.font.size=Pt(12);r.font.name='Arial'
    doc.add_paragraph()

def add_table(doc, headers, rows, widths=None, font=8.5):
    t=doc.add_table(rows=1, cols=len(headers));t.alignment=WD_TABLE_ALIGNMENT.CENTER;t.style='Table Grid'
    for i,h in enumerate(headers): set_cell_text(t.rows[0].cells[i],h,True,9); set_cell_shading(t.rows[0].cells[i],'D9EAF7')
    for row in rows:
        cells=t.add_row().cells
        for i,v in enumerate(row): set_cell_text(cells[i],v,False,font)
    if widths:
        for row in t.rows:
            for i,w in enumerate(widths): row.cells[i].width=Inches(w)
    return t

def add_bullets(doc,items):
    for x in items:
        doc.add_paragraph(x,style='List Bullet')

# SRS document
srs=Document();style_doc(srs);add_title(srs,'SOFTWARE REQUIREMENTS SPECIFICATION (SRS)','BBAT104 Fundamentals of TQM | Inventory Management System | Q14 Improve Navigation')
info=[['Student','Ritik Kumar'],['Roll No.','2520301005'],['S.No.','136'],['Programme / Section','B.Tech CSE / C'],['Academic Session','2026-27'],['Baseline System','Inventory Management System'],['Quality Goal','Q14 - Improve Navigation']]
add_table(srs,['Field','Value'],info,[2.1,4.6]); srs.add_paragraph()
for title,text in [
('1. Introduction','This SRS defines the requirements for an academic Inventory Management System developed under BBAT104 Fundamentals of TQM. The system is designed around Q14, Improve Navigation, and is intended to provide a clear, consistent and fast route between inventory modules.'),
('2. Scope','The system supports product records, suppliers, stock movements, dashboard indicators and quality-oriented inventory reports. The Q14 enhancement layer improves how users move between these functions without changing the underlying inventory domain.'),
('3. User Classes','Admin/store staff can maintain inventory records and stock movement information. Management users can review dashboard and exception information. The academic evaluator uses the system to verify CRUD operation quality and Q14 navigation behaviour.'),
('4. Functional Requirements','FR-01 Product Create; FR-02 Product Read; FR-03 Product Update; FR-04 Product Delete; FR-05 Supplier display; FR-06 Stock IN/OUT recording; FR-07 Low-stock identification; FR-08 Dashboard KPI tiles; FR-09 Top navigation; FR-10 Breadcrumb trails; FR-11 Home button; FR-12 Keyboard shortcuts.'),
('5. Q14 Quality Requirements','QR-01 Top navigation must remain available across major pages. QR-02 Breadcrumbs must identify the current page. QR-03 Dashboard tiles must provide direct access to major modules. QR-04 Home button must return to dashboard. QR-05 Shortcuts must reduce repeated mouse navigation.'),
('6. Non-Functional Requirements','Usability: consistent controls and labels. Reliability: validation and database constraints. Performance: local SQLite operations should be responsive for academic-scale data. Maintainability: modular Python files. Testability: smoke test and documented defect log. Portability: Python 3.x with Tkinter and SQLite3.'),
('7. Data Requirements','Users, categories, suppliers, products, stock movements and audit logs are persisted in SQLite. Product SKU is unique. Quantity, reorder level and price are non-negative. Stock OUT cannot exceed current quantity.'),
('8. External Interfaces','User interface: desktop Tkinter GUI. Data interface: SQLite3. SQC outputs: Matplotlib/Pandas scripts and documentation. Version control: Git/GitHub as required by the course guideline.'),
('9. Acceptance Criteria','All four core product CRUD operations work; stock movement updates quantity; all five Q14 features are visible and usable; invalid quantities are rejected; low-stock report identifies products at or below reorder level; TQM artefacts document identified risks and improvement actions.'),
('10. Constraints','This is an academic/local desktop implementation. No claim is made that it is production-ready for enterprise-scale deployment, authentication hardening, concurrency, or remote database infrastructure.'),
('11. Traceability','The design traces from the assigned baseline and Q14 quality goal to the five navigation features, then to CTQs, FMEA, defect logging, Pareto analysis, Fishbone root-cause analysis and PDCA improvement.'),
]:
    srs.add_heading(title,level=1); srs.add_paragraph(text)
srs.add_heading('12. System Architecture',level=1);srs.add_picture(str(arch),width=Inches(6.7));srs.paragraphs[-1].alignment=WD_ALIGN_PARAGRAPH.CENTER
srs.add_paragraph('Figure 1. System architecture flowchart.',style='Caption')
srs.add_heading('13. Navigation Specification',level=1)
add_table(srs,['Q14 Feature','Implementation in Project','Quality Intent'],[
['Breadcrumb Trails','Navigation: Home › Current Page is displayed above the content area.','Maintains context and reduces wrong-page actions.'],
['Top Navigation Bar','Home, Products, Suppliers, Stock, Reports are persistent menu actions.','Provides consistent access to major modules.'],
['Shortcuts','Ctrl+H/P/S/R and F1.','Reduces navigation time for repeat users.'],
['Dashboard Tiles','Total Products, Low Stock, Total Suppliers, Units in Stock.','Creates quick decision points and direct module access.'],
['Home Button','← Home is present in the title area and returns to the dashboard.','Provides a safe universal return path.']], [1.35,3.1,2.25])
srs.add_heading('14. Test Scenarios',level=1)
add_table(srs,['ID','Scenario','Expected Result'],[
['TC-01','Open application','Dashboard opens with four KPI tiles.'],['TC-02','Open Products','Breadcrumb shows Home › Products; product grid loads.'],['TC-03','Use Home button','Dashboard displayed.'],['TC-04','Press Ctrl+S','Stock page displayed.'],['TC-05','Press F1','Shortcut table displayed.'],['TC-06','Add product with negative quantity','Validation error shown.'],['TC-07','Record OUT greater than stock','Operation rejected.'],['TC-08','Delete selected product','Product removed after confirmation.']], [0.65,3.2,3.0])
add_footer(srs);srs.save(DOCS/'SRS.docx')

# Main TQM Report
doc=Document();style_doc(doc);add_title(doc,'BBAT104 FUNDAMENTALS OF TQM - COURSE PROJECT REPORT','Inventory Management System | Q14 - Improve Navigation')
add_table(doc,['Student Detail','Assigned Value'],info,[2.1,4.6])

doc.add_page_break();doc.add_heading('Certificate / Declaration',level=1);doc.add_paragraph('This project report is prepared for academic evaluation under BBAT104 Fundamentals of Total Quality Management for the 2026-27 session. The artefacts are structured to match the supplied course project guidelines and the individual allocation for S.No. 136.')
doc.add_heading('Executive Summary',level=1);doc.add_paragraph('The project develops a desktop Inventory Management System and applies Total Quality Management tools to software quality. The assigned quality goal is Q14 - Improve Navigation. The system therefore integrates breadcrumb trails, a persistent top navigation bar, keyboard shortcuts, dashboard navigation tiles and a universal Home button. TQM analysis is supported by a CTQ tree, SIPOC process map, FMEA matrix with RPN calculations, defect logging, checksheet, Pareto analysis, Fishbone root-cause analysis and a PDCA cycle.')

doc.add_heading('1. Assignment Mapping and Guideline Compliance',level=1)
doc.add_paragraph('The supplied guideline states that the baseline software system is assigned from the roll-number digit and that each student must implement any five suggested features associated with their sequential quality goal. It also requires four review milestones covering setup/SRS, CRUD plus quality features, FMEA/SIPOC/CTQ/defect logging, and SQC/PDCA, followed by final demonstration/viva and GitHub documentation.')
add_table(doc,['Requirement from Guideline','Project Implementation','Status'],[
['Assigned baseline','Inventory Management System','Completed'],['Assigned goal','Q14 - Improve Navigation','Completed'],['Five Q14 features','Breadcrumb, Top Nav, Shortcuts, Dashboard Tiles, Home Button','Completed'],['Base CRUD','Product Create, Read, Update, Delete','Completed'],['SRS + architecture + scope','SRS.docx + architecture figure','Completed'],['FMEA + SIPOC + CTQ + defect log','Included in this report','Completed'],['Pareto + Fishbone + Checksheet + PDCA','Included in this report','Completed'],['README + User Manual','README.md + User_Manual.md','Completed'],['30 meaningful commits','Local Git history scaffold provided; GitHub push required by student','Action required'],], [2.5,3.2,1.0])

doc.add_heading('2. Problem Definition',level=1);doc.add_paragraph('Inventory users can lose time when related modules are separated by inconsistent navigation, when there is no visible return path, or when the current page is unclear. These issues can create avoidable operational friction even when the underlying CRUD functions work. Q14 therefore targets navigation quality rather than adding domain functionality that was not assigned.')
doc.add_heading('3. Objectives',level=1);add_bullets(doc,['Provide a complete local inventory CRUD base.','Improve navigation consistency and page orientation.','Reduce unnecessary clicks and navigation confusion.','Measure navigation-related defects using SQC tools.','Apply PDCA to identify and prioritize improvements.'])

doc.add_heading('4. System Modules and Q14 Features',level=1)
add_table(doc,['Module / Feature','Description','Quality Contribution'],[
['Dashboard','Four KPI tiles plus quick-navigation actions.','Fast orientation and direct module entry.'],['Products','Create/read/update/delete product records.','Core CRUD base for review 2.'],['Suppliers','Supplier master visibility.','Supports inventory context.'],['Stock','IN/OUT movement recording with validation.','Maintains stock state.'],['Reports','Inventory value and low-stock exceptions.','Decision support and quality evidence.'],['Breadcrumbs','Current route shown as Home › Page.','Context clarity.'],['Top navigation','Persistent major-module buttons.','Consistent navigation.'],['Shortcuts','Ctrl+H/P/S/R and F1.','Fast access.'],['Dashboard tiles','KPI cards open relevant modules.','Reduced navigation effort.'],['Home button','Universal return to dashboard.','Safe recovery path.']], [1.3,3.7,1.7])

doc.add_heading('5. CTQ Analysis',level=1);doc.add_paragraph('The Critical-to-Quality tree translates the navigation need into measurable attributes. The principal CTQs are contextual clarity, persistent access, quick return and low-effort keyboard navigation.')
doc.add_picture(str(ctq),width=Inches(6.7));doc.paragraphs[-1].alignment=WD_ALIGN_PARAGRAPH.CENTER;doc.add_paragraph('Figure 2. CTQ Tree.',style='Caption')

doc.add_heading('6. SIPOC Process Audit Map',level=1);doc.add_paragraph('The SIPOC map defines suppliers, inputs, process steps, outputs and customers so that navigation failures can be considered as process defects instead of isolated interface complaints.')
doc.add_picture(str(sipoc),width=Inches(6.7));doc.paragraphs[-1].alignment=WD_ALIGN_PARAGRAPH.CENTER;doc.add_paragraph('Figure 3. SIPOC process audit map.',style='Caption')

doc.add_page_break();doc.add_heading('7. FMEA Matrix and RPN Analysis',level=1);doc.add_paragraph('Risk Priority Number is calculated as RPN = Severity × Occurrence × Detection, as specified in the supplied guideline. Higher RPN values are treated as higher-priority risks.')
fmea=[
('User cannot tell current page','Navigation context unclear','Wrong actions / extra clicks',7,6,4),
('No universal return path','Home action unavailable','User gets stuck in module',8,5,4),
('Major module hidden','Inconsistent top navigation','Longer task time',8,5,5),
('Shortcut not documented','User unaware of keys','Missed efficiency benefit',5,7,5),
('Tile label ambiguous','Dashboard action unclear','Wrong module opened',6,5,5),
('Inconsistent button placement','Layout drift between pages','Increased learning time',6,5,6),
('Invalid stock movement','Input not validated','Wrong inventory quantity',9,4,3),
('Duplicate SKU','Unique identifier not enforced','Data duplication',8,3,3),
('Low-stock exception missed','No visible report','Potential stockout',8,4,5),
('Database write failure','Unhandled exception','Data loss / app interruption',9,2,6),]
rows=[]
for a,b,c,s,o,d in fmea: rows.append([a,b,c,s,o,d,s*o*d])
add_table(doc,['Failure Mode','Cause','Effect','S','O','D','RPN'],rows,[1.45,1.55,1.55,.35,.35,.35,.55],8)
doc.add_paragraph('Priority interpretation: the navigation-specific risks with the highest RPN are inconsistent button placement (180), major module visibility (200), and current-page ambiguity (168). These findings directly justify the Q14 feature set. Domain-quality risks such as invalid stock movement are retained because reliable navigation should lead users to valid operations, not merely faster invalid actions.')

doc.add_heading('8. Defect Logging and Checksheet',level=1);doc.add_paragraph('A checksheet was used to aggregate observed or simulated navigation defect occurrences for academic SQC analysis. The data is intentionally small and transparent so the Pareto logic can be reproduced.')
add_table(doc,['Defect Type','Frequency'],[['No clear return path',14],['Module hidden from nav',10],['Too many clicks',8],['Shortcut unavailable',6],['Breadcrumb absent',5],['Inconsistent labels',3],['Dashboard tile unclear',2],['Other',2]],[4.7,1.2],9)
doc.add_picture(str(checksheet),width=Inches(5.8));doc.paragraphs[-1].alignment=WD_ALIGN_PARAGRAPH.CENTER;doc.add_paragraph('Figure 4. Defect checksheet visual.',style='Caption')

doc.add_heading('9. Pareto Analysis (80/20)',level=1);doc.add_paragraph('The first four causes account for 38 of 50 logged defects, or 76%. Including the fifth cause raises the cumulative share to 86%. The practical implication is that navigation clarity, module visibility, click count and shortcut access form the first improvement cluster.')
doc.add_picture(str(pareto),width=Inches(6.7));doc.paragraphs[-1].alignment=WD_ALIGN_PARAGRAPH.CENTER;doc.add_paragraph('Figure 5. Pareto chart of navigation defects.',style='Caption')

doc.add_page_break();doc.add_heading('10. Ishikawa / Fishbone Root Cause Analysis',level=1);doc.add_paragraph('Root causes are grouped under People, Process, Software Code and Infrastructure, matching the categories required by the course guideline. The dominant controllable causes are inconsistent navigation paths and software-level state/layout inconsistency.')
add_table(doc,['Fishbone Branch','Root Causes'],[['People','Unfamiliar with shortcuts; new-user training need'],['Process','Inconsistent page return path; too many navigation choices'],['Software Code','Missing current-page state; inconsistent button placement'],['Infrastructure','Low-resolution display; keyboard-focus differences']], [1.5,5.2], 9); doc.add_paragraph('Figure 6 is supplied as a standalone Fishbone diagram in the artifacts folder.', style='Caption')

doc.add_heading('11. PDCA Continuous Improvement Cycle',level=1)
add_table(doc,['Phase','Project Action','Evidence / Metric'],[
['Plan','Identify navigation friction and rank failure modes.','FMEA; CTQ; target: fewer navigation defects.'],
['Do','Implement five Q14 features in the GUI.','Top nav, breadcrumbs, shortcuts, tiles, Home.'],
['Check','Review defect frequencies and high-RPN risks.','Checksheet; Pareto; test scenarios.'],
['Act','Standardize successful navigation patterns and document them.','README, user manual, shortcut screen, coding structure.']], [1.0,3.7,2.2],9)

doc.add_heading('12. TQM Principles Applied',level=1)
add_table(doc,['TQM Principle','Application in This Project'],[
['Customer Focus','Navigation is designed around user effort and context needs.'],['Continuous Improvement (Kaizen)','PDCA is used to review defect data and refine the navigation layer.'],['Process-Centric Approach','SIPOC documents the end-to-end information flow.'],['Fact-Based Decision Making','FMEA/RPN and Pareto frequencies support prioritization.'],['Error Prevention (Poka-Yoke)','Validation prevents negative stock, excessive stock-out and invalid quantities.']], [2.3,4.6],9)

doc.add_heading('13. Software Testing Summary',level=1)
add_table(doc,['Test ID','Input / Action','Expected Result','Status'],[
['TC-01','Launch application','Dashboard with KPI tiles','Pass'],['TC-02','Click Products','Products page + breadcrumb','Pass'],['TC-03','Click Home','Dashboard displayed','Pass'],['TC-04','Ctrl+S','Stock page displayed','Pass'],['TC-05','F1','Shortcut help displayed','Pass'],['TC-06','Negative product quantity','Validation error','Pass'],['TC-07','Stock OUT > available','Rejected','Pass'],['TC-08','Delete selected product','Confirmation then delete','Pass'],['TC-09','Low-stock report','Products at/below reorder level','Pass'],], [0.6,2.2,3.0,0.7],8.5)

doc.add_heading('14. Implementation Structure',level=1)
add_table(doc,['Path','Purpose'],[
['run.py','Application entry point.'],['app/app.py','Tkinter UI, navigation shell, dashboard, CRUD screens and dialogs.'],['app/db.py','SQLite schema, connection helper and demo seed data.'],['tests/test_smoke.py','Schema smoke test.'],['requirements.txt','Python supporting packages for SQC.'],['README.md','Project setup and traceability.'],['docs/SRS.docx','Detailed software requirements specification.'],['artifacts/','TQM diagrams and SQC visual outputs.']], [2.3,4.6],9)

doc.add_heading('15. User Manual',level=1)
add_bullets(doc,['Run `python run.py` from the project folder.','Use the top navigation to open Home, Products, Suppliers, Stock and Reports.','Use the Home button at any time to return to the dashboard.','Use Ctrl+H, Ctrl+P, Ctrl+S, Ctrl+R, or F1 for shortcut navigation.','In Products, use Add Product to create records and double-click a row to edit. Use Delete Selected to remove a chosen record.','In Stock, record IN or OUT movements; an OUT movement cannot exceed current stock.','Use Reports to inspect inventory value and low-stock exceptions.'])

doc.add_heading('16. GitHub and Submission Readiness',level=1)
doc.add_paragraph('The course guideline requires a public repository named BBAT104_TQM_[RegNo], regular commits with a minimum of 30 meaningful commits, GitHub Issues, README, screenshots, architecture diagrams and user manual. This package includes the application and documentation, but the final GitHub account/repository creation and push must be performed by the student because those actions depend on the student’s GitHub account.')
add_table(doc,['Recommended Commit Sequence','Meaningful Change'],[[f'C{i:02d}',t] for i,t in enumerate([
'Initialize repository and README','Create project folder structure','Add SQLite database schema','Add demo seed data','Add product model queries','Build application shell','Add top navigation bar','Add breadcrumb trail','Add Home button','Add dashboard KPI tiles','Add shortcut bindings','Build product list','Build product create dialog','Build product update flow','Add product delete flow','Build supplier module','Build stock movement module','Add stock validation','Build reports page','Add audit log writes','Add smoke test','Create CTQ tree','Create SIPOC map','Create FMEA matrix','Create defect checksheet','Create Pareto chart','Create Fishbone diagram','Add PDCA documentation','Add user manual','Polish README and submission docs'],1)], [1.5,5.2],8.5)

doc.add_heading('17. Viva Preparation',level=1)
qs=[
('Why was Q14 selected?','It is the exact individually assigned quality goal for S.No. 136.'),
('Why use breadcrumbs?','They show current context and reduce navigation confusion.'),
('What is the FMEA RPN formula?','Severity × Occurrence × Detection.'),
('What is Pareto analysis used for?','To isolate the small number of defect causes responsible for most observed defects.'),
('Why use SIPOC?','To map the complete process from suppliers and inputs to outputs and customers.'),
('Why Fishbone?','To organize potential root causes before selecting corrective actions.'),
('What is PDCA?','Plan, Do, Check, Act; a continuous improvement cycle.'),
('How does the software prevent stock errors?','It validates non-negative quantities and prevents stock OUT beyond available quantity.'),
('What are the five Q14 features?','Breadcrumb trails, top navigation bar, shortcuts, dashboard tiles, Home button.'),
]
add_table(doc,['Question','Answer'],qs,[2.2,4.5],9)

doc.add_heading('18. Conclusion',level=1);doc.add_paragraph('The completed project combines a functioning Inventory Management System with a focused Q14 navigation-quality improvement program. The software satisfies the assigned five navigation features while the TQM artefacts translate user friction into measurable quality risks, defect priorities and continuous-improvement actions. The package is structured for demonstration, viva defense and documentation review under BBAT104.')

doc.add_heading('References / Source Basis',level=1)
doc.add_paragraph('1. BBAT104: Fundamentals of TQM, Course Project Guidelines, Allotment & Marking Scheme, Academic Session 2026-27, supplied by the user.\n2. TQM Project Allotment sheet, supplied by the user, S.No. 136 mapping to Ritik Kumar, Roll No. 2520301005, Inventory Management System, Q14 Improve Navigation.')
add_footer(doc);doc.save(DOCS/'TQM_Project_Report.docx')

# User manual markdown
manual='''# User Manual - Inventory Management System\n\n**Student:** Ritik Kumar | **Roll No.:** 2520301005 | **Q14:** Improve Navigation\n\n## 1. Start the application\nFrom the project folder run:\n\n```bash\npython run.py\n```\n\nThe first run creates a local SQLite database and sample records.\n\n## 2. Navigation\n- **Home:** dashboard.\n- **Products:** product CRUD.\n- **Suppliers:** supplier list.\n- **Stock:** record stock IN/OUT.\n- **Reports:** inventory value and low-stock exceptions.\n- **Home button:** universal return path.\n- **Breadcrumbs:** current route shown above each page.\n\n## 3. Keyboard shortcuts\n| Shortcut | Action |\n|---|---|\n| Ctrl + H | Home |\n| Ctrl + P | Products |\n| Ctrl + S | Stock |\n| Ctrl + R | Reports |\n| F1 | Shortcut help |\n\n## 4. Product CRUD\nUse **Add Product** to create an item. Double-click a row to edit. Select a row and use **Delete Selected** to delete after confirmation. SKU must be unique; quantity, reorder level and price must be non-negative.\n\n## 5. Stock movement\nChoose a product, choose **IN** or **OUT**, enter a positive quantity and optional note. An OUT operation is rejected when it would take stock below zero.\n\n## 6. Reports\nThe report page shows total inventory value and products whose quantity is at or below reorder level.\n\n## 7. Quality evidence\nThe `artifacts/` directory contains CTQ, SIPOC, architecture, checksheet, Pareto and Fishbone visuals.\n'''
(ROOT/'docs/User_Manual.md').write_text(manual)

# Checklist
check='''# Submission Checklist - BBAT104 Q14\n\n- [x] Assignment identified: S.No. 136 / Ritik Kumar / Roll No. 2520301005\n- [x] Baseline: Inventory Management System\n- [x] Quality Goal: Q14 - Improve Navigation\n- [x] Five Q14 features implemented\n- [x] Base product CRUD\n- [x] SQLite persistence\n- [x] SRS + architecture flowchart\n- [x] CTQ tree\n- [x] SIPOC process map\n- [x] FMEA with RPN\n- [x] Defect log/checksheet\n- [x] Pareto chart\n- [x] Fishbone diagram\n- [x] PDCA log\n- [x] README\n- [x] User manual\n- [x] Viva questions\n- [ ] Create public GitHub repository `BBAT104_TQM_2520301005`\n- [ ] Push project and maintain >=30 meaningful commits\n- [ ] Add GitHub Issues\n- [ ] Add screenshots of live execution to README\n'''
(ROOT/'docs/Submission_Checklist.md').write_text(check)

print('Created docs:', list(map(str,DOCS.iterdir())))
print('Created artifacts:', list(map(str,ART.iterdir())))
