from src.license_plate_recognizer import LicensePlateRecognizer

def test_recognize_basic():
    rec = LicensePlateRecognizer()
    result = rec.recognize("fake_image")
    assert isinstance(result, str)
    assert len(result) > 0
