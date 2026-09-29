#!/usr/bin/env python3
"""
generate_presentation.py  –  v2
Physics-Based Modeling of the Magnetometer Array
A research progress report for the PI and postdoc hardware team.

Run:  python3 generate_presentation.py
Out:  magnetic_localization_research.pptx
"""

import os
from pptx import Presentation
from pptx.util import Inches, Pt, Emu
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE
from pptx.enum.text import PP_ALIGN

# ─── Palette ──────────────────────────────────────────────────────────────────
C_NAVY   = RGBColor(18, 32, 58)      # primary dark
C_BLUE   = RGBColor(0, 102, 200)     # accent / tag
C_SLATE  = RGBColor(68, 84, 106)     # body text
C_MUTED  = RGBColor(110, 120, 132)   # subtitle / caption
C_BG     = RGBColor(247, 249, 252)   # card fill
C_BORDER = RGBColor(214, 222, 234)   # card border
C_WHITE  = RGBColor(255, 255, 255)
C_GREEN  = RGBColor(34, 153, 84)
C_AMBER  = RGBColor(212, 106, 12)
C_RED    = RGBColor(192, 57, 43)

FH = "Helvetica"   # heading font
FB = "Arial"       # body font

ROOT = os.path.dirname(os.path.abspath(__file__))

def fig(rel):
    p = os.path.join(ROOT, rel)
    return p if os.path.exists(p) else None


# ─── Low-level helpers ────────────────────────────────────────────────────────

def blank(prs):
    return prs.slides.add_slide(prs.slide_layouts[6])


def top_bar(slide, color=C_BLUE):
    bar = slide.shapes.add_shape(
        MSO_SHAPE.RECTANGLE,
        Inches(0), Inches(0), Inches(13.333), Inches(0.10))
    bar.fill.solid(); bar.fill.fore_color.rgb = color
    bar.line.color.rgb = color


def tag(slide, text, left=0.8, top=0.38):
    tb = slide.shapes.add_textbox(Inches(left), Inches(top), Inches(10), Inches(0.30))
    p = tb.text_frame.paragraphs[0]
    p.text = text.upper()
    p.font.size = Pt(9); p.font.bold = True
    p.font.color.rgb = C_BLUE; p.font.name = FH


def heading(slide, text, left=0.8, top=0.65, width=11.7, size=21):
    tb = slide.shapes.add_textbox(Inches(left), Inches(top), Inches(width), Inches(0.75))
    tf = tb.text_frame; tf.word_wrap = True
    p = tf.paragraphs[0]
    p.text = text; p.font.size = Pt(size); p.font.bold = True
    p.font.color.rgb = C_NAVY; p.font.name = FH


def subtitle(slide, text, left=0.8, top=1.38, width=11.7):
    tb = slide.shapes.add_textbox(Inches(left), Inches(top), Inches(width), Inches(0.40))
    tf = tb.text_frame; tf.word_wrap = True
    p = tf.paragraphs[0]
    p.text = text; p.font.size = Pt(12); p.font.italic = True
    p.font.color.rgb = C_MUTED; p.font.name = FB


def header(slide, tag_txt, head_txt, sub_txt=""):
    top_bar(slide)
    tag(slide, tag_txt)
    heading(slide, head_txt)
    if sub_txt:
        subtitle(slide, sub_txt)


def notes(slide, txt):
    slide.notes_slide.notes_text_frame.text = txt


def card(slide, left, top, width, height, fill=C_BG, border=C_BORDER, radius=True):
    shape_type = MSO_SHAPE.ROUNDED_RECTANGLE if radius else MSO_SHAPE.RECTANGLE
    sh = slide.shapes.add_shape(shape_type, Inches(left), Inches(top),
                                 Inches(width), Inches(height))
    sh.fill.solid(); sh.fill.fore_color.rgb = fill
    sh.line.color.rgb = border
    return sh


def bullet_block(slide, left, top, width, height, items, title=None,
                 title_color=C_NAVY, bullet_color=C_BLUE, text_color=C_SLATE,
                 title_size=13, text_size=11.5, gap=5):
    """items: list of (bold_prefix, rest_text) or plain strings."""
    tb = slide.shapes.add_textbox(Inches(left), Inches(top),
                                   Inches(width), Inches(height))
    tf = tb.text_frame; tf.word_wrap = True
    tf.margin_left = tf.margin_top = tf.margin_right = tf.margin_bottom = 0
    first = True
    if title:
        p = tf.paragraphs[0] if first else tf.add_paragraph()
        first = False
        p.text = title; p.font.bold = True
        p.font.size = Pt(title_size); p.font.color.rgb = title_color
        p.space_after = Pt(gap)
    for item in items:
        p = tf.paragraphs[0] if first else tf.add_paragraph()
        first = False
        if isinstance(item, tuple):
            bold_part, rest = item
            r1 = p.add_run(); r1.text = bold_part
            r1.font.bold = True; r1.font.size = Pt(text_size)
            r1.font.color.rgb = bullet_color
            r2 = p.add_run(); r2.text = rest
            r2.font.size = Pt(text_size); r2.font.color.rgb = text_color
        else:
            p.text = item; p.font.size = Pt(text_size)
            p.font.color.rgb = text_color
        p.space_after = Pt(gap)
    return tf


def pill(slide, left, top, width, height, text, fill=C_BLUE, text_color=C_WHITE,
         size=10.5):
    sh = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE,
                                 Inches(left), Inches(top),
                                 Inches(width), Inches(height))
    sh.fill.solid(); sh.fill.fore_color.rgb = fill
    sh.line.color.rgb = fill
    tf = sh.text_frame; tf.word_wrap = True
    tf.margin_left = tf.margin_right = Inches(0.15)
    tf.margin_top = tf.margin_bottom = Inches(0.05)
    p = tf.paragraphs[0]; p.text = text; p.alignment = PP_ALIGN.CENTER
    p.font.size = Pt(size); p.font.bold = True; p.font.color.rgb = text_color


def divider(slide, left, top, width, color=C_BORDER):
    line = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE,
                                   Inches(left), Inches(top),
                                   Inches(width), Inches(0.015))
    line.fill.solid(); line.fill.fore_color.rgb = color
    line.line.color.rgb = color


# ─── SLIDE 1  Title ───────────────────────────────────────────────────────────

def slide_01_title(prs):
    s = blank(prs)
    top_bar(s)

    # Large title
    tb = s.shapes.add_textbox(Inches(0.85), Inches(1.1), Inches(12.2), Inches(1.8))
    tf = tb.text_frame; tf.word_wrap = True
    p = tf.paragraphs[0]
    p.text = "Physics-Based Modeling of the\nMagnetometer Array"
    p.font.size = Pt(34); p.font.bold = True
    p.font.color.rgb = C_NAVY; p.font.name = FH

    tb2 = s.shapes.add_textbox(Inches(0.85), Inches(2.85), Inches(12.2), Inches(0.45))
    p2 = tb2.text_frame.paragraphs[0]
    p2.text = "Simulation, observability, and synthetic-aperture localization"
    p2.font.size = Pt(16); p2.font.italic = True
    p2.font.color.rgb = C_MUTED; p2.font.name = FB

    # Info card
    sh = card(s, 0.85, 3.55, 11.6, 3.25)
    tf3 = sh.text_frame; tf3.word_wrap = True
    tf3.margin_left = tf3.margin_right = Inches(0.45)
    tf3.margin_top = Inches(0.30)

    p0 = tf3.paragraphs[0]
    p0.text = "SCOPE & FRAMING"
    p0.font.size = Pt(10); p0.font.bold = True
    p0.font.color.rgb = C_BLUE; p0.space_after = Pt(10)

    lines = [
        ("Context: ", "The hardware team is developing and testing the physical sensor array. My work runs in parallel on the modeling and simulation side."),
        ("My contribution: ", "A physics-based simulation of the array, used to study geometry, observability, and the limits of static sensing — and to identify what experiments would be most informative."),
        ("Today: ", "I'll walk through what I built, how I validated it, and what the simulations suggest about array geometry, localization limits, and motion-based sensing."),
    ]
    for bold, rest in lines:
        p = tf3.add_paragraph()
        r1 = p.add_run(); r1.text = bold
        r1.font.bold = True; r1.font.size = Pt(13); r1.font.color.rgb = C_NAVY
        r2 = p.add_run(); r2.text = rest
        r2.font.size = Pt(13); r2.font.color.rgb = C_SLATE
        p.space_after = Pt(9)

    notes(s,
        "My work has focused on building a controllable physics-based simulation of the magnetometer "
        "array, using it to study array geometry and observability, and then using those results to "
        "identify limitations of a stationary array and investigate whether controlled motion can "
        "resolve them.\n\n"
        "I won't spend time reviewing the overall magnetometer project — you all know the research "
        "context. I'll jump straight into what I built and what I found.")


# ─── SLIDE 2  Contribution Overview ──────────────────────────────────────────

def slide_02_contributions(prs):
    s = blank(prs)
    header(s, "Overview", "What I've Built and Investigated")

    sections = [
        ("Simulation", C_NAVY, [
            "Physics-based magnetic dipole model",
            "3×3 planar sensor array, Bz measurements",
            "Noise model and detection threshold",
            "Parameter sweeps and visualization",
        ]),
        ("Analysis", C_NAVY, [
            "Array geometry and aperture/depth scaling",
            "6-parameter sensitivity (Jacobian / SVD)",
            "Observability mapping over source space",
            "Static ambiguity search",
        ]),
        ("Motion (Simulation)", C_NAVY, [
            "Multi-pose Jacobian stacking",
            "X and Z translation comparison",
            "Measurement separation under motion",
            "Proposed hardware validation experiment",
        ]),
    ]

    col_w = 3.7
    col_starts = [0.8, 4.6, 8.4]

    for (title, tc, items), left in zip(sections, col_starts):
        sh = card(s, left, 1.85, col_w, 4.55)
        tf = sh.text_frame; tf.word_wrap = True
        tf.margin_left = tf.margin_right = Inches(0.25)
        tf.margin_top = Inches(0.20)

        p0 = tf.paragraphs[0]
        p0.text = title
        p0.font.bold = True; p0.font.size = Pt(14)
        p0.font.color.rgb = C_BLUE; p0.space_after = Pt(10)

        for item in items:
            pi = tf.add_paragraph()
            pi.text = "• " + item
            pi.font.size = Pt(12); pi.font.color.rgb = C_SLATE
            pi.space_after = Pt(7)

    # Bottom banner
    banner = s.shapes.add_shape(MSO_SHAPE.RECTANGLE,
                                 Inches(0.8), Inches(6.55), Inches(11.7), Inches(0.68))
    banner.fill.solid(); banner.fill.fore_color.rgb = C_NAVY
    banner.line.color.rgb = C_NAVY
    btf = banner.text_frame
    btf.margin_left = Inches(0.30); btf.margin_top = Inches(0.10)
    bp = btf.paragraphs[0]
    bp.text = ("Goal: understand what information the current array can recover, "
               "and what geometry or motion is needed to recover more.")
    bp.font.size = Pt(12.5); bp.font.bold = True
    bp.font.color.rgb = C_WHITE; bp.alignment = PP_ALIGN.CENTER

    notes(s,
        "I'll organize my talk around three blocks of work.\n\n"
        "First, the simulator itself and its validation.\n"
        "Second, a series of geometry and observability analyses.\n"
        "Third, a preliminary investigation of whether motion can recover the "
        "information a static array cannot.\n\n"
        "Each block feeds into the next. The simulation enables the analysis. "
        "The analysis identifies the limitations. And the motion study suggests "
        "what we should test with the hardware.")


# ─── SLIDE 3  Simulation Setup ────────────────────────────────────────────────

def slide_03_setup(prs):
    s = blank(prs)
    header(s, "Simulation", "Simulation Setup",
           "Exactly what the simulation controls, and what it assumes")

    # Left: pipeline
    sh_pipe = card(s, 0.80, 1.85, 5.65, 4.65)
    tf = sh_pipe.text_frame; tf.word_wrap = True
    tf.margin_left = tf.margin_right = Inches(0.30)
    tf.margin_top = Inches(0.25)

    p0 = tf.paragraphs[0]
    p0.text = "Simulation Pipeline"
    p0.font.bold = True; p0.font.size = Pt(13)
    p0.font.color.rgb = C_BLUE; p0.space_after = Pt(12)

    pipeline_items = [
        "Source state  θ = [x, y, z, mx, my, mz]ᵀ",
        "↓  Magnetic dipole model  (point dipole, far field)",
        "↓  3×3 planar sensor array  (9 sensors, z-plane)",
        "↓  9 Bz measurements  (± Gaussian noise)",
        "↓  Inverse / observability analysis",
    ]
    for item in pipeline_items:
        pi = tf.add_paragraph()
        pi.text = item
        pi.font.size = Pt(12); pi.font.color.rgb = C_SLATE
        pi.space_after = Pt(8)

    # Right: assumptions
    sh_assump = card(s, 6.65, 1.85, 5.80, 4.65)
    tf2 = sh_assump.text_frame; tf2.word_wrap = True
    tf2.margin_left = tf2.margin_right = Inches(0.30)
    tf2.margin_top = Inches(0.25)

    p1 = tf2.paragraphs[0]
    p1.text = "Assumptions"
    p1.font.bold = True; p1.font.size = Pt(13)
    p1.font.color.rgb = C_BLUE; p1.space_after = Pt(10)

    assump = [
        ("Array: ", "3×3 sensors, equidistant grid, z = 0 plane"),
        ("Measurements: ", "Bz component only (single-axis)"),
        ("Source model: ", "Ideal magnetic dipole  (point source, far field)"),
        ("Aperture: ", "L = 2s  (outer sensor separation)"),
        ("Detection: ", "Assumed 10 nT threshold (simulation parameter)"),
        ("Noise: ", "Gaussian, IID, for uncertainty studies"),
        ("Near field: ", "Point-dipole model breaks down at small r/d;  "
                         "not modeled here (see appendix)"),
    ]
    for bold, rest in assump:
        pa = tf2.add_paragraph()
        r1 = pa.add_run(); r1.text = bold
        r1.font.bold = True; r1.font.size = Pt(11.5); r1.font.color.rgb = C_NAVY
        r2 = pa.add_run(); r2.text = rest
        r2.font.size = Pt(11.5); r2.font.color.rgb = C_SLATE
        pa.space_after = Pt(7)

    # Bottom note
    nt = s.shapes.add_textbox(Inches(0.85), Inches(6.60), Inches(11.5), Inches(0.55))
    pn = nt.text_frame.paragraphs[0]
    pn.text = ("All six source parameters are treated as free. "
               "Dipole field and Jacobian equations are in the appendix.")
    pn.font.size = Pt(10.5); pn.font.italic = True; pn.font.color.rgb = C_MUTED

    notes(s,
        "The simulator takes a six-parameter source state — 3D position and magnetic moment "
        "vector — and computes the nine Bz readings the array would produce.\n\n"
        "I want to be explicit about the assumptions: single-axis sensors, ideal point-dipole "
        "source model, and a 10 nT detection threshold that I've used as a simulation parameter "
        "— not a measured hardware floor.\n\n"
        "I'll put the dipole equation details in the appendix for anyone who wants them.")


# ─── SLIDE 4  Validation ─────────────────────────────────────────────────────

def slide_04_validation(prs):
    s = blank(prs)
    header(s, "Validation", "Validation: The Simulator Reproduces Known Physics",
           "Three quantitative checks before using the simulator for design questions")

    # Three validation cards
    checks = [
        ("Inverse-cube field decay",
         "B ∝ r⁻³",
         "Measured log-log slope: −3.0000\nExpected: −3  ✓",
         C_GREEN),
        ("Moment scaling",
         "r_max ∝ m^(1/3)",
         "Measured slope: 0.3350\nExpected: 1/3 = 0.3333  ✓",
         C_GREEN),
        ("Detection boundary\n(m = 1 A·m², B_min = 10 nT)",
         "Analytical: 2.7144 m",
         "Simulation: ~2.70 m  ✓",
         C_GREEN),
    ]

    card_left = [0.80, 4.65, 8.50]
    card_w = 3.65

    for (title, eq, result, col), left in zip(checks, card_left):
        sh = card(s, left, 1.85, card_w, 3.00)
        tf = sh.text_frame; tf.word_wrap = True
        tf.margin_left = tf.margin_right = Inches(0.28)
        tf.margin_top = Inches(0.22)

        p0 = tf.paragraphs[0]; p0.text = title
        p0.font.bold = True; p0.font.size = Pt(12.5)
        p0.font.color.rgb = C_NAVY; p0.space_after = Pt(8)

        pe = tf.add_paragraph(); pe.text = eq
        pe.font.size = Pt(14); pe.font.bold = True
        pe.font.color.rgb = C_BLUE; pe.space_after = Pt(10)

        pr = tf.add_paragraph(); pr.text = result
        pr.font.size = Pt(12); pr.font.color.rgb = col

    # Figure: distance decay plot
    f = fig("figures/distance_sweep/distance_sweep.png")
    if f:
        s.shapes.add_picture(f, Inches(0.80), Inches(5.00), width=Inches(5.60))

    f2 = fig("figures/detection_range/detection_range.png")
    if f2:
        s.shapes.add_picture(f2, Inches(6.85), Inches(5.00), width=Inches(5.60))

    # Bottom takeaway
    banner = s.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE,
                                 Inches(0.80), Inches(4.95), Inches(11.7), Inches(0.35))
    # Just a note rather than a banner over the images
    nt = s.shapes.add_textbox(Inches(0.85), Inches(4.95), Inches(11.5), Inches(0.35))
    pn = nt.text_frame.paragraphs[0]
    pn.text = ("Validation complete. The simulator matches known analytical behavior across "
               "field decay, moment scaling, and detection boundaries.")
    pn.font.size = Pt(11); pn.font.bold = True; pn.font.color.rgb = C_NAVY

    notes(s,
        "Before using the simulator to answer design questions, I ran three quantitative checks "
        "against analytical predictions.\n\n"
        "The field amplitude drops with a log-log slope of exactly -3.0000 — as expected for a "
        "magnetic dipole. The maximum detection range scales as m^(1/3) with a measured exponent "
        "of 0.3350, within 0.5% of the theoretical 1/3. And the numerical detection boundary for "
        "a 1 A·m² source at a 10 nT threshold is 2.70 m, versus the analytical 2.7144 m.\n\n"
        "This gives me confidence that the simulator is correctly implementing the dipole physics "
        "before I use it to explore geometry and observability questions.")


# ─── SLIDE 5  Spacing & Geometry ─────────────────────────────────────────────

def slide_05_spacing(prs):
    s = blank(prs)
    header(s, "Geometry Study", "Array Geometry Changes What the Sensors Can See",
           "Spacing does not simply increase sensitivity — it changes which field structure the array samples")

    # Left: text
    lbox = s.shapes.add_textbox(Inches(0.85), Inches(1.88), Inches(5.60), Inches(5.0))
    ltf = lbox.text_frame; ltf.word_wrap = True
    ltf.margin_left = ltf.margin_top = 0

    p0 = ltf.paragraphs[0]; p0.text = "Spacing sweep: 1 cm – 1 m"
    p0.font.bold = True; p0.font.size = Pt(13); p0.font.color.rgb = C_NAVY
    p0.space_after = Pt(12)

    results = [
        ("Vertical dipole — ", "Detection range stays at ~2.71 m across all spacings. "
         "The on-axis field peak always falls on the center sensor; outer sensor position is irrelevant."),
        ("Horizontal dipole — ", "Center Bz measurement is at a field null (Bz ≡ 0 on-axis). "
         "Detection range depends on outer sensors reaching the off-axis field lobes."),
        ("Horizontal range: ", "0.74 m at 1 cm spacing  →  2.05 m at 1 m spacing  (nearly 3× increase)"),
    ]
    for bold, rest in results:
        p = ltf.add_paragraph()
        r1 = p.add_run(); r1.text = bold
        r1.font.bold = True; r1.font.size = Pt(12.5); r1.font.color.rgb = C_BLUE
        r2 = p.add_run(); r2.text = rest
        r2.font.size = Pt(12.5); r2.font.color.rgb = C_SLATE
        p.space_after = Pt(12)

    divider(s, 0.85, 5.40, 5.60)

    nt = s.shapes.add_textbox(Inches(0.85), Inches(5.50), Inches(5.60), Inches(1.35))
    ntf = nt.text_frame; ntf.word_wrap = True
    pn = ntf.paragraphs[0]
    pn.text = ("This shows that the array geometry determines which features of the source "
               "field are sampled — not simply 'more is better.' The implication for aperture "
               "sizing depends on the source orientation and target depth. That is addressed in "
               "the next two slides.")
    pn.font.size = Pt(11.5); pn.font.color.rgb = C_MUTED; pn.font.italic = True

    # Right: figure
    f = fig("figures/spacing_sweep/spacing_detection_range.png")
    if f:
        s.shapes.add_picture(f, Inches(6.75), Inches(1.85), width=Inches(5.75))

    notes(s,
        "I swept sensor spacing from 1 cm to 1 meter and recorded detection range for both "
        "vertical and horizontal dipole orientations.\n\n"
        "For a vertical dipole, spacing has no effect. The center sensor always sits directly "
        "below the source and captures the on-axis peak field. Outer sensors are irrelevant "
        "for detection purposes.\n\n"
        "For a horizontal dipole, the story is different. The vertical field is exactly zero "
        "on the dipole's axis — so the center sensor is blind. Detection relies entirely on "
        "outer sensors sampling the off-axis lobes. With tight spacing, all sensors are in "
        "the null. Wider spacing allows the outer sensors to escape that null, expanding "
        "detection range from 0.74 m to 2.05 m.\n\n"
        "The point is that geometry doesn't simply scale sensitivity uniformly — it changes "
        "which field structure the array samples.")


# ─── SLIDE 6  L/z ────────────────────────────────────────────────────────────

def slide_06_lz(prs):
    s = blank(prs)
    header(s, "Geometry Study", "The Key Geometry Parameter Is L/z",
           "Conditioning is largely controlled by the dimensionless aperture-to-depth ratio")

    # Left: explanation text
    lbox = s.shapes.add_textbox(Inches(0.85), Inches(1.85), Inches(5.55), Inches(4.80))
    ltf = lbox.text_frame; ltf.word_wrap = True; ltf.margin_top = 0

    p0 = ltf.paragraphs[0]; p0.text = "L/z  =  array aperture / source depth"
    p0.font.bold = True; p0.font.size = Pt(14); p0.font.color.rgb = C_NAVY
    p0.space_after = Pt(14)

    regimes = [
        ("Small L/z  (<0.5): ",
         "All sensors see similar field values. Little spatial gradient information. "
         "Very poor conditioning."),
        ("L/z ≈ 1–2: ",
         "Sensors span the peak and the inflection region of the field profile. "
         "Best conditioning observed for this 3×3 geometry."),
        ("Very large L/z  (>5): ",
         "Outer sensors contribute progressively less useful signal, "
         "and conditioning degrades again."),
    ]
    for bold, rest in regimes:
        p = ltf.add_paragraph()
        r1 = p.add_run(); r1.text = bold
        r1.font.bold = True; r1.font.size = Pt(12); r1.font.color.rgb = C_BLUE
        r2 = p.add_run(); r2.text = rest
        r2.font.size = Pt(12); r2.font.color.rgb = C_SLATE
        p.space_after = Pt(12)

    # Scale-invariance note
    divider(s, 0.85, 5.32, 5.55)
    nt = s.shapes.add_textbox(Inches(0.85), Inches(5.42), Inches(5.55), Inches(1.35))
    ntf = nt.text_frame; ntf.word_wrap = True
    pn = ntf.paragraphs[0]
    pn.text = ("When aperture and depth are scaled together, the conditioning "
               "behavior is approximately invariant. Curves for z = 0.1, 0.2, "
               "0.5, and 1.0 m collapse onto each other when plotted against L/z.")
    pn.font.size = Pt(11); pn.font.italic = True; pn.font.color.rgb = C_MUTED

    # Right: figure
    f = fig("figures/scaled_aperture_observability/scaled_best_condition.png")
    if f:
        s.shapes.add_picture(f, Inches(6.70), Inches(1.85), width=Inches(5.80))

    # Important caveat pill
    pill(s, 0.85, 6.90, 5.55, 0.38,
         "Observed for the simulated 3×3 geometry — not a universal hardware rule.",
         fill=C_AMBER)

    notes(s,
        "When I swept aperture L across multiple depths, the condition-number curves for "
        "z = 0.1, 0.2, 0.5, and 1.0 m all collapsed onto the same curve when plotted "
        "against L/z.\n\n"
        "This makes sense: the condition number is dimensionless, and dipole field geometry "
        "is scale-invariant under uniform spatial scaling.\n\n"
        "The practical message is that conditioning is largely determined by L/z. "
        "The best-conditioned region I found for this 3×3 geometry is L/z ≈ 1–2. "
        "Below that, sensors are all sampling nearly the same flat peak. "
        "Above it, outer sensors fall into noise.\n\n"
        "Important caveat: this is the observed regime for this specific simulation geometry. "
        "It is not a universal engineering law.")


# ─── SLIDE 7  Detection ≠ Localization ───────────────────────────────────────

def slide_07_det_vs_loc(prs):
    s = blank(prs)
    header(s, "Observability Analysis", "Detection Does Not Imply Localization",
           "A source can remain detectable while the array no longer satisfies the observability criterion")

    # Left: two example cards
    ex1 = card(s, 0.80, 1.85, 5.65, 2.35)
    tf1 = ex1.text_frame; tf1.word_wrap = True
    tf1.margin_left = tf1.margin_right = Inches(0.28); tf1.margin_top = Inches(0.20)
    p0 = tf1.paragraphs[0]; p0.text = "Array: L = 0.20 m   (10 cm sensor spacing)"
    p0.font.bold = True; p0.font.size = Pt(12.5); p0.font.color.rgb = C_NAVY
    p0.space_after = Pt(10)
    cases = [
        ("z = 0.20 m  →  L/z = 1.0  ", "Well-conditioned region exists  ✓"),
        ("z = 0.50 m  →  L/z = 0.40  ", "Zero locations satisfy κ ≤ 100  ✗"),
    ]
    for bold, rest in cases:
        p = tf1.add_paragraph()
        r1 = p.add_run(); r1.text = bold
        r1.font.bold = True; r1.font.size = Pt(12); r1.font.color.rgb = C_BLUE
        r2 = p.add_run(); r2.text = rest
        r2.font.size = Pt(12); r2.font.color.rgb = C_SLATE
        p.space_after = Pt(9)

    ex2 = card(s, 0.80, 4.30, 5.65, 2.30)
    tf2 = ex2.text_frame; tf2.word_wrap = True
    tf2.margin_left = tf2.margin_right = Inches(0.28); tf2.margin_top = Inches(0.20)
    p1 = tf2.paragraphs[0]
    p1.text = "What κ ≤ 100 means in this simulation"
    p1.font.bold = True; p1.font.size = Pt(12.5); p1.font.color.rgb = C_NAVY
    p1.space_after = Pt(10)
    p2 = tf2.add_paragraph()
    p2.text = ("κ is a dimensionless measure of how unevenly the inverse problem is "
               "conditioned. κ ≤ 100 is the practical classification threshold used here "
               "— not a universal guarantee of millimeter accuracy.")
    p2.font.size = Pt(12); p2.font.color.rgb = C_SLATE

    p3 = tf2.add_paragraph(); p3.space_before = Pt(8)
    p3.text = ("For this 20 cm aperture, increasing L toward L/z ≈ 1–2 is one way to "
               "move back into the well-conditioned regime.")
    p3.font.size = Pt(12); p3.font.color.rgb = C_SLATE; p3.space_after = Pt(5)

    # Right: observability map at z=0.20 (L/z=1)
    f = fig("figures/observability_map/practical_observability_z0.20.png")
    if f:
        s.shapes.add_picture(f, Inches(6.70), Inches(1.85), width=Inches(5.80))

    nt = s.shapes.add_textbox(Inches(6.70), Inches(6.68), Inches(5.80), Inches(0.55))
    pn = nt.text_frame.paragraphs[0]
    pn.text = "Left: z = 0.2 m (L/z = 1.0) — well-conditioned zone visible.   At z = 0.5 m (L/z = 0.4), that zone disappears."
    pn.font.size = Pt(10); pn.font.italic = True; pn.font.color.rgb = C_MUTED

    notes(s,
        "I computed two observability maps for the 20 cm aperture array: one at z = 0.2 m "
        "and one at z = 0.5 m.\n\n"
        "At z = 0.2 m, L/z = 1.0. The map shows a clear well-conditioned region — "
        "the yellow zone in the center where κ ≤ 100.\n\n"
        "At z = 0.5 m, L/z drops to 0.4. The well-conditioned map is completely empty — "
        "no grid point satisfies the criterion. The source is still detectable everywhere, "
        "but the array doesn't contain enough spatial gradient information for reliable inversion "
        "under this criterion.\n\n"
        "I want to be careful here: κ ≤ 100 is a practical simulation threshold, not a "
        "universal engineering law. But the result does illustrate the core point: detection "
        "and localization have different spatial limits, and those limits depend on L/z.")


# ─── SLIDE 8  Sensitivity / SVD ──────────────────────────────────────────────

def slide_08_svd(prs):
    s = blank(prs)
    header(s, "Observability Analysis", "Which Source Changes Are Hardest to Distinguish?",
           "Jacobian singular values quantify the six distinguishable directions in parameter space")

    # Left: text
    lbox = s.shapes.add_textbox(Inches(0.85), Inches(1.85), Inches(5.60), Inches(5.00))
    ltf = lbox.text_frame; ltf.word_wrap = True; ltf.margin_top = 0

    p0 = ltf.paragraphs[0]
    p0.text = "J  =  ∂f/∂θ   (9×6 sensitivity matrix)"
    p0.font.bold = True; p0.font.size = Pt(13); p0.font.color.rgb = C_NAVY
    p0.space_after = Pt(8)

    p1 = ltf.add_paragraph()
    p1.text = ("Each entry tells me how much one sensor reading changes when one source "
               "parameter nudges. SVD then finds the six distinguishable directions in "
               "parameter space, ranked by strength.")
    p1.font.size = Pt(12); p1.font.color.rgb = C_SLATE; p1.space_after = Pt(14)

    svd_rows = [
        ("Large σ  →  ", "That combination of parameter changes produces strong, "
                         "distinct signal across sensors.  Easier to distinguish."),
        ("Small σ  →  ", "That combination produces very little signal variation.  "
                         "Hard to distinguish from noise."),
    ]
    for bold, rest in svd_rows:
        p = ltf.add_paragraph()
        r1 = p.add_run(); r1.text = bold
        r1.font.bold = True; r1.font.size = Pt(12.5); r1.font.color.rgb = C_BLUE
        r2 = p.add_run(); r2.text = rest
        r2.font.size = Pt(12.5); r2.font.color.rgb = C_SLATE
        p.space_after = Pt(12)

    divider(s, 0.85, 4.45, 5.60)

    # Local analysis results
    nt = s.shapes.add_textbox(Inches(0.85), Inches(4.55), Inches(5.60), Inches(1.90))
    ntf = nt.text_frame; ntf.word_wrap = True
    pn = ntf.paragraphs[0]
    pn.text = ("Local analysis at r = [0, 0, 0.2], m = [0, 0, 1]  (2 cm spacing):")
    pn.font.size = Pt(12); pn.font.bold = True; pn.font.color.rgb = C_NAVY
    pn.space_after = Pt(7)

    local_items = [
        "z sensitivity is strongest",
        "x / y sensitivity is weaker",
        "mx / my have the weakest local sensitivity, roughly 120× below z",
        "z and mz are coupled in the dominant modes",
    ]
    for item in local_items:
        pi = ntf.add_paragraph()
        pi.text = "• " + item
        pi.font.size = Pt(11.5); pi.font.color.rgb = C_SLATE
        pi.space_after = Pt(5)

    pill(s, 0.85, 6.55, 5.60, 0.38,
         "The six source parameters are not equally observable.",
         fill=C_NAVY)

    # Right: singular value plot
    f = fig("figures/jacobian_analysis/jacobian_singular_values.png")
    if f:
        s.shapes.add_picture(f, Inches(6.70), Inches(1.85), width=Inches(5.80))

    nt2 = s.shapes.add_textbox(Inches(6.70), Inches(6.75), Inches(5.80), Inches(0.45))
    pn2 = nt2.text_frame.paragraphs[0]
    pn2.text = ("Note: singular values (σ₁–σ₆) correspond to orthogonal combinations of "
                "parameter changes, not individual coordinates.")
    pn2.font.size = Pt(9.5); pn2.font.italic = True; pn2.font.color.rgb = C_MUTED

    notes(s,
        "To understand which aspects of the source are hardest to estimate, I compute the "
        "Jacobian — the 9×6 matrix of partial derivatives — and decompose it with SVD.\n\n"
        "Each singular value tells me how strongly a particular combination of source-parameter "
        "changes shows up across the nine sensor readings. Large singular value means easy to "
        "distinguish. Small singular value means nearly invisible.\n\n"
        "Important: the singular values do not map one-to-one onto x, y, z, mx, my, mz. "
        "They correspond to orthogonal combinations of those parameters.\n\n"
        "In the local analysis at 0.2 m depth with 2 cm spacing: z dominates in column norm. "
        "The mx/my column norms are roughly 120× smaller than z — meaning those parameter changes "
        "produce much less variation across the sensors. The full SV spread is much larger because "
        "SVD combines across all parameters; the 120× is the column-norm comparison for individual "
        "parameters. This tells me that moment orientation is much harder to recover than depth "
        "from this configuration.")


# ─── SLIDE 9  Static Ambiguity ────────────────────────────────────────────────

def slide_09_ambiguity(prs):
    s = blank(prs)
    header(s, "Key Finding", "A Static Array Can Produce Ambiguous Solutions",
           "Two physically different configurations produce measurements that are indistinguishable at the assumed noise level")

    # Left: source configs
    sh_a = card(s, 0.80, 1.85, 5.65, 1.75)
    tf_a = sh_a.text_frame; tf_a.word_wrap = True
    tf_a.margin_left = tf_a.margin_right = Inches(0.28); tf_a.margin_top = Inches(0.18)
    pa0 = tf_a.paragraphs[0]; pa0.text = "Reference source  (Source A)"
    pa0.font.bold = True; pa0.font.size = Pt(12.5); pa0.font.color.rgb = C_NAVY
    pa0.space_after = Pt(8)
    pa1 = tf_a.add_paragraph()
    pa1.text = "r = [0, 0, 0.50] m     m = [0, 0, 1.0] A·m²   (vertical)"
    pa1.font.size = Pt(12.5); pa1.font.color.rgb = C_SLATE

    sh_b = card(s, 0.80, 3.70, 5.65, 2.15)
    tf_b = sh_b.text_frame; tf_b.word_wrap = True
    tf_b.margin_left = tf_b.margin_right = Inches(0.28); tf_b.margin_top = Inches(0.18)
    pb0 = tf_b.paragraphs[0]; pb0.text = "Alternative source  (Source B)"
    pb0.font.bold = True; pb0.font.size = Pt(12.5); pb0.font.color.rgb = C_NAVY
    pb0.space_after = Pt(8)
    alt_items = [
        "r = [0.05, 0, 0.50] m  (5 cm lateral offset)",
        "Moment tilt: ≈ 21°  (mx = 0.372, mz = 0.973)",
        "|m| ≈ 1.042 A·m²",
    ]
    for item in alt_items:
        pi = tf_b.add_paragraph()
        pi.text = item; pi.font.size = Pt(12.5); pi.font.color.rgb = C_SLATE
        pi.space_after = Pt(6)

    # Result box
    sh_res = card(s, 0.80, 5.95, 5.65, 1.30, fill=RGBColor(245, 242, 250),
                  border=RGBColor(140, 80, 200))
    tf_r = sh_res.text_frame; tf_r.word_wrap = True
    tf_r.margin_left = tf_r.margin_right = Inches(0.28); tf_r.margin_top = Inches(0.18)
    pr0 = tf_r.paragraphs[0]; pr0.text = "Measurement discrepancy"
    pr0.font.bold = True; pr0.font.size = Pt(12.5); pr0.font.color.rgb = C_NAVY
    pr0.space_after = Pt(6)
    pr1 = tf_r.add_paragraph()
    pr1.text = "Measurement RMSE across all 9 sensors: 3.067 nT"
    pr1.font.bold = True; pr1.font.size = Pt(13); pr1.font.color.rgb = RGBColor(130, 60, 190)
    pr2 = tf_r.add_paragraph()
    pr2.text = "Peak single-sensor difference: 6.5 nT      Assumed noise floor: 10 nT"
    pr2.font.size = Pt(12); pr2.font.color.rgb = C_SLATE

    # Right: ambiguity map
    f = fig("figures/find_static_ambiguity/static_ambiguity_map.png")
    if f:
        s.shapes.add_picture(f, Inches(6.70), Inches(1.85), width=Inches(5.80))

    # Main takeaway
    banner = s.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE,
                                 Inches(6.70), Inches(6.65), Inches(5.80), Inches(0.60))
    banner.fill.solid(); banner.fill.fore_color.rgb = C_NAVY
    banner.line.color.rgb = C_NAVY
    btf = banner.text_frame; btf.word_wrap = True
    btf.margin_left = Inches(0.20); btf.margin_top = Inches(0.08)
    bp = btf.paragraphs[0]
    bp.text = ("A stationary inversion can admit multiple comparably good source "
               "configurations because the measurements themselves are ambiguous.")
    bp.font.size = Pt(11); bp.font.bold = True; bp.font.color.rgb = C_WHITE

    notes(s,
        "This is probably the strongest concrete finding from the static analysis.\n\n"
        "I ran a search: fix Source A as a vertical dipole directly over the center at 0.5 m. "
        "Then sweep candidate positions and orientations to find the alternative configuration "
        "that best matches Source A's nine sensor readings.\n\n"
        "The closest match I found was Source B: 5 cm lateral offset, 21° tilt, moment "
        "magnitude 1.042 A·m². Across all nine sensors, the measurement RMSE between "
        "Source A and Source B is 3.067 nT. The worst single-sensor difference is 6.5 nT.\n\n"
        "With an assumed noise floor of 10 nT, those two configurations are effectively "
        "indistinguishable from a static snapshot.\n\n"
        "I want to be careful with the language here: I'm not saying the inversion will "
        "definitely jump between solutions — that depends on the specific algorithm. "
        "But the measurements themselves are ambiguous, so any inversion has to deal "
        "with that degeneracy.")


# ─── SLIDE 10  Motion Breaks Ambiguity ───────────────────────────────────────

def slide_10_motion(prs):
    s = blank(prs)
    header(s, "Motion Study", "Motion Breaks the Static Ambiguity",
           "The same two configurations become clearly distinguishable when the array moves")

    # Left: numbers
    lbox = s.shapes.add_textbox(Inches(0.85), Inches(1.85), Inches(5.60), Inches(4.70))
    ltf = lbox.text_frame; ltf.word_wrap = True; ltf.margin_top = 0

    p0 = ltf.paragraphs[0]; p0.text = "Effect of translating the array to x = 0.25 m"
    p0.font.bold = True; p0.font.size = Pt(13); p0.font.color.rgb = C_NAVY
    p0.space_after = Pt(14)

    comparisons = [
        ("Static (x = 0): ",       "RMSE = 3.067 nT"),
        ("At x = 0.25 m: ",        "RMSE = 68.38 nT  (~22× larger)"),
        ("Peak sensor diff: ",      "102.06 nT  (>10× assumed noise floor)"),
    ]
    for bold, rest in comparisons:
        p = ltf.add_paragraph()
        r1 = p.add_run(); r1.text = bold
        r1.font.bold = True; r1.font.size = Pt(13); r1.font.color.rgb = C_BLUE
        r2 = p.add_run(); r2.text = rest
        r2.font.size = Pt(13); r2.font.color.rgb = C_SLATE
        p.space_after = Pt(14)

    divider(s, 0.85, 4.78, 5.60)

    nt = s.shapes.add_textbox(Inches(0.85), Inches(4.92), Inches(5.60), Inches(1.85))
    ntf = nt.text_frame; ntf.word_wrap = True
    pn = ntf.paragraphs[0]
    pn.text = ("Motion creates a synthetic aperture by providing additional viewpoints. "
               "The geometric cancellation that makes the two sources indistinguishable "
               "from the center position does not hold across multiple viewing angles.\n\n"
               "This suggests that controlled platform motion could substantially reduce "
               "the static ambiguity problem.")
    pn.font.size = Pt(12); pn.font.color.rgb = C_SLATE

    pill(s, 0.85, 6.88, 5.60, 0.37,
         "Proposed implementation: Arduino-controlled linear stage  (see Slide 12)",
         fill=C_BLUE)

    # Right: figure
    f = fig("figures/motion_breaks_ambiguity/measurement_separation.png")
    if f:
        s.shapes.add_picture(f, Inches(6.70), Inches(1.85), width=Inches(5.80))

    notes(s,
        "Having found the static ambiguity, I asked whether motion can break it.\n\n"
        "I simulated translating the array along x and computed the measurement discrepancy "
        "between Source A and Source B at each position.\n\n"
        "At x = 0 — the static position — RMSE is 3.067 nT, below the assumed noise floor.\n\n"
        "At x = 0.25 m, RMSE jumps to 68.38 nT — roughly 22 times larger. "
        "The peak single-sensor difference reaches 102 nT.\n\n"
        "The intuition is that the lateral offset and tilt of Source B happen to cancel "
        "each other from the center viewpoint. Translating the array breaks that symmetry "
        "and makes the two sources clearly distinguishable.\n\n"
        "Motion creates a synthetic aperture — instead of adding hardware, "
        "motion gives the same sensors additional viewpoints.")


# ─── SLIDE 11  Multi-Pose Jacobian ────────────────────────────────────────────

def slide_11_multipose(prs):
    s = blank(prs)
    header(s, "Motion Study", "Multiple Poses Add Information",
           "Combining 21 poses (±0.1 m, 9 sensors each) substantially strengthens the weakest observable directions")

    # Left: table + explanation
    lbox = s.shapes.add_textbox(Inches(0.85), Inches(1.85), Inches(5.80), Inches(4.80))
    ltf = lbox.text_frame; ltf.word_wrap = True; ltf.margin_top = 0

    p0 = ltf.paragraphs[0]
    p0.text = "Unnormalized multi-pose Jacobian results  (21 poses, 189 total measurements)"
    p0.font.size = Pt(12); p0.font.bold = True; p0.font.color.rgb = C_NAVY
    p0.space_after = Pt(10)

    # Table as formatted text
    rows = [
        ("Configuration",        "κ (cond.)",      "Weakest σ"),
        ("Static (1 pose)",      "986.42",          "2.319 × 10⁻⁸"),
        ("Z translation",        "255.59",          "4.998 × 10⁻⁷"),
        ("X translation",        "504.78",          "1.998 × 10⁻⁷"),
    ]
    col_widths = [2.10, 1.55, 1.95]
    row_top = 2.60
    for ri, row in enumerate(rows):
        for ci, (cell, w) in enumerate(zip(row, col_widths)):
            left = 0.85 + sum(col_widths[:ci])
            ht = 0.40 if ri == 0 else 0.45
            fill = RGBColor(228, 234, 245) if ri == 0 else (C_BG if ri % 2 == 1 else C_WHITE)
            sh = s.shapes.add_shape(MSO_SHAPE.RECTANGLE,
                                     Inches(left), Inches(row_top + ri*0.43),
                                     Inches(w), Inches(ht))
            sh.fill.solid(); sh.fill.fore_color.rgb = fill
            sh.line.color.rgb = C_BORDER
            tf = sh.text_frame; tf.word_wrap = False
            tf.margin_left = Inches(0.10); tf.margin_top = Inches(0.06)
            p = tf.paragraphs[0]; p.text = cell
            p.font.size = Pt(11)
            p.font.bold = (ri == 0)
            p.font.color.rgb = C_NAVY if ri == 0 else C_SLATE

    row_top2 = 4.70
    improvement_items = [
        ("Z translation: ", "κ improves by ~3.86×,  weakest σ improves by ~21.5×"),
        ("X translation: ", "κ improves by ~1.95×,  weakest σ improves by ~8.6×"),
    ]
    for bold, rest in improvement_items:
        p = ltf.add_paragraph() if False else ltf.paragraphs[0] if False else None
    # Use a separate textbox for clarity
    nt2 = s.shapes.add_textbox(Inches(0.85), Inches(row_top2), Inches(5.80), Inches(1.10))
    ntf2 = nt2.text_frame; ntf2.word_wrap = True
    for bold, rest in improvement_items:
        p2 = ntf2.paragraphs[0] if improvement_items.index((bold, rest)) == 0 else ntf2.add_paragraph()
        r1 = p2.add_run(); r1.text = bold
        r1.font.bold = True; r1.font.size = Pt(12.5); r1.font.color.rgb = C_BLUE
        r2 = p2.add_run(); r2.text = rest
        r2.font.size = Pt(12.5); r2.font.color.rgb = C_SLATE
        p2.space_after = Pt(8)

    p_conc = ntf2.add_paragraph()
    p_conc.text = ("Z translation produces the largest improvement in the weakest observable "
                   "direction in this simulation.")
    p_conc.font.size = Pt(12); p_conc.font.color.rgb = C_SLATE; p_conc.space_after = Pt(6)

    # Normalization caveat
    cav = s.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE,
                              Inches(0.85), Inches(5.90), Inches(5.80), Inches(1.30))
    cav.fill.solid(); cav.fill.fore_color.rgb = RGBColor(255, 248, 235)
    cav.line.color.rgb = C_AMBER
    ctf = cav.text_frame; ctf.word_wrap = True
    ctf.margin_left = ctf.margin_right = Inches(0.20); ctf.margin_top = Inches(0.12)
    cp0 = ctf.paragraphs[0]; cp0.text = "⚠  Normalization caveat"
    cp0.font.bold = True; cp0.font.size = Pt(11.5); cp0.font.color.rgb = C_AMBER
    cp0.space_after = Pt(6)
    cp1 = ctf.add_paragraph()
    cp1.text = ("This multi-pose analysis uses an unnormalized Jacobian. The static geometry "
                "study uses a normalized Jacobian. The absolute κ values are not directly "
                "comparable across the two analyses; only the within-motion relative improvements are.")
    cp1.font.size = Pt(11); cp1.font.color.rgb = C_SLATE

    # Right: singular values plot
    f = fig("figures/moving_array_observability/singular_values.png")
    if f:
        s.shapes.add_picture(f, Inches(6.80), Inches(1.85), width=Inches(5.70))

    nt3 = s.shapes.add_textbox(Inches(6.80), Inches(6.75), Inches(5.70), Inches(0.45))
    pn3 = nt3.text_frame.paragraphs[0]
    pn3.text = ("σ₁–σ₆ are orthogonal combinations of source-parameter changes, "
                "not individual coordinates (x, y, z, mx, my, mz).")
    pn3.font.size = Pt(9.5); pn3.font.italic = True; pn3.font.color.rgb = C_MUTED

    notes(s,
        "To get a global picture of how motion improves observability, I stacked the Jacobians "
        "from 21 array poses — 10 cm to each side in either X or Z, for a total of 189 "
        "sensor measurements — and computed the SVD of the combined matrix.\n\n"
        "Static: κ = 986, weakest σ = 2.3×10⁻⁸.\n"
        "Z translation: κ = 256, weakest σ = 5.0×10⁻⁷ — a 21.5× improvement in the weakest direction.\n"
        "X translation: κ = 505, weakest σ = 2.0×10⁻⁷ — an 8.6× improvement.\n\n"
        "Z translation produces the largest improvement in the weakest observable direction. "
        "X translation is the more practical option for a benchtop rig.\n\n"
        "Important caveat: I need to flag that this multi-pose analysis currently uses an "
        "unnormalized Jacobian, while the static observability study uses normalized Jacobians. "
        "I'm not hiding this — the absolute κ values are not directly comparable, "
        "but the within-motion relative improvements are meaningful.\n\n"
        "Also: the σ labels in the plot represent orthogonal combinations of source parameters, "
        "not individual x, y, z coordinates.")


# ─── SLIDE 12  From Simulation to Hardware ───────────────────────────────────

def slide_12_hardware(prs):
    s = blank(prs)
    header(s, "Next Steps", "From Simulation to Hardware",
           "Proposed experiment to test the simulation predictions against physical sensor data")

    # Four-section card layout
    sections = [
        ("❓  Question",
         "Does the static ambiguity predicted by the simulation appear in the real sensor data, "
         "and does controlled motion reduce it as predicted?"),
        ("⚙  Proposed Experiment",
         "Move the physical 3×3 array through controlled X and/or Z positions while measuring "
         "a fixed, calibrated magnetic source. Record raw sensor readings at each pose."),
        ("📏  What to Measure",
         "• Actual sensor noise (spectral density, not assumed)\n"
         "• Sensor-to-sensor offset and calibration variation\n"
         "• Mechanical positioning repeatability\n"
         "• Background field contribution"),
        ("🔁  Compare",
         "B_simulation  ↔  B_hardware\n\n"
         "Use measured hardware noise and errors to replace the idealized simulation "
         "assumptions and re-evaluate the ambiguity metric."),
    ]

    for i, (title, text) in enumerate(sections):
        col = i % 2; row = i // 2
        left = 0.80 + col * 6.05
        top = 1.88 + row * 2.65
        sh = card(s, left, top, 5.75, 2.45)
        tf = sh.text_frame; tf.word_wrap = True
        tf.margin_left = tf.margin_right = Inches(0.28)
        tf.margin_top = Inches(0.22)
        p0 = tf.paragraphs[0]; p0.text = title
        p0.font.bold = True; p0.font.size = Pt(13); p0.font.color.rgb = C_NAVY
        p0.space_after = Pt(8)
        p1 = tf.add_paragraph(); p1.text = text
        p1.font.size = Pt(12); p1.font.color.rgb = C_SLATE

    # Status table
    status_sh = s.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE,
                                    Inches(0.80), Inches(7.05), Inches(11.6), Inches(0.55))
    status_sh.fill.solid(); status_sh.fill.fore_color.rgb = C_BG
    status_sh.line.color.rgb = C_BORDER
    stf = status_sh.text_frame; stf.word_wrap = True
    stf.margin_left = Inches(0.25); stf.margin_top = Inches(0.10)
    sp = stf.paragraphs[0]
    r1 = sp.add_run(); r1.text = "Completed: "
    r1.font.bold = True; r1.font.size = Pt(11.5); r1.font.color.rgb = C_GREEN
    r2 = sp.add_run()
    r2.text = "simulator, validation, geometry sweeps, observability, ambiguity search, preliminary motion simulation.   "
    r2.font.size = Pt(11.5); r2.font.color.rgb = C_SLATE
    r3 = sp.add_run(); r3.text = "Proposed: "
    r3.font.bold = True; r3.font.size = Pt(11.5); r3.font.color.rgb = C_AMBER
    r4 = sp.add_run()
    r4.text = "Arduino linear stage, motion experiment, hardware noise characterization, simulation/hardware comparison."
    r4.font.size = Pt(11.5); r4.font.color.rgb = C_SLATE

    notes(s,
        "The simulation results generate a concrete prediction: the static ambiguity should "
        "appear in real hardware data, and motion should reduce it.\n\n"
        "The proposed experiment is to move the physical array through controlled X and/or Z "
        "positions — using an Arduino-controlled linear stage — while measuring a fixed "
        "calibrated source, and compare the raw sensor readings against simulation predictions.\n\n"
        "The key things to measure on the hardware side are the actual sensor noise, "
        "sensor-to-sensor offsets, and mechanical positioning error. Those replace the "
        "idealized assumptions currently in the simulator.\n\n"
        "I want to be explicit about what is done versus what is proposed. "
        "Everything through the motion simulation is completed. "
        "The physical linear stage and hardware experiment are next steps.")


# ─── APPENDIX SLIDES ─────────────────────────────────────────────────────────

def slide_app_math(prs):
    """Single appendix slide with key equations."""
    s = blank(prs)
    top_bar(s, color=C_SLATE)
    tag(s, "Appendix — Mathematical Reference")
    heading(s, "Equations and Model Definitions", size=18)

    # Two columns of equation cards
    eq_items = [
        ("Dipole field (3D):",
         "B(r) = (μ₀/4π) [ 3(m·r̂)r̂ − m ] / r³"),
        ("Bz component:",
         "Bz = (μ₀/4π) [ 3mz(z/r)²/r³ + terms from mx, my ]   (full form in source)"),
        ("Source parameter vector:",
         "θ = [x, y, z, mx, my, mz]ᵀ"),
        ("Measurement model:",
         "b = f(θ) + ε,   ε ~ N(0, σ²I)"),
        ("Jacobian:",
         "J = ∂f/∂θ  (9×6)"),
        ("Jacobian normalization:",
         "J_norm = J · diag(scales),  scales = [z, z, z, |m|, |m|, |m|]"),
        ("SVD:",
         "J = U Σ Vᵀ,    σ₁ ≥ σ₂ ≥ … ≥ σ₆ ≥ 0"),
        ("Condition number:",
         "κ = σ_max / σ_min  (dimensionless, measures conditioning unevenness)"),
        ("Fisher information (position only):",
         "F = (1/σ²) JᵀJ"),
        ("CRLB:",
         "Cov(θ̂) ≥ F⁻¹"),
        ("Linear moment model:",
         "b = A m,    A constructed from unit-moment dipole fields"),
        ("Detection threshold:",
         "max|Bz| ≥ B_min = 10 nT  (simulation parameter, not measured hardware floor)"),
        ("Ambiguity RMSE:",
         "RMSE = √(mean_i (b_A,i − b_B,i)²)"),
        ("Multi-pose Jacobian:",
         "J_stack = [J(pose₁)ᵀ  J(pose₂)ᵀ … J(pose_N)ᵀ]ᵀ  (unnormalized in motion study)"),
    ]

    col1 = eq_items[:7]; col2 = eq_items[7:]
    for items, left, width in [(col1, 0.75, 5.90), (col2, 6.85, 5.90)]:
        top = 1.75
        for (label, eq) in items:
            sh = card(s, left, top, width, 0.57)
            tf = sh.text_frame; tf.word_wrap = True
            tf.margin_left = Inches(0.18); tf.margin_top = Inches(0.06)
            p0 = tf.paragraphs[0]
            r1 = p0.add_run(); r1.text = label + "  "
            r1.font.bold = True; r1.font.size = Pt(10); r1.font.color.rgb = C_NAVY
            r2 = p0.add_run(); r2.text = eq
            r2.font.size = Pt(10); r2.font.color.rgb = C_SLATE
            top += 0.61

    nt = s.shapes.add_textbox(Inches(0.75), Inches(7.10), Inches(12.0), Inches(0.40))
    pn = nt.text_frame.paragraphs[0]
    pn.text = ("Note: singular values σ₁–σ₆ represent orthogonal combinations of source-parameter "
               "changes — they do not correspond one-to-one to individual parameters (x, y, z, mx, my, mz).")
    pn.font.size = Pt(10); pn.font.italic = True; pn.font.color.rgb = C_MUTED

    notes(s,
        "Full equation reference for discussion. "
        "Key reminder: singular values are not individual parameter sensitivities — "
        "they are the principal axes of the combined 9×6 measurement-to-parameter map.")


# ─── MAIN ─────────────────────────────────────────────────────────────────────

def build():
    prs = Presentation()
    prs.slide_width  = Inches(13.333)
    prs.slide_height = Inches(7.5)

    slide_01_title(prs)
    slide_02_contributions(prs)
    slide_03_setup(prs)
    slide_04_validation(prs)
    slide_05_spacing(prs)
    slide_06_lz(prs)
    slide_07_det_vs_loc(prs)
    slide_08_svd(prs)
    slide_09_ambiguity(prs)
    slide_10_motion(prs)
    slide_11_multipose(prs)
    slide_12_hardware(prs)
    slide_app_math(prs)  # Appendix

    out = os.path.join(ROOT, "magnetic_localization_research.pptx")
    prs.save(out)
    print(f"Saved: {out}")
    print(f"Slides: {len(prs.slides)}")


if __name__ == "__main__":
    build()
