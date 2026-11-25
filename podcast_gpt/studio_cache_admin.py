"""Bounded metadata inventory and explicitly authorized cache-only deletion."""
import re
from pathlib import Path
from . import studio_cache as cache

ACK = 'I_STOPPED_ALL_RENDER_PROCESSES_AND_AUTHORIZE_DELETING_THIS_CACHE_NAMESPACE'
MAX_NAMESPACES = 128
MAX_ENTRIES = 100000


def _children(path, limit):
    result = []
    for child in path.iterdir():
        if len(result) >= limit:
            raise ValueError('Cache inventory limit exceeded; inspect manually')
        result.append(child)
    return sorted(result, key=lambda p: p.name)


def _stamp(path, directory):
    s = cache.plain(path, directory)
    return [s.st_dev, s.st_ino, s.st_size, s.st_mtime_ns, s.st_ctime_ns]


def _scan(path, limit):
    if not cache._sha(path.name):
        raise ValueError('Unexpected cache namespace name')
    rows = []
    total = complete = 0
    newest = None
    directory_stamp = _stamp(path, True)
    for entry in _children(path, limit):
        if not re.fullmatch(r'segment[0-9]{6}', entry.name):
            raise ValueError('Unexpected cache entry name')
        stamp = _stamp(entry, True)
        files = []
        for f in _children(entry, 2):
            if f.name not in ('video.mp4', 'receipt.json'):
                raise ValueError('Unexpected cache file name')
            info = _stamp(f, False)
            total += info[2]
            newest = info[3] if newest is None else max(newest, info[3])
            files.append([f.name, info])
        complete += int(len(files) == 2)
        rows.append([entry.name, stamp, files])
    summary = {'namespace': path.name, 'entries': len(rows), 'complete_pairs': complete,
               'incomplete_entries': len(rows)-complete, 'logical_bytes': total,
               'newest_file_mtime_ns': newest,
               'snapshot_sha256': cache.digest([path.name, directory_stamp, rows])}
    return summary, rows


def inventory(folder):
    folder = Path(folder)
    cache.plain(folder, True)
    base = folder / cache.FOLDER
    namespaces = []
    if cache._exists(base):
        cache.plain(base, True)
        count = 0
        for path in _children(base, MAX_NAMESPACES):
            row, _ = _scan(path, MAX_ENTRIES-count)
            count += row['entries']
            namespaces.append(row)
    return {'namespaces': namespaces, 'namespace_count': len(namespaces),
            'entries': sum(r['entries'] for r in namespaces),
            'logical_bytes': sum(r['logical_bytes'] for r in namespaces),
            'content_verified': False, 'automatic_pruning': False}


def delete_namespace(folder, key, snapshot, *, acknowledgment):
    if acknowledgment != ACK:
        raise ValueError('Explicit stopped-process cache deletion acknowledgment required')
    if not cache._sha(key) or not cache._sha(snapshot):
        raise ValueError('Invalid cache namespace or snapshot')
    folder = Path(folder)
    cache.plain(folder, True)
    base = folder / cache.FOLDER
    cache.plain(base, True)
    path = base / key
    summary, rows = _scan(path, MAX_ENTRIES)
    if summary['snapshot_sha256'] != snapshot:
        raise ValueError('Cache inventory changed; inspect again before deleting')
    # Only known files and directories, never recursive deletion of arbitrary paths.
    # Caller holds the project lock; this does not defend against hostile local writers.
    for name, stamp, files in rows:
        cache.plain(base, True)
        cache.plain(path, True)
        entry = path / name
        if _stamp(entry, True) != stamp:
            raise ValueError('Cache entry changed during deletion')
        for filename, info in files:
            f = entry / filename
            if _stamp(f, False) != info:
                raise ValueError('Cache file changed during deletion')
            f.unlink()
        entry.rmdir()
    path.rmdir()
    return {'namespace': key, 'deleted_entries': summary['entries'],
            'deleted_logical_bytes': summary['logical_bytes'], 'deleted': True}


def inspect(root, pid):
    from . import projects
    folder = projects.project(root, pid)
    with projects.exclusive(folder):
        return {'project_id': pid, **inventory(folder)}


def remove(root, pid, key, snapshot, *, acknowledgment):
    from . import projects
    folder = projects.project(root, pid)
    with projects.exclusive(folder):
        return {'project_id': pid, **delete_namespace(folder, key, snapshot, acknowledgment=acknowledgment)}
