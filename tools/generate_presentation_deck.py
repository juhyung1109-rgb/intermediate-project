# -*- coding: utf-8 -*-
"""
SEMI-GUARD Presentation Deck Generator
Generates an 18-slide, 16:9 widescreen, professional PowerPoint presentation
using python-pptx with embedded high-resolution figures, structured metric cards,
tables, and comprehensive speaker notes.
"""

import os
import sys
from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.enum.text import PP_ALIGN
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE

# Color Palette
DARK_BG = RGBColor(11, 19, 43)        # #0B132B Deep Space Navy
LIGHT_BG = RGBColor(248, 250, 252)    # #F8FAFC Slate 50
CARD_BG = RGBColor(255, 255, 255)     # White
CARD_BORDER = RGBColor(203, 213, 225) # #CBD5E1 Slate 300
PRIMARY = RGBColor(37, 99, 235)       # #2563EB Blue 600
PRIMARY_DARK = RGBColor(15, 23, 42)   # #0F172A Slate 900
PRIMARY_SOFT = RGBColor(239, 246, 255)# #EFF6FF Blue 50
SUCCESS = RGBColor(5, 150, 105)       # #059669 Emerald 600
SUCCESS_SOFT = RGBColor(236, 253, 245)# Emerald 50
DANGER = RGBColor(220, 38, 38)        # #DC2626 Red 600
DANGER_SOFT = RGBColor(254, 242, 242) # Red 50
WARNING = RGBColor(217, 119, 6)       # #D97706 Amber 600
WARNING_SOFT = RGBColor(254, 243, 199)# Amber 50
TEXT_MAIN = RGBColor(30, 41, 59)      # #1E293B Slate 800
TEXT_MUTED = RGBColor(100, 116, 139)  # #64748B Slate 500
TEXT_LIGHT = RGBColor(241, 245, 249)  # #F1F5F9 Slate 100
ACCENT_CYAN = RGBColor(2, 132, 199)   # #0284C7 Sky 600

def set_slide_background(slide, color):
    background = slide.background
    fill = background.fill
    fill.solid()
    fill.fore_color.rgb = color

def add_header(slide, category, title, subtitle):
    # Category Tag
    tx_box = slide.shapes.add_textbox(Inches(0.8), Inches(0.4), Inches(11.7), Inches(0.4))
    tf = tx_box.text_frame
    tf.word_wrap = True
    tf.margin_left = tf.margin_top = tf.margin_right = tf.margin_bottom = 0
    p = tf.paragraphs[0]
    p.text = category.upper()
    p.font.size = Pt(11)
    p.font.bold = True
    p.font.color.rgb = PRIMARY
    p.font.name = "Pretendard"

    # Title
    p2 = tf.add_paragraph()
    p2.text = title
    p2.font.size = Pt(22)
    p2.font.bold = True
    p2.font.color.rgb = PRIMARY_DARK
    p2.font.name = "Pretendard"

    # Subtitle
    if subtitle:
        p3 = tf.add_paragraph()
        p3.text = subtitle
        p3.font.size = Pt(12)
        p3.font.color.rgb = TEXT_MUTED
        p3.font.name = "Pretendard"

def add_footer(slide, current_slide, total_slides=18):
    tx_box = slide.shapes.add_textbox(Inches(0.8), Inches(7.05), Inches(11.7), Inches(0.35))
    tf = tx_box.text_frame
    tf.word_wrap = True
    tf.margin_left = tf.margin_top = tf.margin_right = tf.margin_bottom = 0
    p = tf.paragraphs[0]
    p.text = f"SEMI-GUARD: 반도체 공정 결함 진단 & 설비 예지보전 플랫폼  |  Slide {current_slide} of {total_slides}  |  2026 Fab AI Project"
    p.font.size = Pt(9.5)
    p.font.color.rgb = TEXT_MUTED
    p.font.name = "Pretendard"

def add_card(slide, left, top, width, height, bg_color=CARD_BG, border_color=CARD_BORDER):
    shape = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, left, top, width, height)
    shape.fill.solid()
    shape.fill.fore_color.rgb = bg_color
    if border_color:
        shape.line.color.rgb = border_color
        shape.line.width = Pt(1.2)
    else:
        shape.line.fill.background()
    return shape

def add_metric_badge(slide, left, top, width, height, label, value, subtext, color=PRIMARY, bg_color=PRIMARY_SOFT):
    add_card(slide, left, top, width, height, bg_color=bg_color, border_color=color)
    tx_box = slide.shapes.add_textbox(left + Inches(0.15), top + Inches(0.12), width - Inches(0.3), height - Inches(0.24))
    tf = tx_box.text_frame
    tf.word_wrap = True
    tf.margin_left = tf.margin_top = tf.margin_right = tf.margin_bottom = 0
    
    p0 = tf.paragraphs[0]
    p0.text = label
    p0.font.size = Pt(11)
    p0.font.bold = True
    p0.font.color.rgb = color
    p0.font.name = "Pretendard"
    
    p1 = tf.add_paragraph()
    p1.text = value
    p1.font.size = Pt(22)
    p1.font.bold = True
    p1.font.color.rgb = color
    p1.font.name = "Pretendard"
    
    if subtext:
        p2 = tf.add_paragraph()
        p2.text = subtext
        p2.font.size = Pt(9.5)
        p2.font.color.rgb = TEXT_MUTED
        p2.font.name = "Pretendard"

def add_notes(slide, notes_text):
    notes_slide = slide.notes_slide
    text_frame = notes_slide.notes_text_frame
    text_frame.text = notes_text

print("Helper functions defined.")
