

from collections import namedtuple
from pprint import pprint as pp
import numpy as np
import sys

Pt = namedtuple('Pt', 'x, y')               # Point
Edge = namedtuple('Edge', 'a, b')           # Polygon edge from a to b
Poly = namedtuple('Poly', 'name, edges')    # Polygon

_eps = 0.00001
_huge = sys.float_info.max
_tiny = sys.float_info.min

def rayintersectseg(p, edge):
    ''' takes a point p=Pt() and an edge of two endpoints a,b=Pt() of a line segment returns boolean
    '''
    a,b = edge
    if a.y > b.y:
        a,b = b,a
    if p.y == a.y or p.y == b.y:
        p = Pt(p.x, p.y + _eps)
    
    intersect = False
    
    if (p.y > b.y or p.y < a.y) or (
        p.x > max(a.x, b.x)):
        return False
    
    if p.x < min(a.x, b.x):
        intersect = True
    else:
        if abs(a.x - b.x) > _tiny:
            m_red = (b.y - a.y) / float(b.x - a.x)
        else:
            m_red = _huge
        if abs(a.x - p.x) > _tiny:
            m_blue = (p.y - a.y) / float(p.x - a.x)
        else:
            m_blue = _huge
        intersect = m_blue >= m_red
    return intersect

def _odd(x): return x%2 == 1

def ispointinside(p, poly):
    ln = len(poly)
    return _odd(sum(rayintersectseg(p, edge) for edge in poly.edges ))

def surroundingSquare (poly):
    min_x = poly.edges[0].a.x
    min_y = poly.edges[0].a.y
    max_x = poly.edges[0].a.x
    max_y = poly.edges[0].a.y
    for e in poly.edges:
        if (e.a.x < min_x) or (e.b.x < min_x):
            min_x = min(e.a.x, e.b.x)
        if (e.a.y < min_y) or (e.b.y < min_y):
            min_y = min(e.a.y, e.b.y)
        if (e.a.x > max_x) or (e.b.x > max_x):
            max_x = max(e.a.x, e.b.x)
        if (e.a.y > max_y) or (e.b.y > max_y):
            max_y = max(e.a.y, e.b.y)
    return Poly(name='square', edges=(
           Edge(a=Pt(x=min_x, y=min_y), b=Pt(x=max_x, y=min_y)),
           Edge(a=Pt(x=max_x, y=min_y), b=Pt(x=max_x, y=max_y)),
           Edge(a=Pt(x=max_x, y=max_y), b=Pt(x=min_x, y=max_y)),
           Edge(a=Pt(x=min_x, y=max_y), b=Pt(x=min_x, y=min_y))))

def squareScan (poly, step = 0):
    square = surroundingSquare(poly)
    square_x_min = square.edges[0].a.x
    square_y_min = square.edges[0].a.y
    square_x_max = square.edges[1].b.x
    square_y_max = square.edges[1].b.y
    if step == 0:
        step = min((square_x_max - square_x_min), (square_y_max - square_y_min)) / 150.0
    lines = []
    for y in np.arange(square_y_min - 2*step, square_y_max + 2*step, step):
        waitToLeavePoly = False
        for x in np.arange(square_x_min -2*step, square_x_max + 2*step, step):
            pt = Pt(x=x, y=y)
            if ispointinside(pt, poly) and not(waitToLeavePoly):
                line_x_min = x
                waitToLeavePoly = True
            elif not(ispointinside(pt, poly)) and waitToLeavePoly:
                line_x_max = x
                waitToLeavePoly = False
                line = Edge(a=Pt(x=line_x_min, y=y), b=Pt(x=line_x_max, y=y))
                lines.append(line)
    poly_lines = Poly(name='line', edges=(
                      tuple(lines)))
    return poly_lines

def polypp(poly):
    print ("\n  Polygon(name='%s', edges=(" % poly.name)
    print ('   ', ',\n    '.join(str(e) for e in poly.edges) + '\n    ))')

def getNumberOfPolygons(dxf_source):
    fi = open(dxf_source ,'r')
    nb_polygon = 0
    for line in fi:
        if line == "AcDbPolyline\n":
            nb_polygon += 1
    fi.close()
    return nb_polygon

def extractPolygons(dxf_source):
    file_names = []
    nb_poly = getNumberOfPolygons(dxf_source)
    for i in range(nb_poly):
        file_names.append('.points_poly_' +str(i) +'.txt')
        fo = open(file_names[i], 'w')
        fi = open(dxf_source, 'r')
        start_write = False
        stop_write = False
        idx_poly = 0
        for line in fi:
            if line == "AcDbPolyline\n":
                if idx_poly == i:
                    start_write = True
                idx_poly += 1
            if start_write and line =="  0\n":
                stop_write = True
            if start_write and not(stop_write):
                fo.write(line)
        fo.close()
        fi.close()

    polygons = []
    for i in range(nb_poly):
        fi = open(file_names[i], 'r')
        fi_lines = []
        for fi_line in fi:
            fi_lines.append(fi_line)
        points = []
        xy_parsed = False
        for j in range(len(fi_lines)):
            if fi_lines[j]== " 10\n":
                x = fi_lines[j+1].split("\n")
                x = float(x[0])
            if fi_lines[j] == " 20\n":
                y = fi_lines[j+1].split("\n")
                y = float(y[0])
                xy_parsed = True
            if xy_parsed:
                points.append(Pt(x=x, y=y))
                xy_parsed = False
        fi.close()
        edges = []
        for k in range(len(points)):
            edges.append(Edge(a=points[k], b=points[(k+1)%len(points)]))
        polygons.append(Poly(name="poly"+str(i), edges=tuple(edges))) 
    return polygons

def squareScanDxfFormat(poly_lines):
    dxfFormatStr = ""
    for edge in poly_lines.edges:
        dxfFormatStr += "LINE\n100\nAcDbLine\n"
        dxfFormatStr += " 10\n"
        dxfFormatStr += str(edge.a.x)+"\n"
        dxfFormatStr += " 20\n"
        dxfFormatStr += str(edge.a.y)+"\n"
        dxfFormatStr += " 30\n"
        dxfFormatStr += "0.0\n"
        dxfFormatStr += " 11\n"
        dxfFormatStr += str(edge.b.x)+"\n"
        dxfFormatStr += " 21\n"
        dxfFormatStr += str(edge.b.y)+"\n"
        dxfFormatStr += " 31\n"
        dxfFormatStr += "0.0\n"
        dxfFormatStr += "  0\n"
    return dxfFormatStr

def dxfAblationScan(dxf_source, step = 0):
    fi = open(dxf_source, 'r')
    fo = open("processed_" + dxf_source, 'w')
    polygons = extractPolygons(dxf_source)
    codeToInject = ""
    for i in range(len(polygons)):
        poly_lines = squareScan(polygons[i], step)
        codeToInject += squareScanDxfFormat(poly_lines)
    search_for_endsec = False
    for line in fi:
        if line == "ENTITIES\n":
            fo.write(line)
            search_for_endsec = True
        elif ("ENDSEC" in line) and search_for_endsec:
            fo.write(codeToInject)
            fo.write("ENDSEC\n")
            search_for_endsec = False
        else:
            fo.write(line)
    fi.close()       
    fo.close()       

if __name__ == '__main__':
    #polys = [
    #Poly(name='square', edges=(
    #Edge(a=Pt(x=0, y=0), b=Pt(x=10, y=0)),
    #Edge(a=Pt(x=10, y=0), b=Pt(x=10, y=10)),
    #Edge(a=Pt(x=10, y=10), b=Pt(x=0, y=10)),
    #Edge(a=Pt(x=0, y=10), b=Pt(x=0, y=0))
    #)),
    #Poly(name='square_hole', edges=(
    #Edge(a=Pt(x=0, y=0), b=Pt(x=10, y=0)),
    #Edge(a=Pt(x=10, y=0), b=Pt(x=10, y=10)),
    #Edge(a=Pt(x=10, y=10), b=Pt(x=0, y=10)),
    #Edge(a=Pt(x=0, y=10), b=Pt(x=0, y=0)),
    #Edge(a=Pt(x=2.5, y=2.5), b=Pt(x=7.5, y=2.5)),
    #Edge(a=Pt(x=7.5, y=2.5), b=Pt(x=7.5, y=7.5)),
    #Edge(a=Pt(x=7.5, y=7.5), b=Pt(x=2.5, y=7.5)),
    #Edge(a=Pt(x=2.5, y=7.5), b=Pt(x=2.5, y=2.5))
    #)),
    #Poly(name='strange', edges=(
    #Edge(a=Pt(x=0, y=0), b=Pt(x=2.5, y=2.5)),
    #Edge(a=Pt(x=2.5, y=2.5), b=Pt(x=0, y=10)),
    #Edge(a=Pt(x=0, y=10), b=Pt(x=2.5, y=7.5)),
    #Edge(a=Pt(x=2.5, y=7.5), b=Pt(x=7.5, y=7.5)),
    #Edge(a=Pt(x=7.5, y=7.5), b=Pt(x=10, y=10)),
    #Edge(a=Pt(x=10, y=10), b=Pt(x=10, y=0)),
    #Edge(a=Pt(x=10, y=0), b=Pt(x=2.5, y=2.5))
    #)),
    #Poly(name='exagon', edges=(
    #Edge(a=Pt(x=3, y=0), b=Pt(x=7, y=0)),
    #Edge(a=Pt(x=7, y=0), b=Pt(x=10, y=5)),
    #Edge(a=Pt(x=10, y=5), b=Pt(x=7, y=10)),
    #Edge(a=Pt(x=7, y=10), b=Pt(x=3, y=10)),
    #Edge(a=Pt(x=3, y=10), b=Pt(x=0, y=5)),
    #Edge(a=Pt(x=0, y=5), b=Pt(x=3, y=0))
    #)),
    #]
    #testpoints = (Pt(x=5, y=5), Pt(x=5, y=8),
    #Pt(x=-10, y=5), Pt(x=0, y=5),
    #Pt(x=10, y=5), Pt(x=8, y=5),
    #Pt(x=10, y=10))
    
    #print ("\n TESTING WHETHER POINTS ARE WITHIN POLYGONS")
    #for poly in polys:
    #    polypp(poly)
    #    print ('   ', '\t'.join("%s: %s" % (p, ispointinside(p, poly)) for p in testpoints[:3]))
    #    print ('   ', '\t'.join("%s: %s" % (p, ispointinside(p, poly)) for p in testpoints[3:6]))
    #    print ('   ', '\t'.join("%s: %s" % (p, ispointinside(p, poly)) for p in testpoints[6:]))

    #polypp(surroundingSquare(polys[0]))
    #polypp(squareScan(polys[0], 0.1))


    dxf_source = "sample.dxf"
    dxfAblationScan(dxf_source)   


