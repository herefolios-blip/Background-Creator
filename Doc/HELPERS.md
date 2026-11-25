# Helper reference

Everything here is defined in the Python header that `index.html` writes into every build script. A chat AI that writes a stage must call these helpers and must not redefine or re-import them. Source of truth is `index.html` (script blocks `hlp` and `run`).

Last updated 25 November 2026. Items marked **(unconfirmed)** are written but have not yet been confirmed by one of the user's Blender renders or build logs.

## Conventions

- Units are metres. Rotations are radians. The scene's floor is at z = 0.
- `loc` for furniture is the centre of the footprint on the floor, `(x, y, 0)`. The helper adds the height itself.
- `facing=(fx, fy)` is the direction an item's front points. For furniture against a wall it points from the wall into the room. A sofa facing a camera that looks along +Y uses `(0, -1)`.
- `style` is `'modern'`, `'midcentury'` or `'industrial'` on every furniture helper. Pick one that suits the mood and mix at most two.
- Colours are `(r, g, b)` in linear values below 0.8. Leave `color` and `wood` out to get the style's own palette.
- Every helper tolerates wrong keywords and non-string arguments where it can (`width=`, `depth=`, `height=`, `colour=` are accepted as aliases).
- Helpers that place something call `reserve()` themselves and return an object, or `None` when there is no room. When a helper returns `None`, skip it and anything that sits on it. Do not call `reserve()` again for it.
- Never use `bpy.ops`. Create meshes with `box()`, `cyl()` or the helpers below.
- Node socket colours need four values: use `rgba((r, g, b))` or `kelvin4(k)`. `kelvin(k)` returns three values and is only for `Light.color`.
- `mathutils`, `Vector`, `Matrix` and `Euler` are already imported. `bpy.mathutils` also works because the header aliases it.

## Geometry

| Helper | Purpose |
|---|---|
| `box(name, size, loc, mat=None, col='Set', b=0.006, rot=(0,0,0))` | Cuboid with a bevel modifier. `size` is `(x, y, z)`, `col` is the collection name and must be a string, `mat` a material object. Wood materials align their grain with the longest side automatically. |
| `cyl(name, r, h, loc, mat=None, col='Set', seg=32, b=0.004, rot=(0,0,0))` | Cylinder along local Z, smooth-shaded. |
| `collection(name)` | Get or create a collection under the scene collection. |
| `bevel(obj, w=0.006)` | Add a 2-segment bevel limited by angle. |
| `leaf`, `tube`, `leaf_mat` | Foliage pieces used by `plant()`. Use them for custom foliage only. |

## Materials

| Helper | Purpose |
|---|---|
| `pbr(name, base_rgb, rough=(lo,hi), kind='plaster', bump=0.08, scale=1.0, var=0.12)` | Procedural material with per-object variation. `kind` is `plaster`, `wood`, `carpet`, `fabric`, `paper` or `metal`. `plaster` adds stains, streaks and scuffs, `wood` adds grain, `fabric` and `carpet` add a procedural weave and sheen **(unconfirmed, the weave is fine and may only show close up)**. Any other `kind` (the furniture helpers use `leather`) gets the generic noise breakup. Materials are cached by name in `MATS`. |
| `glass(name='Glass')` | Window glass that does not darken the room for shadow rays. |
| `ph_material(name, pid, scale)`, `ph_hdri(pid)` | Poly Haven downloads. Return `None` on failure, then fall back to `pbr()` or a Nishita sky. Never write a downloader. |
| `rgba(c, a=1.0)`, `kelvin(k)`, `kelvin4(k)` | Colour helpers, see Conventions. |

## Layout and placement

| Helper | Purpose |
|---|---|
| `reserve(name, loc, size, slide=(1,0,0), visible=True, pad=0.05, group=None)` | Returns a collision-free spot or `None`. Floor items search nearby spots in a spiral. Wall items slide along `slide`. See the rules below. |
| `room_bounds()` | `((xmin, ymin), (xmax, ymax))` of the room interior, or `None`. |
| `in_view(loc, size, margin=0.04, floor=False)` | Whether a box is inside the camera frame. With `floor=True` the base may fall below the bottom edge. |

What `reserve()` enforces for floor items:

1. The footprint stays inside the room walls.
2. It stays out of the talent clear zone (`CLEAR_ZONE_W` wide, from the camera to `TALENT_DIST + 0.75` m ahead).
3. It does not collide with anything already reserved.
4. It is inside the camera frame (the base may be cut off).
5. Plants, lamps, stools, tables, chairs, desks, sideboards, cabinets, consoles, TV units, benches, counters, dressers, nightstands and wardrobes may not cover a bookcase or display unit in the camera view. Sofas and beds are exempt.
6. A bookcase or display unit avoids spots where it would be covered by those items. If it has no clear spot it is still built and the `Layout` line says so. Build bookcases and display units first to avoid this.
7. Rugs, carpets and anything under 3 cm tall are only kept inside the walls, so furniture can sit on them.

## Furniture catalogue

All take `name, loc, facing, style` and return an object or `None`.

In the app, the **Furniture pieces** checklist in *Look and lighting* decides which of these (plus `plant` and `art`) the prompt asks for. Each scene preset shows only the pieces that suit it, with sensible ones ticked, and *Show all pieces* reveals the rest. The **Furniture style** dropdown sets `style=` for every call, or leaves it to the AI (*Match the photo*). Choosing *None, clear floor* under *Furniture in front of background* hides the list.

| Helper | Defaults and notes |
|---|---|
| `sofa(name, loc, w=2.0, d=0.92, h=0.85, color, wood, seed, pillows=2, throw=True)` | Legs, base, two arms with padded tops, back frame, seat and back cushions with sag and tilt, throw pillows, a folded throw. Cushion count follows the width. |
| `armchair(name, loc, w=0.82, d=0.86, h=0.82, color, wood, seed, pillows=1, throw=False)` | Same builder as the sofa. |
| `chair(name, loc, color, wood, seed, swivel=0.0)` | Modern: swivel task chair with a five-spoke base. Midcentury: wooden dining or desk chair. Industrial: steel and plywood. Face it toward its desk or table. |
| `desk(name, loc, w=1.4, d=0.7, h=0.75, wood, props=True)` | Front is where the sitter sits, so `facing` points away from the wall. Modern: side panels. Midcentury: legs plus a drawer pedestal. Industrial: steel frame. Props are a closed laptop, a mug and a notebook. |
| `table(name, loc, w=1.0, d=0.55, h=0.45, wood, shape='rect', shelf=None)` | `shape='round'` gives a round top on three legs. A lower shelf is on by default for tables 0.55 m tall or less. |
| `sideboard(name, loc, w=1.6, d=0.45, h=0.78, wood, doors=3, props=True)` | Doors with style-specific hardware. Props are a vase, two books and a bowl. |
| `tv_unit(name, loc, w=1.8, d=0.42, h=0.5, wood, doors=3, tv=True)` | Low cabinet with a dark TV on a stand. |
| `bookcase(name, loc, w=0.9, d=0.32, h=1.9, shelves=5, wood, seed, books=True)` | Boards, kickplate, legs or steel posts, back panel, `book_row()` rows, vases, boxes, candles, a stack and a bowl on top. Books are only built when `facing` is along the Y axis because `book_row()` works in world axes. Shelving is registered with the shelf guard. |
| `rug(name, loc, w=2.4, d=1.7, color, border=None, seed)` | Puffy pile with a curled edge and a border band. Not limited to the camera frame. |
| `curtain(name, loc, w=1.8, h=2.4, color, side='both', seed, rod=True)` | `loc` is the wall base below the window, `w` is the window width. `side` is `both`, `left`, `right` or `center`. Pleated panels and a brass rod. |
| `bed(name, loc, w=1.6, d=2.1, h=1.05, color, wood, seed, pillows=2, throw=True)` **(unconfirmed)** | Headboard, base, mattress, duvet, pillows and a folded throw. `d` runs head to foot and `h` is the headboard height. The headboard is at the back, so `facing` points from the headboard toward the foot (normally from the wall into the room). `color` is the duvet. Modern: upholstered headboard on a platform base. Midcentury: slatted wooden headboard on tapered legs. Industrial: steel frame with a bar headboard. |
| `nightstand(name, loc, w=0.45, d=0.4, h=0.55, wood, drawers=2, props=True)` **(unconfirmed)** | Drawer unit. Returns its top, whose `.location` is the middle of the top surface. Props are a book and a small vase: pass `props=False` to stand a lamp on it. |
| `dresser(name, loc, w=1.2, d=0.5, h=0.85, wood, rows=3, cols=2, props=True)` **(unconfirmed)** | Drawer grid with style-specific pulls (groove, brass, steel bar). Props are a vase, a brass tray and a book. |
| `wardrobe(name, loc, w=1.2, d=0.6, h=2.0, wood, doors=2)` **(unconfirmed)** | Tall doored cabinet with a plinth or legs and style-specific handles. |
| `counter(name, loc, w=2.0, d=0.65, h=1.05, wood, props=True)` **(unconfirmed)** | Cafe or shop counter. The front (customer side) points along `facing`. Modern: fluted wood front with a stone top. Midcentury: panelled front, wood top, brass foot rail. Industrial: ribbed steel front with a zinc top. Props are a till with a screen and three cups. |
| `stool(name, loc, h=0.65, r=0.2, color, wood)` **(unconfirmed)** | Bar or counter stool with a round seat and a footrest. Use `h=0.45` for a low stool. `color` is the seat pad (not used by the industrial style). |
| `bench(name, loc, w=1.4, d=0.4, h=0.45, color, wood, cushion=None)` **(unconfirmed)** | Slab top on legs. Cushioned by default except in the industrial style, which gets steel side rails. |
| `display_unit(name, loc, w=1.2, d=0.45, h=1.4, wood, shelves=4, items=True)` **(unconfirmed)** | Open retail shelving stocked with folded stacks, boxes, bottles and jars. The products are generic shapes, not real items. Registered with the shelf guard like a bookcase (it is renamed `<name>_Shelving` for `reserve()`). |

Style differences:

| Style | Legs and frame | Wood | Upholstery |
|---|---|---|---|
| modern | straight legs or a plinth | light oak | grey-brown fabric |
| midcentury | tall tapered splayed legs, brass pulls | walnut | mustard fabric |
| industrial | black steel, plank tops | dark wood | brown leather |

## Other props

| Helper | Purpose |
|---|---|
| `plant(name, loc, height=0.9, leaves=16, seed=1, pot=None)` | Potted plant with stems that connect every leaf. Reserve its spot first. |
| `book_row(name, x0, x1, y, z, depth=0.2, seed=1, hmin=0.2, hmax=0.32, face=-1)` | Fills one shelf between world x0 and x1. `y` is the shelf back, `z` the shelf top, `face=-1` points spines toward -Y. Normally called by `bookcase()`. |
| `art(name, loc, w, h, facing=(0,-1), seed=1)` | Framed abstract artwork with its own `reserve()`. |
| `door(name, loc, w=0.9, h=2.1, facing=(0,-1))` | Frame, panelled leaf, lever, hinges, kickplate **(unconfirmed)**. |

## Lights

| Helper | Purpose |
|---|---|
| `lamp(name, kind, loc, watts, k=4000, size=0.5, rot=(0,0,0), spot=0.9, col='Lights')` | `kind` is `AREA`, `POINT`, `SPOT` or `SUN`. For `SUN`, `watts` is strength (2 to 6) and `size` is the angle in degrees. Create the light for a lamp or sconce in the dressing stage, right after its fixture, at the fixture's returned `loc`. Do not create fixture lights in the lighting stage. |
| `window_light(name, loc, w, h, aim, watts=900, k=5600, bars=(3,2))` | Large soft window light with camera-invisible bars that cast a pane-shaped shadow pattern **(unconfirmed)**. |
| `fallback_lighting()` | Runner only. Adds a soft area light and a dim world if stage 3 fails. |

## Automatic checks the runner performs

These run after the stages, in this order. They are not called by the AI.

| Check | What it does |
|---|---|
| `contain_props()` | Moves stray props back inside the room and into frame. Rugs are excluded from clusters. |
| `enforce_clear_zone()` | Groups touching pieces, then shifts a group sideways out of the clear zone, or hides the whole group in `ClearZone_Hidden` if there is no spot. |
| `hide_occluded_fixtures()` | Hides sconces whose geometry sits inside furniture. |
| `audit_practical_lights()` | Removes a point or spot light that sits inside furniture, or whose wall fixture is about a third or more hidden from the camera. Floor lamps are not removed. An object whose name also contains a fixture word (for example `Desk_Lamp` or `Nightstand_Lamp`) counts as a fixture, never as furniture, so a lamp's own light is not removed. |
| `remove_orphan_lights()` | Moves a stray light onto the fixture with matching name parts, or switches it off if there is none. A bookcase shelf is not a fixture. |
| `seal_gaps()` | Patches camera rays that hit nothing. |
| `frame_check()` and `auto_ceiling()` | Adds a ceiling if the top of the frame is open. |
| `layout_report()` | Reports overlaps and cut-off decor. |
| `auto_expose()` | Sets exposure so the frame reads evenly. |

## Reading the build log

| Line | Meaning |
|---|---|
| `OK: stageN_...` or `FAILED: stageN_... | traceback` | Whether each stage ran. A failed stage 3 means no key light, so expect an orange, over-exposed result. |
| `Stage 3 did not finish, added Fallback_Soft_Key ...` | The fallback light was used. |
| `Clear zone: moved N objects ... | camera ..., zone ..., shifted ... / hid whole groups ...` | What the clear zone did and why. A hidden whole bookcase means it overlapped the zone and could not move. |
| `Layout: ...` | Items `reserve()` moved, and `NO ROOM for X: skipped` for items it could not place. |
| `Light audit: <light> near <fixture>: kept/REMOVED` | Every practical light and its matched fixture. |
| `Removed lights and fixtures hidden behind furniture` | What the audit removed. |
| `Hid wall fixtures that sat inside furniture` | Sconces hidden by the overlap check. |
| `Moved lights onto their fixtures` | Orphan lights re-attached to a matching fixture. |
| `Switched off lights with no fixture nearby` | Orphan lights that had no fixture. |
| `Frame check: N of M view rays hit nothing` | A non-zero number means an open shell. |
| `Auto exposure set to X EV` | A value below about -1.5 or above +1.5 means the lights are far too strong or too weak. |
