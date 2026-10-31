#!/usr/bin/env python3
"""Five-page, evidence-based AI4Science project description (2026-10-30)."""
from pathlib import Path
from xml.sax.saxutils import escape
import json
import math

from reportlab.pdfgen import canvas
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import Paragraph, Table, TableStyle
from reportlab.graphics.barcode import qr
from reportlab.graphics.shapes import Drawing
from reportlab.graphics import renderPDF
from pypdf import PdfReader

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT/'output/pdf/health-companion-project-description.pdf'
QA = ROOT/'tmp/pdfs/project-description'
OUT.parent.mkdir(parents=True,exist_ok=True)
QA.mkdir(parents=True,exist_ok=True)
W,H = A4
M = 42
CW = W-2*M
INK = '#193e2e'
GREEN = '#28684a'
MUTED = '#627a68'
PALE = '#e5efdf'
BG = '#f5f8f0'
LINE = '#d6e3d0'
AMBER = '#aa7632'
SAND = '#f7eedb'
WHITE = '#ffffff'
SHARE = 'https://sciencepal.ai/share/65ecd584-6adf-4000-88d9-4004e3f82a65'
BENCH = json.loads((ROOT/'output/recording-benchmark-platform-evidence-20261024/report.json').read_text())
pdfmetrics.registerFont(TTFont('CJK','/System/Library/Fonts/Supplemental/Arial Unicode.ttf'))
pdfmetrics.registerFont(TTFont('DocSans','/System/Library/Fonts/Supplemental/Arial.ttf'))
pdfmetrics.registerFont(TTFont('DocSansBold','/System/Library/Fonts/Supplemental/Arial Bold.ttf'))
C = canvas.Canvas(str(OUT),pagesize=A4,pageCompression=1)
C.setTitle('伴AI·健康伙伴 | 项目说明')
C.setAuthor('伴AI·健康伙伴项目（个人参赛）')
C.setSubject('AI4Science：院外轻症连续记录、用药线索与可复核科研工作流')
C.setCreator('ReportLab / Codex-assisted project document')
BOUNDS=[]


def col(value): return colors.HexColor(value)


def rect(x,top,w,h,fill=WHITE,stroke=None,r=10):
    C.setFillColor(col(fill))
    C.setStrokeColor(col(stroke or fill))
    C.setLineWidth(.7)
    C.roundRect(x,H-top-h,w,h,r,fill=1,stroke=bool(stroke))


def text(s,x,top,size=10,color=INK,font='CJK'):
    font={'Helvetica':'DocSans','Helvetica-Bold':'DocSansBold'}.get(font,font)
    C.setFillColor(col(color));C.setFont(font,size)
    C.drawString(x,H-top-size*.83,s)


def right(s,x,top,size=9,color=MUTED,font='CJK'):
    font={'Helvetica':'DocSans','Helvetica-Bold':'DocSansBold'}.get(font,font)
    C.setFillColor(col(color));C.setFont(font,size)
    C.drawRightString(x,H-top-size*.83,s)


def p(s,x,top,w,size=10.3,leading=16.8,color=INK,maxh=None):
    style=ParagraphStyle('p',fontName='CJK',fontSize=size,leading=leading,textColor=col(color),
                         wordWrap='CJK',spaceAfter=0,splitLongWords=True)
    para=Paragraph(escape(s).replace('\n','<br/>'),style)
    _,h=para.wrap(w,1000)
    if maxh is not None:
        assert h<=maxh+.2,(C.getPageNumber(),s[:25],h,maxh)
    assert top+h<=H-49,(C.getPageNumber(),s[:20],top+h)
    para.drawOn(C,x,H-top-h)
    BOUNDS.append({'page':C.getPageNumber(),'text':s,'x':x,'top':top,'width':w,'height':h})
    return h


def badge(label,x,top,w,fill=PALE,color=GREEN):
    rect(x,top,w,22,fill,r=11)
    C.setFont('CJK',8.8);C.setFillColor(col(color));C.drawCentredString(x+w/2,H-top-14.7,label)


def section(label,top):
    rect(M,top+2,3.5,13,GREEN,r=1.5)
    text(label,M+12,top,12.1,GREEN)


def card(x,top,w,h,title,body,accent=GREEN,size=10):
    rect(x,top,w,h,WHITE,LINE)
    compact=h<=85
    rect(x+14,top+(14 if compact else 16),3,13,accent,r=1)
    p(title,x+26,top+(12 if compact else 14),w-40,11.3 if compact else 12,15 if compact else 17,accent,maxh=36)
    offset=36 if compact else 47
    p(body,x+16,top+offset,w-32,size,13.5 if compact else 16.3,MUTED,maxh=h-offset-10)


def arrow(x1,top,x2,color=GREEN,dashed=False):
    C.setStrokeColor(col(color));C.setFillColor(col(color));C.setLineWidth(1.1)
    C.setDash([3,2] if dashed else [])
    C.line(x1,H-top,x2-4,H-top);C.setDash([])
    path=C.beginPath();path.moveTo(x2,H-top);path.lineTo(x2-5,H-top+3);path.lineTo(x2-5,H-top-3);path.close()
    C.drawPath(path,fill=1,stroke=0)


def vline(x,top1,top2,color=LINE):
    C.setStrokeColor(col(color));C.setLineWidth(.8);C.line(x,H-top1,x,H-top2)


def table(rows,widths,top,maxh):
    cells=[]
    for i,row in enumerate(rows):
        style=ParagraphStyle('cell',fontName='CJK',fontSize=9.3,leading=14.2,
                             textColor=col(WHITE if i==0 else INK),wordWrap='CJK')
        cells.append([Paragraph(escape(str(v)).replace('\n','<br/>'),style) for v in row])
    t=Table(cells,colWidths=widths,hAlign='LEFT')
    t.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),col(GREEN)),
                          ('ROWBACKGROUNDS',(0,1),(-1,-1),[col(WHITE),col('#f0f5eb')]),
                          ('VALIGN',(0,0),(-1,-1),'TOP'),('LEFTPADDING',(0,0),(-1,-1),10),
                          ('RIGHTPADDING',(0,0),(-1,-1),10),('TOPPADDING',(0,0),(-1,-1),9),
                          ('BOTTOMPADDING',(0,0),(-1,-1),9),('LINEBELOW',(0,0),(-1,-1),.4,col(LINE))]))
    _,h=t.wrap(CW,1000)
    assert h<=maxh,(top,h,maxh)
    t.drawOn(C,M,H-top-h)
    return h


def page(n,title,deck):
    C.setFillColor(col(BG));C.rect(0,0,W,H,fill=1,stroke=0)
    C.setFillColor(col(GREEN));C.rect(0,H-8,W,8,fill=1,stroke=0)
    text('伴AI·健康伙伴',M,30,10.8,GREEN)
    right('AI IN ACTION / SCIENCE FORWARD',W-M,31,8.2,MUTED,'Helvetica')
    C.setStrokeColor(col(LINE));C.line(M,H-56,W-M,H-56)
    badge(f'{n:02d} / 05',M,76,61)
    p(title,M,112,CW,23.5,32,INK,maxh=65)
    p(deck,M,153,CW,10.6,16.4,MUTED,maxh=33)
    C.setStrokeColor(col(LINE));C.line(M,49,W-M,49)
    text('项目说明 · 个人参赛',M,H-34,8.1,MUTED)
    right(f'{n} / 5   |   2026.10.30',W-M,H-34,8.1,MUTED,'Helvetica')


def kpi(x,top,w,value,label,detail=None):
    rect(x,top,w,62,WHITE,LINE)
    text(value,x+14,top+10,24,GREEN,'Helvetica-Bold')
    text(label,x+14,top+42,9.1,MUTED)
    if detail:right(detail,x+w-12,top+15,8,MUTED)


def page_one():
    page(1,'让院外日常，连接可追溯研究','伴AI·健康伙伴：面向日常轻症的持续关照与科研工作流')
    # The established green mascot is decorative; all important text is selectable.
    C.drawImage(str(ROOT/'apps/web/public/assets/health-mascot-green.png'),W-M-78,H-79-78,
                width=78,height=78,mask='auto',preserveAspectRatio=True)
    p('许多小病没有进入医院，却经历了症状变化、自主用药和恢复。项目把零散自述连接成连续记录，探索如何同时保留来源、缺失和不确定性，为院外用药研究补充可核实资料。',M,204,CW,10.7,18,maxh=72)
    section('两个可验证的科学问题',282)
    gap=13;w=(CW-gap)/2
    card(M,310,w,114,'01 采集问题','追问与随访能否补充有来源的信息？\n如何避免补造缺失字段？')
    card(M+w+gap,310,w,114,'02 分析问题','统一观察窗口下，连续记录能否支持症状与用药分析，并定位待核实线索？')
    section('目标用户与使用场景',446)
    card(M,474,w,130,'个人健康空间','面向适合自主护理的成年人。通过文字或图片描述日常轻症，确认记录、跟进变化、补记实际用药、设置提醒，并在恢复后继续日常关照。',size=9.8)
    card(M+w+gap,474,w,130,'独立科研工作区','面向临床、药学及公共卫生研究者。在独立用途授权下查看结构化记录，分析覆盖与缺失、比较观察窗口，并回到来源核实用药线索。',size=9.8)
    section('从个人关照到科研的使用闭环',624)
    labels=[('自然对话','用户确认记录'),('连续随访','实际用药与变化'),('独立授权','冻结研究输入'),('科研分析','线索与来源复核')]
    gap=15;w=(CW-gap*3)/4
    for i,(a,z) in enumerate(labels):
        x=M+i*(w+gap)
        rect(x,651,w,64,PALE)
        p(a,x+9,662,w-18,10.7,15,GREEN,maxh=16)
        p(z,x+9,686,w-18,8.8,12,MUTED,maxh=15)
        if i<3:arrow(x+w+3,683,x+w+gap-3,'#91ad8e')
    p('预期价值：帮助用户持续理解自身健康过程；为研究者补充院外观察资料，为识别和减少用药风险积累证据。当前已完成可运行原型、真实服务联调及合成数据方法验证。',M,738,CW,9.4,14.5,MUTED,maxh=45)
    C.showPage()


def page_two():
    page(2,'技术方案与运行架构','Go业务服务、LangGraph对话运行时与SciencePal科研Agent分工协作')
    w=(CW-14)/2
    card(M,198,w,61,'用户端','对话、确认、病程、用药与提醒',size=9)
    card(M+w+14,198,w,61,'科研端','队列、窗口、缺失与来源回查',size=9)
    # Compact boxes with explicit role boundaries, not a speculative agent swarm.
    for x in [M+w/2,M+w+14+w/2]:vline(x,259,275,'#91ad8e')
    rect(M,275,CW,60,GREEN)
    text('Go API + worker',M+15,287,13,WHITE,'Helvetica-Bold')
    p('身份与角色、确认事务、幂等回执、资源版本、附件及用途授权',M+15,310,CW-30,9.7,14,WHITE,maxh=15)
    for x in [M+w/2,M+w+14+w/2]:vline(x,335,351,'#91ad8e')
    card(M,351,w,81,'LangGraph 对话运行时','对接OpenRouter图文模型\n动作草案、确认中断与检查点',size=9.3)
    card(M+w+14,351,w,81,'SciencePal 科研Agent','冻结合成输入与Python执行\n产物回传、真实日志与方法版本',size=9.3)
    rect(M,446,CW,43,PALE)
    p('PostgreSQL / pgvector：事实与版本     Redis：公共知识缓存与限流\nDocker Compose：独立部署、健康检查、备份与恢复',M+13,455,CW-26,9.1,13.5,GREEN,maxh=28)
    section('可靠记录与用途边界',511)
    rows=[['机制','实际实现'],
          ['确认后写入','模型提出动作草案；用户确认后由Go校验归属、版本与事务。未知起病、成分或评分不自动补造。'],
          ['失败可恢复','消息先保存；幂等键防重复；上游格式失败最多重试一次，未校验输出不执行工具。'],
          ['用途分离','结构化研究与影像授权分开；真实记录不默认开放聊天、身份与图片，授权撤回使旧快照失效。']]
    table(rows,[111,CW-111],540,202)
    p('工程证据：32项运行时测试；独立19项真实模型完整流程、6项图文接口检查，以及角色隔离、备份恢复等验收通过。上述检查集合不同，不汇总为医学准确率。',M,746,CW,9.2,14.2,MUTED,maxh=43)
    C.showPage()


def page_three():
    page(3,'SciencePal承担核心科研执行','在平台创作科研Agent，通过API联动，交付可检查、可重跑的分析产物')
    p('“伴AI·健康伙伴｜院外健康科研Agent”已在SciencePal创建并实际运行。用户在科研端选择主题和3/7天窗口，启动任务后由系统冻结输入、派发平台执行，并取回结果供查看与下载。',M,199,CW,10.3,17,maxh=52)
    names=[('冻结输入','JSON + manifest'),('平台核验','哈希与版本'),('实际执行','Python 脚本'),('取回产物','报告 / CSV / 日志'),('独立复核','本地重新计算')]
    gap=11;w=(CW-4*gap)/5
    for i,(a,z) in enumerate(names):
        x=M+i*(w+gap)
        rect(x,271,w,73,GREEN if i==2 else PALE)
        p(a,x+8,285,w-16,10.3,15,WHITE if i==2 else GREEN,maxh=16)
        p(z,x+8,310,w-16,7.8,12,WHITE if i==2 else MUTED,maxh=24)
        if i<4:arrow(x+w+2,308,x+w+gap-2,'#91ad8e')
    rect(M,361,CW,51,SAND)
    p('当前外部执行仅接受合成数据。用户端模型在业务侧运行；SciencePal对冻结记录及已有模型观测实际计算，平台数值由本地独立复核，不以语言模型猜数代替执行。',M+13,372,CW-26,9.2,14,INK,maxh=29)
    section('任务A：患者日与用药信息分析',434)
    rect(M,462,CW,119,WHITE,LINE)
    text('82.4%',M+15,476,29,GREEN,'Helvetica-Bold')
    text('267 / 324 患者日有记录',M+15,513,9.5,MUTED)
    p('固定48名合成参与者、7天窗口。\n按事件结束时间及去重规则形成324个应观察患者日。\n输出32条用药待核对候选，候选不等于证实滥用。',M+185,477,CW-200,9.4,15.2,maxh=63)
    values=[137,103,27,57];labels=['已用 137','明确未用 103','未知 27','无记录 57'];palette=['#53835c','#abc499','#d5be85','#dce3d4']
    x=M+15;y=548
    for n,color in zip(values,palette):
        ww=(CW-30)*n/324;rect(x,y,ww,8,color,r=0);x+=ww
    for i,(label,color) in enumerate(zip(labels,palette)):
        x=M+15+i*(CW-30)/4;rect(x,566,5,5,color,r=0);text(label,x+9,563,7.6,MUTED)
    section('任务B：独立记录组件实验',603)
    p('将48例测试事件中实际采集的模型回复、冻结协议和评分脚本交给SciencePal，执行初始描述、通用追问、定向追问三组评分与模板簇bootstrap。认证API取回的报告与本地独立重算一致；结果详见下一页。',M,631,CW,10.1,16.6,maxh=51)
    rect(M,702,CW,77,PALE)
    text('公开科研运行 · 免登录只读',M+14,715,11,GREEN)
    C.linkURL(SHARE,(M+14,H-732,M+230,H-712),relative=0,thickness=0)
    p('扫码或点击查看独立追问组件实验。\n科研端需专用评审账号，凭据经非公开渠道交付。\n报告、CSV、实际日志、输入哈希和方法版本均留存。',M+14,738,CW-109,8.6,12.2,MUTED,maxh=37)
    widget=qr.QrCodeWidget(SHARE);bounds=widget.getBounds();side=61
    drawing=Drawing(side,side,transform=[side/(bounds[2]-bounds[0]),0,0,side/(bounds[3]-bounds[1]),0,0]);drawing.add(widget)
    renderPDF.draw(drawing,C,W-M-72,H-710-side)
    C.linkURL(SHARE,(W-M-72,H-771,W-M-11,H-710),relative=0,thickness=0)
    C.showPage()


def page_four():
    page(4,'验证结果与统计解释','2026.10.24冻结合成组件实验：保留失败与统计不确定性')
    w=(CW-20)/3
    for i,(value,label) in enumerate([('48','保留测试事件'),('16','测试模板簇'),('3','症状主题')]):kpi(M+i*(w+10),199,w,value,label)
    section('来源支持字段的宏平均召回率',282)
    data=BENCH['summary'];names=[('initial','初始描述'),('generic','通用追问'),('directed','定向追问')]
    axis_x=M+107;axis_w=CW-167
    for tick in [0,25,50,75,100]:
        x=axis_x+axis_w*tick/100;vline(x,319,437,'#dde8d7')
        right(str(tick),x+5,441,7.6,MUTED,'Helvetica')
    for i,(key,label) in enumerate(names):
        y=324+i*39;value=data[key]['event_macro_recall']*100
        text(label,M,y+3,10.2,INK)
        rect(axis_x,y,axis_w,17,'#e5edde',r=3)
        rect(axis_x,y,axis_w*value/100,17,['#b2c9ac','#76a582',GREEN][i],r=3)
        text(f'{value:.2f}%',axis_x+axis_w+9,y+1,11.2,GREEN,'Helvetica-Bold')
        text(f'失败 {data[key]["failures"]}',axis_x+axis_w+9,y+17,7.5,MUTED)
    rect(M,471,CW,97,WHITE,LINE)
    text('定向相对通用：+2.01个百分点',M+13,482,11,GREEN)
    left=M+33;aw=CW-66
    def xx(value):return left+(value+8)/22*aw
    yy=H-526
    C.setStrokeColor(col('#bccfb6'));C.setLineWidth(.8);C.line(left,yy,left+aw,yy)
    for tick in [-5,0,5,10]:
        C.line(xx(tick),yy-3,xx(tick),yy+3);text(str(tick),xx(tick)-4,531,7.5,MUTED,'Helvetica')
    C.setStrokeColor(col(AMBER));C.setDash([2,2]);C.line(xx(0),yy-10,xx(0),yy+15);C.setDash([])
    ci=BENCH['paired_directed_minus_generic']['cluster_bootstrap_95_interval'];estimate=BENCH['paired_directed_minus_generic']['estimate']
    a,z=[v*100 for v in ci];C.setStrokeColor(col(GREEN));C.setLineWidth(2);C.line(xx(a),yy+4,xx(z),yy+4)
    for value in [a,z]:C.line(xx(value),yy-1,xx(value),yy+9)
    C.setFillColor(col(GREEN));C.circle(xx(estimate*100),yy+4,3.5,fill=1,stroke=0)
    p('95%区间 [-4.31, +10.69] 包含0，尚未证明定向策略更优。',M+13,549,CW-26,9.3,13.5,AMBER,maxh=15)
    p('实验设计：60个合成事件按模板簇划分为开发12例、测试48例，覆盖呼吸道、皮肤与胃肠主题。同一真实模型；两类追问各一轮、最多3个字段。固定响应器仅披露被询问的预写事实。',M,588,CW,9.8,15.6,maxh=48)
    p('评分口径：每事件“正确且有已披露来源的非空字段数 / 预设非空字段数”后取平均。失败保留在分母并记0；3次连接中断保留原件。区间按16模板簇进行2000次配对bootstrap。',M,650,CW,9.8,15.6,maxh=48)
    rect(M,712,CW,60,PALE)
    p('事后敏感性分析：排除未知文本后，三组为31.35% / 77.29% / 79.17%；差值+1.875个百分点，95%区间[-4.58, +9.79]仍含0。保留原始主结果，不以此替换。',M+12,724,CW-24,9.1,14.2,GREEN,maxh=43)
    p('这些数值是受限结构化采集组件结果，不是诊断、影像理解或临床治疗准确率。',M,778,CW,7.7,10.5,MUTED,maxh=12)
    C.showPage()


def page_five():
    page(5,'创新点、局限与后续计划','把产品可用性、科研可复核性与用药安全目标放在同一条证据链上')
    section('项目创新点',199)
    innovations=[('以连续健康过程组织研究记录','将症状、实际用药、恢复、缺失与来源放入同一时间轴，面向院外记录的完整性与可核实性设计。'),
                 ('个人关照与研究用途分离','用户端与科研端分工，研究授权独立；真实用户记录与外部科研执行保留明确的数据边界。'),
                 ('执行产物与复核依据一起交付','SciencePal实际运行、输入哈希、方法版本与本地重算共同构成复现证据，支持从结果回到来源。')]
    for i,(title,body) in enumerate(innovations):
        top=226+i*72
        rect(M,top,CW,62,WHITE,LINE)
        text(f'0{i+1}',M+12,top+12,19,GREEN,'Helvetica-Bold')
        p(title,M+49,top+10,CW-62,10.8,15,GREEN,maxh=16)
        p(body,M+49,top+32,CW-62,9,13.4,MUTED,maxh=28)
    section('当前局限',461)
    p('全部实验与演示案例为合成数据。字段化初始输入、固定响应器、单模型单轮、模板相关性及未知/null编码歧义限制外部效度；尚无独立真人可用性反馈或临床效能验证。',M,489,CW,9.5,15,maxh=46)
    p('当前提供护理参考、用药记录与线索核对，具体产品用量未发布。在线医生问诊与处方确认、购药尚未接入；早期疾病识别、风险降低及耐药结局均未验证，不据此提出效果结论。',M,543,CW,9.5,15,maxh=46)
    section('下一阶段计划',602)
    plans=[('1  先固定测量定义','澄清未知编码，新增独立自然语言留出集与标注，比较追问预算、信息增量和用户负担。'),
           ('2  再验证真实交互','开展独立可用性反馈与专业审阅，评估记录正确性、纠错成本、提示负担及安全边界。'),
           ('3  接入专业服务并验证','拟对接在线医生，由医生独立评估诊疗与处方；再开展有授权、预设终点的真实观察研究。')]
    for i,(title,body) in enumerate(plans):
        top=629+i*43
        text(title,M,top,9.5,GREEN)
        p(body,M+132,top,CW-132,8.8,13.2,MUTED,maxh=28)
    C.showPage()


def main():
    page_one();page_two();page_three();page_four();page_five();C.save()
    r=PdfReader(OUT)
    assert len(r.pages)==5
    text_all='\n'.join(page.extract_text() for page in r.pages)
    for value in ['SciencePal','82.4%','30.10%','77.95%','79.97%','拟对接在线医生','局限','创新点']:
        assert value in text_all,value
    assert all('2026.10.30' in page.extract_text() for page in r.pages)
    (QA/'text.txt').write_text(text_all)
    (QA/'text-bounds.json').write_text(json.dumps(BOUNDS,ensure_ascii=False,indent=2)+'\n')
    (QA/'metadata.json').write_text(json.dumps({'pdf':str(OUT),'pages':5,'text_characters':len(text_all),
                                             'embedded_cjk_font':True,'date':'2026-10-30',
                                             'benchmark_summary_from_platform_json':True},ensure_ascii=False,indent=2)+'\n')
    print(f'Created {OUT} | 5 pages | {OUT.stat().st_size} bytes')


if __name__=='__main__':main()
