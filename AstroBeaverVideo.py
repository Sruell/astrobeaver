#! /usr/bin/python3 
'''
    Name    : AstroBeaver
    Author  : Sebastian Ruell - Biberwerke
    Date    : 08.05.2023
    Version : 1-00
    
    
    Dependencies
    ------------
    picamera == 1.13
    pidng == 3.4.7
    Pillow == 8.4.0
    PySimpleGUI == 4.55.1
'''

import os
import sys
import io
import time
import PySimpleGUI as sg
from PIL import Image
from time import sleep
import picamera
from datetime import datetime
from pathlib import Path
import numpy as np

# get the home directory
home = str(Path.home())

# set the GUI theme
sg.theme('DarkBlack')

# set the size of the padding around elements
sg.SetOptions(element_padding=(0, 0),
              text_color = 'Red',
              input_text_color ='Red',
              button_color = ('Black', 'Red')) 

# grab the resolution of the screen the program is being run on
SCREEN_WIDTH, SCREEN_HEIGHT = sg.Window.get_screen_size()

# put all key parameters in their own class, Parameters
class Parameters:
    # default image settings
    default_brightness      = 50
    default_contrast        = 0 
    default_saturation      = 0
    default_sharpness       = 0
    #default_image_no        = 1
    #default_exposure        = 1
    default_iso             = 0
    #default_time_step       = 2
    default_vid_time        = 30
    #default_image_size      = (int(SCREEN_HEIGHT/2), int(SCREEN_HEIGHT/2))
    default_preview_size    = (int(SCREEN_HEIGHT/2), int(SCREEN_HEIGHT/2))
    #default_save_folder     = "{}/images".format(os.getcwd())
    #default_save_folder_vid = "{}/videos".format(os.getcwd())
    default_save_folder     = "{}/images".format("/media/sruell/46CA-8C72")
    default_save_folder_vid = "{}/videos".format("/media/sruell/46CA-8C72")
    recordingResolutions = [(4056,3040),(3840,2880),(3840,2160),(2560,1440),(2560,1920),(2028,1520),(2028,1080),(1920,1440),(1920,1088),(1664,1248),(1332,990),(1280,960),(1280,720),(640,320)]
    sensorModes = [
    [0, 1, 2, 3, 4],    #modes
    ['auto', (2028,1080), (2028,1520), (4056,3040), (1332,990)],    #resolution
    ['auto', 50, 50, 10, 120], #max fps
    ['auto', 'partial 2x2', 'full 2x2', 'full no binning', 'partial 2x2'], #binning
    ]
    # other options
    pad_x                   = 5     # default horizontal padding amount around elements
    pad_y                   = 5     # default vertical padding amount around elements
    font_size               = 18    # font size for text elements in the GUI
    GUI_TEXT_SIZE           = (int(12),1) #(int(SCREEN_WIDTH/95), 1) # default size for text elements


def create_layout(parameters):
    '''
    This function is responsible for storing the layout of the GUI which is passed to the window object. All changes to the layout can be made within this function

    Parameters
    ----------
    parameters : Class
                 A class of the parameters used within the program. e.g. camera properties, default save locations etc...

    Returns
    -------
    layout     : List[List[Element]]
                 A list containing all the obejcts that are to be displayed in the GUI
    '''
    # assign the parameters to name p for ease of use
    p=parameters

    # ------ Menu Definition ------ #      
    menu_def = [['Menu', ['Save Location', 'Exit']],
                ['Date-Time',['Set Date-Time']]]     

    # define the column layout for the GUI
    image_column = [
        [sg.Image(filename='', key='video')],
    ]

    # controls column 3 holds the large buttons for the program which control image capture etc...
    recordingResolutions = p.recordingResolutions
    
    controls_column3 = [
        [
        sg.Button('H264', size=(10, 1), font='Helvetica 12', pad=(p.pad_x,p.pad_y)),
        sg.Button('YUV', size=(10, 1), font='Helvetica 12', pad=(p.pad_x,p.pad_y)),
        ],
        [
        sg.Combo(recordingResolutions, default_value=(1920,1088),font=('Helvetica', p.font_size),  expand_x=False, enable_events=True,  readonly=False, key='-RECRES-'),
        sg.Push(),
        sg.Spin([i for i in range(1, 999)], initial_value=p.default_vid_time, font=('Helvetica', p.font_size), key='video_duration_slider', pad=(p.pad_x,p.pad_y)), 
        ],
        [
        sg.Text('Rec resolution', size=(10,1), font=('Helvetica', 12), pad=(0,p.pad_y)),
        sg.Push(),
        sg.Text('duration / s', size=(3,1), font=("Helvetica", 12), pad=(p.pad_x,p.pad_y)),               
        ],
        [
        sg.HorizontalSeparator()
        ],
        [
        sg.Button('- Resize -', size=(10, 1), font='Helvetica 12', pad=(0,p.pad_y)),
        sg.Button('+ Resize +', size=(10, 1), font='Helvetica 12', pad=(p.pad_x,p.pad_y)),
        ],
        [
        sg.Button('Crosshair On', size=(10, 1), font='Helvetica 12', pad=(0,p.pad_y)),
        sg.Button('Crosshair Off', size=(10, 1), font='Helvetica 12', pad=(p.pad_x,p.pad_y)),
        ],
        [
        sg.HorizontalSeparator()
        ],
        [
        sg.Button('ROI', size=(10, 1), font='Helvetica 12', pad=(0,p.pad_y)),
        sg.Button('Settings', size=(10, 1), font='Helvetica 12', pad=(p.pad_x,p.pad_y)),
        ],
        [sg.HorizontalSeparator()],
        [
        sg.Button('Exit', size=(10, 1), font='Helvetica 12', pad=(0,p.pad_y)),
        ],
        [sg.Text('Status:', size=(6,1), font=('Helvetica', 14), pad=(0,p.pad_y)),
         sg.Text('Idle', size=(8, 1), font=('Helvetica', 14), text_color='Red', key='output', pad=(0,p.pad_y))],
    ]

    # define the window layout
    layout = [[sg.Menu(menu_def, )],
              [sg.Column(image_column)],
              [sg.Column(controls_column3)],
            ]

    return layout
    
def roi_window(parameters, camera):
    # assign the parameters to name p for ease of use
    p=parameters
    
    roi_size = [
        [
        sg.Text('ROI', size=(3,1), font=('Helvetica', 12), pad=(0,p.pad_y), tooltip='Define a Region Of Interest'),
        sg.Checkbox('', size=(int(3), 1), enable_events=True, key='roi', pad=(0,p.pad_y)),
        sg.Button('+', size=(3, 1), enable_events=True, font='Helvetica 12', pad=(p.pad_x,p.pad_y)),
        sg.Button('-', size=(3, 1), enable_events=True, font='Helvetica 12', pad=(p.pad_x,p.pad_y)),
        ],
    ]
    
    roi_position = [
        [        
        sg.Button('UP', size=(3, 1), enable_events=True, font='Helvetica 12', pad=(0,p.pad_y)),
        sg.Button('DWN', size=(4, 1), enable_events=True, font='Helvetica 12', pad=(0,p.pad_y)),
        sg.Button('LFT', size=(4, 1), enable_events=True, font='Helvetica 12', pad=(0,p.pad_y)),
        sg.Button('RGT', size=(4, 1), enable_events=True, font='Helvetica 12', pad=(0,p.pad_y)),
        ],   
    ]
    
    roi_controls = [
        [
        sg.Button('Exit', size=(10, 1), font='Helvetica 12', pad=(p.pad_x,p.pad_y)),
        ]
    ]
    
    sensor_controls = [
        [
        sg.Text('Sensor Mode', size=(15,1), font=('Helvetica', 12, "bold"), pad=(0,p.pad_y)),
        ],
        [
        sg.Combo(p.sensorModes[0], default_value=0,font=('Helvetica', p.font_size),  expand_x=False, enable_events=True,  readonly=False, key='sensor_mode'),
        sg.Text(str(p.sensorModes[1][0]), size=(15,1), font=('Helvetica', 12), pad=(p.pad_x,p.pad_y), key='sensor_res'),
        ],
        [
        sg.Text(str(p.sensorModes[3][0]), size=(15,1), font=('Helvetica', 12), pad=(p.pad_x,p.pad_y), key='sensor_bin'),
        sg.Text(str(p.sensorModes[2][0]), size=(15,1), font=('Helvetica', 12), pad=(p.pad_x,p.pad_y), key='sensor_fps'),
        ],
    ]
    
    layout = [
        [
        sg.Column(roi_size),
        sg.VSeperator(),
        sg.Column(sensor_controls),
        ],
        [
        sg.Column(roi_position),
        sg.VSeperator(),
        sg.Column(roi_controls),
        ],
    ]
    
    window = sg.Window("Region Of Interest", layout, modal=False, location=(0,camera.preview.window[3]))
    choice = None
    o = None #overlay
    roi_changed = False
    num_steps = 20
    zoom_pos_x = 0
    zoom_pox_y = 0
    factor_left = 0
    factor_down = 0
    factor_width = 1.0
    factor_height = 1.0
    sensor_mode = 0
    sensor_width = 4056     #pi camera hq
    sensor_height = 3040    #pi camera hq
    
    while True:
        event, values = window.read()
        
        if event == 'sensor_mode':
            sensor_mode = values['sensor_mode']
            window.find_element('sensor_res').Update(p.sensorModes[1][sensor_mode])
            window.find_element('sensor_fps').Update(p.sensorModes[2][sensor_mode])
            window.find_element('sensor_bin').Update(p.sensorModes[3][sensor_mode])
            
            if(sensor_mode in [1,2,3,4]):
                sensor_width = p.sensorModes[1][sensor_mode][0]
                sensor_height = p.sensorModes[1][sensor_mode][1]
            
            recording_index = p.recordingResolutions.index((sensor_width,sensor_height));
            recording_index_min = recording_index #recording resolution cannot be higher than current sensor mode allows
            camera.sensor_mode = sensor_mode
            if(sensor_mode in [1,2,3,4]):
                camera.resolution = p.sensorModes[1][sensor_mode]
            roi_changed = False #reset roi after sensor change
        
        if values['roi'] is True:
            print('Use region of interest')
            preview_width = camera.preview.window[2]
            preview_height = camera.preview.window[3]
                                                
            if(roi_changed is False):
                recording_width = sensor_width
                recording_height = sensor_height
                recording_index = p.recordingResolutions.index((recording_width,recording_height));
                recording_index_min = recording_index #recording resolution cannot be higher than current sensor mode allows
                        
            factor_width = recording_width / sensor_width
            factor_height = recording_height / sensor_height
            
            zoom_prev_width = round(preview_width * factor_width)
            zoom_prev_height = round(preview_height * factor_height)
            
            #place roi centered by default
            if(roi_changed is False):
                zoom_pos_x = int((preview_width - zoom_prev_width)/2)
                zoom_pos_y = int((preview_height - zoom_prev_height)/2);
            
            
            if event == '+':
                if(recording_index-1 >= recording_index_min):
                    roi_changed = True
                    recording_index -= 1
                    resolution = p.recordingResolutions[recording_index]
                    recording_width = resolution[0]
                    recording_height = resolution[1]
                    camera.resolution = resolution
                    
                    #recalc zoom
                    factor_width = recording_width / sensor_width
                    factor_height = recording_height / sensor_height
                    zoom_prev_width = round(preview_width * factor_width)
                    zoom_prev_height = round(preview_height * factor_height)
                    zoom_pos_x = int((preview_width - zoom_prev_width)/2)
                    zoom_pos_y = int((preview_height - zoom_prev_height)/2);
                    print('+ increase roi')
            
            if event == '-':
                if(recording_index+1 <= len(p.recordingResolutions)-1):
                    roi_changed = True
                    recording_index += 1
                    resolution = p.recordingResolutions[recording_index]
                    recording_width = resolution[0]
                    recording_height = resolution[1]
                    camera.resolution = resolution
                    
                    #recalc zoom
                    factor_width = recording_width / sensor_width
                    factor_height = recording_height / sensor_height
                    zoom_prev_width = round(preview_width * factor_width)
                    zoom_prev_height = round(preview_height * factor_height)
                    zoom_pos_x = int((preview_width - zoom_prev_width)/2)
                    zoom_pos_y = int((preview_height - zoom_prev_height)/2);
                    print('- decrease roi')
                
            if event == 'UP':
                step = int((preview_height - zoom_prev_height)/num_steps)
                if(zoom_pos_y >= step):
                    zoom_pos_y -= step
                    roi_changed = True
                    print('move roi UP -'+str(step)+'px')
                
            if event == 'DWN':
                step = int((preview_height - zoom_prev_height)/num_steps)
                if(zoom_pos_y + zoom_prev_height + step <= preview_height):
                    zoom_pos_y += step
                    roi_changed = True
                    print('move roi DOWN +'+str(step)+'px')
            
            if event == 'LFT':
                step = int((preview_width - zoom_prev_width)/num_steps)
                if(zoom_pos_x - step >= 0):
                    zoom_pos_x -= step
                    roi_changed = True
                    print('move roi LEFT -'+str(step)+'px')
            
            if event == 'RGT':
                step = int((preview_width - zoom_prev_width)/num_steps)
                if(zoom_pos_x + step + zoom_prev_width <= preview_width):
                    zoom_pos_x += step
                    roi_changed = True
                    print('move roi RIGHT +'+str(step)+'px')
                
            # draw overlay
            img = Image.open(os.path.join(os.path.dirname(sys.argv[0]),'roi_4_3.png')).convert('RGBA')
            preview_overlay(camera, (zoom_prev_width,zoom_prev_height), img, (zoom_pos_x,zoom_pos_y))
            
            #calculate zoom position relative to upper left corner
            factor_left = zoom_pos_x / preview_width
            factor_down = zoom_pos_y / preview_height
            
            #some debugging output
            print('preview: '+str(camera.preview.window))
            print('sensor: '+str(sensor_width)+'x'+str(sensor_height))
            print('recording: '+str(camera.resolution))
            print('recording_index: '+str(recording_index))
            print('recording_index min: '+str(recording_index_min))
            print('factors: '+str(factor_width)+'x'+str(factor_height))
            print('zoom prev: '+str(zoom_prev_width)+'x'+str(zoom_prev_height))
            print('zoom position: '+str((zoom_pos_x,zoom_pos_y)))
            print('zoom rel pos: '+str((factor_left,factor_down)))
            print("sensor mode: "+str(camera.sensor_mode))
            print("framerate: "+str(camera.framerate))
        else:
            print('No region of interest')
            camera.zoom = (0,0,1.0,1.0)
            remove_overlays(camera)
                
        if event == "Exit" or event == sg.WIN_CLOSED:
            break
                
    '''
    Finally set the camera zoom
    ''' 
    camera.zoom = (factor_left, factor_down, factor_width, factor_height)
    window.close()
    return camera
    
def settings_window(parameters, camera):
    # assign the parameters to name p for ease of use
    p=parameters
    
    # controls column 4 holds the options which can be toggled
    controls_column4 = [
        [
        sg.Text('Grey scale:', font=("Helvetica", p.font_size, "bold"), pad=(0,p.pad_y)),
        sg.Checkbox('', size=(int(10), 1), enable_events=True, default=(camera.color_effects==(128,128)), key='greyscale', pad=(0,p.pad_y))
        ],
        [
        sg.Button('Defaults', size=(10, 1), font='Helvetica 12', pad=(0,p.pad_y)),
        sg.Button('Exit', size=(10, 1), font='Helvetica 12', pad=(p.pad_x,p.pad_y)),
        ]
    ]
    
    # controls column 2 holds the other options such as no. of images, shutter speed etc...
    controls_column2 = [
        [
        sg.Text('ISO', font=("Helvetica", p.font_size, "bold"), pad=(0,p.pad_y)),               
        sg.Spin([i for i in range(0, 900, 100)], size=3, initial_value=camera.iso, enable_events=True, font=('Helvetica', p.font_size), key='iso_slider', pad=(0,p.pad_y))
        ],
        [
        sg.Text('analog gain', font=("Helvetica", (p.font_size - 4)) , pad=(0,p.pad_y)),
        sg.Text(float(camera.analog_gain), key='analog_gain', font=("Helvetica", (p.font_size - 4)), pad=(p.pad_x,p.pad_y)),
        ],
        [
        sg.Text('digital gain', font=("Helvetica", (p.font_size - 4)), pad=(0,p.pad_y)),
        sg.Text(float(camera.digital_gain), key='digital_gain', font=("Helvetica", (p.font_size - 4)), pad=(p.pad_x,p.pad_y)),
        ],
    ]
    
        # controls column 1 holds the camera image settings, e.g. brightness
    controls_column1 = [
        [sg.Text('Brightness', font=("Helvetica", p.font_size, "bold"), size=p.GUI_TEXT_SIZE, pad=(0,p.pad_y)),                
         sg.Spin([i for i in range(0, 100)], initial_value=camera.brightness, enable_events=True, font=('Helvetica', p.font_size), key='brightness_slider', pad=(0,p.pad_y))],
        [sg.Text('Contrast', font=("Helvetica", p.font_size, "bold"), size=p.GUI_TEXT_SIZE),      
         sg.Spin([i for i in range(-100, 100)], initial_value=camera.contrast, enable_events=True, font=('Helvetica', p.font_size), key='contrast_slider', pad=(0,p.pad_y))],
        [sg.Text('Saturation', font=("Helvetica", p.font_size, "bold"), size=p.GUI_TEXT_SIZE),               
         sg.Spin([i for i in range(-100, 100)], initial_value=camera.saturation, enable_events=True, font=('Helvetica', p.font_size), key='saturation_slider', pad=(0,p.pad_y))],
        [sg.Text('Sharpness', font=("Helvetica", p.font_size, "bold"), size=p.GUI_TEXT_SIZE),               
         sg.Spin([i for i in range(0, 100)], initial_value=camera.sharpness, enable_events=True, font=('Helvetica', p.font_size), key='sharpness_slider', pad=(0,p.pad_y))], 
    ]   
    
    layout = [
                [sg.Column(controls_column4), sg.VSeperator(), sg.Column(controls_column2), sg.VSeperator(), sg.Column(controls_column1)]
            ]
    
    window = sg.Window("Settings", layout, modal=False, location=(0,camera.preview.window[3]))
    choice = None
    
    currentColorEffects = camera.color_effects
    
    while True:
        event, values = window.read()
        
        if event == "Exit" or event == sg.WIN_CLOSED:
            window.close()
            return camera
            
        # reset the camera settings to the default values
        if event == 'Defaults':# reset the camera settings to the default values
                window.FindElement('brightness_slider').Update(Parameters.default_brightness)
                window.FindElement('contrast_slider').Update(Parameters.default_contrast)     
                window.FindElement('saturation_slider').Update(Parameters.default_saturation)    
                window.FindElement('sharpness_slider').Update(Parameters.default_sharpness)       
                window.FindElement('greyscale').Update(False)
                window.FindElement('iso_slider').Update(Parameters.default_iso)
                values['brightness_slider'] = Parameters.default_brightness
                values['contrast_slider'] = Parameters.default_contrast
                values['saturation_slider'] = Parameters.default_saturation
                values['sharpness_slider'] = Parameters.default_sharpness
                values['greyscale'] = False
    
        # change the camera settings for the preview
        camera.brightness = int(values['brightness_slider'])  # brightness     min: 0   , max: 255 , increment:1
        camera.contrast   = int(values['contrast_slider'])   # contrast       min: 0   , max: 255 , increment:1  
        camera.saturation = int(values['saturation_slider'])  # saturation     min: 0   , max: 255 , increment:1
        camera.sharpness  = int(values['sharpness_slider'])   #sharpness  min: 0   , max: 255 , increment:1
        if(camera.iso != int(values ['iso_slider'])): #iso takes some time to settle, so only update if it has been changed
            camera.iso        = int(values ['iso_slider'])
            sleep(2)
        
        #update gain readings
        window.FindElement('analog_gain').Update(float(camera.analog_gain))
        window.FindElement('digital_gain').Update(float(camera.digital_gain))
        
        # turn on the grey scale option if it is toggled
        if values['greyscale'] is True:
            currentColorEffects = (128,128)
        else:
            currentColorEffects = None
                
        camera.color_effects = currentColorEffects
                    
    return camera
    window.close()

def create_window(layout):
    '''
    This is the function that builds the GUI window using a supplied layout

    Parameters
    ----------
    layout : List[List[Element]]
             A list containing all the objects that are to be displayed in the GUI

    Returns
    -------
    window : Window object
             The GUI window with al lspecified elements displayed
    '''
    # create invisible window with no layout
    window = sg.Window('AstroBeaverVideo', [[]], location=(1280,0), 
                                                keep_on_top=False, 
                                                finalize=True, 
                                                resizable=False, 
                                                no_titlebar=False, # set this to False so popups sit on top of the main window
                                                auto_size_buttons=True, 
                                                grab_anywhere=False)
                                                #size=(SCREEN_WIDTH,SCREEN_HEIGHT))

    window.extend_layout(window, layout)

    return window

def _pad(resolution, width=32, height=16):
    '''
    pads the specified resolution up to the nearest multiple of *width* and *height*
    this is needed because overlays require padding to the camera's block size (32x16)
    
    Parameters
    ----------
    resolution : tuple
                 The size of the image to be overlayed on the live preview
    
    width  : int
             The default width
            
    height : int
             The default height
             
    Returns
    -------
    resolution_tuple : tuple
                       Tuple containing correctly scaled width and height of the overlay image to use with the live preview

    '''
    
    return (
        ((resolution[0] + (width - 1)) // width) * width,
        ((resolution[1] + (height - 1)) // height) * height,
    )

def remove_overlays(camera):
    '''
    This function removes any overlays currently being displayed on the live preview
    
    Parameters
    ----------
    camera : picamera.camera.PiCamera
             The picamera camera object
    
    Returns
    -------
    None
    '''
    # remove all overlays from the camera preview
    for o in camera.overlays:
        camera.remove_overlay(o)

def preview_overlay(camera=None, resolution=None, overlay=None, pos=(0,0)):
    '''
    This function actually overlays the image on the live preview
    
    Parameters
    ----------
    camera     : picamera.camera.PiCamera
                 The picamera camera object
             
    resolution : tuple
                 The width and height of the window containing the overlay image
    
    overlay    : PIL.Image.Image
                 The overlay image object
    
    Returns
    -------
    None
    '''
    # remove all overlays
    remove_overlays(camera)
    
    # pad it to the right resolution
    pad = Image.new('RGBA', _pad(overlay.size))
    pad.paste(overlay, (0, 0), overlay)
    
    # add the overlay
    overlay = camera.add_overlay(pad.tobytes(), size=overlay.size)
    overlay.fullscreen = False
    overlay.window = (pos[0], pos[1], resolution[0], resolution[1])
    overlay.alpha = 128
    overlay.layer = 3

def folder_file_selecter():
    '''
    This function offers a popup menu allowing for multiple images to be selected
    
    It views a file and file tree
    
    Note, if scanning a large folder then tkinter will eventually complain about too many bitmaps.
    
    This can be fixed by reusing the images within PySimpleGUI (TODO: implement if needed at some point)
    
    Parameters
    ----------
    
    Returns
    -------
    values :
    
    '''
    # base64 versions of images of a folder and a file. PNG files (may not work with PySimpleGUI27, swap with GIFs)
    folder_icon = b'iVBORw0KGgoAAAANSUhEUgAAABAAAAAQCAYAAAAf8/9hAAAACXBIWXMAAAsSAAALEgHS3X78AAABnUlEQVQ4y8WSv2rUQRSFv7vZgJFFsQg2EkWb4AvEJ8hqKVilSmFn3iNvIAp21oIW9haihBRKiqwElMVsIJjNrprsOr/5dyzml3UhEQIWHhjmcpn7zblw4B9lJ8Xag9mlmQb3AJzX3tOX8Tngzg349q7t5xcfzpKGhOFHnjx+9qLTzW8wsmFTL2Gzk7Y2O/k9kCbtwUZbV+Zvo8Md3PALrjoiqsKSR9ljpAJpwOsNtlfXfRvoNU8Arr/NsVo0ry5z4dZN5hoGqEzYDChBOoKwS/vSq0XW3y5NAI/uN1cvLqzQur4MCpBGEEd1PQDfQ74HYR+LfeQOAOYAmgAmbly+dgfid5CHPIKqC74L8RDyGPIYy7+QQjFWa7ICsQ8SpB/IfcJSDVMAJUwJkYDMNOEPIBxA/gnuMyYPijXAI3lMse7FGnIKsIuqrxgRSeXOoYZUCI8pIKW/OHA7kD2YYcpAKgM5ABXk4qSsdJaDOMCsgTIYAlL5TQFTyUIZDmev0N/bnwqnylEBQS45UKnHx/lUlFvA3fo+jwR8ALb47/oNma38cuqiJ9AAAAAASUVORK5CYII='
    file_icon = b'iVBORw0KGgoAAAANSUhEUgAAABAAAAAQCAYAAAAf8/9hAAAACXBIWXMAAAsSAAALEgHS3X78AAABU0lEQVQ4y52TzStEURiHn/ecc6XG54JSdlMkNhYWsiILS0lsJaUsLW2Mv8CfIDtr2VtbY4GUEvmIZnKbZsY977Uwt2HcyW1+dTZvt6fn9557BGB+aaNQKBR2ifkbgWR+cX13ubO1svz++niVTA1ArDHDg91UahHFsMxbKWycYsjze4muTsP64vT43v7hSf/A0FgdjQPQWAmco68nB+T+SFSqNUQgcIbN1bn8Z3RwvL22MAvcu8TACFgrpMVZ4aUYcn77BMDkxGgemAGOHIBXxRjBWZMKoCPA2h6qEUSRR2MF6GxUUMUaIUgBCNTnAcm3H2G5YQfgvccYIXAtDH7FoKq/AaqKlbrBj2trFVXfBPAea4SOIIsBeN9kkCwxsNkAqRWy7+B7Z00G3xVc2wZeMSI4S7sVYkSk5Z/4PyBWROqvox3A28PN2cjUwinQC9QyckKALxj4kv2auK0xAAAAAElFTkSuQmCC'

    # create popup which lets user select folder with images
    starting_path = sg.popup_get_folder('Select Folder to display')

    if not starting_path:
        sys.exit(0)

    treedata = sg.TreeData()

    def add_files_in_folder(parent, dirname):
        '''
        This builds the file tree by looping through the selected folder
        
        Parameters
        ----------
        parent  : 
        
        dirname : str
                  The directory where the images are located 
        Returns
        -------
        None
        '''
        files = os.listdir(dirname)
        for f in files:
            fullname = os.path.join(dirname, f)
            if os.path.isdir(fullname): # if it's a folder, add folder and recurse
                treedata.Insert(parent, fullname, f, values=[], icon=folder_icon)
                add_files_in_folder(fullname, fullname)
            else:
                treedata.Insert(parent, fullname, f, values=[os.stat(fullname).st_size], icon=file_icon)

    add_files_in_folder('', starting_path)

    layout = [[sg.Text('Select images to stack')],
              [sg.Tree(data=treedata,
                       headings=['Size', ],
                       auto_size_columns=True,
                       select_mode=sg.TABLE_SELECT_MODE_EXTENDED,
                       num_rows=20,
                       col0_width=40,
                       key='-TREE-',
                       show_expanded=False,
                       enable_events=True,
                       ),],
              [sg.Button('Ok'), sg.Button('Cancel')]]

    window = sg.Window('Image tree', layout, resizable=True, finalize=True)
    window['-TREE-'].expand(True, True) # resize with the window (Full support for Tree element being released in 4.44.0)

    while True: # Event Loop
        event, images = window.read()
        if event in (sg.WIN_CLOSED, 'Cancel', 'Ok'):
            break
        
    window.close()
    return images['-TREE-']

def set_date_time():
    '''
    This function allows for the time and date to be set on the raspberry pi from within the GUI
    For headless RPi setups this is very useful as it cannot use NTP time synchronisation with no WiFi
    
    It simply takes user input for the date and time and runs a shell command using the os module: 'sudo date -s date_time'
    
    Parameters
    ----------
    None
    
    Returns
    -------
    None
    '''
    # popup window to input date and time
    date_time = sg.popup_get_text("Set Raspberry Pi Date and Time. Format: yyyy-mm-dd hh:mm:ss", "Input date and time", text_color='White')

    # run the command
    os.system('sudo date -s "{}"'.format(date_time))
            
def main():
    '''
    This is the main function that controls the entire program. It has all been wrapped inside a function for easy exit of the various options using a function return

    It has no explicit inputs or returns. Its main purpose is to allow the while loop to run and for pysimplegui to keep the window open whilst showing a live feed of what the camera is seeing.
    
    Parameters
    ----------
    None

    Returns
    -------
    None
    '''   
     
    # create the GUI window using create_window() which takes the layout function as its argument
    window = create_window(create_layout(Parameters()))
    
    # set the default save folder for the images
    cam_folder_save = Parameters.default_save_folder
            
    # set the default save folder for the videos
    vid_folder_save = Parameters.default_save_folder_vid
    
    # init recording resolution
    recordingResolution = (1920,1088)
    
    # if videos folder does not exist, create it
    if not os.path.isdir(vid_folder_save):
        os.mkdir(vid_folder_save)
        
    # list of resolutions to view the live preview
    resolution_list = ["320 x 240", "640 x 480", "1280 x 720", "1920 x 1080", "2560 x 1440"]
    
    # extract out the width and height from the resolution individually
    width, height = [int(num) for num in (resolution_list[0]).split() if num.isdigit()]
    
    # start the preview
    #with picamera.PiCamera(resolution=(3280,2464)) as camera:
    with picamera.PiCamera(resolution=recordingResolution) as camera:
        camera.start_preview(resolution=(350,300), fullscreen=False, window=(0,0,350,300))
        time.sleep(3)
        
        # set a counter to be able to iterate through the resolution options
        res_counter = 0
        while True:
            # datetime object containing current date and time for time stamping the images and videos
            now = datetime.now()
        
            # dd/mm/YY H_M_S
            # note colons were removed as the RPi file system disliked moving files with colons in their name
            current_day_time = now.strftime("%d_%m_%Y_%H_%M_%S")
                
            # setup the events and values which the GUI will call and modify
            window, event, values = sg.read_all_windows(timeout=0)
            
            # recording time
            cam_vid_time    = values['video_duration_slider']     # Grabs the user set video length
            
            #set combo list to current resolution
            window.find_element('-RECRES-').Update(camera.resolution)
            
            # settings window
            if event == 'Settings':
                camera = settings_window(Parameters, camera)
            
            # set the date-time if specified
            if event == 'Set Date-Time':
                set_date_time()
                            
            # change the default save location if selected from the Menu
            if event == 'Save Location':      
                cam_folder_save = sg.PopupGetFolder('save_folder', initial_folder='{}'.format(Parameters.default_save_folder), no_window=True, keep_on_top=True)            
                    
            # closing the program by pressing exit
            if event == sg.WIN_CLOSED or event == 'Exit':
                # stop the live preview
                camera.stop_preview()
                # close the camera
                camera.close()
                # close the GUI window
                window.close()
                
                return
                
            # change recording resolution
            if event == "-RECRES-":
                recordingResolution = values['-RECRES-']
                print("recording resolution changed to "+str(recordingResolution))
                #print("recording resoltuion padded: "+str(_pad(recordingResolution)))
                camera.resolution = recordingResolution
                print("sensor mode: "+str(camera.sensor_mode))
                print("framerate: "+str(camera.framerate))
                
            
            # increase in live preview size
            if event == "+ Resize +":
                # iterate up the resolution options
                if res_counter == len(resolution_list) - 1:
                    pass
                else:
                    res_counter += 1
                
                width, height = [int(num) for num in (resolution_list[res_counter]).split() if num.isdigit()]

                # restart the preview with the new specified resolution
                camera.start_preview(resolution=(width,height), fullscreen=False, window=(0,0,width,height))
                # add a short pause to allow the preview to load correctly
                time.sleep(3)
            
            # decrease in live preview size
            if event == "- Resize -":
                # iterate down the resolution options
                if res_counter == 0:
                    pass
                else:
                    res_counter -= 1
                
                width, height = [int(num) for num in (resolution_list[res_counter]).split() if num.isdigit()]
                
                # restart the preview with the new specified resolution
                camera.start_preview(resolution=(width,height), fullscreen=False, window=(0,0,width,height))
                # add a short pause to allow the preview to load correctly
                time.sleep(3)
            
            if event == "Crosshair On":
                img = Image.open(os.path.join(os.path.dirname(sys.argv[0]),'crosshair.png')).convert('RGBA')
               
                preview_overlay(camera, (width,height), img)
            
            if event == "Crosshair Off":
                remove_overlays(camera)
            
            # configure ROI
            if event == 'ROI':
                camera = roi_window(Parameters, camera)
            
            # record video
            if event == 'H264':
                # update the activity notification
                window.find_element('output').Update('Working...')
                window.Refresh()
                
                # update the activity notification
                window['output'].update('Working...')
                
                #set some defaults
                camera.video_stabilization = False
                camera.image_effect = 'none'
                camera.hflip = False
                camera.vflip = False
                
                #limit framerate
                # h264 cannot exceed 30fps
                if(camera.framerate > 30):
                    print("Max. framerate of 30FPS enforced")
                    camera.framerate = 30
                
                # set the resolution for the video capture
                # h264 offers max 8192 macroblocks of 16x16 on the RPi, that we need to respect
                if(recordingResolution[0]/16*recordingResolution[1]/16 > 8192):
                    camera.resolution=(1920,1088)
                    print("resolution of "+str(recordingResolution)+" is not supported by h264.")
                    print("Switching to max possible resolution of 1920x1088")
                else:
                    camera.resolution=recordingResolution
                    
               
                framesize = camera.resolution
                print('framesize: ' + str(framesize))
                
                # specify the name of the video save file
                video_save_file_name = "{}/Video_{}x{}_{}_{}s.h264".format(vid_folder_save, framesize[0], framesize[1], current_day_time, cam_vid_time)
                
                
                # start the video recording.
                # we use h264 format 
                camera.start_recording(video_save_file_name, format='h264', quality=10, bitrate=0)
                camera.wait_recording(cam_vid_time)
                camera.stop_recording()
                #reset recording resolution to user choice in case it was adapted automatically for the last recording
                camera.resolution=recordingResolution
                    
                # reset the activity notification
                window.find_element('output').Update('Idle')
                window.Refresh()
            
            # record uncompressed raw video
            if event == 'YUV':
                # set the resolution for the video capture
                # resolution has to match the sensor mode, so no cropping is possible
                # force resolution to sensor mode
                if(camera.sensor_mode != 0):
                    recordingResolution = resolution = _pad(Parameters.sensorModes[1][camera.sensor_mode])
                else:
                    recordingResolution = (4056,3040)
                
                camera.stop_preview()
                camera.close()
                sleep(1)
                camera = picamera.PiCamera(resolution=recordingResolution)
                camera.start_preview(resolution=(350,300), fullscreen=False, window=(0,0,350,300)) 
                
                # update the activity notification
                window.find_element('output').Update('Working...')
                window.Refresh()
                                
                # update the activity notification
                window['output'].update('Working...')
                
                #set some defaults
                camera.video_stabilization = False
                camera.image_effect = 'none'
                camera.hflip = False
                camera.vflip = False
                    
                window.find_element('-RECRES-').Update(camera.resolution)
                window.Refresh()
                print('\nResolution has to match the sensor mode, so no cropping is possible. Enforcing highest possible resolution to match sensor mode.')
               
                framesize = _pad(camera.resolution)
                print('framesize: ' + str(framesize))
                print('sensor mode: ' + str(camera.sensor_mode))
                
                # specify the name of the video save file
                video_save_file_name = "{}/Video_{}x{}_{}_{}s.yuv".format(vid_folder_save, framesize[0], framesize[1], current_day_time, cam_vid_time)
                
                # start the video recording.
                # we use YUV format 
                camera.start_recording(video_save_file_name, format='yuv')
                camera.wait_recording(cam_vid_time)
                camera.stop_recording()
                    
                # reset the activity notification
                window.find_element('output').Update('Idle')
                window.Refresh()
                
# run the main function
main()
