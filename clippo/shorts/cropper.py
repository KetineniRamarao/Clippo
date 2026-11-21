import os
import subprocess
from typing import List, Dict, Any, Optional

def calculate_shorts_schedule(
    total_duration: float,
    silences: list,
    num_clips_requested: Optional[int] = None,
    min_dur: float = 45.0,
    max_dur: float = 65.0
) -> List[Dict[str, Any]]:
    # Buffer head and tail
    start_offset = 25.0
    end_offset = max(total_duration - 10.0, start_offset + 30.0)
    available_window = end_offset - start_offset

    if num_clips_requested is not None and num_clips_requested > 0:
        count = num_clips_requested
    else:
        # Smart auto-detection
        if available_window < 180:
            count = 2
        elif available_window < 400:
            count = 4
        elif available_window < 800:
            count = 6
        else:
            count = min(12, int(available_window / 60))

    target_segment_len = min(max_dur, max(min_dur, available_window / count))
    schedule = []
    cursor = start_offset

    from clippo.audio.leveler import snap_timestamp_to_silence

    for i in range(count):
        if cursor >= end_offset - 20.0:
            break
        s_start = snap_timestamp_to_silence(cursor, silences, tolerance=5.0)
        s_end = snap_timestamp_to_silence(s_start + target_segment_len, silences, tolerance=6.0)

        actual_len = s_end - s_start
        if actual_len < min_dur:
            s_end = snap_timestamp_to_silence(s_start + min_dur, silences, tolerance=6.0)
        elif actual_len > max_dur:
            s_end = snap_timestamp_to_silence(s_start + max_dur, silences, tolerance=6.0)

        schedule.append({
            "id": i + 1,
            "start": s_start,
            "end": s_end,
            "duration": round(s_end - s_start, 2)
        })
        cursor = s_end

    return schedule
