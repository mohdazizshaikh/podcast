"""Private opt-in verified studio segment cache; never an approved candidate."""
import hashlib
import json
import os
import re
import shutil
import stat
import tempfile
from pathlib import Path

FOLDER = 'studio-render-cache'
SCHEMA = 1
MAX_BYTES = 256 * 1024**2


def digest(value):
    return hashlib.sha256(json.dumps(value,sort_keys=True,separators=(',',':'),ensure_ascii=False).encode('utf-8')).hexdigest()


def file_digest(path):
    h=hashlib.sha256()
    with path.open('rb') as f:
        for block in iter(lambda:f.read(1024**2),b''):h.update(block)
    return h.hexdigest()


def plain(path, directory):
    s=path.lstat()
    if (stat.S_ISLNK(s.st_mode) or getattr(s,'st_file_attributes',0)&0x400 or
            not (stat.S_ISDIR(s.st_mode) if directory else stat.S_ISREG(s.st_mode))):
        raise ValueError('Unsafe studio cache path')
    return s


def _exists(path):
    return path.exists() or path.is_symlink()


def _directory(path):
    if not _exists(path):path.mkdir()
    plain(path,True)


def _sha(value):
    return isinstance(value,str) and re.fullmatch('[0-9a-f]{64}',value) is not None


def _copy(src,dst):
    with src.open('rb') as a,dst.open('xb') as b:
        shutil.copyfileobj(a,b);b.flush();os.fsync(b.fileno())


class SegmentCache:
    def __init__(self,folder,binding,plan,renderer):
        self.folder=Path(folder)
        plain(self.folder,True)
        self.frames=tuple(row['frames'] for row in plan)
        if not self.frames or len(self.frames)>1000000 or any(type(n) is not int or not 1<=n<=100000000 for n in self.frames):
            raise ValueError('Invalid studio cache plan')
        self.key=digest({'schema':SCHEMA,'binding':binding,'plan':plan,'renderer':renderer})
        base=self.folder/FOLDER;_directory(base)
        self.path=base/self.key;_directory(self.path)

    def _entry(self,index,dependencies):
        if type(index) is not int or not 0<=index<len(self.frames):raise ValueError('Invalid studio cache index')
        if not isinstance(dependencies,(list,tuple)) or len(dependencies) not in (0,2) or not all(_sha(s) for s in dependencies):
            raise ValueError('Invalid studio cache dependencies')
        # Recheck both parents before trusting an entry.
        plain(self.path.parent,True);plain(self.path,True)
        return self.path/f'segment{index:06}',{'schema':SCHEMA,'key':self.key,'index':index,'frames':self.frames[index],'dependencies':list(dependencies)}

    def restore(self,index,dependencies,target,verify_frames):
        entry,expected=self._entry(index,dependencies)
        if not _exists(entry):return False
        plain(entry,True)
        if {p.name for p in entry.iterdir()}!={'video.mp4','receipt.json'}:raise ValueError('Incomplete studio cache entry')
        video=entry/'video.mp4';receipt=entry/'receipt.json'
        info=plain(video,False);meta=plain(receipt,False)
        if not 1<=info.st_size<=MAX_BYTES or meta.st_size>16384:raise ValueError('Invalid studio cache size')
        saved=json.loads(receipt.read_text(encoding='utf-8'))
        sha=file_digest(video)
        expected.update(sha256=sha,bytes=info.st_size)
        if not isinstance(saved,dict) or digest(saved)!=digest(expected):raise ValueError('Studio cache receipt differs')
        target=Path(target)
        _copy(video,target)
        if file_digest(target)!=sha or verify_frames(target)!=self.frames[index]:raise ValueError('Studio cached video verification failed')
        return True

    def save(self,index,dependencies,video):
        entry,record=self._entry(index,dependencies)
        if _exists(entry):raise ValueError('Studio cache entry already exists')
        video=Path(video);info=plain(video,False)
        if not 1<=info.st_size<=MAX_BYTES:raise ValueError('Invalid studio cache video size')
        record.update(sha256=file_digest(video),bytes=info.st_size)
        # Stage outside the cache namespace; publish a complete pair by rename.
        with tempfile.TemporaryDirectory(prefix='studio-cache-stage-',dir=video.parent) as tmp:
            staged=Path(tmp)/'entry';staged.mkdir()
            _copy(video,staged/'video.mp4')
            if file_digest(staged/'video.mp4')!=record['sha256']:raise ValueError('Studio cache copy differs')
            with (staged/'receipt.json').open('x',encoding='utf-8') as f:
                json.dump(record,f,sort_keys=True);f.flush();os.fsync(f.fileno())
            if _exists(entry):raise ValueError('Studio cache entry already exists')
            staged.rename(entry)
