#!/usr/bin/env python
##############################################################################
#
# xpdacq            by Billinge Group
#                   Simon J. L. Billinge sb2896@columbia.edu
#                   (c) 2016 trustees of Columbia University in the City of
#                        New York.
#                   All rights reserved
#
# File coded by:    Timothy Liu, Simon Billinge
#
# See AUTHORS.txt for a list of people who contributed.
# See LICENSE.txt for license information.
#
##############################################################################
#from dataportal import DataBroker as db
#from dataportal import get_events, get_table, get_images
#from metadatastore.commands import find_run_starts

import os
import datetime
import numpy as np
import tifffile as tif
import matplotlib as plt

from xpdacq.control import _get_obj
from xpdacq.config import datapath # at xpd

# fileds used to generate tiff file name. Could be maintained later
_fname_field = ['sa_name', 'bt_experimenters']
#_scan_property = ['xp_isdark']

bt = _get_obj('bt')
db = _get_obj('db')
get_events = _get_obj('get_events')
get_images = _get_obj('get_images')


def bt_uid():
    return bt.get(0).md['bt_uid']

def _feature_gen(header):
    ''' generate a human readable file name. 

    file name is generated by metadata information in header 
    '''
    uid = header.start.uid
    time_stub = _timestampstr(header.start.time)
    feature_list = []
    
    try:
        if header.start['xp_isdark']:
            feature_list.append('dark')
    except KeyError:
        pass

    field = header['start']
    for key in _fname_field:
        try:
            el = field[key]
            if isinstance(el, list):
                # grab the first two experimenters
                feature_list.append(str(el[0]))
                feature_list.append(str(el[1]))
            else:
                # truncate length
                if len(el)>12:
                    value = el[:12]
                else:
                    value = el
                # clear space
                feature = [ ch for ch in list(el) if ch!=' ']
                feature_list.append(''.join(feature))
        except KeyError:
            # exceptioin handle. If user forgot to define require fields
            pass

    print(feature_list)
    f_name = "_".join(feature_list)
    exp_time = _timestampstr(header.start.time)
    return '_'.join([exp_time, f_name])

def _timestampstr(timestamp):
    time = str(datetime.datetime.fromtimestamp(timestamp))
    date = time[:10]
    hour = time[11:16]
    m_hour = hour.replace(':','-')
    timestampstring = '_'.join([date,hour])
    #corrected_timestampstring = timestampstring.replace(':','-')
    return timestampstring

def save_last_tif():
    save_tif(db[-1])

def save_tif(headers, tif_name = False ):
    ''' save images obtained from dataBroker as tiff format files. It returns nothing.

    arguments:
        headers - list - a list of header objects obtained from a query to dataBroker
        file_name - str - optional. File name of tif file being saved. default setting yields a name made of time, uid, feature of your header
      
    '''
    # prepare header
    if type(list(headers)[1]) == str:
        header_list = list()
        header_list.append(headers)
    else:
        header_list = headers
    
    # iterate over header(s)
    for header in header_list:
        print('Plotting and saving your image(s) now....')
        # get images and exposure time from headers level
        try:
            img_field =[el for el in header.descriptors[0]['data_keys'] if el.endswith('_image')][0]
            print('Images are pulling out from %s' % img_field)
            light_imgs = np.array(get_images(header,img_field))
        except IndexError:
            uid = header.start.uid
            print('This header with uid = %s does not contain any image' % uid)
            print('Was area detector correctly mounted then?')
            print('Stop saving')
            return

        # working on events level
        header_events = list(get_events(header))

        try:
            cnt_time = header.start['sc_params']['exposure']
            print('cnt_time = %s' % cnt_time)
        except KeyError:
            print('Opps you forgot to enter exposure time')
            pass
        
        
        # container for final image 
        img_list = list()
        for i in range(light_imgs.shape[0]):
            dummy = light_imgs[i] 
            img_list.append(dummy)
        
        for i in range(len(img_list)):
            img = img_list[i]
            if not tif_name:
                W_DIR = datapath.tif_dir
                dummy_name = _feature_gen(header)
               
                # temperautre is a typo from Dan but it is there...
                if 'temperautre' in header_events[i]['data']:
                    f_name = dummy_name + '_'+str(header_events[i]['data']['temperautre'])+'K'
                else:
                    f_name = dummy_name
                w_name = os.path.join(W_DIR,f_name+'.tiff')
            try:
                fig = plt.figure(f_name)
                plt.imshow(img)
                plt.show()
            except:
                pass # allow matplotlib to crach without stopping experiment
            
            tif.imsave(w_name, img) 
            if os.path.isfile(w_name):
                print('image "%s" has been saved at "%s"' % (f_name, W_DIR))
                print('if you do not see as much as metadata in file name, that means you forgot to enter it')
            else:
                print('Sorry, something went wrong with your tif saving')
                return

    print('||********Saving process SUCCEEDED********||')
