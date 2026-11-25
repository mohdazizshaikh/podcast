"""Private, bounded timing history for successful audited new renders only."""
import json
import logging
import os
import tempfile
import time
from pathlib import Path
from . import studio_cache as cache

FILENAME = 'render-performance.json'
LIMIT = 30
MAX_BYTES = 65536
VARIANTS = ('neural-studio', 'mixed-video', 'mixed-studio')
FORMATS = ('landscape', 'vertical', 'square')
FIELDS = {'variant','format','resume','recorded_unix_ms','rendered_units','restored_units',
          'rendered_frames','restored_frames','rendered_ms','restored_ms','elapsed_ms'}


def validate(row):
    if not isinstance(row,dict) or set(row)!=FIELDS:
        raise ValueError('Invalid render timing fields')
    if row['variant'] not in VARIANTS or row['format'] not in FORMATS or type(row['resume']) is not bool:
        raise ValueError('Invalid render timing mode')
    for k in FIELDS-{'variant','format','resume'}:
        if type(row[k]) is not int or not 0<=row[k]<=10**15:
            raise ValueError('Invalid render timing count')
    for kind in ('rendered','restored'):
        units,frames,ms=(row[kind+'_'+k] for k in ('units','frames','ms'))
        if frames<units or (not units and (frames or ms)):
            raise ValueError('Invalid render timing coverage')
    if not row['rendered_units']+row['restored_units'] or (not row['resume'] and row['restored_units']):
        raise ValueError('Invalid render timing totals')
    if row['rendered_ms']+row['restored_ms']>row['elapsed_ms']:
        raise ValueError('Invalid render timing duration')
    return row


class Timing:
    def __init__(self,variant,fmt,resume,*,clock=time.monotonic_ns,wall=time.time_ns):
        self.clock=clock;self.wall=wall;self.start=clock()
        self.row={'variant':variant,'format':fmt,'resume':resume}
        for kind in ('rendered','restored'):
            for key in ('units','frames','ms'):self.row[kind+'_'+key]=0
        self.pending=None
        self.finished=False

    def begin_unit(self):
        if self.pending is not None or self.finished:raise ValueError('Render timing unit already active or finished')
        self.pending=self.clock()

    def unit(self,frames,*,restored=False):
        if self.pending is None or self.finished or type(frames) is not int or frames<1 or type(restored) is not bool:
            raise ValueError('Invalid render timing unit')
        elapsed=self.clock()-self.pending
        if elapsed<0:raise ValueError('Invalid monotonic clock')
        kind='restored' if restored else 'rendered'
        self.row[kind+'_units']+=1;self.row[kind+'_frames']+=frames;self.row[kind+'_ms']+=elapsed//1000000
        self.pending=None

    def finish(self,expected_frames):
        if self.finished or self.pending is not None or type(expected_frames) is not int or self.row['rendered_frames']+self.row['restored_frames']!=expected_frames:
            raise ValueError('Incomplete render timing coverage')
        row={**self.row,'recorded_unix_ms':self.wall()//1000000,'elapsed_ms':(self.clock()-self.start)//1000000}
        validate(row);self.finished=True
        return row


def read(folder):
    folder=Path(folder);cache.plain(folder,True)
    path=folder/FILENAME
    if not cache._exists(path):return []
    if cache.plain(path,False).st_size>MAX_BYTES:raise ValueError('Oversized render timing history')
    data=json.loads(path.read_text(encoding='utf-8'))
    if not isinstance(data,dict) or set(data)!={'schema','records'} or type(data['schema']) is not int or data['schema']!=1 or not isinstance(data['records'],list) or len(data['records'])>LIMIT:
        raise ValueError('Invalid render timing history')
    return [validate(row) for row in data['records']]


def append(folder,row):
    """Caller holds the project lock; never replace malformed existing history."""
    folder=Path(folder);records=(read(folder)+[validate(row)])[-LIMIT:]
    path=folder/FILENAME
    with tempfile.TemporaryDirectory(prefix='render-history-',dir=folder) as tmp:
        staged=Path(tmp)/FILENAME
        with staged.open('x',encoding='utf-8') as f:
            json.dump({'schema':1,'records':records},f,allow_nan=False);f.flush();os.fsync(f.fileno())
        if cache._exists(path):cache.plain(path,False)
        staged.replace(path)


def save_completed(folder,timing,expected_frames):
    """History is auxiliary; a history-write failure must not invalidate video."""
    try:append(folder,timing.finish(expected_frames))
    except (OSError,ValueError,OverflowError,RecursionError):
        logging.getLogger(__name__).warning('Render history not saved; audited video unchanged')
        return False
    return True


def summarize(records):
    groups={}
    for row in records:
        validate(row)
        key=(row['variant'],row['format'],row['resume'])
        group=groups.setdefault(key,{'variant':key[0],'format':key[1],'resume':key[2],'runs':0,**{k:0 for k in FIELDS-{'variant','format','resume','recorded_unix_ms'}}})
        group['runs']+=1
        for k in FIELDS-{'variant','format','resume','recorded_unix_ms'}:group[k]+=row[k]
    return [groups[k] for k in sorted(groups)]


def inspect(root,pid):
    from . import projects
    folder=projects.project(root,pid)
    with projects.exclusive(folder):
        records=read(folder)
        return {'project_id':pid,'records':records,'summary':summarize(records),'limit':LIMIT,'successful_new_renders_only':True}
