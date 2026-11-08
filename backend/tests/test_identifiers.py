import pytest

from recall_radar.core.identifiers import normalize_model, normalize_upc


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("TL1302Z", "TL1302Z"),  # CPSC 27024 laminator
        ("7927-OZ1", "7927OZ1"),  # CPSC 27007 floor lamp
        ("RWX-RBP02", "RWXRBP02"),
        ("xj-200 b", "XJ200B"),
        ("MMT-8062", "MMT8062"),  # FDA Z-0088-2027 insulin pump
        ("", None),
        (None, None),
        ("---", None),
    ],
)
def test_normalize_model(raw, expected):
    assert normalize_model(raw) == expected


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("0 75465 11111 0", "075465111110"),  # FDA H-0003-2027, printed with spaces
        ("UPC: 7708075247094", "7708075247094"),  # EAN-13
        ("2 67240 ######", None),  # store-packed wildcard: not a real code
        ("123", None),
    ],
)
def test_normalize_upc(raw, expected):
    assert normalize_upc(raw) == expected
