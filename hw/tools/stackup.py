"""Explicit provisional DAQHAT-01 HDI stack; manufacturer approval is still required."""
from pathlib import Path

def block_span(text, token):
    start=text.index(token);depth=0;quoted=False;escaped=False
    for end in range(start,len(text)):
        char=text[end]
        if escaped:escaped=False;continue
        if char=='\\' and quoted:escaped=True;continue
        if char=='"':quoted=not quoted;continue
        if quoted:continue
        if char=='(':depth+=1
        elif char==')':
            depth-=1
            if not depth:return start,end+1
    raise ValueError('Unbalanced KiCad block')

def apply_stackup(path,spec):
    if 'hdi' not in spec:return
    profile=spec['hdi'];copper=profile['copper_thickness_mm'];dielectric=profile['dielectric_thickness_mm'];mask=profile['mask_thickness_mm']
    assert len(copper)==8 and len(dielectric)==7
    assert abs(sum(copper)+sum(dielectric)+2*mask-profile['nominal_thickness_mm'])<1e-6
    names=['F.Cu',*[f'In{i}.Cu' for i in range(1,7)],'B.Cu']
    parts=['(stackup','(layer "F.SilkS" (type "Top Silk Screen"))','(layer "F.Paste" (type "Top Solder Paste"))',f'(layer "F.Mask" (type "Top Solder Mask") (color "Green") (thickness {mask}) (epsilon_r 3.5) (loss_tangent 0.01))']
    for i,(name,thickness) in enumerate(zip(names,copper)):
        parts.append(f'(layer "{name}" (type "copper") (thickness {thickness}))')
        if i<7:
            kind='prepreg' if i in (0,6) else 'core'
            parts.append(f'(layer "dielectric {i+1}" (type "{kind}") (thickness {dielectric[i]}) (material "FR4 - provisional") (epsilon_r 4.3) (loss_tangent 0.02))')
    parts.extend([f'(layer "B.Mask" (type "Bottom Solder Mask") (color "Green") (thickness {mask}) (epsilon_r 3.5) (loss_tangent 0.01))','(layer "B.Paste" (type "Bottom Solder Paste"))','(layer "B.SilkS" (type "Bottom Silk Screen"))','(copper_finish "ENIG")','(dielectric_constraints no)',')'])
    path=Path(path);text=path.read_text();a,z=block_span(text,'(stackup');path.write_text(text[:a]+'\n'.join(parts)+text[z:],encoding='utf-8')
