# Helper reference

These functions are defined in the script header and are described to the AI so it uses them instead of inventing its own.

## Geometry
- `box(name, size=(x,y,z), loc=(x,y,z), mat, col='Set', b=0.006, rot=(rx,ry,rz))` bevelled box built from the data API. Wood materials align their grain to the longest side.
- `cyl(name, r, h, loc, mat, col, seg=32, b=0.004, rot)` smooth-shaded cylinder.
- `tube(name, p0, p1, r0, r1, mat, col, bend)` tapered curved tube, used for plant stems.
- `collection(name)`, `bevel(obj, w)`.

## Materials
- `pbr(name, base_rgb, rough=(lo,hi), kind='plaster|wood|carpet|fabric|paper|metal', bump, scale, var)` procedural material with per-object variation and corner darkening. `plaster` adds stains, streaks and scuffs.
- `glass(name)` architectural glass with the shadow-ray trick.
- `leaf_mat(name, base)` veined translucent leaf shader.
- `ph_material(name, id, scale)` and `ph_hdri(id)` Poly Haven downloads with caching; return `None` on failure.
- `art_mat(seed)` calm abstract colour field for pictures.

## Objects
- `art(name, loc, w, h, facing, seed)` framed, mounted, glazed picture.
- `door(name, loc, w, h, facing)` frame, panelled leaf, lever, hinges, kickplate.
- `plant(name, loc, height, leaves, seed)` pot, soil, stems, veined leaves; `leaf(...)`.
- `book_row(name, x0, x1, y, z, depth, seed, hmin, hmax, face)` one shelf of varied books.

## Lighting
- `kelvin(k)`, `lamp(name, kind, loc, watts, k, size, rot, spot, col)`.
- `window_light(name, loc, w, h, aim, watts, k, bars)` soft window light with camera-invisible bars that cast a pane shadow pattern.

## Layout and checks
- `reserve(name, loc, size, slide, visible, pad, group)` collision-free, in-room, in-frame placement; returns a location or `None`.
- `in_view`, `room_bounds`, `contain_props`, `enforce_clear_zone`, `remove_orphan_lights`, `seal_gaps`, `frame_check`, `auto_ceiling`, `layout_report`, `auto_expose`, `reset_scene`, `report`.

## Constants at the top of a built script
`RESET_SCENE`, `AUTO_EXPOSE`, `AE_TARGET`, `CLEAR_ZONE_W`, `TALENT_DIST`, `CLEAR_ZONE_NAMES`, `RENDER_PREVIEW`, `TEST_CYCLES`, `PREVIEW_SAMPLES`, `FINAL_SAMPLES`, `FINAL`.
