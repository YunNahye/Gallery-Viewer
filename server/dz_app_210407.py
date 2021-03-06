#!/usr/bin/env python
#
# deepzoom_multiserver - Example web application for viewing multiple slides
#
# Copyright (c) 2010-2015 Carnegie Mellon University
#
# This library is free software; you can redistribute it and/or modify it
# under the terms of version 2.1 of the GNU Lesser General Public License
# as published by the Free Software Foundation.
#
# This library is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY
# or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU Lesser General Public
# License for more details.
#
# You should have received a copy of the GNU Lesser General Public License
# along with this library; if not, write to the Free Software Foundation,
# Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.
#
from sqlalchemy import create_engine
from sqlalchemy.sql import text
from collections import OrderedDict
from flask import Flask, abort, make_response, render_template, url_for, jsonify
from flask_cors import CORS, cross_origin
import logging
import simplejson as sjson
import json
from io import BytesIO
import openslide
from openslide import OpenSlide, OpenSlideError
from openslide.deepzoom import DeepZoomGenerator
import os
import pymysql
import platform
from optparse import OptionParser
from threading import Lock
from PIL import Image,ImageOps
from six.moves.html_parser import HTMLParser
import re
import ssl
from urllib.parse import unquote

from xml.etree.ElementTree import parse        #thumb_anno Add
import numpy as np                             #thumb_anno Add
import cv2                                     #thumb_anno Add  pip3 install opencv-python

h_parse = HTMLParser()
SSL_DIR = (os.path.abspath('C:\\sts-bundle\\workspace\\Gallery-Viewer\\server\\') if platform.system() =='Windows' else os.path.abspath('/home/ubuntu/Gallery-Viewer/server/'))
SLIDE_DIR = (os.path.abspath('C:\\Users\\h_cjw\\AppData\\Local\\Packages\\CanonicalGroupLimited.UbuntuonWindows_79rhkp1fndgsc\\LocalState\\rootfs\\home\\ubuntu\\efs\\gallery_repo\\') if platform.system() =='Windows' else os.path.abspath('/home/ubuntu/efs/gallery_repo'))
SLIDE_CACHE_SIZE = 10
DEEPZOOM_FORMAT = 'jpeg'
DEEPZOOM_TILE_SIZE = 254
DEEPZOOM_OVERLAP = 1
DEEPZOOM_LIMIT_BOUNDS = True
DEEPZOOM_TILE_QUALITY = 70
app = Flask(__name__)
app.config.from_object(__name__)
app.config.from_envvar('DEEPZOOM_MULTISERVER_SETTINGS', silent=True)
CORS(app)
logging.disable(logging.DEBUG)
logging.disable(logging.INFO)

logger = logging.getLogger(__name__)


pymysql.install_as_MySQLdb()
engine = create_engine('mysql+pymysql://pathology:Path_db)#!&@54.180.195.254:3306/pathology',pool_pre_ping=True)

class PILBytesIO(BytesIO):
    def fileno(self):
        '''Classic PIL doesn't understand io.UnsupportedOperation.'''
        raise AttributeError('Not supported')


class _SlideCache(object):
    def __init__(self, cache_size, dz_opts):
        self.cache_size = cache_size
        self.dz_opts = dz_opts
        self._lock = Lock()
        self._cache = OrderedDict()

    def get(self, path):
        with self._lock:
            if path in self._cache:
                # Move to end of LRU
                slide = self._cache.pop(path)
                self._cache[path] = slide
                return slide

        osr = OpenSlide(path)
        slide = DeepZoomGenerator(osr, **self.dz_opts)
        try:
            mpp_x = osr.properties[openslide.PROPERTY_NAME_MPP_X]
            mpp_y = osr.properties[openslide.PROPERTY_NAME_MPP_Y]
            slide.mpp = (float(mpp_x) + float(mpp_y)) / 2
            slide.magnification = osr.properties[openslide.PROPERTY_NAME_OBJECTIVE_POWER]
        except (KeyError, ValueError):
            slide.mpp = 0
            slide.magnification = 0

        with self._lock:
            if path not in self._cache:
                if len(self._cache) == self.cache_size:
                    self._cache.popitem(last=False)
                self._cache[path] = slide
        return slide


class _Directory(object):
    def __init__(self, basedir, relpath=''):
        self.name = os.path.basename(relpath)
        self.children = []
        for name in sorted(os.listdir(os.path.join(basedir, relpath))):
            cur_relpath = os.path.join(relpath, name)
            cur_path = os.path.join(basedir, cur_relpath)
            if os.path.isdir(cur_path):
                cur_dir = _Directory(basedir, cur_relpath)
                if cur_dir.children:
                    self.children.append(cur_dir)
            elif OpenSlide.detect_format(cur_path):
                self.children.append(_SlideFile(cur_relpath))


class _SlideFile(object):
    def __init__(self, relpath):
        self.name = os.path.basename(relpath)
        self.url_path = relpath

@app.before_first_request
def _setup():
    app.basedir = os.path.abspath(app.config['SLIDE_DIR'])
    config_map = {
        'DEEPZOOM_TILE_SIZE': 'tile_size',
        'DEEPZOOM_OVERLAP': 'overlap',
        'DEEPZOOM_LIMIT_BOUNDS': 'limit_bounds',
    }
    opts = dict((v, app.config[k]) for k, v in config_map.items())
    app.cache = _SlideCache(app.config['SLIDE_CACHE_SIZE'], opts)


def _get_slide(path):
    path = os.path.abspath(os.path.join(app.basedir, path))
    if not path.startswith(app.basedir + os.path.sep):
        # Directory traversal
        abort(404)
    if not os.path.exists(path):
        abort(404)
    try:
        slide = app.cache.get(path)
        slide.filename = os.path.basename(path)
        return slide
    except OpenSlideError:
        abort(404)


def _get_slide_object(path):
    path = os.path.abspath(os.path.join(app.basedir, path))
    if not path.startswith(app.basedir + os.path.sep):
        abort(404)
    if not os.path.exists(path):
        abort(404)
    try:
        osr = OpenSlide(path)
        return osr
    except OpenSlideError:
        abort(404)

def _get_image_object(path):
    path = os.path.abspath(os.path.join(app.basedir, path))
    return Image.open(path)

def remove_tag(content):
   cleanr =re.compile('<[^>]+>')
   cleantext = re.sub(cleanr, '', content)
   return cleantext

def cropImage(image):
	invert_im = image.convert("RGB")
	invert_im = ImageOps.invert(invert_im)
	left,upper,right,lower = invert_im.getbbox()
	
	newImage = image.crop((left,upper,right,lower))
	return newImage

#thumb_anno Add
def take_current_and_next(it):
    it = iter(it)
    current = next(it)
    for next_ in it:
        yield current, next_
        current = next_

#thumb_anno Add
def hex_to_rgb(value):
    hex_val = hex(int(value))
    hex_val=hex_val.lstrip('0x')
    lv = len(hex_val)
    if lv<4: hex_val = "0"+str(hex_val)
    green = int(hex_val[0:2],16)
    red = int(hex_val[2:4],16)
    blue = 0
    return red,green,blue

@app.route('/')
def index():
    return 'Run Viewer.'
#    return render_template('files.html', root_dir=_Directory(app.basedir))

#               
@app.route('/plug/monthly/viewer/img/<path:path>/<path:path2>')
def plugSimpleImage(path,path2):
    try:
        getImage = _get_image_object(os.path.join(path,path2))
    except ValueError:
        abort(404)
    buf = PILBytesIO()
    getImage.convert('RGB').save(buf, getImage.format, quality=75)
    resp = make_response(buf.getvalue())
    resp.mimetype = 'image/%s' % getImage.format
    return resp
    

  
#
@app.route('/plug/monthly/viewer/sld/<path:path>/<path:path2>.dzi')
def plugViewerDZI(path,path2):
    try:
        slide = _get_slide(os.path.join(path,path2))
    except UnboundLocalError:
        abort(404)
    else:
        format = app.config['DEEPZOOM_FORMAT']
        resp = make_response(slide.get_dzi(format))
        resp.mimetype = 'application/xml'
        return resp

#
@app.route('/plug/monthly/viewer/sld/<path:path>_files/<int:level>/<int:col>_<int:row>.<format>')
def plugViewerDZITile(path, level, col, row, format):
    slide = _get_slide(path)
    format = format.lower()
    if format != 'jpeg' and format != 'png':
        # Not supported by Deep Zoom
        abort(404)
    try:
        tile = slide.get_tile(level, (col, row))
    except ValueError:
        # Invalid level or coordinates
        abort(404)
    buf = PILBytesIO()
    tile.save(buf, format, quality=app.config['DEEPZOOM_TILE_QUALITY'])
    resp = make_response(buf.getvalue())
    resp.mimetype = 'image/%s' % 'jpeg'
    return resp

#
@app.route('/plug/monthly/thumb/<path:path>_<int:sx>_<int:sy>.<format>')
def thumbImageResize(path,sx,sy, format):

    query = text(
        "   SELECT filename,extname "
        "   FROM pathology.HMT_SLIDE  "
        "   WHERE sid = :slideId    "
    )

    query_exe_result = engine.execute(query,slideId=path)
    get_slide_info = query_exe_result.fetchone()
    if get_slide_info==None:
        return ''


    get_slide_path = os.path.join(path,get_slide_info.filename)

    imgStat = [0,-1]
    imgList = ['jpg','jpeg','png']
    slideList = ['svs','vms','vmu','ndpi','scn','mrxs','svslide','bif']

    format = format.lower()
    if format != 'jpeg' and format != 'png':
        abort(404)
    try:
        imgStat[0] = 0
        imgStat[1] = imgList.index(get_slide_info.extname.lower())
    except ValueError:
        imgStat[0] = 0
        imgStat[1] = -1
    
    if imgStat[1]==-1:
        try:
            imgStat[0] = 1
            imgStat[1] = slideList.index(get_slide_info.extname.lower())
        except ValueError:
            imgStat[0] = 1
            imgStat[1] = -1

    if imgStat[1]!=-1:
        if imgStat[0]==0:
            try:
                thumbIm = _get_image_object(get_slide_path)
                thumbIm = thumbIm.resize((sx, sy)) 
            except ValueError:
                abort(404)
            buf = PILBytesIO()
            thumbIm.convert('RGB').save(buf, format, quality=75)
            resp = make_response(buf.getvalue())
            resp.mimetype = 'image/%s' % format
            return resp

        elif imgStat[0]==1: 
            osr = _get_slide_object(get_slide_path)
            try:
                thumbIm = osr.associated_images['thumbnail']
                thumbIm = cropImage(thumbIm)
                new_sx  = sy * thumbIm.size[0] / thumbIm.size[1]
                thumbIm = thumbIm.resize((int(new_sx), sy))
                
            except ValueError:
                abort(404)
            buf = PILBytesIO()
            thumbIm.convert('RGB').save(buf, format, quality=75)
            resp = make_response(buf.getvalue())
            resp.mimetype = 'image/%s' % format
            return resp


#               
@app.route('/gallery/monthly/viewer/img/<path:path>/<path:path2>')
def gallerySimpleImage(path,path2):
    try:
        getImage = _get_image_object(os.path.join(path,unquote(path2)))
    except ValueError:
        abort(404)
    buf = PILBytesIO()
    getImage.convert('RGB').save(buf, getImage.format, quality=75)
    resp = make_response(buf.getvalue())
    resp.mimetype = 'image/%s' % getImage.format
    return resp
    
#
@app.route('/gallery/monthly/viewer/sld/<path:path>/<path:path2>')
def galleryViewerGetInfo(path,path2):
    slide = _get_slide(os.path.join(path,unquote(path2)))
    slideDic = {
        'slide_mpp': slide.mpp,
        'slide_magnification': slide.magnification
    }
    jsonStr = json.dumps(slideDic, default=lambda o: o.__dict__, sort_keys=True, indent=4)
    return jsonStr

#
@app.route('/gallery/monthly/viewer/sld/<path:path>/<path:path2>.dzi')
def galleryViewerDZI(path,path2):
    try:
        slide = _get_slide(os.path.join(path,unquote(path2)))
    except UnboundLocalError:
        abort(404)
    else:
        format = app.config['DEEPZOOM_FORMAT']
        resp = make_response(slide.get_dzi(format))
        resp.mimetype = 'application/xml'
        return resp

#
@app.route('/gallery/monthly/viewer/sld/<path:path>_files/<int:level>/<int:col>_<int:row>.<format>')
def galleryViewerDZITile(path, level, col, row, format):
    slide = _get_slide(path)
    format = format.lower()
    if format != 'jpeg' and format != 'png':
        # Not supported by Deep Zoom
        abort(404)
    try:
        tile = slide.get_tile(level, (col, row))
    except ValueError:
        # Invalid level or coordinates
        abort(404)
    buf = PILBytesIO()
    tile.save(buf, format, quality=app.config['DEEPZOOM_TILE_QUALITY'])
    resp = make_response(buf.getvalue())
    resp.mimetype = 'image/%s' % 'jpeg'
    return resp


#
@app.route('/gallery/monthly/thumb/<path:path>_<int:sx>_<int:sy>.<format>')
def galleryThumbImageResize(path,sx,sy, format):

    query = text(
        "   SELECT filename,extname "
        "   FROM pathology.HMT_SLIDE  "
        "   WHERE sid = :slideId    "
    )

    query_exe_result = engine.execute(query,slideId=path)
    get_slide_info = query_exe_result.fetchone()
    if get_slide_info==None:
        return ''


    get_slide_path = os.path.join(path,get_slide_info.filename)

    imgStat = [0,-1]
    imgList = ['jpg','jpeg','png']
    slideList = ['svs','vms','vmu','ndpi','scn','mrxs','svslide','bif']

    format = format.lower()
    if format != 'jpeg' and format != 'png':
        abort(404)
    try:
        imgStat[0] = 0
        imgStat[1] = imgList.index(get_slide_info.extname.lower())
    except ValueError:
        imgStat[0] = 0
        imgStat[1] = -1
    
    if imgStat[1]==-1:
        try:
            imgStat[0] = 1
            imgStat[1] = slideList.index(get_slide_info.extname.lower())
        except ValueError:
            imgStat[0] = 1
            imgStat[1] = -1

    if imgStat[1]!=-1:
        if imgStat[0]==0:
            try:
                thumbIm = _get_image_object(get_slide_path)
                thumbIm = thumbIm.resize((sx, sy))
            except ValueError:
                abort(404)
            buf = PILBytesIO()
            thumbIm.convert('RGB').save(buf, format, quality=75)
            resp = make_response(buf.getvalue())
            resp.mimetype = 'image/%s' % format
            return resp

        elif imgStat[0]==1: 
            osr = _get_slide_object(get_slide_path)
            try:
                thumbIm = osr.associated_images['thumbnail']
                thumbIm = cropImage(thumbIm)
                new_sx  = sy * thumbIm.size[0] / thumbIm.size[1]
                thumbIm = thumbIm.resize((int(new_sx), sy))
            except ValueError:
                abort(404)
            buf = PILBytesIO()
            thumbIm.convert('RGB').save(buf, format, quality=75)
            resp = make_response(buf.getvalue())
            resp.mimetype = 'image/%s' % format
            return resp

#thumb_anno Add
@app.route('/thumb_anno/<path:path>/<int:sx>/<int:sy>')
def thumbImageAnno(path,sx,sy):

        path=os.path.abspath('/home/ubuntu/efs/thumbnail_anno/SNUH_185.svs')
        osr = OpenSlide(path)

#       get Image
        slide_dim = osr.dimensions
        thumbIm = np.zeros((slide_dim[0], slide_dim[1], 3), np.uint8)
        thumbIm = osr.associated_images['thumbnail']
#       Image resize 
        thumb_ratio = sy / slide_dim[1]
        new_sx  = sy * slide_dim[0] / slide_dim[1]
        thumbIm = thumbIm.resize((int(new_sx), sy))
        thumbIm = np.array(thumbIm)

#       XML draw Image Line
        annotree=parse(os.path.abspath('/home/ubuntu/efs/thumbnail_anno/SNUH_185.xml'))
        root = annotree.getroot()
        annotation_arr = root.findall("Annotation")
        for annotation in annotation_arr:
        	line_color = hex_to_rgb(annotation.get("LineColor"))
        	line_weight = 2
        	regions = annotation.find("Regions")
        	region_arr = regions.findall("Region")
        	for region in region_arr:
        		vertices = region.find("Vertices")
        		vertex_arr = vertices.findall("Vertex")
        		for vertex, next_vertex in take_current_and_next(vertex_arr):
        			v_x= int(int(vertex.get("X"))*thumb_ratio)
        			v_y= int(int(vertex.get("Y"))*thumb_ratio)
        			next_v_x= int(int(next_vertex.get("X"))*thumb_ratio)
        			next_v_y= int(int(next_vertex.get("Y"))*thumb_ratio)
        			thumbIm = cv2.line(thumbIm, (v_x, v_y), (next_v_x,next_v_y ),line_color, line_weight)
        thumbIm =Image.fromarray(thumbIm)
                    
        buf = PILBytesIO()
#        thumbIm=osr.associated_images['thumbnail']
        thumbIm.convert('RGB').save(buf, 'jpeg', quality=75)
        resp = make_response(buf.getvalue())
        resp.mimetype = 'image/%s' % 'jpeg'
        return resp

#
'''
@app.route('/<path:path>')
def slide(path):
    slide = _get_slide(path)
    slide_url = url_for('dzi', path=path)
    return render_template('slide-multipane.html', slide_url=slide_url,
            slide_filename=slide.filename, slide_mpp=slide.mpp, slide_magnification=slide.magnification)
'''
'''
@app.route('/<path:path>.dzi')
def dzi(path):
    slide = _get_slide(path)
    format = app.config['DEEPZOOM_FORMAT']
    resp = make_response(slide.get_dzi(format))
    resp.mimetype = 'application/xml'
    return resp

@app.route('/<path:path>_files/<int:level>/<int:col>_<int:row>.<format>')
def tile(path, level, col, row, format):
    slide = _get_slide(path)
    format = format.lower()
    if format != 'jpeg' and format != 'png':
        # Not supported by Deep Zoom
        abort(404)
    try:
        tile = slide.get_tile(level, (col, row))
    except ValueError:
        # Invalid level or coordinates
        abort(404)
    buf = PILBytesIO()
    tile.save(buf, format, quality=app.config['DEEPZOOM_TILE_QUALITY'])
    resp = make_response(buf.getvalue())
    resp.mimetype = 'image/%s' % format
    return resp
'''

if __name__ == '__main__':
    parser = OptionParser(usage='Usage: %prog [options] [slide-directory]')
    parser.add_option('-B', '--ignore-bounds', dest='DEEPZOOM_LIMIT_BOUNDS',
                default=True, action='store_false',
                help='display entire scan area')
    parser.add_option('-c', '--config', metavar='FILE', dest='config',
                help='config file')
    parser.add_option('-d', '--debug', dest='DEBUG', action='store_true',
                help='run in debugging mode (insecure)')
    parser.add_option('-e', '--overlap', metavar='PIXELS',
                dest='DEEPZOOM_OVERLAP', type='int',
                help='overlap of adjacent tiles [1]')
    parser.add_option('-f', '--format', metavar='{jpeg|png}',
                dest='DEEPZOOM_FORMAT',
                help='image format for tiles [jpeg]')
    parser.add_option('-l', '--listen', metavar='ADDRESS', dest='host',
                default='0.0.0.0',
                help='address to listen on [0.0.0.0]')
    parser.add_option('-p', '--port', metavar='PORT', dest='port',
                type='int', default=32380,
                help='port to listen on [32380]')
    parser.add_option('-Q', '--quality', metavar='QUALITY',
                dest='DEEPZOOM_TILE_QUALITY', type='int',
                help='JPEG compression quality [75]')
    parser.add_option('-s', '--size', metavar='PIXELS',
                dest='DEEPZOOM_TILE_SIZE', type='int',
                help='tile size [254]')

    (opts, args) = parser.parse_args()
    # Load config file if specified
    if opts.config is not None:
        app.config.from_pyfile(opts.config)
    # Overwrite only those settings specified on the command line
    for k in dir(opts):
        if not k.startswith('_') and getattr(opts, k) is None:
            delattr(opts, k)
    app.config.from_object(opts)
    # Set slide directory
    try:
        app.config['SLIDE_DIR'] = args[0]
    except IndexError:
        pass
    ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLS)
    print(os.getcwd())
    ssl_context.load_cert_chain(certfile=os.path.join(SSL_DIR,'ssl.crt'), keyfile=os.path.join(SSL_DIR,'ssl.key'), password='ksp7953094!')
    app.run(host=opts.host, port=opts.port, threaded=True, ssl_context=ssl_context, debug=False)