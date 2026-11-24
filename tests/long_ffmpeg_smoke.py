"""Explicit slow FFmpeg integration smoke, ALL PREVIEWS SYNTHETIC STATIC.

Never interpret as SadTalker lip-sync, real user's 10 minutes or published QA.
CLI: python tests/long_ffmpeg_smoke.py
"""
from __future__ import annotations
import math
import shutil
import struct
import sys
import tempfile
import time
import wave
from pathlib import Path

from PIL import Image

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from podcast_gpt import source,media,neural,review


def main():
    begin=time.monotonic()
    with tempfile.TemporaryDirectory(prefix="SYNTHETIC_45_TURN_NOT_REAL_LIPSYNC_") as tmp:
        root=Path(tmp)/"Private synthetic smoke";source.init(root)
        for i,sp in enumerate(source.SPEAKERS):
            Image.new("RGB",(250+i*20,280),(45+i*40,120,165)).save(root/"portraits"/(sp+".png"))
        for i in range(1,46):
            with wave.open(str(root/"voices"/f"{i:03}.wav"),"wb") as w:
                w.setnchannels(1);w.setsampwidth(2);w.setframerate(source.RATE)
                n=source.RATE+300+i%19
                w.writeframes(b"".join(struct.pack("<h",int(900*math.sin(j*.0017*(i%13+1)))) for j in range(n)))
        source.build_source(root,allow_short=True)
        source.prepare_chunks(root,allow_short=True)
        static=media.render_static(root,allow_short=True)
        media.audit_static(root,allow_short=True)
        manifest=source.verify_chunks(root,allow_short=True)
        for sp in source.SPEAKERS:
            row=next(x for x in manifest["chunks"] if x["speaker"]==sp)
            output=root/"scratch"/(sp+"-STATIC-SYNTHETIC-TEST.mp4")
            media.cmd(["ffmpeg","-y","-hide_banner","-v","error","-loop","1","-framerate","24",
                       "-i",str(root/"portraits"/(sp+".png")),"-i",str(root/"chunks"/(row["id"]+".wav")),
                       "-c:v","libx264","-preset","ultrafast","-pix_fmt","yuv420p","-c:a","aac",
                       "-t",f"{row['duration']:.6f}","-shortest",str(output)],timeout=120)
        for row in manifest["chunks"]:
            mp4=root/"previews"/(row["id"]+".mp4")
            shutil.copyfile(root/"scratch"/(row["speaker"]+"-STATIC-SYNTHETIC-TEST.mp4"),mp4)
            info={"schema":3,"status":neural.MODEL_STATUS,"chunk_id":row["id"],"speaker":row["speaker"],
                  "chunk_sha256":row["chunk_sha256"],"portrait_sha256":row["portrait_sha256"],
                  "source_binding":manifest["source_binding"],"mp4_sha256":source.digest(mp4),
                  "authorized_portraits_self_attested":True,"human_lipsync_approved":False,
                  "full_ten_minute_neural_video_completed":False,
                  "TEST_ONLY_FAKE_MODEL_NOT_GENUINE_SADTALKER":True}
            source.atomic_json(root/"previews"/(row["id"]+".json"),info,new=True)
        assert neural.progress(root,allow_short=True)["verified"]==45
        review.review_pilot(root,allow_short=True)
        review.record_pilot(root,{x:"PASS" for x in source.SPEAKERS},review.ACK,allow_short=True)
        # Real full candidate staging must never consume unrelated C: TEMP.
        original_temp=neural.tempfile.TemporaryDirectory
        temp_roots=[]
        def trace_temp(*args,**kwargs):
            temp_roots.append(kwargs.get("dir"))
            return original_temp(*args,**kwargs)
        neural.tempfile.TemporaryDirectory=trace_temp
        try:
            full=neural.compose_neural(root,allow_short=True)
        finally:
            neural.tempfile.TemporaryDirectory=original_temp
        assert temp_roots==[root/"scratch"]
        audited=neural.audit_neural(root,allow_short=True)
        review.review_full(root,allow_short=True)
        from podcast_gpt import final_review
        template=final_review.template(root,allow_short=True)
        assert template["turns"]==45
        assert audited["candidate_binding"]["video_sha256"]==source.digest(root/"exports"/"original_hindi_full_neural.mp4")
        # Do not create a fake human PASS receipt in the synthetic smoke.
        assert audited["complete_45_turn_video_structurally_audited"] is True
        assert full["synthetic_short_test_only"] is True
        assert full["publication_approved"] is False
        print("SYNTHETIC SHORT SOURCE: 45 turns, 45 STATIC FAKE face chunks, 45-dialogue MP4 + AAC/SRT decoded",flush=True)
        print("DOES NOT DEMONSTRATE REAL pretrained SadTalker, natural lips, authorizations, or 10 minutes",flush=True)
        print(f"Elapsed {time.monotonic()-begin:.1f} sec; synthetic source duration {static['source_seconds']} sec",flush=True)

if __name__=="__main__":main()