def generate_qr_png(data, filename, **kw): return ""
def generate_label_pdf(data, path): return ""
"""Master data controllers: Brand, Merchant, Style, Sample"""
from database import get_connection, next_style_code, next_sample_id, next_dispatch_no

from datetime import datetime


# ── Constants ─────────────────────────────────────────────────────────────────
DEPARTMENTS = [
    "Design",
    "Sampling",
    "QA",
    "Production",
    "Merchandising",
    "Dispatch",
    "Wash",
]

SAMPLE_TYPES = [
    "Proto",
    "Fit",
    "Salesman",
    "Photo",
    "Pre-Production",
    "Top of Production",
]

DEPT_COLORS = {
    "Design":        "#4A90D9",
    "Sampling":      "#7B68EE",
    "QA":            "#E8A838",
    "Production":    "#50C878",
    "Merchandising": "#FF6B6B",
    "Dispatch":      "#20B2AA",
    "Wash":          "#DDA0DD",
}


# ── Brand Controller ──────────────────────────────────────────────────────────
class BrandController:
    @staticmethod
    def get_all():
        conn = get_connection()
        rows = conn.execute("SELECT * FROM brands ORDER BY name").fetchall()
        conn.close()
        return [dict(r) for r in rows]

    @staticmethod
    def create(code, name, country, contact, email, notes):
        conn = get_connection()
        try:
            conn.execute("INSERT INTO brands(code,name,country,contact,email,notes) VALUES(?,?,?,?,?,?)",
                         (code.upper(), name, country, contact, email, notes))
            conn.commit()
            return True, "Brand created"
        except Exception as e:
            return False, str(e)
        finally:
            conn.close()

    @staticmethod
    def update(brand_id, code, name, country, contact, email, notes, active):
        conn = get_connection()
        try:
            conn.execute("""UPDATE brands SET code=?,name=?,country=?,contact=?,email=?,notes=?,active=?
                            WHERE id=?""", (code.upper(), name, country, contact, email, notes, active, brand_id))
            conn.commit()
            return True, "Brand updated"
        except Exception as e:
            return False, str(e)
        finally:
            conn.close()

    @staticmethod
    def delete(brand_id):
        conn = get_connection()
        try:
            conn.execute("UPDATE brands SET active=0 WHERE id=?", (brand_id,))
            conn.commit()
            return True, "Deactivated"
        except Exception as e:
            return False, str(e)
        finally:
            conn.close()

    @staticmethod
    def next_code():
        conn = get_connection()
        n = conn.execute("SELECT COUNT(*) FROM brands").fetchone()[0] + 1
        conn.close()
        return f"BRD{n:03d}"


# ── Merchant Controller ───────────────────────────────────────────────────────
class MerchantController:
    @staticmethod
    def get_all():
        conn = get_connection()
        rows = conn.execute("SELECT * FROM merchants ORDER BY name").fetchall()
        conn.close()
        return [dict(r) for r in rows]

    @staticmethod
    def create(code, name, email, phone, department, notes):
        conn = get_connection()
        try:
            conn.execute("INSERT INTO merchants(code,name,email,phone,department,notes) VALUES(?,?,?,?,?,?)",
                         (code.upper(), name, email, phone, department, notes))
            conn.commit()
            return True, "Merchant created"
        except Exception as e:
            return False, str(e)
        finally:
            conn.close()

    @staticmethod
    def update(mid, code, name, email, phone, department, notes, active):
        conn = get_connection()
        try:
            conn.execute("""UPDATE merchants SET code=?,name=?,email=?,phone=?,department=?,notes=?,active=?
                            WHERE id=?""", (code.upper(), name, email, phone, department, notes, active, mid))
            conn.commit()
            return True, "Merchant updated"
        except Exception as e:
            return False, str(e)
        finally:
            conn.close()

    @staticmethod
    def next_code():
        conn = get_connection()
        n = conn.execute("SELECT COUNT(*) FROM merchants").fetchone()[0] + 1
        conn.close()
        return f"MCH{n:03d}"


# ── Style Controller ──────────────────────────────────────────────────────────
class StyleController:
    @staticmethod
    def get_all(filters=None):
        conn = get_connection()
        q = """SELECT s.*, b.name as brand_name, m.name as merchant_name
               FROM styles s
               LEFT JOIN brands b ON s.brand_id=b.id
               LEFT JOIN merchants m ON s.merchant_id=m.id
               WHERE 1=1"""
        params = []
        if filters:
            if filters.get("status"):
                q += " AND s.status=?"
                params.append(filters["status"])
            if filters.get("brand_id"):
                q += " AND s.brand_id=?"
                params.append(filters["brand_id"])
            if filters.get("search"):
                q += " AND (s.style_code LIKE ? OR s.style_name LIKE ?)"
                params += [f"%{filters['search']}%", f"%{filters['search']}%"]
        q += " ORDER BY s.created_at DESC"
        rows = conn.execute(q, params).fetchall()
        conn.close()
        return [dict(r) for r in rows]

    @staticmethod
    def get_by_id(style_id):
        conn = get_connection()
        row = conn.execute("""SELECT s.*, b.name as brand_name, m.name as merchant_name
               FROM styles s
               LEFT JOIN brands b ON s.brand_id=b.id
               LEFT JOIN merchants m ON s.merchant_id=m.id
               WHERE s.id=?""", (style_id,)).fetchone()
        conn.close()
        return dict(row) if row else None

    @staticmethod
    def create(data: dict, user_id: int):
        conn = get_connection()
        code = next_style_code()
        try:
            conn.execute("""INSERT INTO styles
                (style_code,style_name,brand_id,merchant_id,season,garment_category,
                 fabric,fabric_composition,color,target_fob,target_dispatch,
                 design_notes,sketch_path,created_by)
                VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                (code, data['style_name'], data.get('brand_id'), data.get('merchant_id'),
                 data.get('season'), data.get('garment_category'),
                 data.get('fabric'), data.get('fabric_composition'), data.get('color'),
                 data.get('target_fob'), data.get('target_dispatch'),
                 data.get('design_notes'), data.get('sketch_path'), user_id))
            conn.commit()
            return True, code
        except Exception as e:
            return False, str(e)
        finally:
            conn.close()

    @staticmethod
    def update(style_id, data: dict):
        conn = get_connection()
        try:
            conn.execute("""UPDATE styles SET
                style_name=?,brand_id=?,merchant_id=?,season=?,garment_category=?,
                fabric=?,fabric_composition=?,color=?,target_fob=?,target_dispatch=?,
                design_notes=?,sketch_path=?,status=?,updated_at=datetime('now')
                WHERE id=?""",
                (data['style_name'], data.get('brand_id'), data.get('merchant_id'),
                 data.get('season'), data.get('garment_category'),
                 data.get('fabric'), data.get('fabric_composition'), data.get('color'),
                 data.get('target_fob'), data.get('target_dispatch'),
                 data.get('design_notes'), data.get('sketch_path'), data.get('status'), style_id))
            conn.commit()
            return True, "Updated"
        except Exception as e:
            return False, str(e)
        finally:
            conn.close()

    @staticmethod
    def delete(style_id):
        conn = get_connection()
        conn.execute("UPDATE styles SET status='Cancelled' WHERE id=?", (style_id,))
        conn.commit()
        conn.close()
        return True, "Cancelled"


# ── Sample Controller ─────────────────────────────────────────────────────────
class SampleController:
    @staticmethod
    def get_all(style_id=None, filters=None):
        conn = get_connection()
        q = """SELECT s.*, st.style_code, st.style_name, st.season,
                      b.name as brand_name, u.full_name as created_by_name
               FROM samples s
               JOIN styles st ON s.style_id=st.id
               LEFT JOIN brands b ON st.brand_id=b.id
               LEFT JOIN users u ON s.created_by=u.id
               WHERE 1=1"""
        params = []
        if style_id:
            q += " AND s.style_id=?"
            params.append(style_id)
        if filters:
            if filters.get("status"):
                q += " AND s.current_status=?"
                params.append(filters["status"])
            if filters.get("dept"):
                q += " AND s.current_dept=?"
                params.append(filters["dept"])
            if filters.get("search"):
                q += " AND (s.sample_id LIKE ? OR st.style_code LIKE ?)"
                params += [f"%{filters['search']}%", f"%{filters['search']}%"]
        q += " ORDER BY s.created_at DESC"
        rows = conn.execute(q, params).fetchall()
        conn.close()
        return [dict(r) for r in rows]

    @staticmethod
    def get_by_id(sample_id):
        conn = get_connection()
        row = conn.execute("""SELECT s.*, st.style_code, st.style_name, st.season, st.color as style_color,
                      b.name as brand_name, u.full_name as created_by_name
               FROM samples s
               JOIN styles st ON s.style_id=st.id
               LEFT JOIN brands b ON st.brand_id=b.id
               LEFT JOIN users u ON s.created_by=u.id
               WHERE s.id=?""", (sample_id,)).fetchone()
        conn.close()
        return dict(row) if row else None

    @staticmethod
    def get_by_sample_code(code):
        conn = get_connection()
        row = conn.execute("""SELECT s.*, st.style_code, st.style_name, st.season,
                      b.name as brand_name
               FROM samples s
               JOIN styles st ON s.style_id=st.id
               LEFT JOIN brands b ON st.brand_id=b.id
               WHERE s.sample_id=?""", (code,)).fetchone()
        conn.close()
        return dict(row) if row else None

    @staticmethod
    def create(style_id, data: dict, user_id: int):
        conn = get_connection()
        style_row = conn.execute("SELECT style_code FROM styles WHERE id=?", (style_id,)).fetchone()
        if not style_row:
            conn.close()
            return False, "Style not found"

        sid = next_sample_id(style_row['style_code'])

        # Generate QR
        qr_path = generate_qr_png(sid, f"{sid}.png")

        try:
            conn.execute("""INSERT INTO samples
                (sample_id,style_id,sample_type,size,color,fabric_ref,due_date,
                 current_dept,current_status,qr_path,remarks,created_by)
                VALUES(?,?,?,?,?,?,?,?,?,?,?,?)""",
                (sid, style_id, data['sample_type'], data.get('size'),
                 data.get('color'), data.get('fabric_ref'), data.get('due_date'),
                 'Design', 'Pending', qr_path, data.get('remarks'), user_id))

            # Log initial movement
            row_id = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
            conn.execute("""INSERT INTO sample_movements
                (sample_id,from_dept,to_dept,status,scanned_by,notes)
                VALUES(?,?,?,?,?,?)""",
                (row_id, None, 'Design', 'Created', user_id, 'Sample created'))

            # Update style status
            conn.execute("UPDATE styles SET status='Sampling', updated_at=datetime('now') WHERE id=?",
                         (style_id,))
            conn.commit()

            # Generate label PDF
            style_data = conn.execute("""SELECT st.*, b.name as brand_name
                FROM styles st LEFT JOIN brands b ON st.brand_id=b.id WHERE st.id=?""",
                (style_id,)).fetchone()

            label_data = {
                'sample_id': sid,
                'style_code': style_row['style_code'],
                'sample_type': data['sample_type'],
                'size': data.get('size', ''),
                'color': data.get('color', ''),
                'brand': dict(style_data).get('brand_name', '') if style_data else '',
                'season': dict(style_data).get('season', '') if style_data else '',
                'due_date': data.get('due_date', ''),
            }
            generate_label_pdf(label_data, qr_path)

            return True, sid
        except Exception as e:
            return False, str(e)
        finally:
            conn.close()

    @staticmethod
    def move_sample(sample_db_id, to_dept, status, user_id, notes=""):
        conn = get_connection()
        try:
            cur = conn.execute("SELECT current_dept FROM samples WHERE id=?", (sample_db_id,)).fetchone()
            from_dept = cur['current_dept'] if cur else None

            conn.execute("""UPDATE samples SET current_dept=?,current_status=?,updated_at=datetime('now')
                WHERE id=?""", (to_dept, status, sample_db_id))
            conn.execute("""INSERT INTO sample_movements(sample_id,from_dept,to_dept,status,scanned_by,notes)
                VALUES(?,?,?,?,?,?)""", (sample_db_id, from_dept, to_dept, status, user_id, notes))

            # Auto-update style status
            if to_dept == "QA":
                conn.execute("""UPDATE styles SET status='QA', updated_at=datetime('now')
                    WHERE id=(SELECT style_id FROM samples WHERE id=?)""", (sample_db_id,))
            elif to_dept == "Dispatch":
                conn.execute("""UPDATE samples SET current_status='Dispatched' WHERE id=?""", (sample_db_id,))

            conn.commit()
            return True, "Moved"
        except Exception as e:
            return False, str(e)
        finally:
            conn.close()

    @staticmethod
    def get_movements(sample_db_id):
        conn = get_connection()
        rows = conn.execute("""SELECT m.*, u.full_name as scanned_by_name
               FROM sample_movements m
               LEFT JOIN users u ON m.scanned_by=u.id
               WHERE m.sample_id=?
               ORDER BY m.timestamp""", (sample_db_id,)).fetchall()
        conn.close()
        return [dict(r) for r in rows]


# ── QA Controller ─────────────────────────────────────────────────────────────
class QAController:
    @staticmethod
    def get_samples_in_qa():
        conn = get_connection()
        rows = conn.execute("""SELECT s.*, st.style_code, st.style_name, b.name as brand_name
               FROM samples s
               JOIN styles st ON s.style_id=st.id
               LEFT JOIN brands b ON st.brand_id=b.id
               WHERE s.current_dept='QA'
               ORDER BY s.updated_at DESC""").fetchall()
        conn.close()
        return [dict(r) for r in rows]

    @staticmethod
    def add_check(sample_id, check_type, measurements, defects, result, inspector_id, notes):
        conn = get_connection()
        try:
            conn.execute("""INSERT INTO qa_checks
                (sample_id,check_type,measurements,defects,result,inspector,notes)
                VALUES(?,?,?,?,?,?,?)""",
                (sample_id, check_type, measurements, defects, result, inspector_id, notes))

            # Update sample status
            status_map = {"Pass": "Approved", "Fail": "Rejected", "Conditional Pass": "QA Hold"}
            conn.execute("UPDATE samples SET current_status=?,updated_at=datetime('now') WHERE id=?",
                         (status_map.get(result, "In Progress"), sample_id))
            if result == "Pass":
                conn.execute("""UPDATE styles SET status='Approved', updated_at=datetime('now')
                    WHERE id=(SELECT style_id FROM samples WHERE id=?)""", (sample_id,))

            conn.commit()
            return True, "QA check saved"
        except Exception as e:
            return False, str(e)
        finally:
            conn.close()

    @staticmethod
    def get_checks(sample_id):
        conn = get_connection()
        rows = conn.execute("""SELECT q.*, u.full_name as inspector_name
               FROM qa_checks q LEFT JOIN users u ON q.inspector=u.id
               WHERE q.sample_id=? ORDER BY q.checked_at DESC""", (sample_id,)).fetchall()
        conn.close()
        return [dict(r) for r in rows]


# ── Dispatch Controller ───────────────────────────────────────────────────────
class DispatchController:
    @staticmethod
    def dispatch_sample(sample_id, recipient, address, courier, tracking_no, user_id, notes):
        conn = get_connection()
        dno = next_dispatch_no()
        try:
            conn.execute("""INSERT INTO dispatches
                (dispatch_no,sample_id,recipient,address,courier,tracking_no,dispatched_by,notes)
                VALUES(?,?,?,?,?,?,?,?)""",
                (dno, sample_id, recipient, address, courier, tracking_no, user_id, notes))
            conn.execute("""UPDATE samples SET current_dept='Dispatch',current_status='Dispatched',
                updated_at=datetime('now') WHERE id=?""", (sample_id,))
            conn.execute("""UPDATE styles SET status='Dispatched', updated_at=datetime('now')
                WHERE id=(SELECT style_id FROM samples WHERE id=?)""", (sample_id,))
            conn.commit()
            return True, dno
        except Exception as e:
            return False, str(e)
        finally:
            conn.close()

    @staticmethod
    def get_all():
        conn = get_connection()
        rows = conn.execute("""SELECT d.*, s.sample_id as sample_code, st.style_code,
                      b.name as brand_name, u.full_name as dispatched_by_name
               FROM dispatches d
               JOIN samples s ON d.sample_id=s.id
               JOIN styles st ON s.style_id=st.id
               LEFT JOIN brands b ON st.brand_id=b.id
               LEFT JOIN users u ON d.dispatched_by=u.id
               ORDER BY d.dispatch_date DESC""").fetchall()
        conn.close()
        return [dict(r) for r in rows]


# ── Dashboard Stats ───────────────────────────────────────────────────────────
class DashboardController:
    @staticmethod
    def get_stats():
        conn = get_connection()
        stats = {}
        stats['total_styles']  = conn.execute("SELECT COUNT(*) FROM styles").fetchone()[0]
        stats['total_samples'] = conn.execute("SELECT COUNT(*) FROM samples").fetchone()[0]
        stats['pending_qa']    = conn.execute("SELECT COUNT(*) FROM samples WHERE current_dept='QA'").fetchone()[0]
        stats['dispatched']    = conn.execute("SELECT COUNT(*) FROM samples WHERE current_status='Dispatched'").fetchone()[0]
        stats['approved']      = conn.execute("SELECT COUNT(*) FROM samples WHERE current_status='Approved'").fetchone()[0]
        stats['rejected']      = conn.execute("SELECT COUNT(*) FROM samples WHERE current_status='Rejected'").fetchone()[0]

        # Per-dept counts
        dept_rows = conn.execute("""SELECT current_dept, COUNT(*) as cnt
               FROM samples WHERE current_status NOT IN ('Dispatched','Cancelled')
               GROUP BY current_dept""").fetchall()
        stats['by_dept'] = {r['current_dept']: r['cnt'] for r in dept_rows}

        # Status distribution
        status_rows = conn.execute("""SELECT status, COUNT(*) as cnt FROM styles GROUP BY status""").fetchall()
        stats['style_status'] = {r['status']: r['cnt'] for r in status_rows}

        # Recent movements
        stats['recent_movements'] = [dict(r) for r in conn.execute("""
            SELECT m.*, s.sample_id as sample_code, u.full_name as user_name
            FROM sample_movements m
            JOIN samples s ON m.sample_id=s.id
            LEFT JOIN users u ON m.scanned_by=u.id
            ORDER BY m.timestamp DESC LIMIT 10""").fetchall()]

        conn.close()
        return stats


class WashController:
    def get_all(self, result=None, wash_type=None, search=None):
        conn = get_connection()
        q = "SELECT * FROM wash_reports WHERE 1=1"
        params = []
        if result:
            q += " AND result=?"
            params.append(result)
        if wash_type:
            q += " AND wash_type=?"
            params.append(wash_type)
        if search:
            q += " AND (style_code LIKE ? OR customer LIKE ? OR color LIKE ?)"
            params.extend([f"%{search}%"] * 3)
        q += " ORDER BY created_at DESC"
        rows = [dict(r) for r in conn.execute(q, params).fetchall()]
        conn.close()
        return rows

    def get_by_id(self, record_id):
        conn = get_connection()
        r = conn.execute("SELECT * FROM wash_reports WHERE id=?", (record_id,)).fetchone()
        conn.close()
        return dict(r) if r else None

    def create(self, data):
        conn = get_connection()
        conn.execute("""INSERT INTO wash_reports
            (sample_id, style_code, customer, merchant, season, color, fabric_type,
             sample_type, wash_type, required_wash, wash_unit, sent_date, received_date,
             result, comments, created_by)
            VALUES (:sample_id,:style_code,:customer,:merchant,:season,:color,:fabric_type,
                    :sample_type,:wash_type,:required_wash,:wash_unit,:sent_date,:received_date,
                    :result,:comments,:created_by)""", data)
        conn.commit()
        conn.close()

    def update(self, record_id, data):
        conn = get_connection()
        conn.execute("""UPDATE wash_reports SET
            sample_id=:sample_id, style_code=:style_code, customer=:customer,
            merchant=:merchant, season=:season, color=:color, fabric_type=:fabric_type,
            sample_type=:sample_type, wash_type=:wash_type, required_wash=:required_wash,
            wash_unit=:wash_unit, sent_date=:sent_date, received_date=:received_date,
            result=:result, comments=:comments
            WHERE id=:id""", {**data, "id": record_id})
        conn.commit()
        conn.close()# Add these imports at the top of main_controller.py if not present:
# from datetime import datetime, date

class IndentController:
    """Manages sample request / indent forms (replaces the Excel tracker)."""

    @staticmethod
    def _next_indent_no():
        conn = get_connection()
        n = conn.execute("SELECT COUNT(*) FROM indents").fetchone()[0] + 1
        conn.close()
        from datetime import datetime
        yy = datetime.now().strftime('%y')
        return f"IND{yy}{n:04d}"

    @staticmethod
    def get_all(filters=None):
        conn = get_connection()
        q = """SELECT i.*,
                      b.name  AS customer,
                      m.name  AS merchant_name
               FROM indents i
               LEFT JOIN brands    b ON i.brand_id    = b.id
               LEFT JOIN merchants m ON i.merchant_id = m.id
               WHERE 1=1"""
        params = []
        if filters:
            if filters.get("status"):
                q += " AND i.status=?"; params.append(filters["status"])
            if filters.get("sample_type"):
                q += " AND i.sample_type=?"; params.append(filters["sample_type"])
            if filters.get("is_planned") is not None:
                q += " AND i.is_planned=?"; params.append(filters["is_planned"])
        q += " ORDER BY i.created_at DESC"
        rows = conn.execute(q, params).fetchall()
        conn.close()
        from datetime import date
        today = date.today().isoformat()
        result = []
        for r in rows:
            d = dict(r)
            d["is_overdue"] = bool(
                d.get("target_dispatch")
                and d["target_dispatch"] < today
                and d["status"] not in ("Completed", "Cancelled")
            )
            result.append(d)
        return result

    @staticmethod
    def create(data: dict):
        conn = get_connection()
        indent_no = IndentController._next_indent_no()
        conn.execute("""INSERT INTO indents (
            indent_no, style_code, style_name, brand_id, merchant_id,
            season, sample_type, size, qty, color,
            body_fabric_code, body_fabric_desc, fabric_composition, fabric_status,
            trim_fabric_code, trim_desc, fabric_placement,
            wash_type, special_requirements, print_embroidery,
            thread_top_stitch, thread_body, button_details, erp_ref,
            indent_date, target_dispatch, is_planned, priority, remarks,
            status, created_by
        ) VALUES (
            :indent_no, :style_code, :style_name, :brand_id, :merchant_id,
            :season, :sample_type, :size, :qty, :color,
            :body_fabric_code, :body_fabric_desc, :fabric_composition, :fabric_status,
            :trim_fabric_code, :trim_desc, :fabric_placement,
            :wash_type, :special_requirements, :print_embroidery,
            :thread_top_stitch, :thread_body, :button_details, :erp_ref,
            :indent_date, :target_dispatch, :is_planned, :priority, :remarks,
            'Pending', :created_by
        )""", {**data, "indent_no": indent_no})
        conn.commit()
        conn.close()
        return indent_no

    @staticmethod
    def update(indent_id: int, status: str, is_planned: int, remarks: str):
        conn = get_connection()
        conn.execute("""UPDATE indents
            SET status=?, is_planned=?, remarks=?, updated_at=datetime('now')
            WHERE id=?""", (status, is_planned, remarks, indent_id))
        conn.commit()
        conn.close()


# ── WIP Controller ─────────────────────────────────────────────────────────────
class WIPController:
    """Derives WIP stage from indent status + tracks movement through stages."""

    # Ordered pipeline stages
    STAGES = ["pattern", "cutting", "sewing", "washing", "finishing", "dispatched"]

    # Map sample_type groups → SMS vs Development
    SMS_TYPES = {
        "sms", "pre-sms", "lf sample", "size set", "sealer",
        "gold seal sample", "photoshoot", "presentation",
    }

    @staticmethod
    def _stage_from_status(status: str, wip_stage: str | None) -> str:
        """Derive a display stage label from stored wip_stage or status."""
        if wip_stage:
            return wip_stage
        mapping = {
            "Pending": "U/P",
            "In Progress": "U/S",
            "Completed": "Dispatched",
            "Cancelled": "Cancelled",
        }
        return mapping.get(status, "U/P")

    @staticmethod
    def get_rows():
        conn = get_connection()
        rows = conn.execute("""
            SELECT i.*,
                   b.name AS customer,
                   m.name AS merchant,
                   COALESCE(i.wip_stage, CASE i.status
                     WHEN 'Completed'   THEN 'Dispatched'
                     WHEN 'In Progress' THEN 'U/S'
                     WHEN 'Cancelled'   THEN 'Cancelled'
                     ELSE 'U/P'
                   END) AS wip_stage,
                   CASE
                     WHEN LOWER(i.sample_type) IN (
                       'sms','pre-sms','lf sample','size set','sealer',
                       'gold seal sample','photoshoot','presentation'
                     ) THEN 'sms'
                     ELSE 'dev'
                   END AS sample_group
            FROM indents i
            LEFT JOIN brands    b ON i.brand_id    = b.id
            LEFT JOIN merchants m ON i.merchant_id = m.id
            WHERE i.status NOT IN ('Cancelled')
            ORDER BY i.created_at DESC
        """).fetchall()
        conn.close()
        from datetime import date
        today = date.today().isoformat()
        result = []
        for r in rows:
            d = dict(r)
            d["is_overdue"] = bool(
                d.get("target_dispatch")
                and d["target_dispatch"] < today
                and d.get("wip_stage") not in ("Dispatched",)
            )
            result.append(d)
        return result

    @staticmethod
    def get_summary():
        rows = WIPController.get_rows()
        summary = {s: {"styles": 0, "pcs": 0} for s in
                   ["pattern", "cutting", "sewing", "washing", "finishing", "dispatched"]}
        stage_map = {
            "U/P": "pattern", "U/C": "cutting", "U/S": "sewing",
            "U/W": "washing",  "U/F": "finishing", "Dispatched": "dispatched",
        }
        total_styles, total_pcs = 0, 0
        for r in rows:
            key = stage_map.get(r.get("wip_stage", "U/P"), "pattern")
            summary[key]["styles"] += 1
            summary[key]["pcs"] += r.get("qty") or 0
            total_styles += 1
            total_pcs += r.get("qty") or 0
        summary["total_styles"] = total_styles
        summary["total_pcs"] = total_pcs
        return summary


# ── Output Report Controller ──────────────────────────────────────────────────
class OutputReportController:
    @staticmethod
    def get_rows():
        conn = get_connection()
        rows = conn.execute("""
            SELECT i.*,
                   b.name AS customer,
                   m.name AS merchant,
                   strftime('%Y', i.updated_at) AS dispatch_year,
                   strftime('%m', i.updated_at) AS dispatch_month,
                   date(i.updated_at) AS output_date
            FROM indents i
            LEFT JOIN brands    b ON i.brand_id    = b.id
            LEFT JOIN merchants m ON i.merchant_id = m.id
            WHERE i.status = 'Completed'
            ORDER BY i.updated_at DESC
        """).fetchall()
        conn.close()
        return [dict(r) for r in rows]

    @staticmethod
    def get_years():
        conn = get_connection()
        rows = conn.execute("""
            SELECT DISTINCT strftime('%Y', updated_at) AS y
            FROM indents WHERE status='Completed' ORDER BY y DESC
        """).fetchall()
        conn.close()
        return [r[0] for r in rows if r[0]]