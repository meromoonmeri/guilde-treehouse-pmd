"""Hand-drawn lightning wings for Mega Raichu, one shape per direction.

WHY HAND-DRAWN
--------------
Two automated routes were tried and rejected:

  * splitting the generated rotation sheet by a horizontal cut: it sliced the
    wings in half and left the tail attached;
  * connected-component extraction of the yellow pixels: the wings fragment
    into 20+ components at some angles and merge with the tail at others, so
    directions 3 and 5 came out nearly empty.

A generated plate of wings alone was also attempted; the model returned no
image. So the wings are authored here as pixel data, which is the only way to
get a clean, consistent, reusable shape at this size.

GEOMETRY
--------
Each direction defines a LEFT wing as an ASCII sprite. The right wing is the
mirror of the left unless the view is asymmetric. Coordinates are expressed
relative to the HEAD MARKER of the frame, the black pixel in the -Offsets
sheet, which exists on every frame of every animation. That anchor is what
lets one static wing shape follow a body that is bobbing, walking or lunging.

Characters:
  '#' bright bolt      '+' pale highlight
  'o' dark shading     '.' transparent
"""

# Bright, pale and dark tones, taken from the Mega Raichu artwork.
BOLT = (248, 190, 38)
BOLT_PALE = (247, 230, 82)
BOLT_DARK = (117, 77, 10)
OUTLINE = (7, 7, 7)

CHARS = {"#": BOLT, "+": BOLT_PALE, "o": BOLT_DARK, ".": None}

# Left wing, seen from the front: a jagged bolt sweeping up and out.
FRONT_LEFT = [
    "oo##o.........",
    "o##++#o.......",
    ".o##+++#o.....",
    "..o##+++#o....",
    "...o##+++#o...",
    "....o##+++#o..",
    "....o##+++##o.",
    ".....o##++++#o",
    "......o##+++#o",
    ".......o##++#o",
    "........o##+#o",
    ".........o###o",
    "..........o##o",
    "...........ooo",
]

# Three-quarter view: narrower, more foreshortened.
THREE_Q_LEFT = [
    "oo##o.......",
    "o##++#o.....",
    ".o##+++#o...",
    "..o##+++#o..",
    "...o##+++#o.",
    "....o##+++#o",
    ".....o##++#o",
    "......o##+#o",
    ".......o###o",
    "........o##o",
    ".........ooo",
]

# Side view: the wing points mostly backward, strongly compressed.
SIDE_LEFT = [
    "oo#o......",
    "o##+#o....",
    ".o##++#o..",
    "..o##++#o.",
    "...o##++#o",
    "....o##+#o",
    ".....o###o",
    "......o##o",
    ".......ooo",
]

# Back view: we see the underside, darker, with the highlight lower.
BACK_LEFT = [
    "oo##o.........",
    "o##oo#o.......",
    ".o##oo+#o.....",
    "..o##oo+#o....",
    "...o##oo+#o...",
    "....o##oo+#o..",
    "....o##oo+##o.",
    ".....o##oo++#o",
    "......o##oo+#o",
    ".......o##oo#o",
    "........o##o#o",
    ".........o##oo",
    "..........o##o",
    "...........ooo",
]

# Per direction: (left wing art, dx, dy, mirror_for_right)
# dx/dy place the wing's bottom-inner corner relative to the head marker.
# dx is how far LEFT of the head marker the wing's outer tip starts, dy how
# far ABOVE it. The wings are big, so they start well outside and above.
# The art is drawn tip-first: row 0 col 0 is the OUTER TIP (high and wide),
# the last row is the INNER ROOT that meets the shoulder. dx/dy place the tip
# relative to the head marker, so the root lands on the shoulder.
WINGS = {
    0: (FRONT_LEFT, -16, -13, True),     # down / facing viewer
    1: (THREE_Q_LEFT, -14, -12, True),   # down-right
    2: (SIDE_LEFT, -12, -11, True),      # right
    3: (BACK_LEFT, -15, -12, True),      # up-right
    4: (BACK_LEFT, -16, -13, True),      # up / facing away
    5: (BACK_LEFT, -15, -12, True),      # up-left
    6: (SIDE_LEFT, -12, -11, True),      # left
    7: (THREE_Q_LEFT, -14, -12, True),   # down-left
}


def wing_pixels(direction):
    """Yield (dx, dy, colour) for both wings of a direction.

    Offsets are relative to the head marker. The right wing is the mirrored
    left wing, pushed across the body so the pair straddles the shoulders.
    """
    art, ox, oy, mirror = WINGS[direction]
    height = len(art)
    width = max(len(row) for row in art)

    for row, line in enumerate(art):
        for col, char in enumerate(line):
            colour = CHARS.get(char)
            if colour is not None:
                yield ox + col, oy + row, colour

    if not mirror:
        return
    # Mirror horizontally around the head marker.
    for row, line in enumerate(art):
        for col, char in enumerate(line):
            colour = CHARS.get(char)
            if colour is not None:
                yield -(ox + col) - 1, oy + row, colour
