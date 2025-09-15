from __future__ import annotations

import sqlite3
from pathlib import Path
from time import time
from typing import Optional

DB_PATH = Path("data/trae.db")
"""

DB_PATH.parent.mkdir(parents=True, exist_ok=True)




def _cx():
    cx = sqlite3.connect(str(DB_PATH))
    cx.row_factory = sqlite3.Row
    return cx


def ensure_settings_schema() -> None:
    with _cx() as cx:
        cx.execute(
           
""""""
        CREATE TABLE IF NOT EXISTS settings(
            k TEXT PRIMARY KEY,
                v TEXT NOT NULL,
                mtime REAL NOT NULL
#         );
        """"""

         )
       

        
       
"""
        cx.commit()
       """"""
def get_setting(key: str, default: Optional[str] = None) -> str:
    ensure_settings_schema()
    with _cx() as cx:
        cur = cx.execute("SELECT v FROM settings WHERE k=?", (key,))
        row = cur.fetchone()
        return row["v"] if row else (default if default is not None else "")


def set_setting(key: str, value: str) -> None:
    ensure_settings_schema()
    with _cx() as cx:
        cx.execute(
            "INSERT OR REPLACE INTO settings(k,v,mtime) VALUES(?,?,?)",
            (key, value, time()),
         )
        cx.commit()