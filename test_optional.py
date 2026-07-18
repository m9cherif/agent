import os
os.chdir(r'C:\j.a.r.v.i.s')

from jarvis_app.tools import create_default_registry
reg = create_default_registry()

def safe_print(msg):
    try:
        print(msg)
    except UnicodeEncodeError:
        print(msg.encode('ascii', 'replace').decode())

safe_print("Testing optional tools...")

# Test audio
safe_print("\nTesting audio...")
try:
    result = reg.get('audio').execute({'action': 'volume'})
    safe_print(f"  OK: {result['success']} - {str(result.get('result', ''))[:100]}")
except Exception as e:
    safe_print(f"  ERROR: {e}")

# Test network
safe_print("\nTesting network...")
try:
    result = reg.get('network').execute({'action': 'info'})
    safe_print(f"  OK: {result['success']} - {str(result.get('result', ''))[:100]}")
except Exception as e:
    safe_print(f"  ERROR: {e}")

# Test window
safe_print("\nTesting window...")
try:
    result = reg.get('window').execute({'action': 'list'})
    safe_print(f"  OK: {result['success']} - {str(result.get('result', ''))[:100]}")
except Exception as e:
    safe_print(f"  ERROR: {e}")

# Test OCR
safe_print("\nTesting OCR...")
try:
    import tempfile
    from PIL import Image, ImageDraw
    with tempfile.TemporaryDirectory() as d:
        img = Image.new('RGB', (200, 50), color='white')
        draw = ImageDraw.Draw(img)
        draw.text((10, 10), "Test OCR", fill='black')
        img_path = os.path.join(d, 'test.png')
        img.save(img_path)
        result = reg.get('ocr').execute({'path': img_path})
        safe_print(f"  OK: {result['success']} - {str(result.get('result', ''))[:100]}")
except Exception as e:
    safe_print(f"  ERROR: {e}")

# Test QR code
safe_print("\nTesting QR code...")
try:
    import tempfile
    with tempfile.TemporaryDirectory() as d:
        result = reg.get('qr_code').execute({'action': 'generate', 'data': 'test', 'archive': os.path.join(d, 'qr.png')})
        safe_print(f"  OK: {result['success']} - {str(result.get('result', ''))[:100]}")
except Exception as e:
    safe_print(f"  ERROR: {e}")

# Test archive
safe_print("\nTesting archive...")
try:
    import tempfile
    with tempfile.TemporaryDirectory() as d:
        test_file = os.path.join(d, 'test.txt')
        with open(test_file, 'w') as f:
            f.write('hello archive')
        result = reg.get('archive').execute({'action': 'create', 'paths': [test_file], 'archive': os.path.join(d, 'test.zip')})
        safe_print(f"  OK: {result['success']} - {str(result.get('result', ''))[:100]}")
except Exception as e:
    safe_print(f"  ERROR: {e}")

# Test JSON
safe_print("\nTesting JSON...")
try:
    result = reg.get('json').execute({'action': 'parse', 'data': '{"a": 1, "b": 2}'})
    safe_print(f"  OK: {result['success']} - {str(result.get('result', ''))[:100]}")
except Exception as e:
    safe_print(f"  ERROR: {e}")

# Test crypto/hash
safe_print("\nTesting crypto/hash...")
try:
    result = reg.get('crypto').execute({'action': 'hash', 'data': 'test', 'algorithm': 'sha256'})
    safe_print(f"  OK: {result['success']} - {str(result.get('result', ''))[:100]}")
    result = reg.get('hash').execute({'action': 'string', 'data': 'test', 'algorithm': 'md5'})
    safe_print(f"  OK: {result['success']} - {str(result.get('result', ''))[:100]}")
except Exception as e:
    safe_print(f"  ERROR: {e}")

# Test translate
safe_print("\nTesting translate...")
try:
    result = reg.get('translate').execute({'text': 'hello', 'target': 'es'})
    safe_print(f"  OK: {result['success']} - {str(result.get('result', ''))[:100]}")
except Exception as e:
    safe_print(f"  ERROR: {e}")

safe_print("\n=== All optional tool tests completed ===")