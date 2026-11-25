"""Run the furniture helpers against a stubbed bpy (no Blender needed).

Usage: python tests/stub_test.py [path/to/index.html]
Checks closed meshes, nothing below the floor, footprint size, front/back orientation
and tolerance of bad arguments. Prints TOTAL FAILS: 0 when everything passes.
"""
import sys, types, math, random, re, collections
from unittest.mock import MagicMock

import os
html = open(sys.argv[1] if len(sys.argv) > 1 else os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'index.html'), encoding='utf-8').read()
code = re.search(r'<script type="text/plain" id="hlp">\n(.*?)</script>', html, re.S).group(1)
compile(code, 'hlp', 'exec')

class Mesh:
    def __init__(s, n): s.name = n; s.verts = []; s.faces = []; s.polygons = []; s.materials = []
    def from_pydata(s, v, e, f):
        s.verts = [tuple(x) for x in v]; s.faces = [tuple(x) for x in f]
        s.polygons = [types.SimpleNamespace(vertices=x, use_smooth=False) for x in f]
    def update(s): pass
class BM:
    faces = []
    def from_mesh(s, m): pass
    def to_mesh(s, m): pass
    def free(s): pass
class Nodes:
    def new(s, *a): return MagicMock()
    def get(s, k): return None
    def clear(s): pass
class Mat(dict):
    def __init__(s, n): super().__init__(); s.name = n; s.node_tree = types.SimpleNamespace(nodes=Nodes(), links=types.SimpleNamespace(new=lambda *a: None)); s.use_nodes = False
    def copy(s): return Mat(s.name)
    def __hash__(s): return id(s)
class Obj:
    def __init__(s, n, d): s.name = n; s.data = d; s.location = (0, 0, 0); s.rotation_euler = (0, 0, 0); s.modifiers = types.SimpleNamespace(new=lambda *a: MagicMock()); s.users_collection = []; s.type = 'MESH'; s.hide_render = False; s.parent = None
class Coll:
    def __init__(s, n): s.name = n; s.objects = types.SimpleNamespace(link=lambda o, s=s: (s.items.append(o), o.users_collection.append(s))); s.items = []
class Objs(list):
    def new(s, n, d): o = Obj(n, d); s.append(o); return o
class Colls(list):
    def get(s, n): return next((c for c in s if c.name == n), None)
    def new(s, n): c = Coll(n); s.append(c); return c
bpy = types.ModuleType('bpy')
bpy.data = types.SimpleNamespace(meshes=types.SimpleNamespace(new=Mesh), materials=types.SimpleNamespace(new=Mat), objects=Objs(), collections=Colls(), lights=MagicMock(), images=[], texts=MagicMock())
bpy.context = MagicMock()
bmesh = types.ModuleType('bmesh'); bmesh.new = lambda: BM(); bmesh.ops = types.SimpleNamespace(recalc_face_normals=lambda *a, **k: None)
mu = types.ModuleType('mathutils'); mu.Vector = MagicMock; mu.Matrix = MagicMock; mu.Euler = MagicMock
sys.modules.update({'bpy': bpy, 'bmesh': bmesh, 'mathutils': mu})
sc = types.SimpleNamespace(camera=None, collection=types.SimpleNamespace(children=types.SimpleNamespace(link=lambda c: None)))
G = {'bpy': bpy, 'math': math, 'sc': sc, 'CLEAR_ZONE_W': 0, 'TALENT_DIST': 2.8, 'CLEAR_ZONE_NAMES': []}
exec(compile(code, 'hlp', 'exec'), G)

def rot(p, e):
    a, b, c = e
    x, y, z = p
    y, z = y * math.cos(a) - z * math.sin(a), y * math.sin(a) + z * math.cos(a)
    x, z = x * math.cos(b) + z * math.sin(b), -x * math.sin(b) + z * math.cos(b)
    x, y = x * math.cos(c) - y * math.sin(c), x * math.sin(c) + y * math.cos(c)
    return (x, y, z)
def world(o):
    return [tuple(r + l for r, l in zip(rot(v, o.rotation_euler), o.location)) for v in o.data.verts]

def open_edges(m):
    ec = collections.Counter()
    for f in m.faces:
        if len(set(f)) < 3: return 'degenerate face'
        if any(i < 0 or i >= len(m.verts) for i in f): return 'bad index'
        for i in range(len(f)):
            ec[tuple(sorted((f[i], f[(i + 1) % len(f)])))] += 1
    bad = [e for e, c in ec.items() if c != 2]
    return ('%d open/non-manifold edges' % len(bad)) if bad else None

fails = 0
def check(label, cond, msg=''):
    global fails
    if not cond:
        fails += 1; print('  FAIL', label, msg)

SPEC = {  # fn: (kwargs, front-name keys, back-name keys, expected half-w, half-d, height)
 'bed': (dict(), ('_mattress',), ('_headboard',), 0.9, 1.05, 1.06),
 'nightstand': (dict(), ('_drawer',), ('_body',), 0.25, 0.2, 0.72),
 'dresser': (dict(), ('_drawer',), ('_body',), 0.65, 0.3, 1.2),
 'wardrobe': (dict(), ('_door',), ('_body',), 0.65, 0.35, 2.05),
 'counter': (dict(), ('_flute', '_panel'), ('_body',), 1.05, 0.35, 1.5),
 'stool': (dict(), (), (), 0.3, 0.3, 0.75),
 'bench': (dict(), (), (), 0.75, 0.25, 0.5),
 'display_unit': (dict(), (), ('_back',), 0.65, 0.25, 1.6),
}
FACES = [(0, -1), (1, 0), (0, 1), (-1, 0)]
for fn, (kw, front, back, hw, hd, hh) in SPEC.items():
    for style in ('modern', 'midcentury', 'industrial'):
        for fc in FACES:
            G['LAYOUT'].clear(); G['LAYOUT_LOG'].clear(); G['SHELVES'].clear(); G['FRONTS'].clear()
            before = len(bpy.data.objects)
            L = (3.0, 4.0, 0)
            try:
                r = G[fn]('T_' + fn, L, facing=fc, style=style, **kw)
            except Exception as e:
                import traceback; traceback.print_exc(); fails += 1; print('  EXC', fn, style, fc, repr(e)); continue
            objs = list(bpy.data.objects)[before:]
            tag = '%s/%s/%s' % (fn, style, fc)
            check(tag, r is not None and len(objs) > 4, 'returned %r, %d objs' % (r, len(objs)))
            fx, fy = fc
            th = math.atan2(-fx, fy)
            ex = (math.cos(th), math.sin(th)); ey = (-math.sin(th), math.cos(th))
            lo = [9e9] * 3; hi = [-9e9] * 3
            for o in objs:
                e = open_edges(o.data)
                if e: check(tag, False, o.name + ': ' + e)
                for p in world(o):
                    lx = (p[0] - L[0]) * ex[0] + (p[1] - L[1]) * ex[1]
                    ly = (p[0] - L[0]) * ey[0] + (p[1] - L[1]) * ey[1]
                    for i, v in enumerate((lx, ly, p[2])):
                        lo[i] = min(lo[i], v); hi[i] = max(hi[i], v)
                if not (o.users_collection): check(tag, False, o.name + ' not in a collection')
            check(tag, lo[2] > -0.005, 'below floor %.3f' % lo[2])
            check(tag, lo[2] < 0.03, 'floats: lowest z %.3f' % lo[2])
            check(tag, hi[2] < hh, 'too tall %.2f > %.2f' % (hi[2], hh))
            check(tag, hi[2] > hh * 0.55, 'too short %.2f' % hi[2])
            check(tag, -hw - 0.02 < lo[0] and hi[0] < hw + 0.02, 'x extent %.2f..%.2f (limit %.2f)' % (lo[0], hi[0], hw))
            check(tag, -hd - 0.04 < lo[1] and hi[1] < hd + 0.04, 'y extent %.2f..%.2f (limit %.2f)' % (lo[1], hi[1], hd))
            def cy(keys):
                v = []
                for o in objs:
                    if any(k in o.name for k in keys):
                        w = world(o); v.append(sum((p[0] - L[0]) * ey[0] + (p[1] - L[1]) * ey[1] for p in w) / len(w))
                return sum(v) / len(v) if v else None
            f_, b_ = cy(front), cy(back)
            if front and b_ is not None and f_ is not None:
                check(tag, f_ > b_, 'front %.2f not ahead of back %.2f' % (f_, b_))
            if fn == 'bed':
                check(tag, b_ is not None and b_ < -0.5, 'headboard not at back: %s' % b_)
print('bad param tolerance:')
for fn in SPEC:
    G['LAYOUT'].clear()
    try:
        G[fn](123, (0, 0, 0), facing='x', style=5, width='abc', color='red', wood=None)
        G[fn]('P', (9, 9, 0), facing=(0, 0), style=None)
    except Exception as e:
        fails += 1; print('  EXC', fn, repr(e))
G['LAYOUT'].clear()
a = G['bed']('B1', (0, 0, 0)); b = G['bed']('B2', (0.2, 0.2, 0)); check('collision', a is not None and b is not None and tuple(b[:2]) != (0.2, 0.2) if isinstance(b, tuple) else True)
G['LAYOUT'].clear()
G['bed']('B3', (0, 0, 0)); print('LAYOUT after bed:', len(G['LAYOUT']), 'entry; log:', G['LAYOUT_LOG'])
r = G['nightstand']('N1', (0.0, 0.0, 0)); print('nightstand on top of bed ->', 'None (skipped)' if r is None else 'moved/placed', G['LAYOUT_LOG'][-1:])
# existing helper sanity so the stub is trusted
G['LAYOUT'].clear(); n0 = len(bpy.data.objects); s_ = G['sofa']('S', (0, 0, 0)); bad = [o.name for o in list(bpy.data.objects)[n0:] if open_edges(o.data)]
print('existing sofa: %d objs, open meshes: %s' % (len(bpy.data.objects) - n0, bad[:5]))
print('TOTAL FAILS:', fails)
sys.exit(1 if fails else 0)
