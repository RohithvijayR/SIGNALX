import os
import json
import sqlite3
from datetime import datetime
from typing import List, Dict, Any, Optional

DB_PATH = os.path.join(os.path.dirname(__file__), "..", "..", "..", "data", "analysis_history.db")

def init_db():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS history (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        timestamp TEXT NOT NULL,
        filename TEXT NOT NULL,
        format TEXT NOT NULL,
        sample_rate REAL NOT NULL,
        modulation TEXT NOT NULL,
        confidence REAL NOT NULL,
        fec_scheme TEXT NOT NULL,
        interleaving TEXT NOT NULL,
        snr_db REAL NOT NULL,
        processing_time_ms REAL NOT NULL,
        report_json TEXT NOT NULL
    )
    """)
    conn.commit()
    conn.close()

def save_analysis_record(
    filename: str,
    format_type: str,
    sample_rate: float,
    modulation: str,
    confidence: float,
    fec_scheme: str,
    interleaving: str,
    snr_db: float,
    processing_time_ms: float,
    report_dict: Dict[str, Any]
) -> int:
    init_db()
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    ts = datetime.utcnow().isoformat() + "Z"
    report_json_str = json.dumps(report_dict)

    cursor.execute("""
    INSERT INTO history (timestamp, filename, format, sample_rate, modulation, confidence, fec_scheme, interleaving, snr_db, processing_time_ms, report_json)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (ts, filename, format_type, sample_rate, modulation, confidence, fec_scheme, interleaving, snr_db, processing_time_ms, report_json_str))

    record_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return record_id

def get_analysis_history(limit: int = 50) -> List[Dict[str, Any]]:
    init_db()
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT id, timestamp, filename, format, sample_rate, modulation, confidence, fec_scheme, interleaving, snr_db, processing_time_ms FROM history ORDER BY id DESC LIMIT ?", (limit,))
    rows = cursor.fetchall()
    conn.close()

    result = []
    for r in rows:
        result.append(dict(r))
    return result

def get_analysis_record_by_id(record_id: int) -> Optional[Dict[str, Any]]:
    init_db()
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM history WHERE id = ?", (record_id,))
    row = cursor.fetchone()
    conn.close()

    if row:
        record = dict(row)
        record["report_json"] = json.loads(record["report_json"])
        return record
    return None
