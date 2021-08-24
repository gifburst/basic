#
# PC-BASIC 3.23 - stat_graph.py
#
# Graphics statements
# 
# (c) 2013 Rob Hagemans 
#
# This file is released under the GNU GPL version 3. 
# please see text file COPYING for licence terms.
#

import error
import vartypes
import var
import util
import expressions
import fp
import graphics
import draw_and_play



def parse_coord(ins):
    util.require_read(ins, '(')
    x = fp.unpack(vartypes.pass_single_keep(expressions.parse_expression(ins)))
    util.require_read(ins, ',')
    y = fp.unpack(vartypes.pass_single_keep(expressions.parse_expression(ins)))
    util.require_read(ins, ')')
    return x,y    


def exec_pset(ins, default_colour=-1):
    graphics.require_graphics_mode()
    
    relative = util.skip_white_read_if(ins, '\xCF') # STEP
    x,y = parse_coord(ins)
    
    c = default_colour
    if util.skip_white_read_if(ins, ','):
        c = vartypes.pass_int_keep(expressions.parse_expression(ins))[1]
    util.require(ins, util.end_statement)    
    
    x,y, = graphics.window_coords(x,y)
    
    if relative:
        x += graphics.last_point[0]
        y += graphics.last_point[1]        
    
    graphics.put_point(x,y,c)

        
def exec_preset(ins):
    exec_pset(ins, -2)   
    

def exec_line_graph(ins):
    graphics.require_graphics_mode()
    
    if util.skip_white(ins)=='(':
        coord = parse_coord(ins)
        x0,y0=graphics.window_coords(*coord)
    else:
        x0,y0=graphics.last_point
        
    util.require_read(ins, '\xEA') # -
        
    x1,y1 = graphics.window_coords(*parse_coord(ins))
    
    c = -1    
    mode='L'
    mask=0xffff
    if util.skip_white_read_if(ins, ','):
        expr = expressions.parse_expression(ins, allow_empty=True)
        if expr != None and expr != ('',''):
            c = vartypes.pass_int_keep(expr)[1]
    
        if util.skip_white_read_if(ins, ','):
            if util.skip_white_read_if(ins, 'B'):
                mode='B'
                if util.skip_white_read_if(ins, 'F'):         
                    mode='BF'
            if util.skip_white_read_if(ins, ','):
                mask = vartypes.pass_int_keep(expressions.parse_expression(ins, allow_empty=True), maxint=0xffff)[1]
                    
    util.require(ins, util.end_statement)    
    
    if mode=='L':
        graphics.draw_line(x0,y0,x1,y1,c,mask)
    elif mode=='B':
        # TODO: we don't exactly match GW's way of applying the pattern, haven't found the logic of it
        graphics.draw_box(x0,y0,x1,y1,c,mask)
    elif mode=='BF':
        graphics.draw_box_filled(x0,y0,x1,y1,c)
            
            
def exec_view_graph(ins):
    graphics.require_graphics_mode()
    absolute = util.skip_white_read_if(ins, '\xC8') #SCREEN
    
    if util.skip_white(ins)=='(':
        x0,y0 = parse_coord(ins)
        util.require_read(ins, '\xEA') #-
        x1,y1 = parse_coord(ins)
        
        # not scaled by WINDOW
        x0 = fp.round_to_int(x0)
        x1 = fp.round_to_int(x1)
        y0 = fp.round_to_int(y0)
        y1 = fp.round_to_int(y1)        
        
        fill, border = None, None
        if util.skip_white_read_if(ins, ','):
            [fill, border] = expressions.parse_int_list(ins, 2, err=2)
        
        if fill != None:
            graphics.draw_box_filled(x0,y0,x1,y1, fill)
        if border!= None:
            graphics.draw_box(x0-1,y0-1,x1+1,y1+1, border)
        graphics.set_graph_view(x0,y0, x1,y1, absolute)
        
    else:
        graphics.unset_graph_view()
                
    util.require(ins, util.end_statement)        
    
    
def exec_window(ins):
    graphics.require_graphics_mode()
    cartesian = not util.skip_white_read_if(ins, '\xC8') #SCREEN
    
    if util.skip_white(ins)=='(':
        x0,y0 = parse_coord(ins)
        util.require_read(ins, '\xEA') #-
        x1,y1 = parse_coord(ins)
        graphics.set_graph_window(x0,y0, x1,y1, cartesian)
    else:
        graphics.unset_graph_window()
                
    util.require(ins, util.end_statement)        
    
        
def exec_circle(ins):
    graphics.require_graphics_mode()
    x0,y0 = graphics.window_coords(*parse_coord(ins))
    util.require_read(ins, ',')
    r = fp.unpack(vartypes.pass_single_keep(expressions.parse_expression(ins)))
    
    c = -1
    start, stop = ('',''), ('','')
    aspect = graphics.get_aspect_ratio()
    if util.skip_white_read_if(ins, ','):
        cval = expressions.parse_expression(ins, allow_empty=True)
        if cval != ('',''):
            c = vartypes.pass_int_keep(cval)[1]
        if util.skip_white_read_if(ins, ','):
            start = expressions.parse_expression(ins, allow_empty=True)
            if util.skip_white_read_if(ins, ','):
                stop = expressions.parse_expression(ins, allow_empty=True)
                if util.skip_white_read_if(ins, ','):
                    aspect = fp.unpack(vartypes.pass_single_keep(expressions.parse_expression(ins)))
    util.require(ins, util.end_statement)        

    if fp.equals(aspect, aspect.one):
        rx, dummy = graphics.window_scale(r,fp.MBF_class.zero)
        ry = rx
    else:
        if fp.gt(aspect, aspect.one):
            dummy, ry = graphics.window_scale(fp.MBF_class.zero,r)
            rx = fp.round_to_int(fp.div(r, aspect))
        else:
            rx, dummy = graphics.window_scale(r,fp.MBF_class.zero)
            ry = fp.round_to_int(fp.mul(r, aspect))

    start_octant, start_coord, start_line = -1, -1, False
    if start != ('',''):
        start = fp.unpack(vartypes.pass_single_keep(start))
        start_octant, start_coord, start_line = get_octant(start, rx, ry)
    stop_octant, stop_coord, stop_line = -1, -1, False
    if stop != ('',''):
        stop = fp.unpack(vartypes.pass_single_keep(stop))
        stop_octant, stop_coord, stop_line = get_octant(stop, rx, ry)
        
    
    if fp.equals(aspect, aspect.one):
        graphics.draw_circle(x0,y0,rx,c, start_octant, start_coord, start_line, stop_octant, stop_coord, stop_line)
    else:
        # TODO - make this all more sensible, calculate only once
        startx, starty, stopx, stopy = -1,-1,-1,-1
        if start!=('',''):
            startx = abs(fp.round_to_int(fp.mul(fp.from_int(fp.MBF_class, rx), fp.mbf_cos(start))))
            starty = abs(fp.round_to_int(fp.mul(fp.from_int(fp.MBF_class, ry), fp.mbf_sin(start))))
        if stop!=('',''):
            stopx = abs(fp.round_to_int(fp.mul(fp.from_int(fp.MBF_class, rx), fp.mbf_cos(stop))))
            stopy = abs(fp.round_to_int(fp.mul(fp.from_int(fp.MBF_class, ry), fp.mbf_sin(stop))))
        
        graphics.draw_ellipse(x0,y0,rx,ry,c, start_octant/2, startx, starty, start_line, stop_octant/2, stopx, stopy, stop_line)
            

def get_octant(mbf, rx, ry):
    
    neg = fp.sign(mbf) == -1
    if neg:
        mbf = fp.neg(mbf)

    octant=0
    comp = fp.mbf_pi4
    while fp.gt(mbf,comp):
        comp = fp.add(comp, fp.mbf_pi4)
        octant += 1
        if octant >= 8:
            raise error.RunError(5) # ill fn call
    
    if octant in (0,3,4,7):
        # running var is y
        coord = abs(fp.round_to_int(fp.mul(fp.from_int(fp.MBF_class, ry), fp.mbf_sin(mbf))))
    else:
        # running var is x    
        coord = abs(fp.round_to_int(fp.mul(fp.from_int(fp.MBF_class, rx), fp.mbf_cos(mbf))))
    return octant, coord, neg                 



      
      
# PAINT -if paint *colour* specified, border default= paint colour
# if border *attribute* specified, border default=15      
def exec_paint(ins):
    graphics.require_graphics_mode()
    
    x0,y0 = graphics.window_coords(*parse_coord(ins))
    pattern = ''
    c = graphics.get_colour_index(-1) 
    border= c
    
    if util.skip_white_read_if(ins, ','):
        cval = expressions.parse_expression(ins, allow_empty=True)
        
        
        if cval[0]=='$':
            # pattern given
            pattern = vartypes.pass_string_keep(cval)[1]
            pattern = map(ord, list(pattern))
            if len(pattern)==0:
                # empty pattern "" is illegal function call
                raise error.RunError(5)
            while len(pattern)%graphics.bitsperpixel !=0:
                 # finish off the pattern with zeros
                 pattern.append(0)
            # default for border,  if pattern is specified as string
            # foreground attr
            c=-1
            
        elif cval == ('',''):
            # default
            pass
        else:
            c = vartypes.pass_int_keep(cval)[1]
        
        border = c    
        if util.skip_white_read_if(ins, ','):
            bval = expressions.parse_expression(ins, allow_empty=True)
            if bval == ('',''):
                pass
            else:
                border = vartypes.pass_int_keep(bval)[1]
        
            if util.skip_white_read_if(ins, ','):
                background_pattern = vartypes.pass_string_keep(expressions.parse_expression(ins), err=5)[1]
                # background attribute - I can't find anything this does at all.
                # as far as I can see, this is ignored in GW-Basic as long as it's a string, otherwise error 5
    
    if pattern=='':
        pattern = draw_and_play.solid_pattern(c)
    
    util.require(ins, util.end_statement)         
    graphics.flood_fill(x0,y0, pattern, c, border)        
            
    
                
def exec_get_graph(ins):
    graphics.require_graphics_mode()
    x0,y0 = graphics.window_coords(*parse_coord(ins))
    util.require_read(ins, '\xEA') #-
    x1,y1 = graphics.window_coords(*parse_coord(ins))
    util.require_read(ins, ',') 
    array = var.get_var_name(ins)    
    util.require(ins, util.end_statement)
        
    graphics.get_area(x0,y0,x1,y1, array)
    

    
def exec_put_graph(ins):
    graphics.require_graphics_mode()
    x0,y0 = graphics.window_coords(*parse_coord(ins))
    util.require_read(ins, ',') 
    array = var.get_var_name(ins)    
    action = graphics.operation_xor
    if util.skip_white_read_if(ins, ','):
        c =util.skip_white_read(ins) 
        if c == '\xC6': #PSET
            action = graphics.operation_set
        elif c == '\xC7': #PRESET
            action = graphics.operation_not
        elif c == '\xEE': #AND
            action = graphics.operation_and
        elif c == '\xEF': #OR
            action = graphics.operation_or
        elif c == '\xF0': #XOR
            action = graphics.operation_xor
    util.require(ins, util.end_statement)
    
    graphics.set_area(x0,y0, array, action)
    
    
def exec_draw(ins):
    graphics.require_graphics_mode()
    gml = vartypes.pass_string_keep(expressions.parse_expression(ins))[1]
    util.require(ins, util.end_expression)
    draw_and_play.draw_parse_gml(gml)
    
    
