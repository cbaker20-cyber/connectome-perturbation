"""Conservative per-segment resource screen from the completed CCR validation."""
import math


def segment_screen(measurements, remaining_seconds, memory_mb, free_bytes, history=()):
    if len(measurements) != 6:
        raise ValueError('Require all six fine-step validation measurements')
    expected={(c,branch,stop) for c in ('baseline','mode')
              for branch,stop in (('uninterrupted',20),('restarted',10),('restarted',20))}
    seen=set(); rates=[]; peaks=[]; sizes=[]
    for label,m in measurements.items():
        branch='uninterrupted' if 'uninterrupted' in label else 'restarted'
        key=(m['condition'],branch,m['stop_ms'])
        if key not in expected or key in seen:
            raise ValueError('Missing, duplicate or unexpected validation stage')
        seen.add(key)
        if (m['status']!='complete' or m['dt_ms']!=.0000125 or
                m['tape_duration_s']!=1. or m['seed']!=631401):
            raise ValueError('Validation does not match authorized pair')
        for k in ('seconds','peak_rss_bytes','checkpoint_bytes'):
            if not math.isfinite(m[k]) or m[k]<=0:
                raise ValueError('Invalid measured resource use')
        simulated_ms=20 if branch=='uninterrupted' else 10
        rates.append(m['seconds']/simulated_ms)
        peaks.append(m['peak_rss_bytes']); sizes.append(m['checkpoint_bytes'])
    for m in history:
        if m['status'] != 'checkpoint_saved':
            raise ValueError('Only successful checkpoint segments can update the screen')
        elapsed_ms = m['stop_ms'] - m['begin_tick']*.0000125
        if elapsed_ms != 100:
            raise ValueError('Resource history must describe a 100 ms segment')
        for k in ('seconds','peak_rss_bytes','checkpoint_bytes'):
            if not math.isfinite(m[k]) or m[k] <= 0:
                raise ValueError('Invalid production resource measurement')
        rates.append(m['seconds']/elapsed_ms)
        peaks.append(m['peak_rss_bytes'])
        sizes.append(m['checkpoint_bytes'])
    for value in (remaining_seconds,memory_mb,free_bytes):
        if not math.isfinite(value) or value<=0:
            raise ValueError('Invalid available resources')
    seconds=2*max(rates)*100
    memory=2*max(peaks)
    storage=4*20*max(sizes)
    return dict(allowed=remaining_seconds>=seconds+3600 and memory_mb*1e6>=memory and free_bytes>=storage,
                segment_ms=100,segment_screen_seconds=seconds,reserve_seconds=3600,
                memory_screen_bytes=memory,storage_screen_bytes=storage,workers=1,
                limitation='Prefix-based screen, not a full-duration guarantee; recheck resources before every segment.')
