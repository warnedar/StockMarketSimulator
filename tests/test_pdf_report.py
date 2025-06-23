import sys
import types

# Provide a dummy fpdf module before importing pdf_report
class DummyPDF:
    def __init__(self):
        self.calls = []
        self.w = 100

    def set_auto_page_break(self, *args, **kwargs):
        self.calls.append(("set_auto_page_break", args, kwargs))

    def add_page(self, *args, **kwargs):
        self.calls.append(("add_page", args, kwargs))

    def set_font(self, *args, **kwargs):
        self.calls.append(("set_font", args, kwargs))

    def multi_cell(self, *args, **kwargs):
        self.calls.append(("multi_cell", args, kwargs))

    def image(self, *args, **kwargs):
        self.calls.append(("image", args, kwargs))

    def output(self, path):
        self.calls.append(("output", path))
        self.saved_path = path


dummy_module = types.SimpleNamespace(FPDF=DummyPDF)
sys.modules.setdefault("fpdf", dummy_module)

from stock_market_simulator.utils import pdf_report


def test_create_pdf_report(tmp_path, monkeypatch):
    created = []

    class RecordingPDF(DummyPDF):
        def __init__(self):
            super().__init__()
            created.append(self)

    monkeypatch.setattr(pdf_report, "FPDF", RecordingPDF)

    (tmp_path / "config.txt").write_text("config")
    (tmp_path / "report.txt").write_text("report")
    with open(tmp_path / "plot.png", "wb") as f:
        f.write(b"\x89PNG\r\n\x1a\n")

    result = pdf_report.create_pdf_report(str(tmp_path))

    assert result == str(tmp_path / "report.pdf")
    assert created, "FPDF was not instantiated"
    calls = [c[0] for c in created[0].calls]
    assert "output" in calls
