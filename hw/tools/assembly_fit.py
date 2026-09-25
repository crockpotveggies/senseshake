"""Dimensioned bench assembly envelopes, not physical interference qualification.

Dimensions and routing assumptions are documented in docs/stack-assembly.md.
Coordinates: board top-left XY, top surface Z=0, millimetres.
"""
import math


PI_GAP = 27.179
PI_TOP = -1.6 - PI_GAP
MODULE = (30, 8, 80, 48)
PI_SUPPORTS = ((3.5, 3.5), (61.5, 3.5), (3.5, 52.5))
FFC_WIDTHS = {'J86': 20.5, 'J87': 20.5, 'J88': 30.5, 'J89': 30.5}


def cable_path(ref, x, y):
    """Selected custom flex routing, including a straight stiffener exit.

    Upper pair U-turns below the HAT; lower pair uses a smooth S-drop below
    through-hole tails. All four exit south. Bends are outside the stiffeners.
    These curves prescribe a guide/installation envelope, not a cable STEP.
    """
    z = -2.6
    if ref in ('J86', 'J88'):
        mouth = y - 2.6
        bend = mouth - 6
        path = [(mouth, z), (bend, z)]
        radius = 3.5
        path += [(bend-radius*math.sin(t), z-radius+radius*math.cos(t))
                 for t in [math.pi*i/24 for i in range(1,25)]]
    else:
        mouth = y + 2.6
        bend = mouth + 3
        radius = 3
        angle = math.acos(1-4.1/(2*radius))
        path = [(mouth,z),(bend,z)]
        path += [(bend+radius*math.sin(t),z-radius+radius*math.cos(t))
                 for t in [angle*i/12 for i in range(1,13)]]
        by,bz=path[-1]
        path += [(by+radius*(math.sin(angle)-math.sin(angle-t)),
                  bz-radius*(math.cos(angle-t)-math.cos(angle)))
                 for t in [angle*i/12 for i in range(1,13)]]
    path.append((75,path[-1][1]))
    return [(x, yy, zz) for yy,zz in path]


def review(placements):
    expected={'J86':(17,22,0),'J87':(17,39,180),
              'J88':(57,20,0),'J89':(57,37,180)}
    for ref,(x,y,angle) in expected.items():
        actual=placements[ref]
        assert all(abs(a-b)<.001 for a,b in zip(actual[:3],(x,y,angle))), (ref,actual)
        assert actual[3] == 'back', ref
    # Half a millimetre envelope inflation includes placement/cable guide error.
    support_clearances=[]
    paths={}
    for ref,(x,y,_) in expected.items():
        path=cable_path(ref,x,y);paths[ref]=path
        xmin,xmax=x-FFC_WIDTHS[ref]/2-.5,x+FFC_WIDTHS[ref]/2+.5
        ymin,ymax=min(q[1] for q in path)-.5,max(q[1] for q in path)+.5
        for sx,sy in PI_SUPPORTS:
            distance=math.hypot(max(xmin-sx,sx-xmax,0),max(ymin-sy,sy-ymax,0))-2.4
            assert distance > 0, (ref,'support collision',sx,sy)
            support_clearances.append(distance)
    cable_low=min(z for path in paths.values() for _,_,z in path)-.15
    pi_port_top=PI_TOP+16
    port_margin=cable_low-pi_port_top-1
    heatsink_margin=cable_low-(PI_TOP+2.8+10+.5)-1
    # JTAG housing 2.50 wide, inflate half a millimetre toward the module.
    jtag_margin=82.5-2.5/2-.5-MODULE[2]
    # The keyed three-contact row constrains X to its published 12.22 width,
    # centred on the middle contact; no exact Z mating transform is assumed.
    plug_xmax=14.19+12.22/2+.5
    plug_margin=MODULE[0]-plug_xmax
    # South-going ribbons have completed their S-drop at J90's pin row.
    south=paths['J87']
    at_header=next(z for _,y,z in south if y>=50.9)
    tail_margin=(-1.6-2.0)-(at_header+.15)-.5
    assert min(port_margin,heatsink_margin,jtag_margin,plug_margin,tail_margin)>0
    return dict(status='Pi, heatsink, JTAG and plug envelope checks pass; flex routing conditional',
        pi='Raspberry Pi 4 Model B', pi_supports_xy_mm=PI_SUPPORTS,
        omitted_support_xy_mm=[61.5,52.5],
        pi_to_hat_underside_mm=PI_GAP, module_surface_gap_mm=8,
        minimum_support_margin_mm=min(support_clearances),
        minimum_pi_port_margin_mm=port_margin, heatsink_margin_mm=heatsink_margin,
        jtag_module_margin_mm=jtag_margin, geophone_plug_module_margin_mm=plug_margin,
        geophone_tail_to_flex_margin_mm=tail_margin,
        installation_allowance_mm=1, flex_guide_allowance_mm=.5,
        flex_paths_mm=paths,
        findings=[dict(code='flex_local_clearance',connector='J87',parts=['C95','C96'],
                       disposition='Straight cable exit crosses underside bypass capacitors; do not accept this conceptual path as interference-free. Use a measured downward exit/guide before fitting this optional expansion cable.'),
                  dict(code='flex_tip_and_bend',disposition='Exact mating height, stiffener length and bend capability require the selected cable drawing/sample; no fully qualified harness part number assigned.')],
        limits=['Custom flex: vendor-compatible tips, 0.30 mm end thickness; see assembly drawing',
                'Envelope calculations do not qualify cable fatigue, contact engagement or stack stiffness',
                'Trim through-hole tails to at most 2.0 mm below HAT; inspect before seating',
                'Three Pi supports required with all four flexes; fourth south-right post conflicts',
                'Fan, enclosure and FPGA heatsink not included; thermal qualification pending'])
