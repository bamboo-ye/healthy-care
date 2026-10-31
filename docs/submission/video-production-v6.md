# 第六版视频：更轻快的配乐

将第五版76 BPM的氛围配乐替换为原创器乐曲《Bright Steps》，104 BPM，D大调。使用明亮木琴、拨弦、柔和低音、轻沙锤及低音量鼓点。科研讲解区减少旋律活动，讲解时配乐平滑降低约9.4 dB，片尾淡出。

片头从第0秒加入D–E–F#–A上行提示旋律；4:44片尾画面出现时呼应这一主题。最后一句旁白结束后，4:57.02开始A–F#–D下行回应，并以D大调和弦收束，在4:59前自然结束。提示旋律也遵循讲解避让，不改变现有旁白或画面时间。

复用第五版的1.15倍MiniMax沉稳男声旁白，以及完全相同的画面与字幕。视频流直接复制，不重新编码画面，不重新生成旁白。原片保留。

- 成片：`output/video-v6/healthy-care-demo-v6.mp4`
- 字幕：`output/video-v6/healthy-care-demo-v6.zh-CN.srt`
- 独立配乐：`output/video-v6/audio/bright-steps-104bpm.mp3`
- 混音：`output/video-v6/audio/healthy-care-narration-and-music.mp3`
- 配乐说明：`output/video-v6/audio/music-notes.json`
- 媒体检查：`output/video-v6/verification.json`

配乐由项目脚本原创生成，没有第三方录音采样。此版没有额外模型额度支出。片尾原有MiniMax旁白来源与原创配乐标注继续适用。

重建需含NumPy的Python、ffmpeg与ffprobe：

```sh
python3 scripts/build_demo_video_v6.py compose
python3 scripts/build_demo_video_v6.py mux
python3 scripts/build_demo_video_v6.py verify
```

检查覆盖完整音视频解码、响度与峰值；同时比对第五版和第六版视频流SHA256及字幕文件，确认画面和字幕一致。

最终检查通过：完整音视频解码正常，视频流SHA256与第五版一致，字幕完全一致。整片响度-17.43 LUFS，真峰值-1.25 dBTP。
