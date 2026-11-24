import os, json, ssl, random, math, bmesh, urllib.request
MATS = {}
PH_LOG = []
UA = {'User-Agent': 'BackdropBuilder/1.0'}
def _ctx():
    try:
        import certifi
        return ssl.create_default_context(cafile=certifi.where())
    except Exception:
        return ssl.create_default_context()
def _get(url, timeout=60):
    url = url.get('url') if isinstance(url, dict) else url
    err = None
    for ctx in (_ctx(), ssl._create_unverified_context()):  # 2nd: macOS certificate fallback
        try:
            return urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=timeout, context=ctx).read()
        except Exception as e:
            err = e
    PH_LOG.append('FAIL ' + url + ' ' + str(err))
def ph_json(url):
    b = _get(url, 30)
    return json.loads(b.decode()) if b else None
def ph_download(url, name):
    d = os.path.expanduser('~/.backdrop_ph')
    os.makedirs(d, exist_ok=True)
    p = os.path.join(d, name)
    if not os.path.exists(p):
        b = _get(url)
        if not b:
            return None
        open(p, 'wb').write(b)
        PH_LOG.append('OK ' + name)
    return p
def ph_maps(pid, res='2k'):
    d = ph_json('https://api.polyhaven.com/files/' + pid)
    out = {}
    if not d:
        return out
    for key, tag in (('Diffuse', 'diff'), ('Rough', 'rough'), ('nor_gl', 'nor')):
        try:
            e = d[key][res]
            e = e.get('jpg') or e.get('png') or list(e.values())[0]
            out[tag] = ph_download(e['url'], pid + '_' + res + '_' + tag + os.path.splitext(e['url'])[1])
        except Exception as ex:
            PH_LOG.append('MISSING ' + pid + ' ' + tag + ' ' + repr(ex))
    return out
def ph_hdri(pid, res='2k'):
    try:
        d = ph_json('https://api.polyhaven.com/files/' + pid)
        return ph_download(d['hdri'][res]['hdr']['url'], pid + '_' + res + '.hdr')
    except Exception as ex:
        PH_LOG.append('HDRI ' + pid + ' ' + repr(ex))
def ph_material(name, pid, scale=1.0, res='2k'):
    if name in MATS:
        return MATS[name]
    mps = ph_maps(pid, res)
    if not mps.get('diff'):
        return None
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    nt.nodes.clear()
    N = nt.nodes.new
    L = nt.links.new
    out = N('ShaderNodeOutputMaterial')
    bs = N('ShaderNodeBsdfPrincipled')
    tc = N('ShaderNodeTexCoord')
    mp = N('ShaderNodeMapping')
    mp.inputs['Scale'].default_value = (scale, scale, scale)
    L(tc.outputs['Object'], mp.inputs['Vector'])
    def img(tag, cs):
        n = N('ShaderNodeTexImage')
        n.image = bpy.data.images.load(mps[tag], check_existing=True)
        n.image.colorspace_settings.name = cs
        n.projection = 'BOX'
        n.projection_blend = 0.2
        L(mp.outputs['Vector'], n.inputs['Vector'])
        return n
    L(img('diff', 'sRGB').outputs['Color'], bs.inputs['Base Color'])
    if mps.get('rough'):
        L(img('rough', 'Non-Color').outputs['Color'], bs.inputs['Roughness'])
    if mps.get('nor'):
        nm = N('ShaderNodeNormalMap')
        L(img('nor', 'Non-Color').outputs['Color'], nm.inputs['Color'])
        L(nm.outputs['Normal'], bs.inputs['Normal'])
    L(bs.outputs['BSDF'], out.inputs['Surface'])
    MATS[name] = m
    return m
def collection(name):
    name = name if isinstance(name, str) else 'Set'
    c = bpy.data.collections.get(name)
    if not c:
        c = bpy.data.collections.new(name)
        sc.collection.children.link(c)
    return c
def bevel(o, w=0.006):
    m = o.modifiers.new('Bevel', 'BEVEL')
    m.width = w
    m.segments = 2
    m.limit_method = 'ANGLE'
def _mk(name, v, f, loc, rot, mat, col, b, size, smooth=False):
    if not isinstance(col, str):
        col = 'Set'
    if isinstance(mat, str):
        mat = MATS.get(mat)
    if not isinstance(b, (int, float)):
        b = 0.006
    me = bpy.data.meshes.new(name)
    me.from_pydata(v, [], f)
    me.update()
    bm = bmesh.new()
    bm.from_mesh(me)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    bm.to_mesh(me)
    bm.free()
    if smooth:
        for pg in me.polygons:
            pg.use_smooth = (len(pg.vertices) == 4) if smooth == 'quads' else True
    o = bpy.data.objects.new(name, me)
    o.location = loc
    o.rotation_euler = rot
    collection(col).objects.link(o)
    if mat:
        me.materials.append(mat)
    if b:
        bevel(o, max(0.001, min(b, size / 3)))
    return o
def box(name, size, loc, mat=None, col='Set', b=0.006, rot=(0, 0, 0), **kw):
    mat = kw.get('material', mat)
    col = kw.get('collection', col)
    rot = kw.get('rotation', rot)
    mat = _grain(mat, size)
    x, y, z = size[0] / 2, size[1] / 2, size[2] / 2
    v = [(a * x, c * y, d * z) for a in (-1, 1) for c in (-1, 1) for d in (-1, 1)]
    f = [(0, 1, 3, 2), (4, 6, 7, 5), (0, 4, 5, 1), (2, 3, 7, 6), (0, 2, 6, 4), (1, 5, 7, 3)]
    return _mk(name, v, f, loc, rot, mat, col, b, min(size))
def cyl(name, r, h, loc, mat=None, col='Set', seg=32, b=0.004, rot=(0, 0, 0), **kw):
    mat = kw.get('material', mat)
    col = kw.get('collection', col)
    rot = kw.get('rotation', rot)
    v = []
    f = []
    for i in range(seg):
        a = 2 * math.pi * i / seg
        v += [(r * math.cos(a), r * math.sin(a), -h / 2), (r * math.cos(a), r * math.sin(a), h / 2)]
    for i in range(seg):
        j = (i + 1) % seg
        f.append((2 * i, 2 * j, 2 * j + 1, 2 * i + 1))
    f.append(tuple(2 * i for i in range(seg))[::-1])
    f.append(tuple(2 * i + 1 for i in range(seg)))
    return _mk(name, v, f, loc, rot, mat, col, b, min(r * 2, h), 'quads')
LAYOUT = []
LAYOUT_LOG = []
def in_view(loc, size, margin=0.04, floor=False):
    cam = sc.camera
    if not cam:
        return True
    from bpy_extras.object_utils import world_to_camera_view
    from mathutils import Vector
    bpy.context.view_layer.update()
    cs = []
    for a in (-1, 1):
        for b in (-1, 1):
            for c in (-1, 1):
                cs.append(world_to_camera_view(sc, cam, Vector((loc[0] + a * size[0] / 2, loc[1] + b * size[1] / 2, loc[2] + c * size[2] / 2))))
    if any(q.z <= 0 for q in cs):
        return False
    if any(q.x < margin or q.x > 1 - margin for q in cs):
        return False
    if floor:
        return 0.15 <= max(q.y for q in cs) <= 1 - margin
    return all(margin <= q.y <= 1 - margin for q in cs)
FIXTURE_WORDS = ('lamp', 'sconce', 'light', 'fixture', 'downlight', 'pendant', 'candle', 'shelf', 'led', 'bulb', 'shade', 'lantern')
def remove_orphan_lights():
    from mathutils import Vector
    bpy.context.view_layer.update()
    fx = []
    for o in bpy.data.objects:
        n = o.name.lower()
        if o.type == 'MESH' and any(k in n for k in FIXTURE_WORDS) and not o.hide_render and all(not c.hide_render for c in o.users_collection):
            pts = [o.matrix_world @ Vector(c) for c in o.bound_box]
            fx.append(([min(q[i] for q in pts) - 0.4 for i in range(3)], [max(q[i] for q in pts) + 0.4 for i in range(3)]))
    gone = []
    for o in bpy.data.objects:
        if o.type == 'LIGHT' and o.data.type in ('POINT', 'SPOT') and not o.hide_render:
            p = o.matrix_world.translation
            if not any(all(lo[i] <= p[i] <= hi[i] for i in range(3)) for lo, hi in fx):
                o.hide_render = True
                o.hide_viewport = True
                gone.append(o.name)
    return gone
def _free(loc, size, group, pad):
    for g, lo, hi in LAYOUT:
        if group and g == group:
            continue
        if all(loc[i] - size[i] / 2 - pad < hi[i] and loc[i] + size[i] / 2 + pad > lo[i] for i in range(3)):
            return False
    return True
_RB = []
def room_bounds():
    if _RB:
        return _RB[0]
    from mathutils import Vector
    bpy.context.view_layer.update()
    best = None
    for o in bpy.data.objects:
        n = o.name.lower()
        if o.type == 'MESH' and 'floor' in n and 'lamp' not in n:
            pts = [o.matrix_world @ Vector(c) for c in o.bound_box]
            lo = (min(q.x for q in pts), min(q.y for q in pts))
            hi = (max(q.x for q in pts), max(q.y for q in pts))
            area = (hi[0] - lo[0]) * (hi[1] - lo[1])
            if area > 6 and (not best or area > best[0]):
                best = (area, lo, hi)
    if not best:
        return None
    r = ((best[1][0] + 0.15, best[1][1] + 0.15), (best[2][0] - 0.15, best[2][1] - 0.15))
    _RB.append(r)
    return r
def reserve(name, loc, size, slide=(1, 0, 0), visible=True, pad=0.05, group=None):
    floor_item = loc[2] - size[2] / 2 < 0.3
    b = room_bounds() if floor_item else None
    def ok(l):
        if b and not all(l[i] - size[i] / 2 >= b[0][i] and l[i] + size[i] / 2 <= b[1][i] for i in (0, 1)):
            return False
        return _free(l, size, group, pad) and (not visible or in_view(l, size, floor=floor_item))
    cands = [tuple(loc)]
    if floor_item:
        for k in range(1, 25):
            for a in range(12):
                t = 2 * math.pi * a / 12
                cands.append((loc[0] + 0.15 * k * math.cos(t), loc[1] + 0.15 * k * math.sin(t), loc[2]))
    else:
        for k in range(1, 31):
            for sg in (1, -1):
                t = 0.1 * k * sg
                cands.append((loc[0] + slide[0] * t, loc[1] + slide[1] * t, loc[2] + slide[2] * t))
    for l in cands:
        if ok(l):
            LAYOUT.append((group or name, tuple(l[i] - size[i] / 2 for i in range(3)), tuple(l[i] + size[i] / 2 for i in range(3))))
            if tuple(l) != tuple(loc):
                LAYOUT_LOG.append('%s moved to stay inside the room, in frame and clear of other items' % name)
            return l
    LAYOUT_LOG.append('NO ROOM for ' + name + ': skipped')
    return None
PROP_WORDS = ('plant', 'lamp', 'rug', 'sofa', 'couch', 'chair', 'table', 'shelf', 'book', 'vase', 'cushion', 'stool', 'desk', 'cabinet', 'sideboard', 'ottoman', 'pouf', 'bench', 'mug', 'bookcase')
def contain_props():
    b = room_bounds()
    if not b or not sc.camera:
        return []
    from mathutils import Vector
    bpy.context.view_layer.update()
    items = []
    for o in bpy.data.objects:
        n = o.name.lower()
        if o.type == 'MESH' and o.parent is None and any(k in n for k in PROP_WORDS) and not any(k in n for k in ('wall', 'ceiling', 'window', 'exterior', 'building', 'tree')):
            pts = [o.matrix_world @ Vector(c) for c in o.bound_box]
            items.append((o, [min(q[i] for q in pts) for i in range(3)], [max(q[i] for q in pts) for i in range(3)]))
    par = list(range(len(items)))
    def find(i):
        while par[i] != i:
            par[i] = par[par[i]]
            i = par[i]
        return i
    for i in range(len(items)):
        for j in range(i + 1, len(items)):
            if all(items[i][1][k] < items[j][2][k] + 0.03 and items[i][2][k] > items[j][1][k] - 0.03 for k in range(3)):
                par[find(i)] = find(j)
    cl = {}
    for i, it in enumerate(items):
        cl.setdefault(find(i), []).append(it)
    moved = []
    for members in cl.values():
        lo = [min(m[1][k] for m in members) for k in range(3)]
        hi = [max(m[2][k] for m in members) for k in range(3)]
        if lo[2] > 0.4:
            continue
        size = [hi[k] - lo[k] for k in range(3)]
        c = [(lo[k] + hi[k]) / 2 for k in range(3)]
        if lo[0] >= b[0][0] and lo[1] >= b[0][1] and hi[0] <= b[1][0] and hi[1] <= b[1][1]:
            continue
        x0 = c[0] + max(0, b[0][0] - lo[0]) - max(0, hi[0] - b[1][0])
        y0 = c[1] + max(0, b[0][1] - lo[1]) - max(0, hi[1] - b[1][1])
        cand = [(x0, y0, c[2])]
        for k in range(1, 25):
            for a in range(12):
                t = 2 * math.pi * a / 12
                cand.append((x0 + 0.15 * k * math.cos(t), y0 + 0.15 * k * math.sin(t), c[2]))
        for pos in cand:
            if all(pos[i] - size[i] / 2 >= b[0][i] and pos[i] + size[i] / 2 <= b[1][i] for i in (0, 1)) and in_view(pos, size, floor=True):
                d = Vector(pos) - Vector(c)
                for m in members:
                    m[0].location += d
                moved.append(members[0][0].name)
                break
    bpy.context.view_layer.update()
    return moved
def art_mat(seed):
    key = 'art_%d' % seed
    if key in MATS:
        return MATS[key]
    rnd = random.Random(seed)
    pal = [(0.62, 0.35, 0.28), (0.85, 0.72, 0.52), (0.25, 0.38, 0.45), (0.55, 0.6, 0.45), (0.8, 0.78, 0.72), (0.2, 0.2, 0.22), (0.7, 0.45, 0.5)]
    cs = rnd.sample(pal, 3)
    mean = tuple(sum(c[i] for c in cs) / 3 for i in range(3))
    cs = [tuple(c[i] * 0.55 + mean[i] * 0.45 for i in range(3)) for c in cs]
    m = bpy.data.materials.new(key)
    m.use_nodes = True
    nt = m.node_tree
    nt.nodes.clear()
    N = nt.nodes.new
    L = nt.links.new
    out = N('ShaderNodeOutputMaterial')
    bs = N('ShaderNodeBsdfPrincipled')
    tc = N('ShaderNodeTexCoord')
    mp = N('ShaderNodeMapping')
    nz = N('ShaderNodeTexNoise')
    cr = N('ShaderNodeValToRGB')
    s_ = rnd.uniform(0.6, 1.6)
    mp.inputs['Scale'].default_value = (s_, s_, s_)
    nz.inputs['Scale'].default_value = rnd.uniform(0.8, 1.6)
    nz.inputs['Detail'].default_value = 1
    nz.inputs['Distortion'].default_value = rnd.uniform(0.1, 0.4)
    cr.color_ramp.elements[0].position = 0.3
    cr.color_ramp.elements[1].position = 0.7
    cr.color_ramp.elements[0].color = cs[0] + (1,)
    cr.color_ramp.elements[1].color = cs[1] + (1,)
    e = cr.color_ramp.elements.new(0.5)
    e.color = cs[2] + (1,)
    L(tc.outputs['Generated'], mp.inputs['Vector'])
    L(mp.outputs['Vector'], nz.inputs['Vector'])
    L(nz.outputs['Fac'], cr.inputs['Fac'])
    L(cr.outputs['Color'], bs.inputs['Base Color'])
    bs.inputs['Roughness'].default_value = 0.55
    L(bs.outputs['BSDF'], out.inputs['Surface'])
    MATS[key] = m
    return m
def art(name, loc, w, h, facing=(0, -1), seed=1):
    fx, fy = facing
    th = math.atan2(-fx, fy)
    wide_x = abs(fx) < abs(fy)
    size = (w, 0.05, h) if wide_x else (0.05, w, h)
    loc = reserve(name, loc, size, slide=(1, 0, 0) if wide_x else (0, 1, 0))
    if loc is None:
        return None
    fm = MATS.get('art_frame') or pbr('art_frame', (0.3, 0.22, 0.16), (0.3, 0.45), 'wood', 0.05)
    mt = MATS.get('art_mount') or pbr('art_mount', (0.78, 0.76, 0.7), (0.7, 0.9), 'paper', 0.04, 40, 0.03)
    bw = 0.04
    d = 0.03
    rot = (0, 0, th)
    def at(f_, dx=0.0, dz=0.0):
        return (loc[0] + fx * f_ + math.cos(th) * dx, loc[1] + fy * f_ + math.sin(th) * dx, loc[2] + dz)
    o = box(name + '_top', (w, d, bw), at(0, 0, h / 2 - bw / 2), fm, 'Decor', 0.004, rot)
    box(name + '_bot', (w, d, bw), at(0, 0, -h / 2 + bw / 2), fm, 'Decor', 0.004, rot)
    box(name + '_left', (bw, d, h - 2 * bw), at(0, -(w / 2 - bw / 2)), fm, 'Decor', 0.004, rot)
    box(name + '_right', (bw, d, h - 2 * bw), at(0, w / 2 - bw / 2), fm, 'Decor', 0.004, rot)
    iw, ih = w - 2 * bw, h - 2 * bw
    box(name + '_mount', (iw + 0.01, 0.006, ih + 0.01), at(0.004), mt, 'Decor', 0, rot)
    box(name + '_art', (iw - 0.1, 0.003, ih - 0.1), at(0.0075), art_mat(seed), 'Decor', 0, rot)
    box(name + '_glass', (iw, 0.003, ih), at(0.0115), glass('art_glass'), 'Decor', 0, rot)
    return o
def door(name, loc, w=0.9, h=2.1, facing=(0, -1)):
    fx, fy = facing
    th = math.atan2(-fx, fy)
    wide_x = abs(fx) < abs(fy)
    size = (w + 0.14, 0.12, h) if wide_x else (0.12, w + 0.14, h)
    loc = reserve(name, loc, size, slide=(1, 0, 0) if wide_x else (0, 1, 0))
    if loc is None:
        return None
    fm = MATS.get('door_frame') or pbr('door_frame', (0.82, 0.8, 0.76), (0.45, 0.6), 'plaster', 0.03, 30, 0.04)
    lf = MATS.get('door_leaf') or pbr('door_leaf', (0.42, 0.3, 0.2), (0.35, 0.5), 'wood', 0.05)
    mt = MATS.get('door_metal') or pbr('door_metal', (0.7, 0.62, 0.45), (0.25, 0.4), 'metal', 0.02, 40)
    rot = (0, 0, th)
    def at(dy, dx=0.0, dz=0.0):
        return (loc[0] + fx * dy + math.cos(th) * dx, loc[1] + fy * dy + math.sin(th) * dx, loc[2] + dz)
    box(name + '_jambL', (0.07, 0.07, h), at(0.025, -(w / 2 + 0.035), h / 2), fm, 'Doors', 0.004, rot)
    box(name + '_jambR', (0.07, 0.07, h), at(0.025, w / 2 + 0.035, h / 2), fm, 'Doors', 0.004, rot)
    box(name + '_head', (w + 0.14, 0.07, 0.07), at(0.025, 0, h + 0.035), fm, 'Doors', 0.004, rot)
    o = box(name + '_leaf', (w, 0.04, h), at(0.015, 0, h / 2), lf, 'Doors', 0.003, rot)
    for n, z in ((1, h * 0.26), (2, h * 0.72)):
        box('%s_panel%d' % (name, n), (w * 0.7, 0.008, h * 0.38), at(0.039, 0, z), lf, 'Doors', 0.003, rot)
    box(name + '_rose', (0.05, 0.012, 0.05), at(0.047, w / 2 - 0.07, 1.0), mt, 'Doors', 0.003, rot)
    box(name + '_lever', (0.12, 0.014, 0.02), at(0.06, w / 2 - 0.11, 1.0), mt, 'Doors', 0.003, rot)
    box(name + '_kick', (w - 0.1, 0.006, 0.16), at(0.038, 0, 0.1), mt, 'Doors', 0.002, rot)
    for n, z in ((1, 0.3), (2, h - 0.3)):
        box('%s_hinge%d' % (name, n), (0.02, 0.012, 0.09), at(0.033, -(w / 2 + 0.005), z), mt, 'Doors', 0.002, rot)
    return o
def window_light(name, loc, w, h, aim, watts=900, k=5600, bars=(3, 2), bar=0.045):
    from mathutils import Vector
    dv = Vector(aim).normalized()
    q = dv.to_track_quat('-Z', 'Y')
    rot = tuple(q.to_euler())
    lt = lamp(name, 'AREA', loc, watts, k, w, rot)
    lt.data.shape = 'RECTANGLE'
    lt.data.size = w
    lt.data.size_y = h
    right = q @ Vector((1, 0, 0))
    up = q @ Vector((0, 1, 0))
    gm = pbr('gobo_black', (0.02, 0.02, 0.02), (0.8, 0.9), 'plaster', 0, 1)
    P = Vector(loc) + dv * 0.08
    def put(n, sx, sy, dx, dy):
        p = P + right * dx + up * dy
        o = box(n, (sx, sy, 0.02), (p.x, p.y, p.z), gm, 'Lights', 0, rot)
        try:
            o.visible_camera = False
        except Exception:
            pass
    put(name + '_gt', w, bar, 0, h / 2 - bar / 2)
    put(name + '_gb', w, bar, 0, -h / 2 + bar / 2)
    put(name + '_gl', bar, h, -w / 2 + bar / 2, 0)
    put(name + '_gr', bar, h, w / 2 - bar / 2, 0)
    for i in range(1, bars[0]):
        put('%s_gv%d' % (name, i), bar, h, -w / 2 + w * i / bars[0], 0)
    for i in range(1, bars[1]):
        put('%s_gh%d' % (name, i), w, bar, 0, -h / 2 + h * i / bars[1])
    return lt
def layout_report():
    from mathutils import Vector
    out = list(LAYOUT_LOG)
    keys = ('frame', 'picture', 'poster', 'sconce', 'vent', 'switch', 'socket', '_art', 'artwork')
    parts = ('frame', 'art', 'canvas', 'border', 'top', 'bottom', 'bot', 'left', 'right', 'mat', 'mount', 'glass', 'back')
    items = []
    for o in bpy.data.objects:
        if o.type == 'MESH' and not o.hide_render and any(k in o.name.lower() for k in keys):
            pts = [o.matrix_world @ Vector(c) for c in o.bound_box]
            lo = [min(q[i] for q in pts) for i in range(3)]
            hi = [max(q[i] for q in pts) for i in range(3)]
            stem = '_'.join(t for t in o.name.lower().split('_') if t not in parts) or o.name
            items.append((o.name, stem, lo, hi, pts))
    for a in range(len(items)):
        for b in range(a + 1, len(items)):
            if items[a][1] != items[b][1] and all(items[a][2][i] < items[b][3][i] - 0.02 and items[a][3][i] > items[b][2][i] + 0.02 for i in range(3)):
                out.append('Possible collision: %s / %s' % (items[a][0], items[b][0]))
    if sc.camera:
        from bpy_extras.object_utils import world_to_camera_view
        for n, st, lo, hi, pts in items:
            c = world_to_camera_view(sc, sc.camera, Vector([(lo[i] + hi[i]) / 2 for i in range(3)]))
            if c.z > 0 and 0 < c.x < 1 and 0 < c.y < 1:
                for q in pts:
                    w = world_to_camera_view(sc, sc.camera, q)
                    if w.x < 0.02 or w.x > 0.98 or w.y < 0.02 or w.y > 0.98:
                        out.append('Cut off at frame edge: ' + n)
                        break
    return out
def auto_expose(target=0.42, passes=3):
    rd = sc.render
    old = (rd.resolution_percentage, sc.cycles.samples, rd.filepath, rd.image_settings.file_format)
    path = os.path.join(bpy.app.tempdir, 'ae.png')
    rd.resolution_percentage = max(5, int(480 * 100 / rd.resolution_x))
    sc.cycles.samples = 16
    rd.image_settings.file_format = 'PNG'
    rd.filepath = path
    ev = sc.view_settings.exposure
    try:
        for _ in range(passes):
            bpy.ops.render.render(write_still=True)
            img = bpy.data.images.load(path)
            img.colorspace_settings.name = 'Non-Color'
            px = img.pixels[:]
            bpy.data.images.remove(img)
            lum = sorted(0.2126 * px[i] + 0.7152 * px[i + 1] + 0.0722 * px[i + 2] for i in range(0, len(px), 4))
            cur = max(1e-3, 0.5 * lum[len(lum) // 2] + 0.5 * sum(lum) / len(lum))
            step = math.log2((target / cur) ** 2.2) * 0.85
            ev += max(-3.0, min(3.0, step))
            sc.view_settings.exposure = ev
            if abs(step) < 0.15:
                break
    finally:
        rd.resolution_percentage, sc.cycles.samples, rd.filepath, rd.image_settings.file_format = old
    return ev
def reset_scene():
    n = len(bpy.data.objects)
    for o in list(bpy.data.objects):
        bpy.data.objects.remove(o, do_unlink=True)
    for c in list(bpy.data.collections):
        bpy.data.collections.remove(c)
    for blocks in (bpy.data.meshes, bpy.data.lights, bpy.data.cameras, bpy.data.curves, bpy.data.materials, bpy.data.images):
        for b in list(blocks):
            if b.users == 0 and getattr(b, 'type', '') != 'RENDER_RESULT':
                blocks.remove(b)
    LAYOUT.clear()
    LAYOUT_LOG.clear()
    MATS.clear()
    _RB.clear()
    return n
def _mn(nt, op, a, b=None):
    n = nt.nodes.new('ShaderNodeMath')
    n.operation = op
    for i, x in enumerate((a, b)):
        if x is None:
            continue
        if isinstance(x, (int, float)):
            n.inputs[i].default_value = x
        else:
            nt.links.new(x, n.inputs[i])
    return n.outputs[0]
def _rng(nt, v, a, b, c, d):
    n = nt.nodes.new('ShaderNodeMapRange')
    n.interpolation_type = 'SMOOTHSTEP'
    n.inputs['From Min'].default_value = a
    n.inputs['From Max'].default_value = b
    n.inputs['To Min'].default_value = c
    n.inputs['To Max'].default_value = d
    nt.links.new(v, n.inputs['Value'])
    return n.outputs['Result']
def _grain(m, size):
    if m is None or isinstance(m, str) or m.get('kind') != 'wood':
        return m
    ax = max(range(3), key=lambda i: size[i])
    key = m.name.split('#')[0] + '#' + 'xyz'[ax]
    if key in MATS:
        return MATS[key]
    v = m.copy()
    v.name = key
    mp = v.node_tree.nodes.get('GrainMap')
    if mp:
        sc3 = list(mp.inputs['Scale'].default_value)
        sc3[ax] = sc3[ax] * 0.04
        mp.inputs['Scale'].default_value = sc3
    MATS[key] = v
    return v
def leaf_mat(name='leaf', base=(0.07, 0.24, 0.06)):
    if name in MATS:
        return MATS[name]
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    nt.nodes.clear()
    N = nt.nodes.new
    L = nt.links.new
    out = N('ShaderNodeOutputMaterial')
    bs = N('ShaderNodeBsdfPrincipled')
    tc = N('ShaderNodeTexCoord')
    sp = N('ShaderNodeSeparateXYZ')
    L(tc.outputs['Generated'], sp.inputs['Vector'])
    u = _mn(nt, 'MULTIPLY', _mn(nt, 'ABSOLUTE', _mn(nt, 'SUBTRACT', sp.outputs['Y'], 0.5)), 2.0)
    mid = _rng(nt, u, 0.0, 0.05, 1.0, 0.0)
    ph = _mn(nt, 'ADD', _mn(nt, 'MULTIPLY', sp.outputs['X'], 14.0), _mn(nt, 'MULTIPLY', u, 3.0))
    side = _mn(nt, 'ABSOLUTE', _mn(nt, 'SUBTRACT', _mn(nt, 'FRACT', ph), 0.5))
    sv = _mn(nt, 'MULTIPLY', _rng(nt, side, 0.0, 0.1, 1.0, 0.0), 0.55)
    vein = _mn(nt, 'MAXIMUM', mid, sv)
    nz = N('ShaderNodeTexNoise')
    nz.inputs['Scale'].default_value = 7
    L(tc.outputs['Generated'], nz.inputs['Vector'])
    oi = N('ShaderNodeObjectInfo')
    c1 = N('ShaderNodeMix')
    c1.data_type = 'RGBA'
    c1.inputs[6].default_value = tuple(c * 0.7 for c in base) + (1,)
    c1.inputs[7].default_value = tuple(min(1, c * 1.6) for c in base) + (1,)
    L(_mn(nt, 'ADD', nz.outputs['Fac'], _mn(nt, 'MULTIPLY', _mn(nt, 'SUBTRACT', oi.outputs['Random'], 0.5), 0.6)), c1.inputs[0])
    c2 = N('ShaderNodeMix')
    c2.data_type = 'RGBA'
    c2.inputs[7].default_value = (0.38, 0.5, 0.2, 1)
    L(vein, c2.inputs[0])
    L(c1.outputs[2], c2.inputs[6])
    L(c2.outputs[2], bs.inputs['Base Color'])
    bs.inputs['Roughness'].default_value = 0.42
    for k in ('Subsurface Weight', 'Subsurface'):
        if k in bs.inputs:
            bs.inputs[k].default_value = 0.15
            break
    bp = N('ShaderNodeBump')
    bp.inputs['Strength'].default_value = 0.25
    bp.inputs['Distance'].default_value = 0.002
    L(vein, bp.inputs['Height'])
    L(bp.outputs['Normal'], bs.inputs['Normal'])
    L(bs.outputs['BSDF'], out.inputs['Surface'])
    MATS[name] = m
    return m
def leaf(name, length, width, loc, rot=(0, 0, 0), mat=None, col='Plants', bend=0.35, segs=10):
    cols = (-1.0, -0.5, 0.0, 0.5, 1.0)
    nc = len(cols)
    v = []
    f = []
    for i in range(segs + 1):
        t = i / segs
        w = width * math.sin(math.pi * (t ** 0.75)) * 0.5
        for s_ in cols:
            z = -bend * length * t * t + 0.03 * length * (1 - abs(s_)) * (1 - t) - 0.05 * width * s_ * s_ * math.sin(math.pi * t)
            v.append((length * t, s_ * w, z))
    for i in range(segs):
        for j in range(nc - 1):
            a = i * nc + j
            f.append((a, a + nc, a + nc + 1, a + 1))
    return _mk(name, v, f, loc, rot, mat or leaf_mat(), col, 0, length, True)
def tube(name, p0, p1, r0, r1, mat=None, col='Plants', bend=0.0, rings=7, seg=8):
    from mathutils import Vector
    a = Vector(p0)
    b = Vector(p1)
    c = (a + b) / 2 + Vector((0, 0, 1)) * ((b - a).length * bend)
    v = []
    f = []
    for i in range(rings):
        t = i / (rings - 1)
        p = a * (1 - t) ** 2 + c * (2 * t * (1 - t)) + b * (t * t)
        tg = ((c - a) * (2 * (1 - t)) + (b - c) * (2 * t)).normalized()
        up = Vector((0, 0, 1)) if abs(tg.z) < 0.95 else Vector((1, 0, 0))
        n1 = tg.cross(up).normalized()
        n2 = tg.cross(n1)
        r = r0 + (r1 - r0) * t
        for k in range(seg):
            ang = 2 * math.pi * k / seg
            q = p + n1 * (r * math.cos(ang)) + n2 * (r * math.sin(ang))
            v.append((q.x, q.y, q.z))
    for i in range(rings - 1):
        for k in range(seg):
            k2 = (k + 1) % seg
            f.append((i * seg + k, i * seg + k2, (i + 1) * seg + k2, (i + 1) * seg + k))
    return _mk(name, v, f, (0, 0, 0), (0, 0, 0), mat, col, 0, max(r0, r1) * 2, True)
BOOK_COLS = [(0.42, 0.16, 0.14), (0.16, 0.28, 0.38), (0.2, 0.33, 0.24), (0.6, 0.5, 0.3), (0.3, 0.2, 0.3), (0.12, 0.12, 0.13), (0.55, 0.28, 0.16), (0.66, 0.62, 0.55), (0.25, 0.3, 0.42), (0.45, 0.15, 0.22)]
def _bmat(rnd):
    k = rnd.randrange(len(BOOK_COLS))
    return pbr('book_%d' % k, BOOK_COLS[k], (0.45, 0.85), 'fabric', 0.12, 25, 0.1)
def _book(name, x, y, z, w, h, d, sy, rnd, rot=(0, 0, 0), col='Books'):
    box(name, (w, d, h), (x, y + sy * d / 2, z + h / 2), _bmat(rnd), col, 0.002, rot)
    if rot == (0, 0, 0) and rnd.random() < 0.8:
        lab = pbr('label_gold', (0.7, 0.55, 0.25), (0.3, 0.5), 'metal', 0.05, 30)
        for n, hz in enumerate((0.16, 0.84)):
            box('%s_band%d' % (name, n), (w * 1.02, 0.003, 0.006 + 0.008 * rnd.random()), (x, y + sy * (d + 0.0015), z + h * hz), lab, col, 0)
        if rnd.random() < 0.6:
            box(name + '_title', (w * 0.7, 0.003, 0.05 + 0.04 * rnd.random()), (x, y + sy * (d + 0.0015), z + h * 0.55), pbr('label_cream', (0.8, 0.76, 0.62), (0.6, 0.8), 'paper', 0.05, 30), col, 0)
def book_row(name, x0, x1, y, z, depth=0.2, seed=1, hmin=0.2, hmax=0.32, face=-1):
    rnd = random.Random(seed)
    sy = -1 if face < 0 else 1
    gap = rnd.choice([0.0, 0.0, 0.28])
    end = x1 - gap
    x = x0 + rnd.uniform(0.0, 0.03)
    tall = rnd.uniform(hmin, hmax)
    i = 0
    while True:
        w = rnd.uniform(0.022, 0.05)
        if x + w > end:
            break
        if rnd.random() < 0.2:
            tall = rnd.uniform(hmin, hmax)
        h = tall * rnd.uniform(0.88, 1.04)
        d = depth * rnd.uniform(0.8, 0.98)
        pull = rnd.choice([0, 0, 0, 0.01, 0.02])
        _book('%s_%d' % (name, i), x + w / 2, y + sy * pull, z, w, h, d, sy, rnd)
        x += w + rnd.choice([0, 0.001, 0.002])
        i += 1
    if gap:
        if rnd.random() < 0.5:
            w = rnd.uniform(0.025, 0.04)
            h = rnd.uniform(hmin, hmax)
            th = -rnd.uniform(0.14, 0.24)
            xr = x1 - 0.01
            cx = xr + (-w / 2 * math.cos(th) + h / 2 * math.sin(th))
            cz = z + (w / 2 * math.sin(th) + h / 2 * math.cos(th))
            box('%s_lean' % name, (w, depth * 0.85, h), (cx, y + sy * depth * 0.425, cz), _bmat(rnd), 'Books', 0.002, (0, th, 0))
        else:
            zc = z
            for k in range(rnd.randint(2, 4)):
                bw, bd, bh = rnd.uniform(0.2, 0.25), rnd.uniform(0.15, 0.19), rnd.uniform(0.02, 0.04)
                box('%s_flat%d' % (name, k), (bw, bd, bh), (x1 - 0.14 + rnd.uniform(-0.01, 0.01), y + sy * (bd / 2 + 0.02), zc + bh / 2), _bmat(rnd), 'Books', 0.002, (0, 0, rnd.uniform(-0.15, 0.15)))
                zc += bh
def plant(name, loc, height=0.9, leaves=16, seed=1, pot=None):
    rnd = random.Random(seed)
    ph = height * 0.3
    pm = pot or pbr('pot_terracotta', (0.55, 0.3, 0.2), (0.7, 0.9), 'plaster', 0.15, 6)
    cyl(name + '_pot', 0.14, ph, (loc[0], loc[1], loc[2] + ph / 2), pm, 'Plants', 32, 0.006)
    cyl(name + '_soil', 0.125, 0.012, (loc[0], loc[1], loc[2] + ph - 0.004), pbr('soil', (0.06, 0.045, 0.035), (0.85, 1.0), 'plaster', 0.3, 8), 'Plants', 24, 0)
    sm = pbr('stem_green', (0.14, 0.26, 0.07), (0.4, 0.6), 'plaster', 0.08, 30, 0.2)
    for i in range(leaves):
        a = rnd.uniform(0, 2 * math.pi)
        ca, sa = math.cos(a), math.sin(a)
        ln = height * rnd.uniform(0.3, 0.5)
        ro = rnd.uniform(0.04, 0.15)
        p0 = (loc[0] + 0.015 * ca, loc[1] + 0.015 * sa, loc[2] + ph)
        p1 = (loc[0] + ro * ca, loc[1] + ro * sa, loc[2] + ph + height * rnd.uniform(0.25, 0.55))
        tube('%s_stem%d' % (name, i), p0, p1, 0.0045, 0.003, sm, 'Plants', 0.15)
        lm = leaf_mat('leaf_%d' % (i % 3), (0.07 + 0.02 * (i % 3), 0.24 - 0.02 * (i % 3), 0.06))
        leaf('%s_leaf%d' % (name, i), ln, ln * rnd.uniform(0.35, 0.5), p1, (rnd.uniform(-0.25, 0.25), -rnd.uniform(0.15, 0.7), a), lm)
def kelvin(k):
    t = k / 100.0
    r = 255 if t <= 66 else 329.698727446 * ((t - 60) ** -0.1332047592)
    g = 99.4708025861 * math.log(t) - 161.1195681661 if t <= 66 else 288.1221695283 * ((t - 60) ** -0.0755148492)
    b = 255 if t >= 66 else (0 if t <= 19 else 138.5177312231 * math.log(t - 10) - 305.0447927307)
    return tuple((max(0, min(255, x)) / 255.0) ** 2.2 for x in (r, g, b))
def lamp(name, kind, loc, watts, k=4000, size=0.5, rot=(0, 0, 0), spot=0.9, col='Lights'):
    d = bpy.data.lights.new(name, kind)
    d.energy = watts
    d.color = kelvin(k)
    if kind == 'AREA':
        d.size = size
    elif kind == 'SUN':
        d.angle = math.radians(size if size > 1 else 0.53)
    else:
        d.shadow_soft_size = size
    if kind == 'SPOT':
        d.spot_size = spot
        d.spot_blend = 0.5
    o = bpy.data.objects.new(name, d)
    o.location = loc
    o.rotation_euler = rot
    collection(col).objects.link(o)
    return o
def enforce_clear_zone():
    if not sc.camera or not (CLEAR_ZONE_W or CLEAR_ZONE_NAMES):
        return [], 'off, or no scene camera (sc.camera=%s)' % sc.camera
    from mathutils import Vector
    bpy.context.view_layer.update()
    mw = sc.camera.matrix_world
    o = mw.translation
    fw = mw.to_3x3() @ Vector((0, 0, -1))
    f = Vector((fw.x, fw.y, 0))
    if f.length < 1e-6:
        return [], 'camera looks straight up or down'
    f.normalize()
    r = Vector((f.y, -f.x, 0))
    half = CLEAR_ZONE_W / 2
    back = TALENT_DIST + 0.75
    hid = collection('ClearZone_Hidden')
    moved = []
    st = {'meshes': 0, 'named': 0, 'shell': 0, 'flat': 0, 'thin': 0, 'outside': 0}
    for ob in list(bpy.data.objects):
        if ob.type != 'MESH' or ob.name == 'Auto_Ceiling' or not getattr(ob, 'visible_camera', True) or hid in ob.users_collection[:]:
            continue
        st['meshes'] += 1
        n = ob.name.lower()
        if not any(k in n for k in CLEAR_ZONE_NAMES):
            if not CLEAR_ZONE_W:
                continue
            if any(k in n for k in ('floor', 'ceiling', 'wall', 'rug', 'carpet')):
                st['named'] += 1
                continue
            if any(c.name.lower().startswith('shell') for c in ob.users_collection):
                st['shell'] += 1
                continue
            pts = [ob.matrix_world @ Vector(c) for c in ob.bound_box]
            lat = [(p - o).dot(r) for p in pts]
            al = [(p - o).dot(f) for p in pts]
            zs = [p.z for p in pts]
            wl = max(lat) - min(lat)
            wa = max(al) - min(al)
            if max(zs) < 0.05 or min(zs) > 2.2 or wl > 8 or wa > 8:
                st['flat'] += 1
                continue
            if min(wl, wa) < 0.12 and min(zs) > 0.5:
                st['thin'] += 1
                continue
            if not (max(lat) > -half and min(lat) < half and max(al) > 0.3 and min(al) < back):
                st['outside'] += 1
                continue
        for c in list(ob.users_collection):
            c.objects.unlink(ob)
        hid.objects.link(ob)
        moved.append(ob.name)
    hid.hide_render = True
    hid.hide_viewport = True
    info = 'camera (%.1f, %.1f, %.1f) facing (%.2f, %.2f), zone %.1f m wide to %.1f m ahead, skipped: %s' % (o.x, o.y, o.z, f.x, f.y, CLEAR_ZONE_W, back, st)
    return moved, info
def seal_gaps(nx=48, ny=27):
    cam = sc.camera
    b = room_bounds()
    if not cam or not b:
        return []
    from mathutils import Vector
    bpy.context.view_layer.update()
    R = globals().get('ROOM')
    zt = R['h'] if isinstance(R, dict) and isinstance(R.get('h'), (int, float)) else None
    if zt is None:
        zs = [(ob.matrix_world @ Vector(c)).z for ob in bpy.data.objects if ob.type == 'MESH' and 'ceiling' in ob.name.lower() for c in ob.bound_box]
        if not zs:
            return []
        zt = max(zs)
    lo = [b[0][0] - 0.2, b[0][1] - 0.2, -0.05]
    hi = [b[1][0] + 0.2, b[1][1] + 0.2, zt + 0.05]
    wins = []
    for ob in bpy.data.objects:
        if ob.type == 'MESH' and any(k in ob.name.lower() for k in ('window', 'glass', 'skylight', 'door')):
            pts = [ob.matrix_world @ Vector(c) for c in ob.bound_box]
            wins.append(([min(q[a] for q in pts) - 0.3 for a in range(3)], [max(q[a] for q in pts) + 0.3 for a in range(3)]))
    dg = bpy.context.evaluated_depsgraph_get()
    tr, br, bl, tl = cam.data.view_frame(scene=sc)
    mw = cam.matrix_world
    o = mw.translation.copy()
    faces = {}
    for j in range(ny):
        for i in range(nx):
            p = bl + (br - bl) * ((i + 0.5) / nx) + (tl - bl) * ((j + 0.5) / ny)
            d = (mw.to_3x3() @ p).normalized()
            if sc.ray_cast(dg, o, d)[0]:
                continue
            ts = [((hi[k] - o[k]) / d[k] if d[k] > 0 else (lo[k] - o[k]) / d[k]) if abs(d[k]) > 1e-9 else 1e9 for k in range(3)]
            k = ts.index(min(ts))
            H = o + d * ts[k]
            if any(all(w[0][a] <= H[a] <= w[1][a] for a in range(3)) for w in wins):
                continue
            faces.setdefault((k, 1 if d[k] > 0 else -1), []).append(H)
    done = []
    for (k, sg), pts in faces.items():
        a1, a2 = [x for x in range(3) if x != k]
        c = [0, 0, 0]
        sz = [0.01, 0.01, 0.01]
        for a in (a1, a2):
            mn = min(q[a] for q in pts) - 0.25
            mx = max(q[a] for q in pts) + 0.25
            c[a] = (mn + mx) / 2
            sz[a] = mx - mn
        c[k] = (hi[k] if sg > 0 else lo[k]) + sg * 0.005
        m = MATS.get('ceiling') if (k == 2 and sg > 0 and MATS.get('ceiling')) else pbr('seal_paint', (0.7, 0.68, 0.64), (0.5, 0.7), 'plaster', 0.03, 1.0)
        ob = box('Seal_%d%s' % (k, '+' if sg > 0 else '-'), tuple(sz), tuple(c), m, 'Shell', 0)
        try:
            ob.visible_shadow = False
        except Exception:
            pass
        done.append(ob.name)
    return done
def frame_check(nx=16, ny=9):
    cam = sc.camera
    if not cam:
        return (0, 0, 0)
    bpy.context.view_layer.update()
    dg = bpy.context.evaluated_depsgraph_get()
    tr, br, bl, tl = cam.data.view_frame(scene=sc)
    mw = cam.matrix_world
    o = mw.translation.copy()
    miss = top = 0
    for j in range(ny):
        for i in range(nx):
            p = bl + (br - bl) * ((i + 0.5) / nx) + (tl - bl) * ((j + 0.5) / ny)
            d = (mw.to_3x3() @ p).normalized()
            if not sc.ray_cast(dg, o, d)[0]:
                miss += 1
                if j >= ny - 2:
                    top += 1
    return (miss, nx * ny, top)
def auto_ceiling():
    from mathutils import Vector
    objs = [o for o in bpy.data.objects if o.type == 'MESH' and o.name != 'Auto_Ceiling']
    shell = [o for o in objs if any(c.name.lower().startswith('shell') for c in o.users_collection)] or objs
    pts = [o.matrix_world @ Vector(c) for o in shell for c in o.bound_box]
    if not pts:
        return
    x0, x1 = min(p.x for p in pts), max(p.x for p in pts)
    y0, y1 = min(p.y for p in pts), max(p.y for p in pts)
    z = max(p.z for p in pts)
    R = globals().get('ROOM')
    if isinstance(R, dict) and isinstance(R.get('h'), (int, float)):
        z = R['h']
    m = MATS.get('ceiling') or pbr('auto_ceiling', (0.85, 0.85, 0.83), (0.5, 0.7))
    o = box('Auto_Ceiling', (x1 - x0, y1 - y0, 0.05), ((x0 + x1) / 2, (y0 + y1) / 2, z + 0.025), m, 'Shell', 0)
    try:
        o.visible_shadow = False
    except Exception:
        pass
def report(lines, title='Build finished'):
    txt = bpy.data.texts.get('build_log') or bpy.data.texts.new('build_log')
    txt.clear()
    txt.write('\n'.join(lines))
    def draw(self, ctx):
        for l in lines[:12]:
            self.layout.label(text=l[:90])
        self.layout.label(text='Full log: Text Editor > build_log')
    try:
        bpy.context.window_manager.popup_menu(draw, title=title, icon='INFO')
    except Exception:
        pass
    print('\n'.join(lines))
def pbr(name, base_rgb=(0.6, 0.6, 0.6), rough=(0.5, 0.7), kind='plaster', bump=0.08, scale=1.0, var=0.12, **kw):
    base = tuple(kw.get('base', kw.get('color', kw.get('base_color', base_rgb))))[:3]
    if 'roughness' in kw:
        rough = kw['roughness']
    if not isinstance(rough, (tuple, list)):
        rough = (max(0, rough - 0.05), min(1, rough + 0.05))
    if name in MATS:
        return MATS[name]
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    nt.nodes.clear()
    N = nt.nodes.new
    L = nt.links.new
    out = N('ShaderNodeOutputMaterial')
    bs = N('ShaderNodeBsdfPrincipled')
    tc = N('ShaderNodeTexCoord')
    mp = N('ShaderNodeMapping')
    L(tc.outputs['Object'], mp.inputs['Vector'])
    mp.inputs['Scale'].default_value = (scale, scale, scale)
    mp.name = 'GrainMap'
    oi = N('ShaderNodeObjectInfo')
    off = N('ShaderNodeCombineXYZ')
    L(_mn(nt, 'MULTIPLY', oi.outputs['Random'], 41.0), off.inputs['X'])
    L(_mn(nt, 'MULTIPLY', oi.outputs['Random'], 17.0), off.inputs['Y'])
    L(_mn(nt, 'MULTIPLY', oi.outputs['Random'], 29.0), off.inputs['Z'])
    L(off.outputs['Vector'], mp.inputs['Location'])
    n1 = N('ShaderNodeTexNoise')
    n1.inputs['Scale'].default_value = 3
    n1.inputs['Detail'].default_value = 8
    n2 = N('ShaderNodeTexNoise')
    n2.inputs['Scale'].default_value = 60
    vo = N('ShaderNodeTexVoronoi')
    vo.inputs['Scale'].default_value = 30
    for t in (n1, n2, vo):
        L(mp.outputs['Vector'], t.inputs['Vector'])
    fac = n1.outputs['Fac']
    if kind == 'wood':
        wv = N('ShaderNodeTexWave')
        wv.inputs['Scale'].default_value = 25
        wv.bands_direction = 'DIAGONAL'
        wv.inputs['Distortion'].default_value = 8
        wv.inputs['Detail'].default_value = 3
        L(mp.outputs['Vector'], wv.inputs['Vector'])
        fac = wv.outputs['Fac']
    mx = N('ShaderNodeMix')
    mx.data_type = 'RGBA'
    mx.inputs[6].default_value = tuple(max(0, c * (1 - var)) for c in base) + (1,)
    mx.inputs[7].default_value = tuple(min(1, c * (1 + var)) for c in base) + (1,)
    L(_mn(nt, 'ADD', fac, _mn(nt, 'MULTIPLY', _mn(nt, 'SUBTRACT', oi.outputs['Random'], 0.5), 0.5)), mx.inputs[0])
    ao = N('ShaderNodeAmbientOcclusion')
    ao.inputs['Distance'].default_value = 0.3
    L(mx.outputs[2], ao.inputs['Color'])
    m2 = N('ShaderNodeMix')
    m2.data_type = 'RGBA'
    m2.inputs[0].default_value = 0.7
    L(mx.outputs[2], m2.inputs[6])
    L(ao.outputs['Color'], m2.inputs[7])
    cc = m2.outputs[2]
    if kind == 'plaster':
        sz = N('ShaderNodeSeparateXYZ')
        L(tc.outputs['Generated'], sz.inputs['Vector'])
        st = N('ShaderNodeTexNoise')
        st.inputs['Scale'].default_value = 0.8
        st.inputs['Detail'].default_value = 6
        sk = N('ShaderNodeTexNoise')
        sk.inputs['Scale'].default_value = 4
        m3 = N('ShaderNodeMapping')
        m3.inputs['Scale'].default_value = (14, 14, 0.5)
        L(tc.outputs['Generated'], m3.inputs['Vector'])
        L(tc.outputs['Generated'], st.inputs['Vector'])
        L(m3.outputs['Vector'], sk.inputs['Vector'])
        lv = _mn(nt, 'ADD', _mn(nt, 'MULTIPLY', st.outputs['Fac'], 0.35), _mn(nt, 'MULTIPLY', sk.outputs['Fac'], 0.25))
        sf = _mn(nt, 'MAXIMUM', _mn(nt, 'MULTIPLY', lv, 0.6), _mn(nt, 'MULTIPLY', _rng(nt, sz.outputs['Z'], 0.0, 0.12, 1.0, 0.0), 0.3))
        sm = N('ShaderNodeMix')
        sm.data_type = 'RGBA'
        sm.blend_type = 'MULTIPLY'
        sm.inputs[7].default_value = (0.72, 0.7, 0.67, 1)
        L(sf, sm.inputs[0])
        L(cc, sm.inputs[6])
        pt = N('ShaderNodeCombineXYZ')
        tone = _mn(nt, 'ADD', 0.96, _mn(nt, 'MULTIPLY', oi.outputs['Random'], 0.08))
        for ax in ('X', 'Y', 'Z'):
            L(tone, pt.inputs[ax])
        sm2 = N('ShaderNodeMix')
        sm2.data_type = 'RGBA'
        sm2.blend_type = 'MULTIPLY'
        sm2.inputs[0].default_value = 1.0
        L(sm.outputs[2], sm2.inputs[6])
        L(pt.outputs['Vector'], sm2.inputs[7])
        cc = sm2.outputs[2]
    L(cc, bs.inputs['Base Color'])
    ad = N('ShaderNodeMath')
    ad.operation = 'ADD'
    L(n2.outputs['Fac'], ad.inputs[0])
    L(vo.outputs['Distance'], ad.inputs[1])
    mr = N('ShaderNodeMapRange')
    mr.inputs['From Max'].default_value = 2.0
    mr.inputs['To Min'].default_value = rough[0]
    mr.inputs['To Max'].default_value = rough[1]
    L(ad.outputs[0], mr.inputs['Value'])
    L(mr.outputs['Result'], bs.inputs['Roughness'])
    bp = N('ShaderNodeBump')
    bp.inputs['Strength'].default_value = bump
    bp.inputs['Distance'].default_value = 0.01
    L(n2.outputs['Fac'], bp.inputs['Height'])
    L(bp.outputs['Normal'], bs.inputs['Normal'])
    if kind == 'metal':
        bs.inputs['Metallic'].default_value = 1.0
    L(bs.outputs['BSDF'], out.inputs['Surface'])
    m['kind'] = kind
    MATS[name] = m
    return m
def glass(name='Glass', tint=(0.92, 0.96, 1.0, 1.0)):
    if name in MATS:
        return MATS[name]
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    nt.nodes.clear()
    N = nt.nodes.new
    L = nt.links.new
    out = N('ShaderNodeOutputMaterial')
    lp = N('ShaderNodeLightPath')
    tr = N('ShaderNodeBsdfTransparent')
    tr.inputs['Color'].default_value = tint
    gl = N('ShaderNodeBsdfGlossy')
    gl.inputs['Roughness'].default_value = 0.02
    fr = N('ShaderNodeFresnel')
    fr.inputs['IOR'].default_value = 1.45
    inn = N('ShaderNodeMixShader')
    L(fr.outputs[0], inn.inputs[0])
    L(tr.outputs[0], inn.inputs[1])
    L(gl.outputs[0], inn.inputs[2])
    sh = N('ShaderNodeBsdfTransparent')
    mo = N('ShaderNodeMixShader')
    L(lp.outputs['Is Shadow Ray'], mo.inputs[0])
    L(inn.outputs[0], mo.inputs[1])
    L(sh.outputs[0], mo.inputs[2])
    L(mo.outputs[0], out.inputs['Surface'])
    MATS[name] = m
    return m
