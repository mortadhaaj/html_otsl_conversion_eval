"""
Constants for table conversion.

Defines OTSL tokens, tags, and patterns used throughout the conversion system.
"""

# OTSL Cell Type Tags (modern docling format)
TAG_FILLED_CELL = 'fcel'  # Full cell with content
TAG_EMPTY_CELL = 'ecel'   # Empty cell
TAG_LEFT_CELL = 'lcel'    # Left-looking cell (colspan continuation)
TAG_UP_CELL = 'ucel'      # Upward-looking cell (rowspan continuation)
TAG_CROSS_CELL = 'xcel'   # Cross cell (both colspan and rowspan continuation)

# OTSL Header Tags
TAG_COL_HEADER = 'ched'   # Column header marker
TAG_ROW_HEADER = 'rhed'   # Row header marker
TAG_SECTION_ROW = 'srow'  # Section row marker

# OTSL Separator Tags
TAG_NEWLINE = 'nl'        # Newline/row separator
TAG_LOCATION = 'loc'      # Location coordinate (followed by number)

# OTSL Token Map (for reference - older format used single chars)
TOKEN_FILLED = 'F'
TOKEN_EMPTY = 'E'
TOKEN_LEFT = 'L'
TOKEN_UP = 'U'
TOKEN_CROSS = 'X'
TOKEN_NEWLINE = 'N'

# Tag to Token mapping
TAG_TO_TOKEN = {
    TAG_FILLED_CELL: TOKEN_FILLED,
    TAG_EMPTY_CELL: TOKEN_EMPTY,
    TAG_LEFT_CELL: TOKEN_LEFT,
    TAG_UP_CELL: TOKEN_UP,
    TAG_CROSS_CELL: TOKEN_CROSS,
    TAG_NEWLINE: TOKEN_NEWLINE,
}

TOKEN_TO_TAG = {v: k for k, v in TAG_TO_TOKEN.items()}

# LaTeX patterns
LATEX_INLINE_PATTERN = r'\$([^\$]+)\$'
LATEX_DISPLAY_PATTERN = r'\$\$([^\$]+)\$\$'

# HTML math tags
HTML_MATH_TAGS = ['math', 'formula', 'equation', 'sup', 'sub']

# HTML table tags
HTML_TABLE_TAGS = ['table', 'thead', 'tbody', 'tfoot', 'tr', 'th', 'td', 'caption']

# TEDS normalization options
TEDS_NORMALIZE_ADD_THEAD = 'add_thead'
TEDS_NORMALIZE_REMOVE_THEAD = 'remove_thead'
TEDS_NORMALIZE_FLATTEN = 'flatten'  # KITAB-Bench style
TEDS_NORMALIZE_PRESERVE = 'preserve'
TEDS_NORMALIZE_MINIMAL = 'minimal'
