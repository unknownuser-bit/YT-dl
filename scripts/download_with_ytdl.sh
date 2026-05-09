#!/bin/bash

VIDEO_FORMAT="bestvideo[height<=SED_HEIGHT][ext=mp4]+bestaudio[ext=m4a]/best[height<=SED_HEIGHT][ext=mp4]/best"
VIDEO_FORMAT_BEST="bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best"
SUPPORTED_VIDEO_HEIGHT_REGEX="(144|360|480|720|1080)"

make_ffmpeg_video_format_from_video_height(){
    readonly height="$1"
    echo "$VIDEO_FORMAT" | sed -e "s/SED_HEIGHT/$height/g"
}

is_string_video_quality(){
    readonly input_quality="$1"
    matched_video_height="$(echo $input_quality | grep -oE $SUPPORTED_VIDEO_HEIGHT_REGEX )"
    [ "$input_quality" == "$matched_video_height" ]
}

usage(){
    echo "usage: $0 -q QUALITY -u URL [-o OUTPUT_DIRECTORY]"
    echo "QUALITY: Quality of the media $SUPPORTED_VIDEO_HEIGHT_REGEX for videos, 'audio' for audio"
    echo "URL: URL of the media"
    echo "OUTPUT_DIRECTORY: Destination directory, current directory by default"
    exit 1
}

handle_args(){
    required_args=2
    # Parse command line options
    while getopts "q:u:o:h" opt; do
        case $opt in
            q)
                ARGS_QUALITY="$OPTARG"
                required_args=$((required_args - 1))
                ;;
            u)
                ARGS_URL="$OPTARG"
                required_args=$((required_args - 1))
                ;;
            o)
                ARGS_OUT_DIR="$OPTARG"
                ;;
            h)
                usage
                ;;
            \?)
                echo "Invalid option: -$OPTARG" >&2
                usage
                ;;
            :)
                echo "Option -$OPTARG requires an argument" >&2
                usage
                ;;
        esac
    done
    if [[ $required_args -ne 0 ]]; then
        echo "unmet required args: $required_args" >&2
        usage
    fi
}

handle_args $@

if [[ "$ARGS_QUALITY" == "audio" ]]; then
    format="bestaudio/best"
    audio_flags="--extract-audio --audio-format mp3"
elif [[ "$ARGS_QUALITY" == "best" ]]; then
    format=$VIDEO_FORMAT_BEST
elif is_string_video_quality "$ARGS_QUALITY"; then
    format=$(make_ffmpeg_video_format_from_video_height "$ARGS_QUALITY")
    echo $format
    audio_flags=""
else
    echo "invalid media format" >&2
    usage
fi

# Download through WARP SOCKS5 proxy
yt-dlp \
    --proxy "socks5://127.0.0.1:1080" \
    --format "$format" \
    $audio_flags \
    --output "$ARGS_OUT_DIR/%(title)s.%(ext)s" \
    --no-playlist \
    --retries 10 \
    --fragment-retries 10 \
    --concurrent-fragments 4 \
    --no-check-certificates \
    --prefer-free-formats \
    --no-warnings \
    "$ARGS_URL"

if [[ $? ]]; then
    # Try with different user agent
    yt-dlp \
        --proxy "socks5://127.0.0.1:1080" \
        --format "$format" \
        $audio_flags \
        --output "$ARGS_OUT_DIR/%(title)s.%(ext)s" \
        --no-playlist \
        --retries 10 \
        --fragment-retries 10 \
        --user-agent "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36" \
        --extractor-args "youtube:player_client=android" \
        "$ARGS_URL"
fi