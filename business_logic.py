"""
PLM Business Logic Engine
Implements: OTIF, Delay Calculation, Alert System, Stage Tracking
Based on: SAMPLE___WASH_TRACKER.xlsx + Namrata GP Report
"""
from datetime import datetime, date, timedelta
from database import get_connection

# ── Constants ─────────────────────────────────────────────────────────────────
WASH_LEAD_TIMES = {
    "BASIC": 1, "NON-WASH": 0, "RFD/OD": 3,
    "DENIM -CRITICAL": 5, "DENIM - NON CRITICAL": 3,
    "NON-DENIM CRITICAL": 4, "TBC": 3, "SPECIAL WASH": 3,
}

STAGE_ORDER = ["pattern", "cutting", "sewing", "washing", "finishing", "dispatched"]
STAGE_LABELS = {
    "U/P": "pattern", "U/C": "cutting", "U/S": "sewing",
    "U/W": "washing", "U/F": "finishing", "Dispatched": "dispatched",
}

ALERT_THRESHOLDS = {
    "overdue_days": 0,        # overdue same day target passes
    "warning_days": 2,        # warn 2 days before target
    "critical_days": -3,      # critical if 3+ days late
    "wash_approval_days": 5,  # alert if wash pending > 5 days
    "qa_pending_days": 3,     # alert if in QA > 3 days
}

# ── Date Helpers ──────────────────────────────────────────────────────────────
def _parse_date(d):
    if not d:
        return None
    if isinstance(d, (date, datetime)):
        return d if isinstance(d, date) else d.date()
    for fmt in ("%Y-%m-%d", "%d/%m/%Y", "%m/%d/%Y"):
        try:
            return datetime.strptime(str(d), fmt).date()
        except ValueError:
            continue
    return None

def _days_diff(target, actual=None):
    """Returns delay in days (positive = late, negative = early)."""
    t = _parse_date(target)
    a = _parse_date(actual) if actual else date.today()
    if not t:
        return None
    return (a - t).days

def _today():
    return date.today()

# ── OTIF Calculation ──────────────────────────────────────────────────────────
def calc_otif(records, target_field, actual_field, status_field=None, done_status=None):
    """
    Generic OTIF: On Time In Full
    OTIF% = (completed on time) / total_completed * 100
    """
    total = 0
    on_time = 0
    for r in records:
        target = _parse_date(r.get(target_field))
        actual = _parse_date(r.get(actual_field))
        if not actual:
            continue
        if status_field and done_status:
            if r.get(status_field) not in (done_status if isinstance(done_status, list) else [done_status]):
                continue
        total += 1
        if target and actual <= target:
            on_time += 1
    if total == 0:
        return {"otif_pct": 0, "on_time": 0, "total": 0, "delayed": 0}
    pct = round(on_time * 100 / total, 1)
    return {"otif_pct": pct, "on_time": on_time, "total": total, "delayed": total - on_time}

def get_sample_otif():
    """OTIF for sample dispatch: target_dispatch vs actual_dispatch_date."""
    conn = get_connection()
    rows = conn.execute("""
        SELECT i.target_dispatch, i.actual_dispatch_date, i.status
        FROM indents i
        WHERE i.status IN ('Completed', 'Dispatched')
        AND i.actual_dispatch_date IS NOT NULL
    """).fetchall()
    conn.close()
    records = [dict(r) for r in rows]
    return calc_otif(records, "target_dispatch", "actual_dispatch_date",
                     "status", ["Completed", "Dispatched"])

def get_wash_otif():
    """OTIF for wash process: sent_date+leadtime vs received_date."""
    conn = get_connection()
    rows = conn.execute("""
        SELECT wr.sent_date, wr.received_date, wr.wash_type, wr.result
        FROM wash_reports wr
        WHERE wr.received_date IS NOT NULL AND wr.result IN ('Pass','Fail','Rework')
    """).fetchall()
    conn.close()
    total = 0
    on_time = 0
    for r in rows:
        sent = _parse_date(r["sent_date"])
        received = _parse_date(r["received_date"])
        wash_type = r["wash_type"] or "BASIC"
        lead = WASH_LEAD_TIMES.get(wash_type, 3)
        if not sent or not received:
            continue
        expected = sent + timedelta(days=lead)
        total += 1
        if received <= expected:
            on_time += 1
    if total == 0:
        return {"otif_pct": 0, "on_time": 0, "total": 0, "delayed": 0}
    pct = round(on_time * 100 / total, 1)
    return {"otif_pct": pct, "on_time": on_time, "total": total, "delayed": total - on_time}

# ── Delay Calculation ─────────────────────────────────────────────────────────
def calc_indent_delay(indent_row):
    """
    Returns delay analysis for a single indent row.
    delay_days: positive = overdue, negative = ahead
    status: 'on_time', 'warning', 'overdue', 'critical'
    """
    target = _parse_date(indent_row.get("target_dispatch"))
    actual_complete = _parse_date(indent_row.get("actual_dispatch_date")) if indent_row.get("status") in ("Completed","Dispatched") else None
    today = _today()

    if not target:
        return {"delay_days": None, "status": "no_target", "label": "No Target"}

    if actual_complete:
        delay = (actual_complete - target).days
    else:
        delay = (today - target).days

    if indent_row.get("status") in ("Completed", "Dispatched"):
        if delay <= 0:
            return {"delay_days": delay, "status": "on_time", "label": "On Time"}
        return {"delay_days": delay, "status": "delayed", "label": f"+{delay}d Late"}

    # Still in progress
    if delay >= 3:
        return {"delay_days": delay, "status": "critical", "label": f"CRITICAL +{delay}d"}
    if delay > 0:
        return {"delay_days": delay, "status": "overdue", "label": f"Overdue +{delay}d"}
    if delay >= -2:
        return {"delay_days": delay, "status": "warning", "label": f"Due in {-delay}d"}
    return {"delay_days": delay, "status": "on_time", "label": f"{-delay}d to go"}

def calc_wash_delay(wash_row):
    """Delay for wash process based on sent date + lead time vs received date."""
    sent = _parse_date(wash_row.get("sent_date"))
    received = _parse_date(wash_row.get("received_date"))
    wash_type = wash_row.get("wash_type") or "BASIC"
    lead = WASH_LEAD_TIMES.get(wash_type, 3)

    if not sent:
        return {"delay_days": None, "status": "no_data", "label": "—"}

    expected = sent + timedelta(days=lead)
    if received:
        delay = (received - expected).days
        if delay <= 0:
            return {"delay_days": delay, "status": "on_time", "label": "On Time"}
        return {"delay_days": delay, "status": "delayed", "label": f"+{delay}d Late"}

    # Still pending
    today = _today()
    delay = (today - expected).days
    if delay > 0:
        return {"delay_days": delay, "status": "overdue", "label": f"Overdue +{delay}d"}
    if delay >= -1:
        return {"delay_days": delay, "status": "warning", "label": "Due Today/Tomorrow"}
    return {"delay_days": delay, "status": "on_time", "label": f"{-delay}d remaining"}

# ── Approval Lead Time ────────────────────────────────────────────────────────
def calc_avg_approval_time():
    """Average days from sample creation to QA approval."""
    conn = get_connection()
    rows = conn.execute("""
        SELECT s.created_at, q.checked_at
        FROM qa_checks q
        JOIN samples s ON q.sample_id = s.id
        WHERE q.result = 'Pass'
    """).fetchall()
    conn.close()
    if not rows:
        return 0
    diffs = []
    for r in rows:
        c = _parse_date(r["created_at"])
        a = _parse_date(r["checked_at"])
        if c and a:
            diffs.append((a - c).days)
    return round(sum(diffs) / len(diffs), 1) if diffs else 0

# ── Alert System ──────────────────────────────────────────────────────────────
def generate_alerts():
    """
    Generate all system alerts.
    Returns list of alert dicts with: type, level, title, message, link, entity_id
    """
    alerts = []
    conn = get_connection()
    today = _today()

    # 1. Overdue / near-due indents
    rows = conn.execute("""
        SELECT i.id, i.indent_no, i.style_name, i.style_code, i.target_dispatch,
               i.status, i.wip_stage, b.name as customer, m.name as merchant
        FROM indents i
        LEFT JOIN brands b ON i.brand_id = b.id
        LEFT JOIN merchants m ON i.merchant_id = m.id
        WHERE i.status NOT IN ('Completed', 'Cancelled')
    """).fetchall()

    for r in rows:
        d = dict(r)
        info = calc_indent_delay(d)
        if info["status"] == "critical":
            alerts.append({
                "type": "delay", "level": "critical",
                "title": f"CRITICAL: {d['indent_no']} overdue by {info['delay_days']} days",
                "message": f"{d['customer']} | {d['style_name'] or d['style_code']} — Target was {d['target_dispatch']}",
                "link": f"/indent",
                "entity_id": d["id"], "icon": "🚨"
            })
        elif info["status"] == "overdue":
            alerts.append({
                "type": "delay", "level": "warning",
                "title": f"Overdue: {d['indent_no']} (+{info['delay_days']}d)",
                "message": f"{d['customer']} | {d['style_name'] or d['style_code']}",
                "link": f"/indent",
                "entity_id": d["id"], "icon": "⚠️"
            })
        elif info["status"] == "warning":
            alerts.append({
                "type": "due_soon", "level": "info",
                "title": f"Due Soon: {d['indent_no']} in {-info['delay_days']}d",
                "message": f"{d['customer']} | {d['style_name'] or d['style_code']}",
                "link": f"/indent",
                "entity_id": d["id"], "icon": "⏰"
            })

    # 2. Wash overdue (no received date, past expected)
    wash_rows = conn.execute("""
        SELECT id, style_code, customer, sent_date, wash_type, result
        FROM wash_reports
        WHERE received_date IS NULL AND result = 'Pending'
    """).fetchall()
    for r in wash_rows:
        d = dict(r)
        info = calc_wash_delay(d)
        if info["status"] in ("overdue",):
            alerts.append({
                "type": "wash_delay", "level": "warning",
                "title": f"Wash Overdue: {d['style_code']} ({d['wash_type']})",
                "message": f"Sent: {d['sent_date']} — No receipt yet. {info['label']}",
                "link": "/wash",
                "entity_id": d["id"], "icon": "🌊"
            })

    # 3. QA pending too long
    qa_rows = conn.execute("""
        SELECT s.id, s.sample_id, s.updated_at, st.style_code, b.name as brand_name
        FROM samples s
        JOIN styles st ON s.style_id = st.id
        LEFT JOIN brands b ON st.brand_id = b.id
        WHERE s.current_dept = 'QA' AND s.current_status = 'Pending'
    """).fetchall()
    for r in qa_rows:
        d = dict(r)
        last_updated = _parse_date(d.get("updated_at"))
        if last_updated:
            days_in_qa = (today - last_updated).days
            if days_in_qa >= ALERT_THRESHOLDS["qa_pending_days"]:
                alerts.append({
                    "type": "qa_stuck", "level": "warning",
                    "title": f"QA Stuck: {d['sample_id']} ({days_in_qa}d pending)",
                    "message": f"Style: {d['style_code']} | Brand: {d['brand_name']}",
                    "link": "/qa",
                    "entity_id": d["id"], "icon": "🔍"
                })

    # 4. Indents with no WIP stage update (stuck)
    stuck_rows = conn.execute("""
        SELECT id, indent_no, style_code, wip_stage, updated_at, status
        FROM indents
        WHERE status = 'In Progress' AND wip_stage IN ('U/P', 'U/C')
        AND julianday('now') - julianday(updated_at) > 5
    """).fetchall()
    for r in stuck_rows:
        d = dict(r)
        alerts.append({
            "type": "stage_stuck", "level": "info",
            "title": f"Stage Stuck: {d['indent_no']} at {d['wip_stage']}",
            "message": f"No update for 5+ days. Style: {d['style_code']}",
            "link": "/wip",
            "entity_id": d["id"], "icon": "⏳"
        })

    # 5. Missing data alerts
    missing_rows = conn.execute("""
        SELECT id, indent_no, style_code, style_name
        FROM indents
        WHERE (target_dispatch IS NULL OR target_dispatch = '')
        AND status NOT IN ('Cancelled', 'Completed')
    """).fetchall()
    for r in missing_rows:
        d = dict(r)
        alerts.append({
            "type": "missing_data", "level": "info",
            "title": f"Missing Target: {d['indent_no']}",
            "message": f"No dispatch target set for {d['style_name'] or d['style_code']}",
            "link": "/indent",
            "entity_id": d["id"], "icon": "📋"
        })

    conn.close()

    # Sort: critical first
    priority = {"critical": 0, "warning": 1, "info": 2}
    alerts.sort(key=lambda a: priority.get(a["level"], 3))
    return alerts

def get_alert_counts():
    alerts = generate_alerts()
    return {
        "total": len(alerts),
        "critical": sum(1 for a in alerts if a["level"] == "critical"),
        "warning": sum(1 for a in alerts if a["level"] == "warning"),
        "info": sum(1 for a in alerts if a["level"] == "info"),
    }

# ── Enhanced Dashboard Stats ──────────────────────────────────────────────────
def get_enhanced_dashboard_stats():
    """Full dashboard stats including OTIF, delays, approvals."""
    conn = get_connection()
    today = _today().isoformat()

    stats = {}

    # Basic counts
    stats["total_styles"] = conn.execute("SELECT COUNT(*) FROM styles").fetchone()[0]
    stats["total_samples"] = conn.execute("SELECT COUNT(*) FROM samples").fetchone()[0]
    stats["pending_qa"] = conn.execute("SELECT COUNT(*) FROM samples WHERE current_dept='QA'").fetchone()[0]
    stats["dispatched"] = conn.execute("SELECT COUNT(*) FROM samples WHERE current_status='Dispatched'").fetchone()[0]
    stats["approved"] = conn.execute("SELECT COUNT(*) FROM samples WHERE current_status='Approved'").fetchone()[0]
    stats["rejected"] = conn.execute("SELECT COUNT(*) FROM samples WHERE current_status='Rejected'").fetchone()[0]

    # Indent-based stats
    stats["total_indents"] = conn.execute("SELECT COUNT(*) FROM indents").fetchone()[0]
    stats["active_indents"] = conn.execute(
        "SELECT COUNT(*) FROM indents WHERE status NOT IN ('Completed','Cancelled')").fetchone()[0]
    stats["overdue_indents"] = conn.execute(
        f"SELECT COUNT(*) FROM indents WHERE target_dispatch < '{today}' AND status NOT IN ('Completed','Cancelled')").fetchone()[0]

    # OTIF scores
    stats["sample_otif"] = get_sample_otif()
    stats["wash_otif"] = get_wash_otif()

    # Avg approval time
    stats["avg_approval_days"] = calc_avg_approval_time()

    # Stage summary for WIP
    from main_controller import WIPController
    wip_summary = WIPController.get_summary()
    stats["wip_summary"] = wip_summary

    # By dept pipeline
    dept_rows = conn.execute("""
        SELECT current_dept, COUNT(*) as cnt
        FROM samples WHERE current_status NOT IN ('Dispatched','Cancelled')
        GROUP BY current_dept
    """).fetchall()
    stats["by_dept"] = {r["current_dept"]: r["cnt"] for r in dept_rows}

    # Style status distribution
    status_rows = conn.execute("SELECT status, COUNT(*) as cnt FROM styles GROUP BY status").fetchall()
    stats["style_status"] = {r["status"]: r["cnt"] for r in status_rows}

    # Wash stats
    stats["wash_pending"] = conn.execute(
        "SELECT COUNT(*) FROM wash_reports WHERE result='Pending'").fetchone()[0]
    stats["wash_pass"] = conn.execute(
        "SELECT COUNT(*) FROM wash_reports WHERE result='Pass'").fetchone()[0]
    stats["wash_fail"] = conn.execute(
        "SELECT COUNT(*) FROM wash_reports WHERE result IN ('Fail','Rework')").fetchone()[0]

    # Delay breakdown (indents)
    indent_rows = conn.execute("""
        SELECT id, target_dispatch, updated_at, status, wip_stage
        FROM indents WHERE status NOT IN ('Cancelled')
    """).fetchall()
    delay_counts = {"on_time": 0, "warning": 0, "overdue": 0, "critical": 0, "no_target": 0}
    for r in indent_rows:
        d = dict(r)
        info = calc_indent_delay(d)
        s = info["status"]
        if s in delay_counts:
            delay_counts[s] += 1
        else:
            delay_counts["on_time"] += 1
    stats["delay_breakdown"] = delay_counts

    # Monthly dispatch trend (last 6 months)
    monthly = conn.execute("""
        SELECT strftime('%Y-%m', updated_at) as month, COUNT(*) as cnt
        FROM indents
        WHERE status = 'Completed'
        AND updated_at >= date('now', '-6 months')
        GROUP BY month
        ORDER BY month
    """).fetchall()
    stats["monthly_dispatch"] = [{"month": r["month"], "count": r["cnt"]} for r in monthly]

    # Recent movements
    stats["recent_movements"] = [dict(r) for r in conn.execute("""
        SELECT m.*, s.sample_id as sample_code, u.full_name as user_name
        FROM sample_movements m
        JOIN samples s ON m.sample_id=s.id
        LEFT JOIN users u ON m.scanned_by=u.id
        ORDER BY m.timestamp DESC LIMIT 10
    """).fetchall()]

    # Alerts
    alert_counts = get_alert_counts()
    stats["alert_counts"] = alert_counts

    conn.close()
    return stats

# ── Stage-wise Progress ───────────────────────────────────────────────────────
def get_stage_progress():
    """Funnel / stage-wise count for pipeline visualization."""
    conn = get_connection()
    rows = conn.execute("""
        SELECT wip_stage, COUNT(*) as cnt
        FROM indents
        WHERE status NOT IN ('Cancelled')
        GROUP BY wip_stage
    """).fetchall()
    conn.close()
    stage_map = {
        "U/P": "Pattern", "U/C": "Cutting", "U/S": "Sewing",
        "U/W": "Washing", "U/F": "Finishing", "Dispatched": "Dispatched",
    }
    result = {v: 0 for v in stage_map.values()}
    for r in rows:
        label = stage_map.get(r["wip_stage"], "Pattern")
        result[label] += r["cnt"]
    return result
