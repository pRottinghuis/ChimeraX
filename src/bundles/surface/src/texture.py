# === UCSF ChimeraX Copyright ===
# Copyright 2016 Regents of the University of California.
# All rights reserved.  This software provided pursuant to a
# license agreement containing restrictions on its disclosure,
# duplication and use.  For details see:
# http://www.rbvi.ucsf.edu/chimerax/docs/licensing.html
# This notice must be embedded in or attached to all copies,
# including partial copies, of the software or any revisions
# or derivations thereof.
# === UCSF ChimeraX Copyright ===

def color_image(session, surfaces, file = None, coords = None, write_colors = None):
    '''
    Color surfaces using images read from files and specify texture coordinates
    that define how to map the image onto the surface.

    Parameters
    ----------
    surfaces : list of Surface
        Act on these surfaces and their child drawings.
    file : string
        Path to image file, e.g. PNG or JPEG image.  If the value is the string "none" then
        any texture is removed from the surface.
    coords : "sphere", "pole", "south", "vertexcolors" or None
        Defines how to map the image axes onto the surface.  "sphere" assigns
        texture coordinates to each surface vertex based on longitude and lattitude.
        The image x axis is longitude (texture coordinate u), and image y axis is
        lattitude (texture coordinate v).  "pole" has the north pole at the middle
        of the image and the south pole on a circle touching the image edges.
        "south" is like pole only centered on the south pole.  "vertexcolors" sets
        unique texture coordinates for each unique vertex color.  The corresponding
        texture image can be written to a file with the write_colors argument.
        None means no texture coordinates are assigned and uses existing texture
        coordinates for the model.
    write_colors : file name
        Write vertex color texture to the specified file name.  Only used if coords
        is specified as "vertexcolors".  This is used to write out a texture image
        that could for example be used with an exported OBJ surface file that gives
        texture coordinates.  This only works well if each distinct color is a
        separate disconnected surface piece.  If a single connected surface has
        different vertex colors the blending between two different colors will be
        wrong in texture space because the vertex to texture coordinate mapping
        makes no attempt to wrap the texture coordinates onto the surface.  Instead
        each distinct color is simply assigned a unique texture coordinate without
        regard to the spatial arrangement of colors on the surface.
    '''
    
    rgba = None if file is None or file == 'none' else image_file_as_rgba(file)
    dlist = drawings(surfaces)

    if coords == 'vertexcolors':
        crgba = _set_vertex_color_texture_coordinates(session, dlist)
        trgba = crgba if rgba is None else rgba
        for d in dlist:
            _set_texture(session, d, trgba)
        if write_colors is not None:
            from PIL import Image
            # Flip y-axis since PIL image has row 0 at top,
            # opengl has row 0 at bottom.
            pi = Image.fromarray(crgba[::-1,:,:])
            pi.save(write_colors)
    else:
        for d in dlist:
            if coords is not None:
                uv = texture_coordinates(d, coords)
                d.texture_coordinates = uv
            if file == 'none':
                _remove_texture(session, d)
            elif rgba is not None:
                _set_texture(session, d, rgba)

    msg = 'Textured %d drawings: %s' % (len(dlist), ', '.join(d.name for d in dlist))
    session.logger.info(msg)
    
def drawings(models):
    dlist = []
    for m in models:
        for d in m.all_drawings():
            if not d.triangles is None and len(d.triangles) > 0:
                dlist.append(d)
    return dlist

def image_file_as_rgba(path):
    from os.path import expanduser, isfile
    p = expanduser(path)
    if not isfile(p):
        from chimerax.core.errors import UserError
        raise UserError('texture image file "%s" does not exist' % p)
    from PyQt5.QtGui import QImage
    qi = QImage(p)
    from chimerax.graphics import qimage_to_numpy
    rgba = qimage_to_numpy(qi)
    return rgba

def texture_coordinates(drawing, geometry = 'sphere'):
    d = drawing
    v = d.vertices
    nv = len(v)
    from numpy import arctan2, sqrt, empty, float32, pi, sin, cos
    uv = empty((nv,2), float32)
    x,y,z = v[:,0], v[:,1], v[:,2]
    phi = arctan2(y, x)	# Phi, -pi to pi
    dxy = sqrt(x*x + y*y)
    psi = arctan2(dxy, z)	# Psi, 0 to pi
    if geometry == 'sphere':
        uv[:,0] = phi
        uv[:,0] /= 2*pi
        uv[:,0] += 0.5
        uv[:,1] = psi
        uv[:,1] /= pi
    elif geometry == 'pole':
        r = psi/(2*pi)
        uv[:,0] = r*cos(phi) + 0.5
        uv[:,1] = r*sin(phi) + 0.5
    elif geometry == 'south':
        r = (pi-psi)/(2*pi)
        uv[:,0] = r*cos(phi) + 0.5
        uv[:,1] = r*sin(phi) + 0.5
    return uv

def _set_vertex_color_texture_coordinates(session, drawings, max_width = 1024):
    # Number the unique colors
    color_num = {}
    dcolor_nums = {}
    for d in drawings:
        vc = d.get_vertex_colors(create = True)
        color_nums = dcolor_nums[d] = []
        for c in vc:
            tc = tuple(c)
            if tc not in color_num:
                color_num[tc] = len(color_num)
            color_nums.append(color_num[tc])

    # Make list of colors for palette texture.
    color_list = list(color_num.keys())
    color_list.sort(key = lambda c: color_num[c])

    # Make grid of colors
    nc = len(color_list)
    w = min(max_width, nc)
    h = (nc+w-1) // w
    from numpy import empty, float32, uint8, array
    uvn = empty((nc,2), float32)
    rgba = empty((h,w,4), uint8)
    for n in range(nc):
        r,c = n // w, n % w
        uvn[n,0] = (c + 0.5) / w	# x image coord
        uvn[n,1] = (r + 0.5) / h	# y image coord
        rgba[r,c,:] = color_list[n]
    
    # Set texture coordinates
    opaque = (rgba[:,:,3] == 255).all()
    white = array((255,255,255,255),uint8)
    for d in drawings:
        vc = d.get_vertex_colors(create = True)
        uv = empty((len(vc), 2), float32)
        for i,cnum in enumerate(dcolor_nums[d]):
            uv[i,:] = uvn[cnum,:]
        d.color = white		# Color modulates texture colors
        d.vertex_colors = None	# Vertex colors modulate texture colors
        d.texture_coordinates = uv
        d.opaque_texture = opaque
    
    return rgba

def _set_texture(session, drawing, rgba):
    _remove_texture(session, drawing)
    from chimerax.graphics import Texture
    t = Texture(rgba)
    t.linear_interpolation = False
    drawing.texture = t
    drawing.opaque_texture = (rgba[:,:,3] == 255).all()

def _remove_texture(session, drawing):
    if drawing.texture is None:
        return
    # TODO: Need a better mechanism to make sure discarded textures are released.
    session.main_view.render.make_current()
    drawing.texture.delete_texture()
    drawing.texture = None

def register_color_image_command(logger):
    from chimerax.core.commands import CmdDesc, register, SurfacesArg, OpenFileNameArg, EnumOf, SaveFileNameArg
    desc = CmdDesc(
        required = [('surfaces', SurfacesArg)],
        keyword = [('file', OpenFileNameArg),
                   ('coords', EnumOf(('sphere','pole','south','vertexcolors'))),
                   ('write_colors', SaveFileNameArg),],
        synopsis = 'Color surfaces with images from files'
    )
    register('color image', desc, color_image, logger=logger)
