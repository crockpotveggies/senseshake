"""Quarter-turn catalog registration at the existing SMT body centre.

Land-pattern lengths differ across libraries. Check numbered-pad overlap rather
than shifting the component to force unlike pad centroids to coincide. Bottom
SMT uses a local X reflection followed by CCW rotation in the top-view board
frame. Absolute CPL coordinates are never mirrored.
"""
from collections import Counter
import math


def quarter_size(width, height, angle):
    if not all(math.isfinite(v) for v in (width,height,angle)) or min(width,height)<=0:
        raise ValueError('Invalid SMT geometry: dimensions must be finite and positive')
    q=round(angle/90)
    if abs(angle-q*90)>.001:
        raise ValueError('Non-orthogonal pad requires explicit review')
    return (height,width) if q%2 else (width,height)


def catalog_rectangles(entry):
    ox,oy=entry['origin_easyeda']; aliases=entry.get('pad_aliases',{})
    result=[]
    for shape in entry['pad_shapes']:
        a=shape.split('~')
        if a[0]!='PAD' or not a[8]: raise ValueError('Expected numbered catalog pad')
        if a[1] not in ('RECT','OVAL','ELLIPSE','POLYGON'):
            raise ValueError('Unsupported catalog pad shape')
        number=str(int(a[8])) if a[8].isdecimal() else a[8]
        x,y=(float(a[2])-ox)*.254,-(float(a[3])-oy)*.254
        if a[1]=='POLYGON':
            points=[float(v) for v in a[10].split()]
            xs,ys=points[::2],points[1::2]
            width,height=(max(xs)-min(xs))*.254,(max(ys)-min(ys))*.254
        else:
            width,height=quarter_size(float(a[4])*.254,float(a[5])*.254,float(a[11]))
        result.append((aliases.get(number,number),x,y,width,height))
    return result


def register_smd(entry,item):
    source=catalog_rectangles(entry)
    target=[]
    for pad in item['pads']:
        width,height=quarter_size(*pad['size_mm'],pad['rotation_deg'])
        target.append((pad['number'],pad['xy_mm'][0],-pad['xy_mm'][1],width,height))
    if (not source or not all(math.isfinite(v) for p in source+target for v in p[1:])
            or any(min(p[3:])<=0 for p in source+target)
            or not all(math.isfinite(v) for v in item['footprint_origin_mm'])
            or not math.isfinite(item['rotation_deg'])):
        raise ValueError('Invalid SMT geometry: nonfinite coordinate or invalid pad envelope')
    if Counter(p[0] for p in source)!=Counter(p[0] for p in target):
        raise ValueError('Supplier/native pad identities or counts differ')
    nonpolar=entry.get('nonpolar_two_terminal',False)
    if nonpolar and (len(source)!=2 or {p[0] for p in source}!={'1','2'}):
        raise ValueError('Nonpolar exception requires exactly two terminals')
    x0,y0=item['footprint_origin_mm']; y0=-y0
    side=item['side']; fits=[]
    if side not in ('Top','Bottom'):raise ValueError('Invalid SMT side')
    for angle in (0,90,180,270):
        c,s=round(math.cos(math.radians(angle))),round(math.sin(math.radians(angle)))
        remaining=list(target); scores=[];errors=[]
        for number,x,y,width,height in source:
            if side=='Bottom':x=-x
            x,y=x0+c*x-s*y,y0+s*x+c*y
            width,height=quarter_size(width,height,angle)
            candidates=[]
            for i,(n,tx,ty,tw,th) in enumerate(remaining):
                if not nonpolar and n!=number:continue
                overlap_x=max(0,min(x+width/2,tx+tw/2)-max(x-width/2,tx-tw/2))
                overlap_y=max(0,min(y+height/2,ty+th/2)-max(y-height/2,ty-th/2))
                score=min(overlap_x/min(width,tw),overlap_y/min(height,th))
                candidates.append((score,-math.hypot(x-tx,y-ty),i))
            if not candidates:raise ValueError('Unmatched SMT pin')
            score,error,index=max(candidates);remaining.pop(index)
            scores.append(score);errors.append(-error)
        # This is a registration check, not solder-joint qualification. The
        # 60% per-axis overlap threshold rejects perpendicular/misnumbered pads.
        if min(scores)>=.60:
            fits.append(dict(x_mm=x0,y_up_mm=y0,rotation_deg=angle,
                             min_pad_overlap_fraction=min(scores),max_pad_error_mm=max(errors),
                             pads_checked=len(source)))
    if not fits:raise ValueError(f'No SMT orientation with sufficient pad overlap: {item["reference"]}')
    if not nonpolar and len(fits)!=1:
        raise ValueError('Ambiguous polarized SMT orientation')
    if nonpolar:
        if len(fits)!=2 or (fits[1]['rotation_deg']-fits[0]['rotation_deg'])%360!=180:
            raise ValueError('Nonpolar SMT must have exactly two opposite orientations')
        native=item['rotation_deg']%360
        fits.sort(key=lambda f:abs((f['rotation_deg']-native+180)%360-180))
    return fits[0]
