"""Explicit budget-based cache retention; preview before any deletion."""
from . import studio_cache as cache, studio_cache_admin as admin

ACK = 'I_STOPPED_ALL_RENDER_PROCESSES_AND_AUTHORIZE_THIS_CACHE_PRUNE_PLAN'
MIB = 1024 ** 2


def policy(max_mib, keep_newest, protected):
    if type(max_mib) is not int or not 0 <= max_mib <= 1048576:
        raise ValueError('Cache budget must be 0 to 1048576 whole MiB')
    if type(keep_newest) is not int or not 0 <= keep_newest <= admin.MAX_NAMESPACES:
        raise ValueError('Invalid newest namespace retention count')
    if not isinstance(protected, list) or len(protected) > admin.MAX_NAMESPACES or not all(cache._sha(k) for k in protected) or len(set(protected)) != len(protected):
        raise ValueError('Invalid protected cache namespaces')
    return {'max_mib': max_mib, 'keep_newest': keep_newest, 'protected': sorted(protected)}


def plan(folder, max_mib, keep_newest=1, protected=None):
    rules = policy(max_mib, keep_newest, [] if protected is None else protected)
    inv = admin.inventory(folder)
    rows = sorted(inv['namespaces'], key=lambda r: (r['newest_file_mtime_ns'] if r['newest_file_mtime_ns'] is not None else -1, r['namespace']))
    known = {r['namespace'] for r in rows}
    if not set(rules['protected']) <= known:
        raise ValueError('Protected cache namespace not found; inspect again')
    keep = set(rules['protected']) | {r['namespace'] for r in rows[max(0,len(rows)-keep_newest):] if keep_newest}
    remaining = inv['logical_bytes']
    selected = []
    for row in rows:
        if remaining <= max_mib * MIB:
            break
        if row['namespace'] in keep or not row['logical_bytes']:
            continue
        selected.append(row)
        remaining -= row['logical_bytes']
    result = {'policy': rules, 'inventory_sha256': cache.digest(inv),
              'protected_namespaces': sorted(keep), 'delete': selected,
              'initial_logical_bytes': inv['logical_bytes'],
              'planned_deleted_logical_bytes': inv['logical_bytes']-remaining,
              'remaining_logical_bytes': remaining, 'budget_met': remaining <= max_mib * MIB,
              'automatic_pruning': False}
    return {**result, 'plan_sha256': cache.digest(result)}


def apply(folder, max_mib, keep_newest, protected, plan_sha256, *, acknowledgment):
    if acknowledgment != ACK:
        raise ValueError('Explicit stopped-process cache prune acknowledgment required')
    if not cache._sha(plan_sha256):
        raise ValueError('Invalid cache prune plan digest')
    current = plan(folder, max_mib, keep_newest, protected)
    if current['plan_sha256'] != plan_sha256:
        raise ValueError('Cache prune plan changed; preview again')
    removed = []
    for row in current['delete']:
        removed.append(admin.delete_namespace(folder, row['namespace'], row['snapshot_sha256'], acknowledgment=admin.ACK))
    return {'plan_sha256': plan_sha256, 'removed': removed,
            'deleted_logical_bytes': sum(r['deleted_logical_bytes'] for r in removed),
            'remaining_logical_bytes': current['remaining_logical_bytes'], 'budget_met': current['budget_met']}


def inspect(root, pid, max_mib, keep_newest=1, protected=None):
    from . import projects
    folder = projects.project(root, pid)
    with projects.exclusive(folder):
        return {'project_id': pid, **plan(folder, max_mib, keep_newest, protected)}


def prune(root, pid, max_mib, keep_newest, protected, plan_sha256, *, acknowledgment):
    from . import projects
    folder = projects.project(root, pid)
    with projects.exclusive(folder):
        return {'project_id': pid, **apply(folder, max_mib, keep_newest, protected, plan_sha256, acknowledgment=acknowledgment)}
