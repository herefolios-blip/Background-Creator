def _t(name, fn):
    try:
        fn()
        return 'PASS: ' + name
    except Exception as e:
        return 'FAIL: ' + name + ' ' + repr(e)
def _ph2():
    assert ph_material('t_ph', 'brown_planks_03'), str(PH_LOG[-3:])
def _ph():
    assert ph_json('https://api.polyhaven.com/files/brown_planks_03'), str(PH_LOG[-1:])
R = [
    _t('pbr plaster', lambda: pbr('t_plaster', (0.7, 0.7, 0.7))),
    _t('pbr wood', lambda: pbr('t_wood', (0.4, 0.25, 0.12), (0.3, 0.45), 'wood')),
    _t('glass', lambda: glass('t_glass')),
    _t('box', lambda: box('t_box', (1, 1, 1), (0, 0, 0.5), MATS['t_plaster'])),
    _t('cyl', lambda: cyl('t_cyl', 0.2, 0.5, (2, 0, 0.25), MATS['t_wood'])),
    _t('configure_render', configure_render),
    _t('poly haven reachable', _ph),
    _t('poly haven texture', _ph2),
]
R.append('Blender ' + bpy.app.version_string)
report(R, 'Helper self-test')
