"""T1 ribbon installation geometry in board-top XY/Z millimetres.

Cable paths are installation limits, not supplier-certified cable solids.
The separate spacer and guide CAD implement the mounting/exit constraints.
"""
import math

PI_GAP = 27.179
PI_TOP = -1.6 - PI_GAP
MODULE = (30, 8, 80, 48)
PI_SUPPORTS = ((3.5, 3.5), (61.5, 3.5), (3.5, 52.5), (61.5, 52.5))
FFC_WIDTHS = {'J86': 20.5, 'J87': 20.5, 'J88': 30.5, 'J89': 30.5}
EXPECTED = {'J86': (17,22,0), 'J87': (17,36,180),
            'J88': (57,20,0), 'J89': (57,37,180)}
# Bound the slot by the ENTIRE 2 mm connector height: no guessed mating Z.
CABLE_THICKNESS = .33
SLOT_Z = (-3.435, -1.765)
CABLE_ALLOWANCE = .5
# Custom FPC: reinforced tip projects <=0.5 mm outside the housing.
# A full 1 mm straight exit precedes the 1.5 mm static bend (body <=0.15 mm).
STRAIGHT = 1
NORTH_Z, SOUTH_Z = -10.2, -7.2
# Rectangular solid envelopes (xmin,ymin,zmin,xmax,ymax,zmax).
# Bosses deliberately use bounding boxes, conservative for the round part.
SPACER_BOXES = {
    'top_boss': (58.5,49.5,-6.1,64.5,55.5,-1.6),
    'upper_arm': (31,50.5,-6.1,61.5,55.5,-4.1),
    'offset_web': (31,50,-12,39,56,-6.1),
    'lower_arm': (31,50,-14,61.5,55,-12),
    'bottom_boss': (58.5,49.5,PI_TOP,64.5,55.5,-12),
}
GUIDE_BOX = (5.25,56,-11.4,73.75,58,-5.9)
GUIDE_SLOTS = [(x-w/2,55,z-.45,x+w/2,59,z+.45)
               for x,w in ((17,21.5),(57,31.5)) for z in (SOUTH_Z,NORTH_Z)]


def cable_path(ref,x,y,slot_z=-2.6):
    """Smooth centreline with 1.6 mm centreline radius (>=1.5 mm inner radius), outside the reinforced tips."""
    z=slot_z
    radius=1.6
    if ref in ('J86','J88'):
        mouth=y-2.6; bend=mouth-STRAIGHT
        path=[(mouth,z),(bend,z)]
        path += [(bend-radius*math.sin(t),z-radius+radius*math.cos(t))
                 for t in [math.pi/2*i/60 for i in range(1,61)]]
        path.append((bend-radius,NORTH_Z+radius))
        path += [(bend-radius*math.cos(t),NORTH_Z+radius-radius*math.sin(t))
                 for t in [math.pi/2*i/60 for i in range(1,61)]]
    else:
        mouth=y+2.6; bend=mouth+STRAIGHT
        path=[(mouth,z),(bend,z)]
        path += [(bend+radius*math.sin(t),z-radius+radius*math.cos(t))
                 for t in [math.pi/2*i/60 for i in range(1,61)]]
        path.append((bend+radius,SOUTH_Z+radius))
        path += [(bend+2*radius-radius*math.cos(t),SOUTH_Z+radius-radius*math.sin(t))
                 for t in [math.pi/2*i/60 for i in range(1,61)]]
    path.append((75,path[-1][1]))
    return [(x,yy,zz) for yy,zz in path]


def path_boxes(path,width,allowance=CABLE_ALLOWANCE):
    """Conservative segment AABBs contain the cable plus install tolerance.

    Segment AABBs include the full thickness on each axis, so curved segments
    cannot slip between sampled collision tests. Sagitta at 1.5 degrees <.001.
    """
    r=CABLE_THICKNESS/2+allowance+.001
    for a,b in zip(path,path[1:]):
        yield (a[0]-width/2-allowance,min(a[1],b[1])-r,min(a[2],b[2])-r,
               a[0]+width/2+allowance,max(a[1],b[1])+r,max(a[2],b[2])+r)


def box_gap(a,b):
    """Signed separating-axis margin; <=0 means overlap/touch, not clearance."""
    return max(a[0]-b[3],b[0]-a[3],a[1]-b[4],b[1]-a[4],a[2]-b[5],b[2]-a[5])


def clearance(path,width,obstacle):
    return min(box_gap(box,obstacle) for box in path_boxes(path,width))


def default_obstacles(placements):
    # Conservative body+courtyard bounds; actual board geometry supplied by
    # prefab_review replaces these in the board audit, including all PTH tails.
    return {'C95':(13.7,43.55,-2.5,16.7,45.45,-1.6),
            'C96':(17.75,43,-2.5,19.65,46,-1.6),
            'D90':(14.4,45.8,-2.7,17.8,49.4,-1.6),
            'Pi_GPIO_socket':(6.8,1.025,PI_TOP+2.54,58.2,5.975,-1.6)}


def review(placements,obstacles=None,spacer_boxes=None):
    for ref,(x,y,angle) in EXPECTED.items():
        actual=placements[ref]
        assert all(abs(a-b)<.001 for a,b in zip(actual[:3],(x,y,angle))),(ref,actual)
        assert actual[3]=='back',ref
    obstacles=dict(default_obstacles(placements) if obstacles is None else obstacles)
    for i,(sx,sy) in enumerate(PI_SUPPORTS[:3]):
        obstacles[f'Pi_post_{i+1}']=(sx-2.4,sy-2.4,PI_TOP,sx+2.4,sy+2.4,-1.6)
    for key,box in (SPACER_BOXES if spacer_boxes is None else spacer_boxes).items():
        obstacles['spacer_'+key]=box
    minima={};paths={};samples=0
    # Nine possible slot heights span the entire connector. Add both endpoints
    # explicitly. All are checked with inflated envelopes, not nominal lines.
    for ref,(x,y,_) in EXPECTED.items():
        paths[ref]=cable_path(ref,x,y)
        for i in range(9):
            z=SLOT_Z[0]+(SLOT_Z[1]-SLOT_Z[0])*i/8
            path=cable_path(ref,x,y,z);samples+=1
            for key,box in obstacles.items():
                if key==ref:continue  # Intended contact with its own socket.
                margin=clearance(path,FFC_WIDTHS[ref],box)
                minima[key]=min(minima.get(key,math.inf),margin)
                assert margin>0,(ref,key,round(margin,4),z)
    # Cross-cable envelopes: same-lane, every upper/lower slot-height corner.
    pair_margin=math.inf
    for north,south in [('J86','J87'),('J88','J89')]:
        for nz in SLOT_Z:
            for sz in SLOT_Z:
                a=list(path_boxes(cable_path(north,*EXPECTED[north][:2],nz),FFC_WIDTHS[north]))
                b=list(path_boxes(cable_path(south,*EXPECTED[south][:2],sz),FFC_WIDTHS[south]))
                pair_margin=min(pair_margin,min(box_gap(aa,bb) for aa in a for bb in b))
    assert pair_margin>0,('ribbon-to-ribbon',pair_margin)
    # Lower guide edge is the lowest object above Pi ports, not the ribbons.
    pi_port_top=PI_TOP+16
    port_margin=NORTH_Z-CABLE_THICKNESS/2-pi_port_top-1
    guide_port_margin=GUIDE_BOX[2]-pi_port_top-1
    heatsink_margin=NORTH_Z-CABLE_THICKNESS/2-(PI_TOP+13.3)-1
    jtag_margin=82.5-2.5/2-.5-MODULE[2]
    plug_margin=MODULE[0]-(14.19+12.22/2+.5)
    assert min(port_margin,guide_port_margin,heatsink_margin,jtag_margin,plug_margin)>0
    pi_obstacles=[(65.5,2.5,PI_TOP,86.5,18.5,PI_TOP+16),
                  (65.5,21.5,PI_TOP,86.5,36.5,PI_TOP+16),
                  (65.5,39.5,PI_TOP,86.5,54.5,PI_TOP+16),
                  (22,19,PI_TOP,40,37,PI_TOP+13.3),
                  (6.5,51,PI_TOP,15.5,57,PI_TOP+3.2),
                  (22.5,51,PI_TOP,29.5,57,PI_TOP+3),
                  (35.5,51,PI_TOP,42.5,57,PI_TOP+3)]
    fixture_pi_margins={}
    for key,box in {**SPACER_BOXES,'guide':GUIDE_BOX}.items():
        fixture_pi_margins[key]=min(box_gap(box,other) for other in pi_obstacles)-.5
        assert fixture_pi_margins[key]>0,(key,'Pi interference',fixture_pi_margins[key])
    # A closed slot constrains the terminal straight sections within the wider
    # tolerance used above. Keep connector tips/stiffeners outside all bends.
    for ref,path in paths.items():
        assert next(y for _,y,z in reversed(path[:-1]) if abs(z-path[-1][2])<1e-8)<54
    return dict(status='Selected ribbon/spacer CAD envelopes pass; first-article fit remains unmeasured',
        pi='Raspberry Pi 4 Model B',pi_supports_xy_mm=PI_SUPPORTS,
        omitted_support_xy_mm=None,pi_to_hat_underside_mm=PI_GAP,module_surface_gap_mm=8,
        slot_height_cases=samples,slot_z_bounds_mm=SLOT_Z,
        fixture_to_pi_margin_mm=fixture_pi_margins,minimum_inner_bend_radius_mm=1.5,
        clearance_by_obstacle_mm=minima,minimum_obstacle_margin_mm=min(minima.values()),
        ribbon_to_ribbon_margin_mm=pair_margin,minimum_pi_port_margin_mm=port_margin,
        guide_to_pi_port_margin_mm=guide_port_margin,heatsink_margin_mm=heatsink_margin,
        jtag_module_margin_mm=jtag_margin,geophone_plug_module_margin_mm=plug_margin,
        installation_allowance_mm=1,flex_guide_allowance_mm=CABLE_ALLOWANCE,
        flex_paths_mm=paths,findings=[],
        limits=['150 mm custom FFC; 0.50 mm pitch, 0.30 +/-0.03 mm mating thickness',
                'Custom <=0.15 mm FPC body; reinforced tip <=0.5 mm exposed; 1 mm straight exit; supplier to approve 1.5 mm static bends',
                'Use offset spacer and dual-level guide CAD; no straight fourth post or through-bolt',
                'Trim PTH tails to <=2 mm below HAT; inspect and radius/deburr all guide edges',
                'Harness far-end pinout, contact engagement, strain, stiffness and physical fit remain first-article checks',
                'Fan, enclosure and FPGA heatsink not included; thermal qualification pending'])
