from io import BytesIO

from PIL import Image

from kinwatch.models import PrivacyZone
from kinwatch.ring.privacy import apply_privacy_zones, parse_privacy_zones


def _png(color=(255, 0, 0)) -> bytes:
    image = Image.new("RGB", (100, 100), color)
    buf = BytesIO()
    image.save(buf, format="PNG")
    return buf.getvalue()


def test_privacy_zone_is_blacked_out():
    raw = _png((255, 0, 0))
    zones = [PrivacyZone(id="z", vertices=[(0.5, 0.0), (1.0, 0.0), (1.0, 1.0), (0.5, 1.0)])]
    out = apply_privacy_zones(raw, zones)
    image = Image.open(BytesIO(out))
    assert image.getpixel((10, 10))[0] > 200
    assert image.getpixel((90, 10)) == (0, 0, 0)


def test_parse_privacy_zones_from_configurations():
    config = {
        "attributes": {
            "image_enhancements": {
                "privacy_zones": [{"id": "n", "vertices": [{"x": 0.8, "y": 0.0}, {"x": 1.0, "y": 1.0}]}]
            }
        }
    }
    zones = parse_privacy_zones(config)
    assert zones[0].id == "n"
    assert zones[0].vertices[0] == (0.8, 0.0)
