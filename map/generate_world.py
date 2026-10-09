#!/usr/bin/env python3
"""Generate a self-contained SDF 1.8 campus and an independently reusable car.

Python standard library only. Coordinates and dimensions are in real-world meters.
Edit config.json for road spacing, illumination, camera and spawn settings.
Edit BUILDINGS and the scenery section for campus layout changes.
"""
from pathlib import Path
import json
import math
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parent
C = json.loads((ROOT / 'config.json').read_text())
WHITE = '0.95 0.95 0.92 1'
ASPHALT = '0.2 0.2 0.2 1'
BUILDINGS = [
    # name, x, y, length, width, height, color
    ('A_administration', -16, 17, 15, 19, 12, '0.85 0.42 0.16 1'),
    ('C_classrooms', -16, 36, 15, 10, 10, '0.63 0.72 0.48 1'),
    ('E_workshops', 16, 27, 16, 28, 7, '0.22 0.49 0.67 1'),
    ('library', 16, -15, 15, 14, 9, '0.73 0.62 0.45 1'),
    ('technology', 16, -35, 15, 12, 11, '0.58 0.63 0.69 1'),
    ('student_services', -16, -12, 15, 11, 6, '0.80 0.63 0.34 1'),
]


def el(parent, tag, text=None, **attrs):
    e = ET.SubElement(parent, tag, attrs)
    if text is not None:
        e.text = str(text)
    return e


def nums(values):
    return ' '.join(f'{v:.8g}' for v in values)


def pose(parent, values):
    el(parent, 'pose', nums(values))


def material(v, color):
    m = el(v, 'material')
    el(m, 'ambient', color)
    el(m, 'diffuse', color)
    el(m, 'specular', '0.05 0.05 0.05 1')


def geometry(parent, kind, size):
    shape = el(el(parent, 'geometry'), kind)
    if kind == 'box':
        el(shape, 'size', nums(size))
    elif kind == 'cylinder':
        el(shape, 'radius', size[0])
        el(shape, 'length', size[1])
    elif kind == 'sphere':
        el(shape, 'radius', size[0])


def part(link, name, p, size, color, kind='box', collide=True, shadows=True):
    v = el(link, 'visual', name=name)
    pose(v, p)
    geometry(v, kind, size)
    material(v, color)
    el(v, 'cast_shadows', str(shadows).lower())
    if collide:
        c = el(link, 'collision', name=name + '_collision')
        pose(c, p)
        geometry(c, kind, size)
        return c


def static(parent, name, p=(0, 0, 0, 0, 0, 0)):
    m = el(parent, 'model', name=name)
    el(m, 'static', 'true')
    pose(m, p)
    return el(m, 'link', name='link')


def inertia(link, mass, ix, iy, iz):
    i = el(link, 'inertial')
    el(i, 'mass', mass)
    t = el(i, 'inertia')
    for key, value in [('ixx', ix), ('iyy', iy), ('izz', iz),
                       ('ixy', 0), ('ixz', 0), ('iyz', 0)]:
        el(t, key, value)


def plugin(parent, filename, name, values=()):
    p = el(parent, 'plugin', filename=filename, name=name)
    for k, v in values:
        el(p, k, v)
    return p


def car(parent, p):
    m = el(parent, 'model', name='ute_car')
    pose(m, p)
    el(m, 'self_collide', 'false')
    body = el(m, 'link', name='chassis')
    pose(body, (0, 0, 0.72, 0, 0, 0))
    # Conservative box approximation to body + cabin mass distribution.
    inertia(body, 1100, 390, 1850, 2000)
    part(body, 'body', (0, 0, 0, 0, 0, 0), (4.4, 1.8, 0.60), '0.08 0.32 0.70 1')
    part(body, 'cabin', (-0.25, 0, 0.55, 0, 0, 0), (2.25, 1.58, 0.60), '0.12 0.38 0.75 1')
    part(body, 'windshield', (0.885, 0, 0.55, 0, 0, 0), (0.025, 1.42, 0.45), '0.09 0.18 0.23 1', collide=False)
    for side in (-1, 1):
        part(body, f'window_{side}', (-0.25, side * 0.80, 0.55, 0, 0, 0), (1.95, 0.025, 0.43), '0.09 0.18 0.23 1', collide=False)
        part(body, f'headlamp_{side}', (2.205, side * 0.58, 0.08, 0, 0, 0), (0.025, 0.36, 0.16), WHITE, collide=False)
        part(body, f'taillamp_{side}', (-2.205, side * 0.58, 0.08, 0, 0, 0), (0.025, 0.36, 0.16), '0.85 0.035 0.025 1', collide=False)
    # Camera ahead of body, 1.10 m above road, looking along local +X.
    part(body, 'camera_housing', (2.24, 0, 0.38, 0, 0, 0), (0.12, 0.18, 0.12), '0.04 0.04 0.04 1', collide=False)
    sensor = el(body, 'sensor', name='front_camera', type='camera')
    pose(sensor, (2.31, 0, 0.38, 0, 0.08, 0))
    el(sensor, 'always_on', 'true')
    el(sensor, 'update_rate', C['camera_rate'])
    el(sensor, 'topic', '/ute_car/front_camera/image')
    cam = el(sensor, 'camera')
    el(cam, 'horizontal_fov', 1.3962634)
    im = el(cam, 'image')
    el(im, 'width', C['camera_width'])
    el(im, 'height', C['camera_height'])
    el(im, 'format', 'R8G8B8')
    clip = el(cam, 'clip')
    el(clip, 'near', 0.05)
    el(clip, 'far', 180)
    el(cam, 'camera_info_topic', '/ute_car/front_camera/camera_info')

    # Wheelbase 2.65 m, track 1.56 m; outer tire width 1.80 m.
    for front, x in [(True, 1.325), (False, -1.325)]:
        for side, y in [('left', 0.78), ('right', -0.78)]:
            name = ('front_' if front else 'rear_') + side
            parent_link = 'chassis'
            if front:
                knuckle = el(m, 'link', name=name + '_knuckle')
                pose(knuckle, (x, y, 0.32, 0, 0, 0))
                inertia(knuckle, 3, 0.015, 0.015, 0.015)
                parent_link = name + '_knuckle'
                joint(m, name + '_steer', 'chassis', parent_link, (0, 0, 1), True)
            wheel = el(m, 'link', name=name + '_wheel')
            pose(wheel, (x, y, 0.32, 0, 0, 0))
            # Cylinder geometry is rotated; the link frame stays aligned with car.
            inertia(wheel, 18, 0.5472, 0.9216, 0.5472)
            c = part(wheel, 'tire', (0, 0, 0, math.pi / 2, 0, 0), (0.32, 0.24), '0.045 0.045 0.045 1', 'cylinder')
            ode = el(el(el(c, 'surface'), 'friction'), 'ode')
            el(ode, 'mu', 1.0)
            el(ode, 'mu2', 1.0)
            part(wheel, 'hub', (0, 0.125 if y > 0 else -0.125, 0, math.pi / 2, 0, 0), (0.18, 0.012), '0.65 0.68 0.72 1', 'cylinder', False)
            joint(m, name + '_axle', parent_link, name + '_wheel', (0, 1, 0))
    plugin(m, 'gz-sim-ackermann-steering-system', 'gz::sim::systems::AckermannSteering', [
        ('left_joint', 'rear_left_axle'), ('right_joint', 'rear_right_axle'),
        ('left_steering_joint', 'front_left_steer'), ('right_steering_joint', 'front_right_steer'),
        ('wheel_base', 2.65), ('wheel_separation', 1.56), ('kingpin_width', 1.56),
        ('wheel_radius', 0.32), ('steering_limit', 0.50), ('steer_p_gain', 8),
        ('min_velocity', -3), ('max_velocity', 8),
        ('min_acceleration', -3), ('max_acceleration', 2),
        ('topic', '/model/ute_car/cmd_vel'), ('odom_topic', '/model/ute_car/odometry'),
        ('odom_publish_frequency', 30)])
    plugin(m, 'gz-sim-joint-state-publisher-system', 'gz::sim::systems::JointStatePublisher',
           [('topic', '/model/ute_car/joint_state')])
    return m


def joint(model, name, parent, child, axis, steering=False):
    j = el(model, 'joint', name=name, type='revolute')
    el(j, 'parent', parent)
    el(j, 'child', child)
    a = el(j, 'axis')
    el(a, 'xyz', nums(axis))
    lim = el(a, 'limit')
    el(lim, 'lower', -0.70 if steering else -1e16)
    el(lim, 'upper', 0.70 if steering else 1e16)
    el(lim, 'effort', 1500)
    el(lim, 'velocity', 3 if steering else 100)
    dyn = el(a, 'dynamics')
    el(dyn, 'damping', 0.2 if steering else 0.02)


def building(w, spec):
    name, x, y, sx, sy, h, color = spec
    l = static(w, name, (x, y, 0, 0, 0, 0))
    part(l, 'block', (0, 0, h / 2, 0, 0, 0), (sx, sy, h), color)
    part(l, 'roof', (0, 0, h + 0.12, 0, 0, 0), (sx + 0.3, sy + 0.3, 0.24), '0.83 0.82 0.76 1')
    # Simple ribbon windows, no external meshes or textures.
    for floor in range(1, int(h / 3) + 1):
        for side in (-1, 1):
            part(l, f'windows_y_{floor}_{side}', (0, side * (sy / 2 + 0.018), floor * 2.8 - 0.4, 0, 0, 0), (sx - 1.3, 0.03, 1.0), '0.16 0.30 0.36 1', collide=False)
            part(l, f'windows_x_{floor}_{side}', (side * (sx / 2 + 0.018), 0, floor * 2.8 - 0.4, 0, 0, 0), (0.03, sy - 1.3, 1.0), '0.16 0.30 0.36 1', collide=False)
    part(l, 'entry', (0, -sy / 2 - 0.018, 1.3, 0, 0, 0), (2.1, 0.04, 2.6), '0.12 0.22 0.24 1', collide=False)


def tree(w, idx, x, y):
    l = static(w, f'tree_{idx:03}', (x, y, 0, 0, 0, 0))
    part(l, 'trunk', (0, 0, 1.6, 0, 0, 0), (0.20, 3.2), '0.30 0.19 0.10 1', 'cylinder')
    part(l, 'canopy', (0, 0, 4.2, 0, 0, 0), (1.65,), '0.15 0.39 0.12 1', 'sphere', False)
    part(l, 'crown', (0.4, 0, 5.2, 0, 0, 0), (1.20,), '0.21 0.46 0.15 1', 'sphere', False)


def gui(w):
    # Keep the normal editing tools, plus in-app driving and camera panels.
    # The generated world embeds this configuration and needs no external file.
    w.append(ET.parse(ROOT / 'gui_layout.xml').getroot())


def make_world():
    root = ET.Element('sdf', version='1.8')
    w = el(root, 'world', name=C['world_name'])
    p = el(w, 'physics', name='physics', type='ignored')
    el(p, 'max_step_size', 0.001)
    el(p, 'real_time_factor', 1)
    el(w, 'gravity', '0 0 -9.81')
    for short, cls in [('physics', 'Physics'), ('user-commands', 'UserCommands'), ('scene-broadcaster', 'SceneBroadcaster')]:
        plugin(w, f'gz-sim-{short}-system', f'gz::sim::systems::{cls}')
    plugin(w, 'gz-sim-sensors-system', 'gz::sim::systems::Sensors', [('render_engine', 'ogre2')])
    s = el(w, 'scene')
    el(s, 'ambient', '0.48 0.48 0.48 1')
    el(s, 'background', '0.68 0.81 0.91 1')
    el(s, 'shadows', str(C['shadows']).lower())
    sun = el(w, 'light', name='sun', type='directional')
    pose(sun, (0, 0, 60, 0, 0, 0))
    el(sun, 'cast_shadows', str(C['shadows']).lower())
    el(sun, 'diffuse', '0.85 0.83 0.77 1')
    el(sun, 'specular', '0.15 0.15 0.15 1')
    el(sun, 'direction', nums(C['sun_direction']))
    gui(w)
    l = static(w, 'ground')
    part(l, 'ground', (0, 0, -0.1, 0, 0, 0), (106, 154, 0.2), '0.35 0.46 0.27 1')
    # Ground collision is continuous. Road markings/surface are only millimeters high.
    roads = static(w, 'roads_and_markings')
    xs, ys, width = C['road_x'], C['road_y'], C['road_width']
    half = width / 2
    segments = []
    for x in xs:
        for a, b in zip(ys, ys[1:]):
            segments.append((x, (a+b)/2, width, b-a-width, True))
    for y in ys:
        for a, b in zip(xs, xs[1:]):
            segments.append(((a+b)/2, y, b-a-width, width, False))
    segments.append((0, (-72 + ys[0]-half)/2, width, ys[0]-half+72, True))
    for i, (x, y, sx, sy, vertical) in enumerate(segments):
        part(roads, f'asphalt_{i}', (x, y, 0.001, 0, 0, 0), (sx, sy, 0.002), ASPHALT, collide=False, shadows=False)
        length = sy if vertical else sx
        for sign in (-1, 1):
            px = x + sign*(half-0.18) if vertical else x
            py = y if vertical else y + sign*(half-0.18)
            size = (0.12, length, 0.002) if vertical else (length, 0.12, 0.002)
            part(roads, f'edge_{i}_{sign}', (px, py, 0.005, 0, 0, 0), size, WHITE, collide=False, shadows=False)
        for n in range(int(length/6)):
            offset = -length/2 + 3 + n*6
            px, py = (x, y+offset) if vertical else (x+offset, y)
            size = (0.12, 3, 0.002) if vertical else (3, 0.12, 0.002)
            part(roads, f'dash_{i}_{n}', (px, py, 0.005, 0, 0, 0), size, WHITE, collide=False, shadows=False)
    for i, x in enumerate(xs):
        for j, y in enumerate(ys):
            part(roads, f'junction_{i}_{j}', (x, y, 0.001, 0, 0, 0), (width, width, 0.002), ASPHALT, collide=False, shadows=False)
    # Raised sidewalks around the four interior blocks; grass remains inside.
    paths = static(w, 'sidewalks')
    for i, (xa, xb) in enumerate(zip(xs, xs[1:])):
        for j, (ya, yb) in enumerate(zip(ys, ys[1:])):
            x0, x1, y0, y1 = xa+half, xb-half, ya+half, yb-half
            for side, x in [('w', x0+0.8), ('e', x1-0.8)]:
                part(paths, f'walk_{i}_{j}_{side}', (x, (y0+y1)/2, 0.075, 0, 0, 0), (1.6, y1-y0, 0.15), '0.68 0.67 0.61 1')
            for side, y in [('s', y0+0.8), ('n', y1-0.8)]:
                part(paths, f'walk_{i}_{j}_{side}', ((x0+x1)/2, y, 0.075, 0, 0, 0), (x1-x0-3.2, 1.6, 0.15), '0.68 0.67 0.61 1')
    for spec in BUILDINGS:
        building(w, spec)
    sports = static(w, 'sports_field')
    part(sports, 'turf', (-16, -32, 0.012, 0, 0, 0), (16, 20, 0.02), '0.17 0.43 0.26 1', collide=False)
    for sign in (-1, 1):
        part(sports, f'sideline_{sign}', (-16+sign*7, -32, 0.025, 0, 0, 0), (0.10, 18, 0.002), WHITE, collide=False)
        part(sports, f'endline_{sign}', (-16, -32+sign*9, 0.025, 0, 0, 0), (14, 0.10, 0.002), WHITE, collide=False)
    part(sports, 'halfway', (-16, -32, 0.025, 0, 0, 0), (14, 0.1, 0.002), WHITE, collide=False)
    trees = [(x, y) for x in (-39, 39) for y in range(-54, 59, 9)]
    trees += [(x, 56) for x in range(-27, 30, 9)]
    trees += [(x, y) for x in (-6.5, 6.5) for y in (-61, -36, -24, -10, 12, 24, 38)]
    trees += [(-26, y) for y in (-37, -25, 12, 27, 38)]
    for i, (x, y) in enumerate(trees):
        tree(w, i, x, y)
    gate = static(w, 'main_gate')
    for sign in (-1, 1):
        part(gate, f'pillar_{sign}', (sign*5, -57, 2.6, 0, 0, 0), (0.65, 0.8, 5.2), '0.80 0.75 0.62 1')
    part(gate, 'header', (0, -57, 5.4, 0, 0, 0), (10.7, 0.9, 0.8), '0.12 0.35 0.56 1')
    # Lamps and benches: simple primitives with collisions and cast shadows.
    for idx, (x, y) in enumerate([(x,y) for x in (-37,37) for y in (-40,-16,16,40)]):
        l = static(w, f'lamp_{idx}', (x,y,0,0,0,0))
        part(l, 'pole', (0,0,3.3,0,0,0), (0.08,6.6), '0.25 0.27 0.29 1', 'cylinder')
        part(l, 'fixture', (0,0,6.6,0,0,0), (0.7,0.4,0.15), '0.8 0.8 0.7 1')
    for idx, (x,y) in enumerate([(-25,-19),(25,-24),(-25,5),(25,7)]):
        l = static(w, f'bench_{idx}', (x,y,0,0,0,0))
        part(l, 'seat', (0,0,0.5,0,0,0), (1.8,0.5,0.13), '0.48 0.29 0.12 1')
        part(l, 'back', (0,0.22,0.85,0,0,0), (1.8,0.12,0.6), '0.48 0.29 0.12 1')
        for sign in (-1,1):
            part(l, f'leg_{sign}', (sign*0.65,0,0.25,0,0,0), (0.10,0.4,0.5), '0.2 0.2 0.2 1')
    car(w, C['spawn'])
    return root


def save(root, path):
    ET.indent(root, space='  ')
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text('<?xml version="1.0" ?>\n' + ET.tostring(root, encoding='unicode') + '\n')


if __name__ == '__main__':
    assert C['road_width'] > 4.4, 'Road must comfortably fit two 1.8 m cars.'
    root = make_world()
    save(root, ROOT / 'worlds' / 'ute_city.sdf')
    model = ET.Element('sdf', version='1.8')
    car(model, (0,0,0.04,0,0,0))
    save(model, ROOT / 'models' / 'ute_car' / 'model.sdf')
    print('Generated worlds/ute_city.sdf and models/ute_car/model.sdf')
