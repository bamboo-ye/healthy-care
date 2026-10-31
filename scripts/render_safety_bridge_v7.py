#!/usr/bin/env python3
"""Native motion cards for the approved safety and planned doctor-service bridge."""
import argparse
import math
from pathlib import Path
import subprocess

from PIL import Image, ImageDraw
import build_demo_video_v2 as b

OUT = b.ROOT / 'output/video-v7'
WORK = OUT / 'render'
WORK.mkdir(parents=True, exist_ok=True)
TIMES = [0, 2.8, 9.8, 14.1, 22, 30, 38]
LABELS = ['健康咨询', '风险意识', '持续连接', '连续记录', '专业服务', '院外研究']
AMBER = '#b88136'
AMBER_BG = '#f5ead6'


def arrow(d, x1, y, x2, color=b.GREEN, dashed=False):
    if dashed:
        for x in range(int(x1), int(x2 - 10), 19):
            d.line((x, y, min(x + 10, x2 - 10), y), fill=color, width=4)
    else:
        d.line((x1, y, x2, y), fill=color, width=4)
    d.polygon([(x2, y), (x2 - 13, y - 9), (x2 - 13, y + 9)], fill=color)


def person(d, cx, cy, color=b.GREEN):
    d.ellipse((cx - 28, cy - 57, cx + 28, cy - 1), outline=color, width=5)
    d.arc((cx - 59, cy + 4, cx + 59, cy + 111), 180, 360, fill=color, width=5)


def panel(im, x, y, w, h, title, lines, active=False, color=b.GREEN):
    d = ImageDraw.Draw(im)
    d.rounded_rectangle((x + 5, y + 9, x + w + 5, y + h + 9), 25, fill='#dfe9dc')
    d.rounded_rectangle((x, y, x + w, y + h), 25, fill='white',
                        outline=color if active else '#d6e3d2', width=3 if active else 2)
    b.text(d, (x + 28, y + 28), title, 32, color)
    for i, line in enumerate(lines):
        b.text(d, (x + 28, y + 100 + 48 * i), line, 27, b.MUTED)


def stepper(im, stage, t):
    d = ImageDraw.Draw(im)
    for i, label in enumerate(LABELS):
        x = 104 + i * 292
        d.rounded_rectangle((x, 147, x + 251, 203), 28,
                            fill=b.GREEN if stage == i else '#e2ecdd')
        b.text(d, (x + 125, 175), label, 24, 'white' if i == stage else b.MUTED, 'mm')
        if i < 5:
            arrow(d, x + 264, 175, x + 281, '#a8c3a8')
    d.rounded_rectangle((104, 223, 1816, 228), 2, fill='#d6e4d1')
    if t > 0:
        d.rounded_rectangle((104, 223, 104 + 1712 * t / 38, 228), 2, fill='#7ca27d')


def draw_stage(stage, local, t):
    im = b.BASE.copy()
    b.brand_header(im, 'SAFETY / 持续关照与专业连接')
    stepper(im, stage, t)
    d = ImageDraw.Draw(im)
    e = b.ease(local / .85)
    shift = round(40 * (1 - e))
    headings = [
        ('日常健康决策', 'AI，走进日常健康决策。'),
        ('需要正视的风险', '便利背后，也有安全风险。'),
        ('持续连接', '让一次问答，连接持续关照。'),
        ('记录与随访', '记录变化，也保留需要核实的线索。'),
        ('专业服务规划', '在线医生 · 处方确认'),
        ('院外用药研究', '让院外用药过程可见、可追溯。'),
    ]
    kicker, title = headings[stage]
    b.text(d, (104, 274), kicker, 26, b.GREEN)
    b.text(d, (104, 330), title, 60, b.INK)
    if stage == 0:
        panel(im, 110, 456 + shift, 610, 271, '用户描述', ['哪里不舒服？', '从真实感受开始'])
        person(d, 630, 611 + shift)
        arrow(d, 780, 593 + shift, 1040)
        dot = 780 + 260 * ((local * .45) % 1)
        d.ellipse((dot - 7, 586 + shift, dot + 7, 600 + shift), fill='#7ca27d')
        panel(im, 1100, 456 + shift, 695, 271, 'AI健康信息', ['理解症状与日常护理', '进入个人健康决策'])
        b.badge(im, '日常求助，正在发生', 625, 816, 670)
    elif stage == 1:
        panel(im, 110, 457 + shift, 430, 261, 'AI回答', ['信息与建议', '仍需判断其适用性'])
        arrow(d, 590, 588 + shift, 745, AMBER, True)
        panel(im, 800, 457 + shift, 430, 261, '自主判断', ['是否适合自己？', '信息是否完整？'])
        arrow(d, 1280, 588 + shift, 1410, AMBER, True)
        panel(im, 1460, 457 + shift, 350, 261, '实际用药', ['采取行动', '影响健康过程'])
        for i, label in enumerate(['误判', '用药不当', '延误就医']):
            a = b.ease((local - .4 - .25 * i) / .8)
            b.badge(im, label, 280 + 520 * i, 817 + round((1 - a) * 25), 330, AMBER_BG)
    elif stage == 2:
        panel(im, 110, 460 + shift, 510, 264, '用户', ['持续描述变化', '补充实际用药'])
        arrow(d, 655, 590 + shift, 850)
        mascot = b.MASCOT.copy()
        mascot.thumbnail((310, 310), Image.Resampling.LANCZOS)
        b.paste(im, mascot, 815, 423 + shift + 4 * math.sin(local))
        arrow(d, 1150, 590 + shift, 1280)
        panel(im, 1330, 460 + shift, 475, 264, '持续关照', ['记录 · 提醒 · 随访', '与用户保持连接'])
        b.badge(im, '从一次问答，走向连续健康过程', 530, 816, 860)
    elif stage == 3:
        d.line((210, 737 + shift, 1715, 737 + shift), fill='#afc7ae', width=5)
        entries = [('症状', ['当时的感受', '之后的变化']),
                   ('实际用药', ['真实使用情况', '记忆中的空白']),
                   ('恢复', ['日常活动变化', '后续随访'])]
        for i, (title, lines) in enumerate(entries):
            x = 110 + 590 * i
            offset = round(35 * (1 - b.ease((local - .14 * i) / .9)))
            panel(im, x, 448 + offset, 510, 250, title, lines, i == 1,
                  AMBER if i == 1 else b.GREEN)
            d.ellipse((x + 242, 726 + shift, x + 264, 748 + shift), fill=AMBER if i == 1 else b.GREEN)
        b.badge(im, '待核实', 704, 817, 235, AMBER_BG)
        arrow(d, 972, 843, 1090, AMBER, True)
        b.badge(im, '回到来源记录', 1130, 817, 480)
    elif stage == 4:
        # Persistent status label; this is explicitly a future concept, not a UI recording.
        b.badge(im, '拟接入 · 概念演示', 1435, 267, 380, '#e6eee0')
        entries = [('记录摘要', ['病程与实际用药', '由用户选择转交']),
                   ('在线医生', ['问诊与诊疗需求评估', '由医生独立判断']),
                   ('处方确认', ['由医生完成', '适用情形经诊疗评估'])]
        for i, (title, lines) in enumerate(entries):
            x = 110 + 590 * i
            offset = round(35 * (1 - b.ease((local - i * .25) / .85)))
            panel(im, x, 450 + offset, 510, 292, title, lines, i == 1)
            if i < 2:
                arrow(d, x + 538, 590 + offset, x + 578, '#95ad92', True)
        # Neutral document marks avoid suggesting an actually issued prescription.
        d.rounded_rectangle((1690, 638, 1747, 707), 7, outline='#b3c8ae', width=2)
        for y in [658, 674, 690]:
            d.line((1702, y, 1735, y), fill='#c2d2bc', width=2)
        b.badge(im, '可选的专业服务连接', 570, 817, 780)
    else:
        entries = [('研究授权', ['由用户单独决定', '用途清楚可见']),
                   ('观察队列', ['连接连续记录', '保留缺失与未知']),
                   ('线索分析', ['观察窗口与用药', '找到待核实信息']),
                   ('来源回查', ['回到对应记录', '逐步核实发现'])]
        for i, (title, lines) in enumerate(entries):
            x = 110 + 445 * i
            offset = round(30 * (1 - b.ease((local - i * .18) / .8)))
            panel(im, x, 450 + offset, 370, 280, title, lines, i == 0)
            if i < 3:
                arrow(d, x + 385, 591 + offset, x + 428, '#97b396')
        b.badge(im, '为识别和减少风险积累证据', 520, 817, 880)
    b.text(d, (1816, 967), '安全性与服务规划示意', 22, b.MUTED, 'ra')
    return im.convert('RGB')


def frame(t):
    stage = next((i for i in range(6) if TIMES[i] <= t < TIMES[i + 1]), 5)
    local = t - TIMES[stage]
    current = draw_stage(stage, local, t)
    if stage > 0 and local < .25:
        previous = draw_stage(stage - 1, TIMES[stage] - TIMES[stage - 1] - .01, TIMES[stage] - .01)
        current = Image.blend(previous, current, b.ease(local / .25))
    if stage == 4:
        # Keep the planned-status badge fully legible even during the crossfade.
        overlay = current.convert('RGBA')
        b.badge(overlay, '拟接入 · 概念演示', 1435, 267, 380, '#e6eee0')
        current = overlay.convert('RGB')
    return current


def render():
    target = WORK / 'safety-bridge-visual.mp4'
    p = subprocess.Popen(['ffmpeg', '-v', 'error', '-y', '-f', 'rawvideo', '-pix_fmt', 'rgb24',
                          '-s', '1920x1080', '-r', '30', '-i', '-', '-an', '-c:v', 'libx264',
                          '-preset', 'veryfast', '-crf', '19', '-pix_fmt', 'yuv420p', str(target)], stdin=subprocess.PIPE)
    try:
        for i in range(38 * 30):
            p.stdin.write(frame(i / 30).tobytes())
            if i % 300 == 0:
                print(f'Safety animation {i // 30}/38 s', flush=True)
    finally:
        p.stdin.close()
    assert p.wait() == 0
    print('Safety animation rendered', flush=True)


def preview():
    for t in [1.5, 6, 12, 18, 23, 26, 29.5, 34]:
        frame(t).save(WORK / f'safety-design-{t:g}.png')
    print('Eight storyboard frames rendered', flush=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('stage', choices=['preview', 'render'])
    {'preview': preview, 'render': render}[parser.parse_args().stage]()
