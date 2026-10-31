#!/usr/bin/env python3
"""Replace v5 music with a brighter 104 BPM original instrumental score."""
import argparse
import hashlib
import json
import math
from pathlib import Path
import shutil
import subprocess

import numpy as np

from build_demo_video_v5 import ROOT, TOTAL, probe, run, write_wav

OUT = ROOT / 'output/video-v6'
AUDIO = OUT / 'audio'
SOURCE = ROOT / 'output/video-v5'
ALIGNMENT = json.loads((SOURCE / 'narration-alignment.json').read_text())


def compose(outro_start=284, closing_start=297.02, research_start=129, research_end=284,
            safety_start=None, safety_end=None):
    AUDIO.mkdir(parents=True, exist_ok=True)
    sr = 24000
    bpm = 104
    beat = 60 / bpm
    bar = 4 * beat
    section = 2 * bar
    rng = np.random.default_rng(291104)
    music = np.zeros((round(TOTAL * sr), 2), dtype=np.float32)
    chords = [
        (50, [62, 66, 69, 76]), (43, [62, 66, 69, 74]),
        (45, [61, 64, 69, 76]), (50, [61, 66, 69, 74]),
        (47, [62, 66, 69, 73]), (43, [62, 67, 69, 74]),
        (45, [59, 64, 69, 76]), (50, [62, 66, 69, 76]),
    ]

    def place(start, mono, amp, pan=0, echo=False):
        pos = round(start * sr)
        if pos >= len(music):
            return
        n = min(len(mono), len(music) - pos)
        gains = np.array([math.sqrt((1 - pan) / 2), math.sqrt((1 + pan) / 2)])
        music[pos:pos + n] += mono[:n, None] * amp * gains
        if echo:
            for lag, level in [(beat * .75, .13), (beat * 1.5, .045)]:
                q = round((start + lag) * sr)
                m = min(len(mono), len(music) - q)
                if m > 0:
                    music[q:q + m] += mono[:m, None] * amp * level * gains[::-1]

    def pitched(start, note, amp, instrument, pan=0, length=2.2):
        t = np.arange(round(sr * length), dtype=np.float32) / sr
        freq = 440 * 2 ** ((note - 69) / 12)
        if instrument == 'pluck':
            tone = np.zeros(len(t), dtype=np.float32)
            for h in range(1, 7):
                tone += np.sin(2 * math.pi * freq * h * t) * np.exp(-t * (2.7 + h * 1.3)) / h ** 1.4
            tone *= (1 - np.exp(-t * 400))
        elif instrument == 'mallet':
            tone = (np.sin(2 * math.pi * freq * t) * np.exp(-t * 3)
                    + .2 * np.sin(2 * math.pi * freq * 4.0 * t) * np.exp(-t * 12)
                    + .04 * np.sin(2 * math.pi * freq * 9.0 * t) * np.exp(-t * 18))
            tone *= (1 - np.exp(-t * 400))
        elif instrument == 'bass':
            tone = (np.sin(2 * math.pi * freq * t) + .1 * np.sin(2 * math.pi * freq * 2 * t))
            tone *= (1 - np.exp(-t * 50)) * np.exp(-t * 3.6)
        else:
            phase = rng.uniform(0, 2 * math.pi)
            tone = np.sin(2 * math.pi * freq * t + phase) + .18 * np.sin(2 * math.pi * freq * 1.001 * t + phase)
            tone *= np.minimum(1, t / .55) * np.minimum(1, (length - t) / .7)
        tone *= np.minimum(1, (length - t) / .06)
        place(start, tone, amp, pan, instrument in ['pluck', 'mallet'])

    def percussion(start, kind, amp, pan=0):
        length = .34 if kind == 'kick' else .15
        t = np.arange(round(length * sr), dtype=np.float32) / sr
        if kind == 'kick':
            phase = 2 * math.pi * (50 * t + 65 * (1 - np.exp(-t * 32)) / 32)
            tone = np.sin(phase) * np.exp(-t * 18) * np.minimum(1, t / .004)
        else:
            noise = rng.normal(0, 1, len(t)).astype(np.float32)
            airy = (noise - np.roll(noise, 1)) * .5
            if kind == 'shaker':
                tone = airy * (1 - np.exp(-t * 600)) * np.exp(-t * 52)
            else:
                tone = (.35 * airy + .65 * np.sin(2 * math.pi * 780 * t)) * np.exp(-t * 70)
        tone *= np.minimum(1, (length - t) / .02)
        place(start, tone, amp, pan)

    melody = [[74, 76, 78, 76], [74, 71, 69, 71], [73, 76, 78, 76], [74, 69, 66, 69],
              [74, 78, 76, 73], [74, 71, 69, 67], [73, 71, 69, 73], [74, 76, 78, 74]]
    for i in range(math.ceil(TOTAL / section)):
        start = i * section
        root, chord = chords[i % len(chords)]
        research = research_start <= start < research_end
        activity = .75 if research else 1.0
        for note in chord[:3]:
            pitched(start, note - 12, .014, 'pad', -.16 if i % 2 else .16, section + .5)
        for j, offset in enumerate([0, 2, 1, 2, 0, 2, 1, 3]):
            if start + j * beat >= 295:
                continue
            human = rng.uniform(-.006, .006) if j else 0
            pitched(start + j * beat + human, chord[offset], .065 * activity * (1 if j % 2 == 0 else .76),
                    'pluck', -.25 if j % 2 == 0 else .25, 1.8)
        for j in [0, 4]:
            pitched(start + j * beat, root - 12, .042, 'bass', 0, 2.0)
        is_transition = start < 24 or research_start - 20 <= start < research_start or start >= outro_start
        # A simple four-note phrase adds lift around animation and transitions.
        for j, note in enumerate(melody[i % 8]):
            if is_transition or (not research and j in [0, 2]) or (research and i % 4 == 0 and j == 0):
                pitched(start + (.5 + j * 2) * beat, note, .038 * activity, 'mallet', .22 if j % 2 else -.22, 1.9)
    for i in range(math.ceil(TOTAL / beat)):
        start = i * beat
        if start < 2 * bar or start >= 294:
            continue
        research = research_start <= start < research_end
        risk_intro = safety_start is not None and safety_start <= start < safety_start + 9.8
        risk_gain = .3 if risk_intro else 1
        if i % 4 in [0, 2]:
            percussion(start, 'kick', (.04 if i % 4 == 0 else .029) * risk_gain)
        if i % 4 in [1, 3]:
            percussion(start + .008, 'rim', (.009 if research else .016) * risk_gain, -.12)
        percussion(start, 'shaker', .009 * risk_gain, -.35)
        percussion(start + beat / 2 + .006, 'shaker', .0065 * risk_gain, .35)
    for note in [50, 62, 66, 69, 74]:
        pitched(294.4, note, .024, 'mallet', 0, 4.6)
    t = np.arange(len(music), dtype=np.float32) / sr
    music *= (np.minimum(1, t / 2.2) * np.minimum(1, (TOTAL - t) / 4.2))[:, None]
    # A short sonic signature is clear at the first frame, before the music bed
    # has faded in. It returns on the outro card, then resolves after the voice.
    for j, note in enumerate([74, 76, 78, 81]):
        pitched(j * .09, note, .115, 'mallet', -.18 + j * .12, 1.15)
        pitched(outro_start + j * .14, note, .09, 'mallet', -.18 + j * .12, 1.35)
    for j, note in enumerate([81, 78, 74]):
        pitched(closing_start + j * .32, note, .12 if j < 2 else .15,
                'mallet', .16 - j * .16, TOTAL - (closing_start + j * .32))
    for note in [50, 62, 66, 69, 74]:
        pitched(closing_start + .66, note, .028, 'pad', 0, TOTAL - closing_start - .66)
    # Finish the signature's reverberation cleanly within the existing picture.
    music *= np.minimum(1, (TOTAL - t) / .16)[:, None]
    peak = float(np.max(np.abs(music)))
    assert peak < .95, peak
    write_wav(AUDIO / 'bright-steps-104bpm-raw.wav', music, sr)
    run(['ffmpeg', '-hide_banner', '-loglevel', 'error', '-y', '-i', AUDIO / 'bright-steps-104bpm-raw.wav',
         '-af', 'highpass=f=45,lowpass=f=10500,loudnorm=I=-27:TP=-9:LRA=6',
         '-ar', 48000, '-ac', 2, '-c:a', 'pcm_s24le', AUDIO / 'bright-steps-104bpm.wav'])
    # Reuse the proven narration positions while giving music a smooth release.
    rate = 100
    target = np.ones(TOTAL * rate, dtype=np.float32)
    for cue in ALIGNMENT['cues']:
        a = max(0, round((cue['voice_start'] - .24) * rate))
        b = min(len(target), round((cue['voice_end'] + .15) * rate))
        target[a:b] = .34
    duck = np.ones_like(target)
    for i in range(1, len(duck)):
        tau = .1 if target[i] < duck[i - 1] else 1.05
        alpha = 1 - math.exp(-1 / (tau * rate))
        duck[i] = duck[i - 1] + alpha * (target[i] - duck[i - 1])
    pcm = subprocess.check_output(['ffmpeg', '-v', 'error', '-i', str(AUDIO / 'bright-steps-104bpm.wav'),
                                   '-f', 'f32le', '-ar', '48000', '-ac', '2', '-'])
    score = np.frombuffer(pcm, dtype='<f4').reshape(-1, 2).copy()
    env = np.interp(np.arange(len(score)) / 48000, np.arange(len(duck)) / rate, duck)
    score *= env[:, None]
    write_wav(AUDIO / 'background-music-ducked.wav', score, 48000)
    (AUDIO / 'music-notes.json').write_text(json.dumps({
        'title': 'Bright Steps', 'bpm': bpm, 'key': 'D major',
        'type': 'original procedural instrumental score',
        'instruments': ['soft mallet', 'plucked strings', 'soft bass', 'light shaker', 'muted kick and rim'],
        'third_party_samples': False, 'duration_seconds': TOTAL,
        'music_target_lufs_before_ducking': -27, 'narration_duck_gain': .34,
        'narration_source': str(SOURCE / 'audio/narration-aligned.wav'),
        'sonic_signatures': [
            {'start': 0, 'notes': ['D5', 'E5', 'F#5', 'A5'], 'purpose': 'opening rising signature'},
            {'start': outro_start, 'notes': ['D5', 'E5', 'F#5', 'A5'], 'purpose': 'outro card signature reprise'},
            {'start': closing_start, 'notes': ['A5', 'F#5', 'D5'], 'purpose': 'closing response after narration'},
            {'start': closing_start + .66, 'purpose': 'D major resolving chord'},
        ],
    }, ensure_ascii=False, indent=2) + '\n')
    print('New 104 BPM score ready', flush=True)


def mux():
    AUDIO.mkdir(parents=True, exist_ok=True)
    mixed = AUDIO / 'final-mix.wav'
    run(['ffmpeg', '-hide_banner', '-loglevel', 'error', '-y',
         '-i', SOURCE / 'audio/narration-aligned.wav', '-i', AUDIO / 'background-music-ducked.wav',
         '-filter_complex', '[0:a]aformat=channel_layouts=stereo[v];[v][1:a]amix=inputs=2:duration=longest:normalize=0,volume=3dB,alimiter=limit=0.89:level=0[a]',
         '-map', '[a]', '-t', TOTAL, '-ar', 48000, '-ac', 2, '-c:a', 'pcm_s24le', mixed])
    target = OUT / 'healthy-care-demo-v6.mp4'
    run(['ffmpeg', '-v', 'error', '-y', '-i', SOURCE / 'healthy-care-demo-v5.mp4', '-i', mixed,
         '-map', '0:v:0', '-map', '1:a:0', '-c:v', 'copy', '-c:a', 'aac', '-b:a', '192k',
         '-ar', 48000, '-ac', 2, '-t', TOTAL, '-movflags', '+faststart',
         '-metadata', 'comment=Voice: MiniMax Speech 2.8 HD, native speed 1.15. Music: Bright Steps, original score, 104 BPM.', target])
    shutil.copyfile(SOURCE / 'healthy-care-demo-v5.zh-CN.srt', OUT / 'healthy-care-demo-v6.zh-CN.srt')
    run(['ffmpeg', '-v', 'error', '-y', '-i', mixed, '-c:a', 'libmp3lame', '-q:a', 2,
         AUDIO / 'healthy-care-narration-and-music.mp3'])
    run(['ffmpeg', '-v', 'error', '-y', '-i', AUDIO / 'bright-steps-104bpm.wav', '-c:a', 'libmp3lame', '-q:a', 2,
         AUDIO / 'bright-steps-104bpm.mp3'])
    (OUT / 'healthy-care-demo-v6.mp4.sha256').write_text(hashlib.sha256(target.read_bytes()).hexdigest() + '  ' + target.name + '\n')
    print('Replaced music; original video stream copied without re-encoding', flush=True)


def verify():
    path = OUT / 'healthy-care-demo-v6.mp4'
    info = probe(path)
    video = next(s for s in info['streams'] if s['codec_type'] == 'video')
    audio = next(s for s in info['streams'] if s['codec_type'] == 'audio')
    assert len(info['streams']) == 2
    assert abs(float(info['format']['duration']) - TOTAL) < .05
    assert (video['width'], video['height'], video['r_frame_rate']) == (1920, 1080, '30/1')
    assert audio['codec_name'] == 'aac' and audio['channels'] == 2 and audio['sample_rate'] == '48000'
    hashes = []
    for p in [SOURCE / 'healthy-care-demo-v5.mp4', path]:
        hashes.append(subprocess.check_output(['ffmpeg', '-v', 'error', '-i', str(p), '-map', '0:v:0',
                                              '-c:v', 'copy', '-f', 'hash', '-hash', 'sha256', '-'], text=True).strip())
    assert hashes[0] == hashes[1], hashes
    assert (SOURCE / 'healthy-care-demo-v5.zh-CN.srt').read_bytes() == (OUT / 'healthy-care-demo-v6.zh-CN.srt').read_bytes()
    run(['ffmpeg', '-v', 'error', '-i', path, '-f', 'null', '-'])
    m = run(['ffmpeg', '-hide_banner', '-i', path, '-af', 'loudnorm=I=-17:TP=-1:LRA=8:print_format=json',
             '-f', 'null', '-'], capture_output=True, text=True)
    level, _ = json.JSONDecoder().raw_decode(m.stderr[m.stderr.rfind('{'):])
    assert -20 < float(level['input_i']) < -14, level
    assert float(level['input_tp']) < -.5, level
    report = {'file': str(path), 'duration_seconds': TOTAL, 'resolution': [1920, 1080], 'fps': 30,
              'full_decode_passed': True, 'video_stream_identical_to_v5': True,
              'video_stream_sha256': hashes[0].split('=')[1], 'subtitles_identical_to_v5': True,
              'narration_source_reused': str(SOURCE / 'audio/narration-aligned.wav'), 'narration_speed': 1.15,
              'music': 'Bright Steps', 'music_bpm': 104, 'original_music': True, 'narration_ducking': True,
              'opening_musical_signature': True, 'closing_musical_signature': True,
              'measured_integrated_lufs': float(level['input_i']), 'measured_true_peak_dbtp': float(level['input_tp']),
              'additional_model_credits_used': 0}
    (OUT / 'verification.json').write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps(report, ensure_ascii=False, indent=2), flush=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('stage', choices=['compose', 'mux', 'verify'])
    args = parser.parse_args()
    {'compose': compose, 'mux': mux, 'verify': verify}[args.stage]()
