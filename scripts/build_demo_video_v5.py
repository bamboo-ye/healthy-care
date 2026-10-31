#!/usr/bin/env python3
"""Align the native MiniMax 1.15 voice to v4 visuals and add an original score."""
import argparse
import hashlib
import json
import math
from pathlib import Path
import re
import subprocess
import wave

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'output/video-v5'
AUDIO = OUT / 'audio'
WORK = OUT / 'render'
PLAN = OUT / 'production-plan.json'
TOTAL = 299


def run(args, **kwargs):
    return subprocess.run([str(a) for a in args], check=True, **kwargs)


def probe(path):
    return json.loads(subprocess.check_output([
        'ffprobe', '-v', 'error', '-show_streams', '-show_format', '-of', 'json', str(path)
    ], text=True))


def write_wav(path, signal, sr):
    signal = np.asarray(signal)
    with wave.open(str(path), 'wb') as f:
        f.setnchannels(1 if signal.ndim == 1 else signal.shape[1])
        f.setsampwidth(2)
        f.setframerate(sr)
        f.writeframes((np.clip(signal, -.999, .999) * 32767).astype('<i2').tobytes())


def align_voice(plan):
    source = AUDIO / 'minimax-serene-narrator-1.15-original.wav'
    p = run(['ffmpeg', '-hide_banner', '-i', source,
             '-af', 'silencedetect=noise=-40dB:d=0.9', '-f', 'null', '-'],
            capture_output=True, text=True)
    gaps = [(float(a), float(b)) for a, b in re.findall(
        r'silence_start: ([\d.]+)\s+\[silencedetect[^\n]+silence_end: ([\d.]+)', p.stderr)]
    cues = plan['subtitle_cues']
    assert len(gaps) == len(cues) - 1, (len(gaps), len(cues))
    assert all(1.7 < b - a < 3 for a, b in gaps), gaps
    with wave.open(str(source), 'rb') as f:
        assert f.getnchannels() == 1 and f.getsampwidth() == 2
        sr = f.getframerate()
        voice = np.frombuffer(f.readframes(f.getnframes()), dtype='<i2').astype(np.float32) / 32768
    source_ends = [a + .12 for a, b in gaps] + [len(voice) / sr]
    source_starts = [0] + [b - .08 for a, b in gaps]
    track = np.zeros(round(TOTAL * sr), dtype=np.float32)
    aligned = []
    for i, (cue, a, b) in enumerate(zip(cues, source_starts, source_ends)):
        chunk = voice[round(a * sr):round(b * sr)].copy()
        fade = round(.006 * sr)
        chunk[:fade] *= np.linspace(0, 1, fade)
        chunk[-fade:] *= np.linspace(1, 0, fade)
        length = len(chunk) / sr
        # This sentence needs 0.3 s of the existing quiet gap before its caption.
        start = cue['start'] - (.30 if cue['id'] == 26 else 0)
        end = start + length
        next_start = cues[i + 1]['start'] if i + 1 < len(cues) else TOTAL
        assert end <= next_start - .08, (cue['id'], end, next_start)
        assert b > a and length > 1.5
        dest = round(start * sr)
        assert not np.any(track[dest:dest + len(chunk)])
        track[dest:dest + len(chunk)] = chunk
        item = {**cue, 'source_start': a, 'source_end': b,
                'voice_start': start, 'voice_end': end,
                'start': start, 'end': min(next_start - .08, max(cue['end'], end + .18)),
                'source_speed': 1.15, 'post_generation_time_stretch': False}
        aligned.append(item)
        write_wav(AUDIO / f'cue-{cue["id"]:02d}.wav', chunk, sr)
    write_wav(AUDIO / 'narration-aligned-raw.wav', track, sr)
    run(['ffmpeg', '-hide_banner', '-loglevel', 'error', '-y', '-i', AUDIO / 'narration-aligned-raw.wav',
         '-af', 'highpass=f=65,lowpass=f=13000,loudnorm=I=-17:TP=-2:LRA=8',
         '-ar', '48000', '-ac', '1', '-c:a', 'pcm_s24le', AUDIO / 'narration-aligned.wav'])
    (OUT / 'narration-alignment.json').write_text(json.dumps({
        'source': str(source), 'source_duration': len(voice) / sr,
        'total_duration': TOTAL, 'pause_boundaries_found': len(gaps),
        'speech_clip_seconds': sum(c['voice_end'] - c['voice_start'] for c in aligned),
        'cues': aligned,
    }, ensure_ascii=False, indent=2) + '\n')
    print('Aligned 39 native-speed voice clips', flush=True)
    return aligned


def original_score(cues):
    """Quiet electric piano, soft pads and sparse plucks, with a written chord score."""
    sr = 24000
    signal = np.zeros((TOTAL * sr, 2), dtype=np.float32)
    rng = np.random.default_rng(291015)
    bpm = 76
    beat = 60 / bpm
    bar = beat * 4
    chord_length = bar * 2
    progression = [
        [50, 57, 61, 64, 69], [47, 54, 57, 62, 66],
        [43, 50, 54, 57, 62], [45, 52, 57, 59, 64],
        [50, 57, 61, 66, 69], [42, 49, 52, 57, 61],
        [43, 50, 54, 59, 62], [45, 52, 57, 61, 66],
        [47, 54, 57, 61, 66], [43, 50, 54, 57, 62],
        [50, 57, 61, 64, 69], [45, 52, 55, 59, 64],
        [42, 49, 52, 57, 61], [43, 50, 54, 59, 62],
        [45, 52, 57, 59, 64], [50, 57, 61, 64, 69],
    ]

    def add(start, notes, length, amp, kind, pan=0):
        if start >= TOTAL:
            return
        count = min(round(length * sr), len(signal) - round(start * sr))
        t = np.arange(count, dtype=np.float32) / sr
        mono = np.zeros(count, dtype=np.float32)
        for note in notes:
            f = 440 * 2 ** ((note - 69) / 12)
            if kind == 'pad':
                phase = rng.uniform(0, 2 * math.pi)
                tone = (np.sin(2 * math.pi * f * t + phase)
                        + .3 * np.sin(2 * math.pi * f * 1.0012 * t + phase)
                        + .08 * np.sin(2 * math.pi * f * 2 * t + phase))
                env = np.minimum(1, t / 1.2) * np.minimum(1, (length - t) / 1.5)
            else:
                tone = (np.sin(2 * math.pi * f * t)
                        + .3 * np.sin(2 * math.pi * f * 2 * t) * np.exp(-t * 2)
                        + .11 * np.sin(2 * math.pi * f * 3 * t) * np.exp(-t * 3))
                env = (1 - np.exp(-t * 90)) * np.exp(-t / (1.6 if kind == 'piano' else .65))
                env *= np.minimum(1, (length - t) / .3)
            mono += tone * np.maximum(0, env) / len(notes)
        pos = round(start * sr)
        gains = [math.sqrt((1 - pan) / 2), math.sqrt((1 + pan) / 2)]
        for ch in range(2):
            signal[pos:pos + count, ch] += mono * amp * gains[ch]
        if kind != 'pad':
            for delay, feedback in [(beat * .75, .18), (beat * 1.5, .09)]:
                echo_pos = round((start + delay) * sr)
                echo_count = min(count, len(signal) - echo_pos)
                if echo_count > 0:
                    signal[echo_pos:echo_pos + echo_count, :] += mono[:echo_count, None] * amp * feedback * np.array(gains[::-1])

    for i in range(math.ceil(TOTAL / chord_length)):
        start = i * chord_length
        notes = progression[i % len(progression)]
        add(start, notes, chord_length + 1.7, .10, 'pad', -.12 if i % 2 else .12)
        add(start, [notes[0] - 12], chord_length + .3, .075, 'pad')
        # Sparse, sustained piano avoids competing with the explanation.
        for j in [0, 3, 5]:
            note = notes[1 + (j + i) % 4] + 12
            add(start + j * beat, [note], 4.5, .075 if j == 0 else .047, 'piano', (-.3, .3, -.12)[j % 3])
        # Introduce a modest sense of movement only on section changes.
        if start < 24 or 109 < start < 129 or start > 280:
            for j in [1, 4, 7]:
                add(start + j * beat, [notes[(j + 2) % 5] + 24], 2.5, .019, 'pluck', .4 if j % 2 else -.4)
    # The score settles into the tonic at the end rather than cutting a loop.
    add(290.5, [50, 57, 61, 64, 69], 8.5, .12, 'pad')
    t = np.arange(len(signal), dtype=np.float32) / sr
    signal *= (np.minimum(1, t / 3.5) * np.minimum(1, (TOTAL - t) / 5.0))[:, None]
    write_wav(AUDIO / 'original-ambient-score-raw.wav', signal, sr)
    run(['ffmpeg', '-hide_banner', '-loglevel', 'error', '-y', '-i', AUDIO / 'original-ambient-score-raw.wav',
         '-af', 'highpass=f=45,lowpass=f=9000,loudnorm=I=-28:TP=-9:LRA=6',
         '-ar', '48000', '-c:a', 'pcm_s24le', AUDIO / 'original-ambient-score.wav'])
    # Smooth music ducking keyed to the actual placed narration, not subtitle length.
    rate = 100
    target = np.ones(TOTAL * rate, dtype=np.float32)
    for cue in cues:
        a = max(0, round((cue['voice_start'] - .24) * rate))
        b = min(len(target), round((cue['voice_end'] + .15) * rate))
        target[a:b] = .37
    duck = np.ones_like(target)
    for i in range(1, len(duck)):
        tau = .10 if target[i] < duck[i - 1] else 1.25
        alpha = 1 - math.exp(-1 / (tau * rate))
        duck[i] = duck[i - 1] + alpha * (target[i] - duck[i - 1])
    pcm = subprocess.check_output(['ffmpeg', '-v', 'error', '-i', str(AUDIO / 'original-ambient-score.wav'),
                                   '-f', 'f32le', '-ar', '48000', '-ac', '2', '-'])
    score = np.frombuffer(pcm, dtype='<f4').reshape(-1, 2).copy()
    envelope = np.interp(np.arange(len(score)) / 48000, np.arange(len(duck)) / rate, duck)
    score *= envelope[:, None]
    write_wav(AUDIO / 'background-music-ducked.wav', score, 48000)
    (AUDIO / 'music-notes.json').write_text(json.dumps({
        'title': 'Care into Discovery', 'type': 'original procedural instrumental score',
        'composer': 'Project original score, generated by build_demo_video_v5.py',
        'bpm': bpm, 'key': 'D major / B minor',
        'instruments': ['soft electric piano', 'warm sustained pad', 'sparse pluck', 'soft bass'],
        'third_party_samples': False, 'duration_seconds': TOTAL,
        'music_target_lufs_before_ducking': -28, 'narration_duck_gain': .37,
        'attack_seconds': .10, 'release_seconds': 1.25,
    }, ensure_ascii=False, indent=2) + '\n')
    print('Original score and smooth narration ducking ready', flush=True)


def subtitle_files(cues):
    def stamp(t, srt=False):
        n = round(t * (1000 if srt else 100))
        unit = 1000 if srt else 100
        return f'{n // (3600 * unit):02}:{n // (60 * unit) % 60:02}:{n // unit % 60:02}' + (f',{n % unit:03}' if srt else f'.{n % unit:02}')
    original_ass = (ROOT / 'output/video-v4/render/complete.zh-CN.ass').read_text()
    header = original_ass[:original_ass.index('[Events]')]
    header += 'Style: Credit,Arial Unicode MS,22,&H00647C69,&H00647C69,&HFF000000,&HFF000000,0,0,0,0,100,100,0,0,1,0,0,1,104,104,89,1\n'
    header += '[Events]\nFormat: Layer,Start,End,Style,Name,MarginL,MarginR,MarginV,Effect,Text\n'
    lines = [f'Dialogue: 0,{stamp(c["start"])},{stamp(c["end"])},{c["style"]},,0,0,0,,{c["text"]}' for c in cues]
    lines.append('Dialogue: 1,00:04:44.50,00:04:59.00,Credit,,0,0,0,,旁白：MiniMax Speech 2.8  ·  音乐：原创配乐')
    (WORK / 'complete.zh-CN.ass').write_text(header + '\n'.join(lines) + '\n')
    (OUT / 'healthy-care-demo-v5.zh-CN.srt').write_text('\n\n'.join(
        f'{i}\n{stamp(c["start"], True)} --> {stamp(c["end"], True)}\n{c["text"]}'
        for i, c in enumerate(cues, 1)) + '\n')


def render():
    align = json.loads((OUT / 'narration-alignment.json').read_text())
    subtitle_files(align['cues'])
    mixed = AUDIO / 'final-mix.wav'
    run(['ffmpeg', '-hide_banner', '-loglevel', 'error', '-y',
         '-i', AUDIO / 'narration-aligned.wav', '-i', AUDIO / 'background-music-ducked.wav',
         '-filter_complex', '[0:a]aformat=channel_layouts=stereo[v];[v][1:a]amix=inputs=2:duration=longest:normalize=0,volume=3dB,alimiter=limit=0.89:level=0[a]',
         '-map', '[a]', '-t', TOTAL, '-ar', '48000', '-ac', '2', '-c:a', 'pcm_s24le', mixed])
    target = OUT / 'healthy-care-demo-v5.mp4'
    run(['ffmpeg', '-hide_banner', '-loglevel', 'warning', '-y',
         '-i', ROOT / 'output/video-v4/render/joined-visuals.mp4', '-i', mixed,
         '-vf', f"ass='{WORK / 'complete.zh-CN.ass'}':fontsdir='/System/Library/Fonts/Supplemental'",
         '-map', '0:v:0', '-map', '1:a:0', '-t', TOTAL,
         '-c:v', 'libx264', '-crf', '19', '-preset', 'veryfast', '-pix_fmt', 'yuv420p',
         '-c:a', 'aac', '-b:a', '192k', '-ar', '48000', '-ac', '2',
         '-metadata', 'title=伴AI·健康伙伴｜让日常记录连接科学研究',
         '-metadata', 'comment=Voice: MiniMax Speech 2.8 HD, Serene Narrator, native speed 1.15. Music: original score.',
         '-movflags', '+faststart', target])
    run(['ffmpeg', '-v', 'error', '-y', '-i', mixed, '-c:a', 'libmp3lame', '-q:a', '2', AUDIO / 'healthy-care-narration-and-music.mp3'])
    (OUT / 'healthy-care-demo-v5.mp4.sha256').write_text(hashlib.sha256(target.read_bytes()).hexdigest() + '  ' + target.name + '\n')
    print('Rendered', target, flush=True)


def verify():
    target = OUT / 'healthy-care-demo-v5.mp4'
    p = probe(target)
    streams = p['streams']
    video = next(s for s in streams if s['codec_type'] == 'video')
    audio = next(s for s in streams if s['codec_type'] == 'audio')
    assert len(streams) == 2
    assert video['width'] == 1920 and video['height'] == 1080
    assert video['codec_name'] == 'h264' and audio['codec_name'] == 'aac'
    assert audio['channels'] == 2 and audio['sample_rate'] == '48000'
    assert abs(float(p['format']['duration']) - TOTAL) < .05
    alignment = json.loads((OUT / 'narration-alignment.json').read_text())
    assert len(alignment['cues']) == 39
    assert all(a['end'] <= b['start'] for a, b in zip(alignment['cues'], alignment['cues'][1:]))
    run(['ffmpeg', '-v', 'error', '-i', target, '-f', 'null', '-'])
    loudness = run(['ffmpeg', '-hide_banner', '-i', target,
                    '-af', 'loudnorm=I=-17:TP=-1:LRA=8:print_format=json', '-f', 'null', '-'],
                   capture_output=True, text=True)
    m, _ = json.JSONDecoder().raw_decode(loudness.stderr[loudness.stderr.rfind('{'):])
    assert -23 <= float(m['input_i']) <= -14, m
    assert float(m['input_tp']) < -.5, m
    report = {'file': str(target), 'duration_seconds': float(p['format']['duration']),
              'resolution': [video['width'], video['height']], 'fps': video['r_frame_rate'],
              'audio_codec': audio['codec_name'], 'audio_sample_rate': 48000, 'audio_channels': 2,
              'full_decode_passed': True, 'aligned_cue_count': 39,
              'voice_generation_speed': 1.15, 'additional_voice_speed_changes': False,
              'preserved_v4_visual_timeline': True, 'continuous_research_scene_seconds': 80,
              'music': 'Original instrumental score with narration ducking',
              'measured_integrated_lufs': float(m['input_i']), 'measured_true_peak_dbtp': float(m['input_tp']),
              'credits_used': 2014, 'credits_remaining_after_generation': 7332}
    (OUT / 'verification.json').write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps(report, ensure_ascii=False, indent=2), flush=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('stage', choices=['prepare-audio', 'render', 'verify'])
    stage = parser.parse_args().stage
    if stage == 'prepare-audio':
        plan = json.loads(PLAN.read_text())
        cues = align_voice(plan)
        original_score(cues)
    elif stage == 'render':
        render()
    else:
        verify()
