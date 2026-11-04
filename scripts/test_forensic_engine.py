"""Quick end-to-end test of the ForensicEngine."""
import json, os, sys, tempfile
sys.path.insert(0, r"c:\Users\SGI\Downloads\forensic")

from forensic_engine.engine import ForensicEngine

# Minimal valid 1x1 PNG
PNG_1X1 = bytes([
    0x89,0x50,0x4e,0x47,0x0d,0x0a,0x1a,0x0a,
    0x00,0x00,0x00,0x0d,0x49,0x48,0x44,0x52,
    0x00,0x00,0x00,0x01,0x00,0x00,0x00,0x01,
    0x08,0x02,0x00,0x00,0x00,0x90,0x77,0x53,
    0xde,0x00,0x00,0x00,0x0c,0x49,0x44,0x41,
    0x54,0x08,0xd7,0x63,0xf8,0xcf,0xc0,0x00,
    0x00,0x00,0x02,0x00,0x01,0xe2,0x21,0xbc,
    0x33,0x00,0x00,0x00,0x00,0x49,0x45,0x4e,
    0x44,0xae,0x42,0x60,0x82,
])

tf = tempfile.NamedTemporaryFile(suffix=".png", delete=False)
tf.write(PNG_1X1)
tf.close()

try:
    engine = ForensicEngine()
    report = engine.process_file(tf.name)
    print("=== FORENSIC ENGINE REPORT ===")
    print(json.dumps({
        "metadata":   report["metadata"],
        "categories": list(report["categories"].keys()),
        "execution":  report["execution"]
    }, indent=2))
    err_count = report["execution"]["errors"]
    ext_count = report["execution"]["extractors_run"]
    print(f"\nResult: {ext_count} extractors run, {err_count} errors")
    if err_count == 0:
        print("✅ ForensicEngine: ALL EXTRACTORS PASSED")
    else:
        # Print which failed
        for cat, cdata in report["categories"].items():
            for res in cdata["results"]:
                if res.get("status") == "error":
                    print(f"  ❌ FAIL [{cat}] {res.get('extractor')}: {res.get('summary')}")
finally:
    os.unlink(tf.name)
