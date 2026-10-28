"""Code 128 barcodes for unit labels (SRS REQ-10, HI-1).

A keyboard-wedge scanner types the unit identifier into whichever field has focus, so
the label only has to carry the identifier as a standard Code 128 symbol.
"""

import io

from barcode import Code128
from barcode.writer import SVGWriter

OPTIONS = {
    "write_text": False,  # the label prints the identifier itself, in larger type
    "module_width": 0.35,
    "module_height": 14,
    "quiet_zone": 4,
}


def code128_svg(value):
    """The barcode for `value` as SVG bytes."""
    buffer = io.BytesIO()
    Code128(value, writer=SVGWriter()).write(buffer, OPTIONS)
    return buffer.getvalue()
