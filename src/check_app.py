"""Run the dashboard headlessly and fail if any panel raises. Confirms the app works against the
database the run just built, without opening a browser."""
import os
import sys

from streamlit.testing.v1 import AppTest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

at = AppTest.from_file(os.path.join(ROOT, "app.py"), default_timeout=120).run()
if at.exception:
    for e in at.exception:
        print(e.message)
    sys.exit(1)
labels = [m.label for m in at.metric]
assert len(labels) == 5, labels
at.slider[0].set_value(6).run()
assert not at.exception
print(f"dashboard OK: {len(at.metric)} KPI tiles, {len(at.tabs)} tabs, {len(at.dataframe)} tables")
