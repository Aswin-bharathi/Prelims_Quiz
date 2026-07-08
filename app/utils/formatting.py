def format_duration(seconds):
    seconds = int(seconds or 0)
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    secs = seconds % 60
    return f"{hours:02d}:{minutes:02d}:{secs:02d}"


def slugify(name):
    return name.strip().lower().replace(' ', '-').replace('_', '-')
