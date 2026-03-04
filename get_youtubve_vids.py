from yt_dlp import YoutubeDL

playlist_url = "https://youtube.com/playlist?list=PLpjGWkxGjRHUSjBuvQ3fK08Tnmq5zFe1u"

ydl_opts = {
    'quiet': True,
    'skip_download': True,
    'extract_flat': True  # Only fetch metadata
}

with YoutubeDL(ydl_opts) as ydl:
    info = ydl.extract_info(playlist_url, download=False)
    videos = []
    for entry in info['entries']:
        videos.append({
            "title": entry.get('title', 'Unknown Title'),
            "youtube_id": entry['id']
        })

# Print results
for v in videos:
    print(v, ",\n")