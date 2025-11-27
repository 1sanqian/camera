#!/bin/bash
# 4路摄像头监控 - FFmpeg 命令
# 使用 SDL 显示窗口

ffmpeg \
-f v4l2 -framerate 15 -video_size 640x480 -input_format mjpeg -i /dev/video0 \
-f v4l2 -framerate 15 -video_size 320x240 -input_format mjpeg -i /dev/video1 \
-f v4l2 -framerate 15 -video_size 320x240 -input_format mjpeg -i /dev/video2 \
-f v4l2 -framerate 15 -video_size 320x240 -input_format mjpeg -i /dev/video3 \
-filter_complex "
color=black:s=1000x750 [bg];
[0:v] scale=640x480 [main];
[1:v] scale=320x240 [sub1];
[2:v] scale=320x240 [sub2];
[3:v] scale=320x240 [sub3];
[sub1][sub2][sub3] hstack=inputs=3 [subs];
[bg][main] overlay=x=(W-w)/2:y=10 [tmp];
[tmp][subs] overlay=x=(W-w)/2:y=500
" \
-map "[tmp]" -vcodec libx264 -preset ultrafast -pix_fmt yuv420p -f sdl "4路摄像头监控"

