"""
SampleFlow PLM — Demo Seed Data
Clear pilot story:
  - 12 completed indents: 8 ON TIME, 4 DELAYED → OTIF = 66.7%
  - 5 active in-progress indents
  - 4 overdue indents → alerts fire immediately
  - Wash OTIF: 7/10 = 70%
"""
import sqlite3, hashlib, os
from datetime import date, timedelta

DB_PATH = os.environ.get("DB_PATH", os.path.join(os.path.dirname(os.path.abspath(__file__)), "plm_data.db"))
if os.environ.get("RENDER"):
    DB_PATH = "/tmp/plm_data.db"

def hp(p): return hashlib.sha256(p.encode()).hexdigest()
def f(n):  return (date.today() + timedelta(days=n)).isoformat()
def p(n):  return (date.today() - timedelta(days=abs(n))).isoformat()

def get_conn():
    c = sqlite3.connect(DB_PATH)
    c.row_factory = sqlite3.Row
    c.execute("PRAGMA foreign_keys = ON")
    return c

def reset_and_seed():
    db = get_conn()
    c = db.cursor()
    for t in ["sample_movements","qa_checks","dispatches","wash_reports",
              "indents","samples","styles","merchants","brands","users"]:
        try: c.execute(f"DELETE FROM {t}")
        except: pass
    db.commit()

    # USERS
    users = [
        ("admin",     hp("admin123"), "Roshni Anand",       "Admin",        "roshni@aipl.com"),
        ("merch1",    hp("pass123"),  "Prasad / Asha",      "Merchandiser", "prasad@aipl.com"),
        ("merch2",    hp("pass123"),  "Deepthi Menon",      "Merchandiser", "deepthi@aipl.com"),
        ("merch3",    hp("pass123"),  "Shruthi Krishnan",   "Merchandiser", "shruthi@aipl.com"),
        ("merch4",    hp("pass123"),  "Nimmy Thomas",       "Merchandiser", "nimmy@aipl.com"),
        ("sampling1", hp("pass123"),  "Madhunayak B",       "Sampling",     "madhu@aipl.com"),
        ("qa1",       hp("pass123"),  "Ganesh Rajan",       "QA",           "ganesh@aipl.com"),
        ("manager1",  hp("pass123"),  "Planning Head",      "Manager",      "manager@aipl.com"),
    ]
    c.executemany("INSERT INTO users(username,password,full_name,role,email) VALUES(?,?,?,?,?)", users)

    # BRANDS
    brands = [
        ("LEV", "Levi's",                     "USA",       "Levi's Sourcing",   "sourcing@levi.com",       "Denim + woven shirts"),
        ("DOC", "Dockers",                    "USA",       "Dockers Sourcing",  "sourcing@dockers.com",    "Levi Strauss subsidiary"),
        ("SUP", "Superdry",                   "UK",        "Superdry PD",       "pd@superdry.com",         "Casual lifestyle"),
        ("JOU", "Joules",                     "UK",        "Joules Sourcing",   "sourcing@joules.com",     "SS26"),
        ("UCB", "United Colours of Benetton", "Italy",     "UCB Sampling",      "samples@benetton.com",    "AW26 tiered sealer"),
        ("MUJ", "Muji",                       "Japan",     "Muji PD",           "pd@muji.com",             "SS26 AW26"),
        ("LAM", "La Martina",                 "Argentina", "La Martina QA",     "qa@lamartina.com",        "PP+GPT combined"),
        ("DRS", "Dressman",                   "Norway",    "Dressman Sourcing", "sourcing@dressman.com",   "Menswear SS26"),
        ("THF", "Tommy Hilfiger",             "USA",       "TH Sourcing",       "sourcing@tommy.com",      "Premium menswear"),
        ("FAR", "Farah",                      "UK",        "Farah PD",          "pd@farah.com",            "Heritage casualwear"),
    ]
    c.executemany("INSERT INTO brands(code,name,country,contact,email,notes) VALUES(?,?,?,?,?,?)", brands)

    # MERCHANTS
    merchants = [
        ("MCH001","Prasad / Asha",   "prasad@aipl.com",  "+91-9876541001","Woven - Muji UCB"),
        ("MCH002","Deepthi Menon",   "deepthi@aipl.com", "+91-9876541002","Woven - Levi's Dockers"),
        ("MCH003","Shruthi Krishnan","shruthi@aipl.com", "+91-9876541003","Woven - Levi's"),
        ("MCH004","Nimmy Thomas",    "nimmy@aipl.com",   "+91-9876541004","Woven - UCB La Martina"),
        ("MCH005","Asha Nair",       "asha@aipl.com",    "+91-9876541005","Woven - Superdry Joules"),
    ]
    c.executemany("INSERT INTO merchants(code,name,email,phone,department) VALUES(?,?,?,?,?)", merchants)
    db.commit()

    bids = {r["code"]: r["id"] for r in db.execute("SELECT code,id FROM brands")}
    mids = {r["code"]: r["id"] for r in db.execute("SELECT code,id FROM merchants")}
    uids = {r["username"]: r["id"] for r in db.execute("SELECT username,id FROM users")}

    # STYLES
    styles_data = [
        ("AC23BA6A",  "Oxford BD Shirt White",      "MUJ","MCH001","AW26","Shirts","Oxford",   "100% Cotton","White",       8.5,  f(7)),
        ("AC23BA6B",  "Oxford BD Shirt Smoky Green","MUJ","MCH001","AW26","Shirts","Oxford",   "100% Cotton","Smoky Green", 8.5,  f(7)),
        ("LSA260001", "LS Slim Oxford Shirt",        "LEV","MCH002","AW26","Shirts","Oxford",   "100% Cotton","White",       12.5, f(14)),
        ("LSA260002", "LS Poplin Check Shirt",       "LEV","MCH003","AW26","Shirts","Poplin",   "100% Cotton","Blue Check",  11.0, f(20)),
        ("LSA260003", "LS Denim Overshirt",          "LEV","MCH002","AW26","Jackets","Denim",   "100% Cotton","Indigo",      18.0, f(12)),
        ("DOC260001", "Dockers Chino Shirt",         "DOC","MCH002","AW26","Shirts","Poplin",   "98%C 2%E",   "Khaki",       14.0, f(18)),
        ("SUP260001", "Superdry Linen Shirt",        "SUP","MCH005","SS26","Shirts","Linen",    "55%L 45%C",  "Ecru",        10.0, f(5)),
        ("JOU260001", "Joules Seersucker Shirt",     "JOU","MCH005","SS26","Shirts","Seersucker","100% Cotton","Navy",        9.5,  f(12)),
        ("UCB260001", "UCB Oxford Proto",            "UCB","MCH004","AW26","Shirts","Oxford",   "100% Cotton","Cobalt Blue", 13.0, f(8)),
        ("LAM260001", "La Martina Polo PP",          "LAM","MCH004","SS26","Polo",  "Pique",    "100% Cotton","Navy",        22.0, f(3)),
        ("LSA260004", "LS Chambray Work Shirt",      "LEV","MCH003","SS26","Shirts","Chambray", "100% Cotton","Light Blue",  11.0, p(3)),
        ("DOC260002", "Dockers Poplin Solid White",  "DOC","MCH002","SS26","Shirts","Poplin",   "100% Cotton","White",       12.0, p(8)),
        ("MUJ260010", "Muji Linen Overshirt",        "MUJ","MCH001","SS26","Shirts","Linen",    "100% Linen", "Off White",   14.0, p(12)),
        ("LEV260010", "LS Twill Casual Shirt",       "LEV","MCH002","SS26","Shirts","Twill",    "100% Cotton","Navy",        13.0, p(6)),
    ]
    sty_ids = {}
    for row in styles_data:
        sc,sn,bc,mc,season,cat,fab,comp,col,fob,tgt = row
        status = "Dispatched" if tgt < date.today().isoformat() else "Sampling"
        c.execute("""INSERT INTO styles(style_code,style_name,brand_id,merchant_id,season,
                     garment_category,fabric,fabric_composition,color,target_fob,
                     target_dispatch,status,created_by) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                  (sc,sn,bids[bc],mids[mc],season,cat,fab,comp,col,fob,tgt,status,uids["admin"]))
        sty_ids[sc] = c.lastrowid
    db.commit()

    # INDENTS
    # ON TIME (8): actual_dispatch_date <= target_dispatch
    # DELAYED (4): actual_dispatch_date > target_dispatch
    # ACTIVE (5): wip_stage in progress, future target
    # OVERDUE (4): past target, not dispatched → alerts fire
    indent_data = [
        # ─── COMPLETED — ON TIME (8) ─── actual <= target
        # indent_no, sc, sname, bc, mc, season, stype, size, qty, color, wash, tgt, actual_dispatch, wip, status, priority
        ("IND260001","LSA260004","LS Chambray Shirt","LEV","MCH003","SS26","Development","M",1,"Light Blue","BASIC",         p(5), p(7), "Dispatched","Completed","Normal"),
        ("IND260002","LSA260004","LS Chambray Shirt","LEV","MCH003","SS26","Fit",        "M",1,"Light Blue","BASIC",         p(10),p(12),"Dispatched","Completed","Normal"),
        ("IND260003","DOC260002","Dockers Poplin",   "DOC","MCH002","SS26","Development","M",1,"White",     "NON-WASH",      p(8), p(10),"Dispatched","Completed","Normal"),
        ("IND260004","DOC260002","Dockers Poplin",   "DOC","MCH002","SS26","PP",         "M",2,"White",     "NON-WASH",      p(12),p(14),"Dispatched","Completed","Normal"),
        ("IND260005","MUJ260010","Muji Linen",       "MUJ","MCH001","SS26","Development","M",1,"Off White",  "BASIC",         p(12),p(14),"Dispatched","Completed","Normal"),
        ("IND260006","MUJ260010","Muji Linen",       "MUJ","MCH001","SS26","Salesman",   "M",2,"Off White",  "BASIC",         p(12),p(13),"Dispatched","Completed","Normal"),
        ("IND260007","LEV260010","LS Twill Casual",  "LEV","MCH002","SS26","Development","M",1,"Navy",       "NON-WASH",      p(6), p(8), "Dispatched","Completed","Normal"),
        ("IND260008","LEV260010","LS Twill Casual",  "LEV","MCH002","SS26","Salesman",   "M",2,"Navy",       "NON-WASH",      p(6), p(7), "Dispatched","Completed","Normal"),
        # ─── COMPLETED — DELAYED (4) ─── actual > target
        ("IND260009","AC23BA6A","Oxford BD Shirt",   "MUJ","MCH001","AW26","Development","M",1,"White",       "BASIC",         p(12),p(8), "Dispatched","Completed","High"),
        ("IND260010","AC23BA6B","Oxford BD Shirt",   "MUJ","MCH001","AW26","Development","M",1,"Smoky Green", "BASIC",         p(10),p(5), "Dispatched","Completed","High"),
        ("IND260011","LSA260003","LS Denim Overshirt","LEV","MCH002","AW26","Development","M",1,"Indigo",      "DENIM -CRITICAL",p(8),p(4),"Dispatched","Completed","High"),
        ("IND260012","DOC260001","Dockers Chino",    "DOC","MCH002","AW26","Development","M",1,"Khaki",        "NON-WASH",      p(6), p(2),"Dispatched","Completed","Normal"),
        # ─── ACTIVE — IN PROGRESS (5) ───
        ("IND260013","LSA260001","LS Slim Oxford",   "LEV","MCH002","AW26","Development","M",1,"White",       "NON-WASH",      f(14),None,"U/C",  "In Progress","High"),
        ("IND260014","LSA260002","LS Check Shirt",   "LEV","MCH003","AW26","Development","M",1,"Blue Check",  "NON-WASH",      f(20),None,"U/P",  "In Progress","Normal"),
        ("IND260015","SUP260001","Superdry Linen",   "SUP","MCH005","SS26","PP",         "M",2,"Ecru",         "BASIC",         f(5), None,"U/F",  "In Progress","High"),
        ("IND260016","UCB260001","UCB Oxford Proto", "UCB","MCH004","AW26","Development","M",1,"Cobalt Blue", "BASIC",         f(8), None,"U/S",  "In Progress","High"),
        ("IND260017","JOU260001","Joules Seersucker","JOU","MCH005","SS26","Development","M",1,"Navy",         "BASIC",         f(12),None,"U/W",  "In Progress","Normal"),
        # ─── OVERDUE — ALERTS FIRE (4) ───
        ("IND260018","LAM260001","La Martina PP",    "LAM","MCH004","SS26","PP",         "M",3,"Navy",         "NON-WASH",      p(5), None,"U/F",  "In Progress","Critical"),
        ("IND260019","UCB260001","UCB Size Set XL",  "UCB","MCH004","AW26","Size Set",   "XL",2,"Cobalt Blue", "BASIC",         p(2), None,"U/W",  "In Progress","High"),
        ("IND260020","LSA260002","LS Check Fit",     "LEV","MCH003","AW26","Fit",        "M",1,"Blue Check",   "NON-WASH",      p(3), None,"U/S",  "In Progress","High"),
        ("IND260021","DOC260001","Dockers Chino SMS","DOC","MCH002","AW26","Salesman",   "M",2,"Khaki",         "NON-WASH",      p(4), None,"U/F",  "In Progress","High"),
    ]

    for row in indent_data:
        ino,sc,sn,bc,mc,season,stype,size,qty,color,wash,tgt,actual_d,wip,status,priority = row
        c.execute("""INSERT INTO indents(indent_no,style_code,style_name,brand_id,merchant_id,
                     season,sample_type,size,qty,color,wash_type,body_fabric_code,
                     target_dispatch,wip_stage,status,priority,is_planned,actual_dispatch_date,
                     indent_date,created_by,created_at,updated_at) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                  (ino,sc,sn,bids[bc],mids[mc],season,stype,size,qty,
                   color,wash,f"FAB-{sc[:3]}-001",tgt,wip,status,priority,1,actual_d,
                   p(21),uids["merch1"],p(21),actual_d or p(1)))
    db.commit()

    # SAMPLES (linked to styles)
    samples_data = [
        ("AC23BA6A-S001","AC23BA6A","Development","M","Approved", "Dispatch",p(8)),
        ("AC23BA6B-S001","AC23BA6B","Development","M","Approved", "Dispatch",p(5)),
        ("LSA260001-S001","LSA260001","Development","M","In Progress","Sampling",f(14)),
        ("LSA260002-S001","LSA260002","Development","M","In Progress","Sampling",f(20)),
        ("LSA260003-S001","LSA260003","Development","M","Approved", "QA",    p(4)),
        ("DOC260001-S001","DOC260001","Development","M","In Progress","Sampling",f(18)),
        ("SUP260001-S001","SUP260001","PP",         "M","In Progress","Sampling",f(5)),
        ("JOU260001-S001","JOU260001","Development","M","In Progress","Sampling",f(12)),
        ("UCB260001-S001","UCB260001","Development","M","In Progress","QA",   f(8)),
        ("LAM260001-S001","LAM260001","PP",         "M","In Progress","QA",   p(5)),
        ("LSA260004-S001","LSA260004","Development","M","Dispatched","Dispatch",p(7)),
        ("DOC260002-S001","DOC260002","Development","M","Dispatched","Dispatch",p(10)),
        ("MUJ260010-S001","MUJ260010","Salesman",   "M","Dispatched","Dispatch",p(12)),
        ("LEV260010-S001","LEV260010","Salesman",   "M","Dispatched","Dispatch",p(6)),
    ]
    samp_ids = {}
    for sid,sc,stype,size,status,dept,due in samples_data:
        stid = sty_ids.get(sc)
        if not stid: continue
        c.execute("""INSERT INTO samples(sample_id,style_id,sample_type,size,due_date,
                     current_dept,current_status,created_by) VALUES(?,?,?,?,?,?,?,?)""",
                  (sid,stid,stype,size,due,dept,status,uids["merch1"]))
        samp_ids[sid] = c.lastrowid
    db.commit()

    # WASH RECORDS — 7 on time, 2 delayed, 1 pending
    wash_data = [
        ("AC23BA6A","Muji","Prasad / Asha","AW26","White",     "Oxford Cotton","Development","BASIC",          "SAMUDRA WASH PLANT",p(15),p(14),"Pass","Standard laundry - shade stable"),
        ("AC23BA6B","Muji","Prasad / Asha","AW26","Smoky Green","Oxford Cotton","Development","BASIC",          "SAMUDRA WASH PLANT",p(12),p(11),"Pass","Colour consistent"),
        ("LSA260003","Levi's","Deepthi Menon","AW26","Indigo","Denim",         "Development","DENIM -CRITICAL", "GLOBAL WASH UNIT",  p(20),p(15),"Pass","Shade stable - recipe finalised"),
        ("LSA260004","Levi's","Shruthi Krishnan","SS26","Light Blue","Chambray","Development","BASIC",          "SAMUDRA WASH PLANT",p(10),p(9), "Pass","Basic wash - dispatched ok"),
        ("DOC260002","Dockers","Deepthi Menon","SS26","White", "Poplin",       "PP",         "NON-WASH",        "—",                 p(15),p(15),"Pass","Non-wash - direct dispatch"),
        ("MUJ260010","Muji","Prasad / Asha","SS26","Off White","Linen",        "Salesman",   "BASIC",           "SAMUDRA WASH PLANT",p(14),p(13),"Pass","Linen softener - Muji approved"),
        ("LEV260010","Levi's","Deepthi Menon","SS26","Navy",   "Twill",        "Salesman",   "NON-WASH",        "—",                 p(8), p(8), "Pass","Non-wash - dispatched to Levi's USA"),
        ("UCB260001","UCB","Nimmy Thomas","AW26","Cobalt Blue","Oxford Cotton","Development","BASIC",           "RAMDHAN WASH",      p(9), p(7), "Pass","Received 2 days late - shade ok"),
        ("SUP260001","Superdry","Asha Nair","SS26","Ecru",     "Linen",        "PP",         "BASIC",           "SAMUDRA WASH PLANT",p(5), p(2), "Pass","Received 3 days late"),
        ("JOU260001","Joules","Asha Nair","SS26","Navy",       "Seersucker",   "Development","BASIC",           "SAMUDRA WASH PLANT",p(2), None, "Pending","Sent to Samudra - awaiting return"),
    ]
    for row in wash_data:
        sc,cust,merch,season,col,fab,stype,wtype,wunit,sent,recv,result,comments = row
        c.execute("""INSERT INTO wash_reports(style_code,customer,merchant,season,color,fabric_type,
                     sample_type,wash_type,wash_unit,sent_date,received_date,result,comments,created_by)
                     VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                  (sc,cust,merch,season,col,fab,stype,wtype,wunit,sent,recv,result,comments,uids["sampling1"]))
    db.commit()

    # QA CHECKS
    qa_data = [
        ("AC23BA6A-S001","Measurement Check","Pass","All measurements within tolerance - Muji spec"),
        ("AC23BA6A-S001","Visual Inspection","Pass","Oxford weave consistent - button placement correct"),
        ("AC23BA6B-S001","Measurement Check","Pass","Good fit within Muji spec"),
        ("LSA260003-S001","Wash Test","Pass","Denim shade stable after 3 cycles"),
        ("UCB260001-S001","Measurement Check","Conditional Pass","Minor chest seam - within UCB tolerance"),
        ("LAM260001-S001","Final Approval","Conditional Pass","GPT pending - construction meets spec"),
    ]
    for sid,ctype,result,notes in qa_data:
        pk = samp_ids.get(sid)
        if not pk: continue
        c.execute("""INSERT INTO qa_checks(sample_id,check_type,result,notes,inspector,checked_at)
                     VALUES(?,?,?,?,?,?)""",
                  (pk,ctype,result,notes,uids["qa1"],p(3)))
    db.commit()

    # DISPATCHES
    dispatch_data = [
        ("DSP260001","LSA260004-S001","Levi's Sourcing USA",       "1155 Battery St San Francisco CA","FedEx","FEX-LEV-004A",p(7)),
        ("DSP260002","DOC260002-S001","Dockers Sourcing USA",      "1155 Battery St San Francisco CA","FedEx","FEX-DOC-002", p(10)),
        ("DSP260003","MUJ260010-S001","Muji Japan Product Dev",    "1-4-1 Kaigan Minato-ku Tokyo",    "DHL",  "DHL-MUJ-010", p(12)),
        ("DSP260004","LEV260010-S001","Levi's Sourcing USA",       "1155 Battery St San Francisco CA","FedEx","FEX-LEV-010", p(6)),
        ("DSP260005","AC23BA6A-S001", "Muji Japan Product Dev",    "1-4-1 Kaigan Minato-ku Tokyo",    "DHL",  "DHL-MUJ-001", p(8)),
        ("DSP260006","AC23BA6B-S001", "Muji Japan Product Dev",    "1-4-1 Kaigan Minato-ku Tokyo",    "DHL",  "DHL-MUJ-002", p(5)),
        ("DSP260007","LSA260003-S001","Levi's Sourcing USA",       "1155 Battery St San Francisco CA","FedEx","FEX-LEV-003", p(4)),
    ]
    for dno,sid,recipient,address,courier,tracking,ddate in dispatch_data:
        pk = samp_ids.get(sid)
        if not pk: continue
        c.execute("""INSERT INTO dispatches(dispatch_no,sample_id,recipient,address,courier,
                     tracking_no,dispatch_date,dispatched_by) VALUES(?,?,?,?,?,?,?,?)""",
                  (dno,pk,recipient,address,courier,tracking,ddate,uids["admin"]))
    db.commit()

    # SAMPLE MOVEMENTS
    movements = [
        ("AC23BA6A-S001", "Design","Sampling","In Progress",p(18)),
        ("AC23BA6A-S001", "Sampling","QA",    "Approved",   p(14)),
        ("AC23BA6A-S001", "QA",     "Dispatch","Approved",  p(8)),
        ("AC23BA6B-S001", "Design","Sampling","In Progress",p(15)),
        ("AC23BA6B-S001", "Sampling","QA",    "Approved",   p(11)),
        ("AC23BA6B-S001", "QA",     "Dispatch","Approved",  p(5)),
        ("LSA260001-S001","Design","Sampling","In Progress",p(7)),
        ("LSA260003-S001","Design","Sampling","In Progress",p(22)),
        ("LSA260003-S001","Sampling","QA",    "Approved",   p(4)),
        ("LSA260004-S001","Sampling","QA",    "Approved",   p(9)),
        ("LSA260004-S001","QA",     "Dispatch","Approved",  p(7)),
    ]
    for sid,frm,to,status,ts in movements:
        pk = samp_ids.get(sid)
        if not pk: continue
        c.execute("""INSERT INTO sample_movements(sample_id,from_dept,to_dept,status,scanned_by,timestamp)
                     VALUES(?,?,?,?,?,?)""",
                  (pk,frm,to,status,uids["sampling1"],ts))
    db.commit()
    db.close()

    print("=" * 60)
    print("  SampleFlow — Seed Data Complete")
    print("=" * 60)
    print("  ── PILOT STORY ──────────────────────────────────")
    print(f"  Completed ON TIME  : 8 indents  ─── targets met")
    print(f"  Completed DELAYED  : 4 indents  ─── targets missed")
    print(f"  Sample OTIF        : 66.7%  (8/12)")
    print(f"  Active WIP         : 5 indents")
    print(f"  OVERDUE (alerts🚨) : 4 indents")
    print(f"  Wash records       : 10  (7 on time → Wash OTIF 70%)")
    print(f"  Dispatches         : 7")
    print(f"  QA checks          : 6")
    print("  ── LOGINS ───────────────────────────────────────")
    print("  admin     / admin123  — Admin (all access)")
    print("  merch1    / pass123   — Merchandiser Prasad")
    print("  merch2    / pass123   — Merchandiser Deepthi")
    print("  sampling1 / pass123   — Sampling Madhunayak")
    print("  qa1       / pass123   — QA Ganesh")
    print("  manager1  / pass123   — Manager Planning Head")
    print("=" * 60)

if __name__ == "__main__":
    reset_and_seed()
