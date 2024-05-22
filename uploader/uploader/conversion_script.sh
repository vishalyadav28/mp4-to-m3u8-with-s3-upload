#!/bin/bash

# Input parameters
input_file="$1"   # Input video file
output_dir="$2"   # Output directory for the segmented files and playlists
segment_time=5            # Duration of each segment in seconds
bitrates=("800k" "1200k" "2000k")  # Bitrate options for video renditions

# Create the output directory if it doesn't exist
mkdir -p "$output_dir"

# Extract audio stream
ffmpeg -i "$input_file" -vn -acodec copy "$output_dir/audio.m4a"

# Function to extract video resolution
get_video_resolution() {
    ffprobe -v error -select_streams v:0 -show_entries stream=width,height -of csv=s=x:p=0 "$input_file"
}

# Extract video resolution
resolution=$(get_video_resolution)

# Generate HLS segments and playlists for each bitrate
for bitrate in "${bitrates[@]}"; do
    playlist_name="playlist_${bitrate}.m3u8"
    output_subdir="${output_dir}/${bitrate}"
    mkdir -p "$output_subdir"

    # Encode video at specified bitrate
    ffmpeg -i "$input_file" -c:v libx264 -b:v "${bitrate}" -preset medium -g $(($segment_time * 2)) -hls_time "$segment_time" -hls_playlist_type vod -hls_segment_filename "$output_subdir/video_${bitrate}_%03d.ts" "$output_subdir/$playlist_name"

    # Calculate bandwidth based on the specified bitrate (converting bitrate string to integer)
    bandwidth=$(( ${bitrate//k/000} * 1000 ))

    # Create variant playlist for this bitrate
    echo "#EXTM3U" > "$output_subdir/$playlist_name"
    echo "#EXT-X-VERSION:3" >> "$output_subdir/$playlist_name"
    for ts_file in "$output_subdir"/video_${bitrate}_*.ts; do
        echo "#EXTINF:$segment_time," >> "$output_subdir/$playlist_name"
        echo "$(basename "$ts_file")" >> "$output_subdir/$playlist_name"
    done
    echo "#EXT-X-ENDLIST" >> "$output_subdir/$playlist_name"
done

# Create master playlist
master_playlist="$output_dir/master_playlist.m3u8"
echo "#EXTM3U" > "$master_playlist"
for bitrate in "${bitrates[@]}"; do
    bandwidth=$(( ${bitrate//k/000} * 1000 ))
    echo "#EXT-X-STREAM-INF:BANDWIDTH=${bandwidth},RESOLUTION=${resolution}" >> "$master_playlist"
    echo "${bitrate}/playlist_${bitrate}.m3u8" >> "$master_playlist"
done
