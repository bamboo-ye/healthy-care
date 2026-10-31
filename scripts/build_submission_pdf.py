#!/usr/bin/env python3
"""Render the five-page competition brief; no external calls or fabricated evidence."""
from pathlib import Path
import re
from xml.sax.saxutils import escape
from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.pagesizes import A4
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak, Table, TableStyle, Image
from pypdf import PdfReader
from reportlab.lib.utils import ImageReader

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'output/pdf/health-companion-brief.pdf'
FONT=Path('/System/Library/Fonts/Supplemental/Arial Unicode.ttf')
# Supply a font path when reproducing on a different OS.
import os
FONT=Path(os.getenv('HEALTH_BRIEF_FONT',str(FONT)))
pdfmetrics.registerFont(TTFont('BriefCJK',str(FONT)))
INK=colors.HexColor('#304c3d');GREEN=colors.HexColor('#287453');MUTED=colors.HexColor('#687a6a');PALE=colors.HexColor('#edf4e9')
styles={
 'title':ParagraphStyle('title',fontName='BriefCJK',fontSize=22,leading=31,textColor=INK,spaceAfter=16,wordWrap='CJK'),
 'body':ParagraphStyle('body',fontName='BriefCJK',fontSize=10.2,leading=18,textColor=INK,spaceAfter=14,wordWrap='CJK',alignment=TA_LEFT),
 'small':ParagraphStyle('small',fontName='BriefCJK',fontSize=8,leading=13,textColor=MUTED,spaceAfter=10,wordWrap='CJK'),
 'cell':ParagraphStyle('cell',fontName='BriefCJK',fontSize=9,leading=15,textColor=INK,wordWrap='CJK'),
}
def paragraph(text,kind='body'):
    text=text.replace('—','-').replace('→',' → ')
    text=escape(text)
    text=re.sub(r'\[([^\]]+)\]\((https://[^\s)]+)\)',r'<link href="\2" color="#287453"><u>\1</u></link>',text)
    return Paragraph(text,styles[kind])

def decorate(canvas,doc):
    canvas.saveState()
    w,h=A4
    canvas.setFillColor(colors.HexColor('#f9fcf6'));canvas.rect(0,0,w,h,fill=1,stroke=0)
    canvas.setFillColor(GREEN);canvas.rect(0,h-13,w,13,fill=1,stroke=0)
    canvas.setFont('BriefCJK',9);canvas.setFillColor(GREEN)
    canvas.drawString(48,h-42,'伴AI · 健康伙伴')
    canvas.setFont('BriefCJK',8);canvas.setFillColor(MUTED)
    canvas.drawRightString(w-48,h-42,'AI in Action: Science Forward')
    canvas.setStrokeColor(colors.HexColor('#d8e5d0'));canvas.line(48,49,w-48,49)
    canvas.drawString(48,33,'合成资料技术验收 · 已取得真实平台运行证据')
    canvas.drawRightString(w-48,33,f'{doc.page} / 5  |  2026.10.26')
    canvas.restoreState()

source=(ROOT/'docs/submission/project-brief.md').read_text()
sections=re.split(r'^## 第\d页 · ',source,flags=re.M)[1:]
assert len(sections)==5
story=[]
for index,section in enumerate(sections):
    title,body=section.split('\n',1)
    story.append(paragraph(f'{index+1:02d}  {title}','title'))
    blocks=re.split(r'\n\s*\n',body.strip())
    for block in blocks:
        if block.startswith('|'):
            rows=[]
            for line in block.splitlines():
                values=[v.strip() for v in line.strip().strip('|').split('|')]
                if all(re.fullmatch(r'[: -]+',v) for v in values):continue
                rows.append([paragraph(v,'cell') for v in values])
            table=Table(rows,colWidths=([140,65,195,70] if len(rows[0])==4 else [145,180,145]),hAlign='LEFT',repeatRows=1)
            table.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),PALE),('VALIGN',(0,0),(-1,-1),'TOP'),('LEFTPADDING',(0,0),(-1,-1),10),('RIGHTPADDING',(0,0),(-1,-1),10),('TOPPADDING',(0,0),(-1,-1),9),('BOTTOMPADDING',(0,0),(-1,-1),9),('LINEBELOW',(0,0),(-1,-1),.4,colors.HexColor('#d8e5d0'))]))
            story.extend([table,Spacer(1,15)])
        else:
            kind='small' if 'c4fae359' in block else 'body'
            # Keep identifiers legible and wrappable without inserting characters into them.
            story.append(paragraph(block.replace('\n',' '),kind))
    screenshots={0:('deployment-login.png','主部署实际入口 - 独立健康应用'),2:('sciencepal-completed-20261023.png','SciencePal实际任务 - 平台执行与产物已完成')}
    if index in screenshots:
        filename,caption=screenshots[index];path=ROOT/'docs/screenshots'/filename
        width,height=ImageReader(str(path)).getSize();factor=min(470/width,(180 if index==3 else 235)/height)
        story.extend([Spacer(1,14),paragraph(caption,'small'),Image(str(path),width=width*factor,height=height*factor,hAlign='LEFT')])
    if index==1:
        rows=[['责任边界','持久化与核对'],['Go业务与worker','确认事务、幂等回执、角色和用途授权'],['LangGraph运行时','持久检查点、中断恢复、受限工具'],['PostgreSQL / Redis','事实不依赖缓存；丢失缓存可回源'],['部署与恢复','9份迁移、每日备份、独立恢复验收']]
        table=Table([[paragraph(v,'cell') for v in row] for row in rows],colWidths=[150,320])
        table.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),PALE),('VALIGN',(0,0),(-1,-1),'TOP'),('TOPPADDING',(0,0),(-1,-1),10),('BOTTOMPADDING',(0,0),(-1,-1),10),('LINEBELOW',(0,0),(-1,-1),.4,colors.HexColor('#d8e5d0'))]))
        story.extend([Spacer(1,18),table])
    if index<4:story.append(PageBreak())
OUT.parent.mkdir(parents=True,exist_ok=True)
SimpleDocTemplate(str(OUT),pagesize=A4,rightMargin=48,leftMargin=48,topMargin=77,bottomMargin=67,title='伴AI·健康伙伴 - 五页项目说明',author='伴AI·健康伙伴项目',subject='Synthetic technical validation with real multimodal model and SciencePal execution').build(story,onFirstPage=decorate,onLaterPages=decorate)
reader=PdfReader(OUT)
assert len(reader.pages)==5,f'Expected exactly five pages; got {len(reader.pages)}'
for i,page in enumerate(reader.pages):
    assert f'{i+1:02d}' in page.extract_text(),f'Missing section on page {i+1}'
print(f'Created {OUT} (5 pages)')
