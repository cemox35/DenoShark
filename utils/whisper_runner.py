"""
Whisper Runner — subprocess modunda çalışan worker.

DenoShark.exe --whisper-worker <audio> <srt> <model> <lang> şeklinde başlatılır.
İlerleme ve sonuç JSON satırları olarak stdout'a yazılır.
Böylece ctranslate2 native crash yaparsa sadece bu process ölür.
"""
import sys
import json
from datetime import timedelta
from pathlib import Path


def _send(msg_type: str, value):
    """Ana process'e JSON satırı gönder."""
    print(json.dumps({"type": msg_type, "value": value}), flush=True)


def _fmt_time(seconds: float) -> str:
    total_s = int(seconds)
    h = total_s // 3600
    m = (total_s % 3600) // 60
    s = total_s % 60
    ms = int(round((seconds - total_s) * 1000))
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"


def run_worker_main(args: list):
    """
    --whisper-worker bayrağıyla başlatıldığında çalışır.
    args = [audio_path, output_srt, model_size, language_or_None]
    """
    if len(args) < 4:
        _send("error", "Eksik argüman")
        _send("done", False)
        return

    audio_path = args[0]
    output_srt = args[1]
    model_size = args[2]
    language = args[3] if args[3] != "None" else None

    try:
        _send("progress", 10)
        _send("status", f"📥 Model yükleniyor ({model_size})...")

        from faster_whisper import WhisperModel
        model = WhisperModel(model_size, device="cpu", compute_type="float32")

        _send("progress", 30)
        _send("status", "🎤 Transkripsiyon başlatılıyor...")

        segments_gen, info = model.transcribe(
            audio_path,
            language=language,
            word_timestamps=True,
        )

        MAX_DURATION = 2.5
        MAX_WORDS = 6
        split_segments = []

        for segment in segments_gen:
            words = getattr(segment, "words", None)
            if not words:
                split_segments.append((segment.start, segment.end, segment.text.strip()))
                continue

            current_words = []
            current_start = -1.0

            for w in words:
                if current_start < 0:
                    current_start = w.start
                current_words.append(w)
                if (w.end - current_start) >= MAX_DURATION or len(current_words) >= MAX_WORDS:
                    text = "".join(x.word for x in current_words).strip()
                    split_segments.append((current_start, w.end, text))
                    current_words = []
                    current_start = -1.0

            if current_words:
                text = "".join(x.word for x in current_words).strip()
                split_segments.append((current_start, current_words[-1].end, text))

        _send("progress", 85)
        _send("status", "💾 SRT dosyası yazılıyor...")

        lines = []
        for i, (start, end, text) in enumerate(split_segments, 1):
            lines.append(str(i))
            lines.append(f"{_fmt_time(start)} --> {_fmt_time(end)}")
            lines.append(text)
            lines.append("")

        Path(output_srt).parent.mkdir(parents=True, exist_ok=True)
        with open(output_srt, "w", encoding="utf-8") as f:
            f.write("\n".join(lines))

        _send("progress", 100)
        _send("status", f"✅ Tamamlandı! ({len(split_segments)} segment, dil: {info.language})")
        _send("done", True)

    except Exception:
        import traceback
        tb = traceback.format_exc()
        _send("error", tb)
        _send("done", False)
