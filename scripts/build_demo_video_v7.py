#!/usr/bin/env python3
"""Produce the approved 4:59 film with safety bridge and planned doctor service."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import shutil
import subprocess
import wave

import numpy as np

from build_demo_video_v5 import ROOT, TOTAL, probe, run, write_wav

OUT = ROOT / 'output/video-v7'
AUDIO = OUT / 'audio'
WORK = OUT / 'render'
V5 = ROOT / 'output/video-v5'
PLAN = json.loads((ROOT / 'output/video-v7-plan/proposed-timeline.json').read_text())
CHAPTERS = PLAN['scenes']
SCENES = {s['id']: s for s in CHAPTERS}
OLD = json.loads((V5 / 'narration-alignment.json').read_text())['cues']
OLD_SCENES = {s['id']: s for s in json.loads((V5 / 'production-plan.json').read_text())['scenes']}
SAFETY = json.loads((OUT / 'safety-bridge-plan.json').read_text())
OFFSETS = {
    'intro': [.3, 6.3, 12.8, 18.2],
    'user': [.6, 10.5, 19.5, 27.5, 32.5, 37.5, 41.8],
    'recovery': [.15, 4.7], 'consent': [.4, 6.3],
    'research-idea': [.3, 5.1, 10.1, 15.1],
    'research': [.35, 5.8, 15.5, 30.5, 45.5, 60.5, 69.2, 75.3],
    'sciencepal': [.5, 4.15, 8.4, 16.4, 25.0, 29.6],
    'review': [.35, 7.35, 15.3, 21.8], 'outro': [.2, 4.0],
}
RETIME = {
    'user': [(0, 14, 10), (14, 26, 9), (26, 38, 8), (38, 45, 5), (45, 52, 5), (52, 60, 9)],
    'recovery': [(0, 5, 4.5), (5, 10, 3.5)],
    'consent': [(0, 15, 12)],
    'sciencepal': [(0, 10, 8), (10, 20, 8), (20, 30, 9), (30, 40, 9)],
    'review': [(0, 10, 7), (10, 22, 8), (22, 35, 11)],
    'outro': [(0, 15, 11)],
}


def read_wav(path):
    with wave.open(str(path), 'rb') as f:
        assert f.getnchannels() == 1 and f.getsampwidth() == 2
        return f.getframerate(), np.frombuffer(f.readframes(f.getnframes()), '<i2').astype(np.float32) / 32768


def prepare_audio():
    source = AUDIO / 'minimax-safety-1.15-original.wav'
    p = run(['ffmpeg', '-hide_banner', '-i', source,
             '-af', 'silencedetect=noise=-40dB:d=0.9', '-f', 'null', '-'], capture_output=True, text=True)
    gaps = [(float(a), float(z)) for a, z in re.findall(
        r'silence_start: ([\d.]+)\s+\[silencedetect[^\n]+silence_end: ([\d.]+)', p.stderr)]
    assert len(gaps) == 5 and all(1.7 < z-a < 3 for a, z in gaps)
    sr, raw = read_wav(source)
    starts = [0] + [z - .08 for a, z in gaps]
    ends = [a + .12 for a, z in gaps] + [len(raw) / sr]
    clips = []
    safety_starts = [.1, 2.85, 9.85, 14.2, 22.0, 30.0]
    for i, (c, a, z, local) in enumerate(zip(SAFETY['captions'], starts, ends, safety_starts)):
        clip = raw[round(a * sr):round(z * sr)].copy()
        path = AUDIO / f'safety-cue-{i+1}.wav'
        write_wav(path, clip, sr)
        clips.append({'source_id': f'safety-{i+1}', 'scene': 'safety-bridge', 'text': c['text'],
                      'style': 'Default', 'path': str(path), 'voice_start': 90 + local,
                      'voice_end': 90 + local + len(clip) / sr,
                      'source_start': a, 'source_end': z, 'planned_doctor_service': i == 4})
    for sid, offsets in OFFSETS.items():
        cues = [c for c in OLD if c['scene'] == sid]
        assert len(cues) == len(offsets)
        for cue, local in zip(cues, offsets):
            path = V5 / 'audio' / f'cue-{cue["id"]:02}.wav'
            clip_sr, clip = read_wav(path)
            assert clip_sr == sr
            start = SCENES[sid]['start'] + local
            clips.append({'source_id': cue['id'], 'scene': sid, 'text': cue['text'],
                          'style': cue['style'], 'path': str(path), 'voice_start': start,
                          'voice_end': start + len(clip) / sr, 'reused_original_voice': True})
    clips.sort(key=lambda c: c['voice_start'])
    track = np.zeros(TOTAL * sr, dtype=np.float32)
    for i, cue in enumerate(clips):
        next_start = clips[i+1]['voice_start'] if i+1 < len(clips) else TOTAL
        assert cue['voice_end'] <= next_start - .07, (cue, next_start)
        assert cue['voice_end'] <= SCENES[cue['scene']]['end'] + .05, cue
        _, clip = read_wav(cue['path'])
        n = round(sr * .006)
        clip[:n] *= np.linspace(0, 1, n)
        clip[-n:] *= np.linspace(1, 0, n)
        start = round(cue['voice_start'] * sr)
        assert not np.any(track[start:start+len(clip)])
        track[start:start+len(clip)] = clip
        cue.update(id=i+1, start=cue['voice_start'], end=next_start-.15, source_speed=1.15,
                   post_generation_time_stretch=False)
    assert len(clips) == 45
    write_wav(AUDIO / 'narration-aligned-raw.wav', track, sr)
    run(['ffmpeg', '-v', 'error', '-y', '-i', AUDIO / 'narration-aligned-raw.wav',
         '-af', 'highpass=f=65,lowpass=f=13000,loudnorm=I=-17:TP=-2:LRA=8',
         '-ar', 48000, '-ac', 1, '-c:a', 'pcm_s24le', AUDIO / 'narration-aligned.wav'])
    (OUT / 'narration-alignment.json').write_text(json.dumps({
        'duration_seconds': TOTAL, 'cues': clips, 'new_voice_credits': 355,
        'remaining_credits_after_generation': 6977, 'native_generation_speed': 1.15,
        'additional_time_stretch': False}, ensure_ascii=False, indent=2)+'\n')
    print('45 narration cues aligned, including six new safety passages', flush=True)


def visuals():
    maps = {}
    for chapter in CHAPTERS:
        sid = chapter['id']
        target = WORK / f'{sid}-visual.mp4'
        if sid == 'safety-bridge':
            assert target.exists(), 'Render safety animation first'
            maps[sid] = {'source': 'native approved animation', 'duration': 38}
            continue
        source = Path(OLD_SCENES[sid]['visual_source'])
        if sid not in RETIME:
            shutil.copyfile(source, target)
            maps[sid] = {'source': str(source), 'duration': chapter['duration'], 'unchanged': True}
            continue
        parts = RETIME[sid]
        assert abs(sum(d for a, z, d in parts) - chapter['duration']) < .01
        if not target.exists():
            filters = []
            for i, (a, z, seconds) in enumerate(parts):
                filters.append(f'[0:v]trim=start={a}:end={z},setpts=(PTS-STARTPTS)*{seconds/(z-a):.10f},'
                               f'fps=30,tpad=stop_mode=clone:stop_duration=1,trim=duration={seconds}[v{i}]')
            filters.append(''.join(f'[v{i}]' for i in range(len(parts))) + f'concat=n={len(parts)}:v=1:a=0[out]')
            run(['ffmpeg', '-v', 'error', '-y', '-i', source, '-filter_complex', ';'.join(filters),
                 '-map', '[out]', '-an', '-t', chapter['duration'], '-r', 30,
                 '-c:v', 'libx264', '-preset', 'veryfast', '-crf', 19, '-pix_fmt', 'yuv420p', target])
        assert abs(float(probe(target)['format']['duration']) - chapter['duration']) < .05
        maps[sid] = {'source': str(source), 'duration': chapter['duration'],
                     'parts': [{'start': a, 'end': z, 'duration': d} for a, z, d in parts],
                     'all_source_intervals_retained': True}
        print('Retimed visual:', sid, flush=True)
    assert hashlib.sha256((WORK/'research-visual.mp4').read_bytes()).digest() == hashlib.sha256(
        Path(OLD_SCENES['research']['visual_source']).read_bytes()).digest()
    listing = WORK / 'concat-visuals.txt'
    listing.write_text(''.join(f"file '{WORK/(c['id']+'-visual.mp4')}'\n" for c in CHAPTERS))
    run(['ffmpeg', '-v', 'error', '-y', '-f', 'concat', '-safe', 0, '-i', listing,
         '-map', '0:v:0', '-an', '-c:v', 'copy', WORK/'joined-visuals.mp4'])
    (OUT/'edit-map.json').write_text(json.dumps(maps, ensure_ascii=False, indent=2)+'\n')
    print('299-second visual timeline assembled', flush=True)


def music():
    import build_demo_video_v6 as score
    score.OUT = OUT
    score.AUDIO = AUDIO
    score.ALIGNMENT = json.loads((OUT/'narration-alignment.json').read_text())
    score.compose(outro_start=288, closing_start=297.55, research_start=148,
                  research_end=288, safety_start=90, safety_end=128)
    notes_path = AUDIO/'music-notes.json'
    notes = json.loads(notes_path.read_text())
    notes.update(narration_source=str(AUDIO/'narration-aligned.wav'), safety_section=[90,128],
                 opening_risk_music_reduced=[90,99.8], research_section=[148,288])
    notes_path.write_text(json.dumps(notes,ensure_ascii=False,indent=2)+'\n')


def subtitles(cues):
    def stamp(t, srt=False):
        unit = 1000 if srt else 100
        n = round(t * unit)
        return f'{n//(3600*unit):02}:{n//(60*unit)%60:02}:{n//unit%60:02}' + (f',{n%unit:03}' if srt else f'.{n%unit:02}')
    original = (V5/'render/complete.zh-CN.ass').read_text()
    header = original[:original.index('[Events]')]
    header += '[Events]\nFormat: Layer,Start,End,Style,Name,MarginL,MarginR,MarginV,Effect,Text\n'
    lines = [f'Dialogue: 0,{stamp(c["start"])},{stamp(c["end"])},{c["style"]},,0,0,0,,{c["text"]}' for c in cues]
    lines += ['Dialogue: 1,00:04:48.50,00:04:59.00,Credit,,0,0,0,,旁白：MiniMax Speech 2.8  ·  音乐：原创配乐']
    (WORK/'complete.zh-CN.ass').write_text(header+'\n'.join(lines)+'\n')
    (OUT/'healthy-care-demo-v7.zh-CN.srt').write_text('\n\n'.join(
        f'{i}\n{stamp(c["start"],True)} --> {stamp(c["end"],True)}\n{c["text"]}'
        for i,c in enumerate(cues,1))+'\n')


def render():
    alignment = json.loads((OUT/'narration-alignment.json').read_text())
    subtitles(alignment['cues'])
    mixed = AUDIO/'final-mix.wav'
    run(['ffmpeg','-v','error','-y','-i',AUDIO/'narration-aligned.wav','-i',AUDIO/'background-music-ducked.wav',
         '-filter_complex','[0:a]aformat=channel_layouts=stereo[v];[v][1:a]amix=inputs=2:duration=longest:normalize=0,volume=3dB,alimiter=limit=0.89:level=0[a]',
         '-map','[a]','-t',TOTAL,'-ar',48000,'-ac',2,'-c:a','pcm_s24le',mixed])
    target = OUT/'healthy-care-demo-v7.mp4'
    run(['ffmpeg','-hide_banner','-loglevel','warning','-y','-i',WORK/'joined-visuals.mp4','-i',mixed,
         '-vf',f"ass='{WORK/'complete.zh-CN.ass'}':fontsdir='/System/Library/Fonts/Supplemental'",
         '-map','0:v:0','-map','1:a:0','-t',TOTAL,'-r',30,'-c:v','libx264','-preset','veryfast','-crf',19,
         '-pix_fmt','yuv420p','-c:a','aac','-b:a','192k','-ar',48000,'-ac',2,'-movflags','+faststart',
         '-metadata','title=伴AI·健康伙伴｜让日常记录连接科学研究',
         '-metadata','comment=MiniMax Speech 2.8 HD, native speed 1.15. Planned online doctor service is explicitly labelled as a concept.',target])
    run(['ffmpeg','-v','error','-y','-i',mixed,'-c:a','libmp3lame','-q:a',2,AUDIO/'healthy-care-narration-and-music.mp3'])
    run(['ffmpeg','-v','error','-y','-ss',90,'-i',target,'-t',38,'-c:v','libx264','-preset','veryfast',
         '-crf',19,'-c:a','aac','-b:a','192k','-movflags','+faststart',OUT/'safety-bridge-preview.mp4'])
    (OUT/'healthy-care-demo-v7.mp4.sha256').write_text(hashlib.sha256(target.read_bytes()).hexdigest()+'  '+target.name+'\n')
    (OUT/'timeline.json').write_text(json.dumps({**PLAN,'status':'rendered','audio':True,'voice_speed':1.15,
        'subtitle_cues':alignment['cues'],'planned_doctor_service_seconds':[112,120],
        'research_source_unchanged':True},ensure_ascii=False,indent=2)+'\n')
    print('Full film and 38-second bridge preview rendered',flush=True)


def verify():
    target = OUT/'healthy-care-demo-v7.mp4'
    p = probe(target)
    assert len(p['streams']) == 2
    v = next(s for s in p['streams'] if s['codec_type']=='video')
    a = next(s for s in p['streams'] if s['codec_type']=='audio')
    assert (v['width'],v['height'],v['r_frame_rate'])==(1920,1080,'30/1')
    assert a['sample_rate']=='48000' and a['channels']==2 and a['codec_name']=='aac'
    assert abs(float(p['format']['duration'])-299)<.05
    cues = json.loads((OUT/'narration-alignment.json').read_text())['cues']
    assert len(cues)==45 and all(x['end']<=y['start'] for x,y in zip(cues,cues[1:]))
    assert all(not c['post_generation_time_stretch'] for c in cues)
    doctor = next(c for c in cues if c.get('planned_doctor_service'))
    assert 112<=doctor['voice_start']<doctor['voice_end']<120
    assert '拟接入' in doctor['text']
    assert (WORK/'research-visual.mp4').read_bytes()==Path(OLD_SCENES['research']['visual_source']).read_bytes()
    run(['ffmpeg','-v','error','-i',target,'-f','null','-'])
    levels = run(['ffmpeg','-hide_banner','-i',target,'-af','loudnorm=I=-17:TP=-1:LRA=8:print_format=json','-f','null','-'],capture_output=True,text=True)
    m,_=json.JSONDecoder().raw_decode(levels.stderr[levels.stderr.rfind('{'):])
    assert -20<float(m['input_i'])<-14 and float(m['input_tp'])<-.5,m
    report={'file':str(target),'duration_seconds':299,'resolution':[1920,1080],'fps':30,'full_decode_passed':True,
            'subtitle_count':45,'native_narration_speed':1.15,'additional_voice_speed_changes':False,
            'safety_bridge':[90,128],'planned_doctor_service':[112,120],'research_continuous_segment':[148,228],
            'research_source_unchanged':True,'doctor_service_status':'planned_concept_not_connected',
            'measured_integrated_lufs':float(m['input_i']),'measured_true_peak_dbtp':float(m['input_tp']),
            'new_voice_credits':355,'remaining_credits_after_generation':6977}
    (OUT/'verification.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps(report,ensure_ascii=False,indent=2),flush=True)


if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('stage',choices=['prepare-audio','visuals','music','render','verify'])
    stage=parser.parse_args().stage
    {'prepare-audio':prepare_audio,'visuals':visuals,'music':music,'render':render,'verify':verify}[stage]()
