import math
import struct
import wave
from pathlib import Path

import pytest
from PIL import Image

from podcast_gpt import source

@pytest.fixture
def private_studio(tmp_path):
    root=tmp_path/"Private Hindi Studio"
    source.init(root)
    for k,sp in enumerate(source.SPEAKERS):
        Image.new("RGB",(230+k*10,250+k*10),(48+k*48,97+k*13,154+k*18)).save(root/"portraits"/(sp+".png"))
    for i in range(1,46):
        frames=source.RATE+320+(i%9)*10
        path=root/"voices"/f"{i:03}.wav"
        with wave.open(str(path),"wb") as w:
            w.setnchannels(1);w.setsampwidth(2);w.setframerate(source.RATE)
            data=b"".join(struct.pack("<h",int(1200*math.sin((j+3)*.0028*(i%11+1)))) for j in range(frames))
            w.writeframes(data)
    return root

@pytest.fixture
def signed_studio(private_studio):
    source.build_source(private_studio,allow_short=True)
    return private_studio

@pytest.fixture
def chunk_studio(signed_studio):
    source.prepare_chunks(signed_studio,allow_short=True)
    return signed_studio