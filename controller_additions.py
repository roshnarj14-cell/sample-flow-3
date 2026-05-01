# ── PASTE THIS BLOCK AT THE BOTTOM OF main_controller.py ─────────────────────
# Add these imports at the top of main_controller.py if not present:
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
