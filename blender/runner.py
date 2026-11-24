LOG = []
if RESET_SCENE:
    LOG.append('Scene reset: removed %d old objects before building' % reset_scene())
for i in range(1, 6):
    f = next((g for n, g in sorted(globals().items()) if n.startswith('stage%d_' % i) and callable(g)), None)
    if f is None:
        LOG.append('SKIPPED: no function named stage%d_...' % i)
        continue
    try:
        f()
        LOG.append('OK: ' + f.__name__)
    except Exception:
        import traceback
        tb = traceback.format_exc().strip().splitlines()
        LOG.append('FAILED: ' + f.__name__ + ' | ' + ' | '.join(l.strip() for l in tb[-3:]))
try:
    cp = contain_props()
    if cp:
        LOG.append('Moved stray props back inside the room and into frame: ' + ', '.join(cp[:6]))
except Exception as e:
    LOG.append('Contain check failed: ' + repr(e))
try:
    zn, zi = enforce_clear_zone()
    LOG.append('Clear zone: moved %d objects %s | %s' % (len(zn), ', '.join(zn[:6]), zi))
except Exception as e:
    LOG.append('Clear zone failed: ' + repr(e))
try:
    og = remove_orphan_lights()
    if og:
        LOG.append('Switched off lights with no fixture nearby (they cause stray glow): ' + ', '.join(og[:6]))
except Exception as e:
    LOG.append('Orphan light check failed: ' + repr(e))
try:
    configure_render()
except Exception as e:
    LOG.append('FAILED: configure_render ' + repr(e))
try:
    sg = seal_gaps()
    if sg:
        LOG.append('Sealed gaps in the shell with patches: ' + ', '.join(sg))
except Exception as e:
    LOG.append('Seal check failed: ' + repr(e))
try:
    fm = frame_check()
    if fm[2] >= 3:
        auto_ceiling()
        LOG.append('Open top of frame detected: added Auto_Ceiling')
        fm = frame_check()
    LOG.append('Frame check: %d of %d view rays hit nothing' % (fm[0], fm[1]))
except Exception as e:
    LOG.append('Frame check failed: ' + repr(e))
try:
    lr = layout_report()
    LOG.append('Layout: ' + ('; '.join(lr[:8]) if lr else 'no collisions or cut-off decor found'))
except Exception as e:
    LOG.append('Layout check failed: ' + repr(e))
if AUTO_EXPOSE:
    try:
        LOG.append('Auto exposure set to %+.2f EV' % auto_expose(AE_TARGET))
    except Exception as e:
        LOG.append('Auto exposure failed: ' + repr(e))
LOG.append('Meshes: %d, lights: %d, cameras: %d' % tuple(sum(1 for o in bpy.data.objects if o.type == t) for t in ('MESH', 'LIGHT', 'CAMERA')))
LOG.append('Poly Haven: ' + (', '.join(PH_LOG[:6]) if PH_LOG else 'no downloads attempted'))
report(LOG)
if RENDER_PREVIEW:
    sc.render.filepath = '//preview.png'
    bpy.ops.render.render(write_still=True)
