from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DB_PATH = PROJECT_ROOT / "electric-measures.db"
BOKEH_APP_PATH = Path(__file__).with_name("dataviz.py")
