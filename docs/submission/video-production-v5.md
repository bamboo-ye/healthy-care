# 第五版视频：男声旁白与背景音乐

2026-10-29制作。成片：`output/video-v5/healthy-care-demo-v5.mp4`。沿用第四版4分59秒的画面顺序、真实产品录屏及80秒科研连续操作。

旁白通过MiniMax官方网页生成：Speech 2.8 HD，Serene Narrator沉稳男声，原生语速1.15，音高0。完整文稿一次生成，下载无损WAV后按38个明确停顿分成39处讲解，分别放回对应画面。后期未再改变语速。原始WAV含用于分段的停顿，长253.38秒；这些停顿被原片中的操作、查看结果和转场时间替代。

压短了10处较密集的字幕或讲解用语，含义与功能流程保持一致。配套SRT和成片烧录字幕一致。片尾注明MiniMax旁白来源。

背景音乐《Care into Discovery》由项目脚本原创生成，采用轻柔电钢琴、持续氛围和弦、稀疏拨弦与低音，76 BPM。没有人声或第三方采样。音乐在讲解期间自动降低约8.6 dB，使用平滑起落，并在片尾淡出。

## 文件

- 成片：`output/video-v5/healthy-care-demo-v5.mp4`
- 字幕：`output/video-v5/healthy-care-demo-v5.zh-CN.srt`
- 单独混音：`output/video-v5/audio/healthy-care-narration-and-music.mp3`
- 原始MiniMax旁白：`output/video-v5/audio/minimax-serene-narrator-1.15-original.wav`
- 对齐旁白：`output/video-v5/audio/narration-aligned.wav`
- 原创音乐：`output/video-v5/audio/original-ambient-score.wav`
- 文稿与生成设置：`output/video-v5/production-plan.json`
- 39处讲解时间与来源音频区间：`output/video-v5/narration-alignment.json`
- 媒体验收：`output/video-v5/verification.json`

本次MiniMax生成使用2014点，生成后余额7332点。未购买订阅。原视频与试听保留。

## 重建

原始旁白WAV需先从MiniMax网页生成并放入上述目录。使用含NumPy的Python运行：

```sh
python3 scripts/build_demo_video_v5.py prepare-audio
python3 scripts/build_demo_video_v5.py render
python3 scripts/build_demo_video_v5.py verify
```

需要ffmpeg/ffprobe及macOS中的中文字体。`verification.json`记录实际媒体检查结果，包含整片解码、分辨率、音频格式、字幕数量与响度。

## 最终检查

整片音视频完整解码通过；1920×1080、30fps，AAC 48kHz双声道；39处旁白区间不重叠。整片实测响度-17.27 LUFS，真峰值-1.45 dBTP。已检查10处关键画面，字幕和片尾来源标注显示正常。
