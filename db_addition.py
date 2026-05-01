# ── PASTE THIS INSIDE init_db() in database.py, after the wash_reports table ──

    # ── INDENTS (Sample Request Forms) ─────────────────────────────────────────
    c.execute("""
    CREATE TABLE IF NOT EXISTS indents (
        id                  INTEGER PRIMARY KEY AUTOINCREMENT,
        indent_no           TEXT    UNIQUE NOT NULL,
        style_code          TEXT,
        style_name          TEXT,
        brand_id            INTEGER REFERENCES brands(id),
        merchant_id         INTEGER REFERENCES merchants(id),
        season              TEXT,
        sample_type         TEXT    NOT NULL,
        size                TEXT,
        qty                 INTEGER DEFAULT 1,
        color               TEXT,
        -- Fabric details
        body_fabric_code    TEXT,
        body_fabric_desc    TEXT,
        fabric_composition  TEXT,
        fabric_status       TEXT,
        trim_fabric_code    TEXT,
        trim_desc           TEXT,
        fabric_placement    TEXT,
        -- Process details
        wash_type           TEXT,
        special_requirements TEXT,
        print_embroidery    TEXT,
        -- Thread / button
        thread_top_stitch   TEXT,
        thread_body         TEXT,
        button_details      TEXT,
        erp_ref             TEXT,
        -- Dates
        indent_date         TEXT,
        target_dispatch     TEXT,
        -- Planning
        is_planned          INTEGER DEFAULT 0,
        priority            TEXT    DEFAULT 'Normal',
        wip_stage           TEXT    DEFAULT 'U/P',
        -- Status & audit
        status              TEXT    DEFAULT 'Pending'
                                    CHECK(status IN ('Pending','In Progress','Completed','Cancelled')),
        remarks             TEXT,
        created_by          INTEGER REFERENCES users(id),
        created_at          TEXT    DEFAULT (datetime('now')),
        updated_at          TEXT    DEFAULT (datetime('now'))
    )""")
