"""
Module for controlling most Foscam IP cameras.
"""
import httplib
import urllib
import socket
import select
import time
import datetime
import os
import errno


# Move these out of the code.
auth = '<b64 of username:password>'
port = 80

# Foscam camera API constants
DEFAULT_MI = 0.8  # default movement increment, in seconds
R320_240 = 8
R64move_interval80 = 32
PTZ_TYPE = 0
PTZ_STOP = 1
TILT_UP = 0
TILT_UP_STOP = 1
TILT_DOWN = 2
TILT_DOWN_STOP = 3
PAN_LEFT = 6
PAN_LEFT_STOP = 5
PAN_RIGHT = 4
PAN_RIGHT_STOP = 7
PTZ_LEFT_UP = 91
PTZ_RIGHT_UP = 90
PTZ_LEFT_DOWN = 93
PTZ_RIGHT_DOWN = 92
PTZ_CENTER = 25
PTZ_VPATROL = 26
PTZ_VPATROL_STOP = 27
PTZ_HPATROL = 28
PTZ_HPATROL_STOP = 29
PTZ_PELCO_D_HPATROL = 20
PTZ_PELCO_D_HPATROL_STOP = 21
IO_ON = 95
IO_OFF = 94


def get_image_path(host="default", now=None):
    """
    Returns a unix path based on the supplied host and time.
    The time defaults to now.
    """
    if not now:
        now = datetime.datetime.now()
    return "%s/%s" % (host, now.date().isoformat())


def decoder_control(command, host):
    """
    Dispatches command request to camera at host.
    """
    url = '/decoder_control.cgi?'
    request = urllib.urlencode({'command': command})
    connection = httplib.HTTPConnection(host, port)
    connection.set_debuglevel(0)
    try:
        connection.request("GET", url + request, '',
                           {'Authorization': 'Basic %s' % auth})
    except httplib.socket.error, err:
        raise socket.error("connect failed")
    response = connection.getresponse()
    try:
        resp = response.read()
    except socket.sslerror, e:
        raise
    return resp


def snapshot(host):
    """
    Take a snapshot from the camera at host.
    Deposit image in the usual place.
    """
    url = "/snapshot.cgi?"
    request = urllib.urlencode({'user': 'admin'})
    connection = httplib.HTTPConnection(host, port)
    connection.set_debuglevel(0)
    try:
        connection.request("GET", url + request, '',
                           {'Authorization': 'Basic %s' % auth})
    except httplib.socket.error, err:
        raise socket.error("connect failed")
    response = connection.getresponse()
    try:
        resp = response.read()
    except socket.sslerror, e:
        raise
    now = datetime.datetime.now()
    imgname = ("img_%s.jpg" % now.strftime("%Y%m%d%H%M%S"))
    path = "/var/www/chadcam/img/%s" % get_image_path(host, now)
    try:
        os.makedirs(path)
    except OSError as exc:
        if exc.errno == errno.EEXIST and os.path.isdir(path):
            pass
        else:
            raise
    imgfd = 0
    try:
        # prevent multiple simultaneous snapshots from trampling eachother.
        imgfd = os.open("%s/%s" % (path, imgname),
                        os.O_CREAT | os.O_EXCL | os.O_EXLOCK | os.O_RDWR, 0644)
        os.write(imgfd, resp)
    except IOError as e:
        print "Failed to write image file %s: %s" % (imgname, e)
    finally:
        if imgfd:
            os.close(imgfd)
    return imgname


def tilt_up(host, move_interval=DEFAULT_MI):
    """
    Tilt camera at host upward. The higher the move_interval, the
    farther the camera moves up.
    move_interval is in seconds and can be a floating point value.
    """
    decoder_control(TILT_UP, host)
    time.sleep(move_interval)
    decoder_control(TILT_UP_STOP, host)


def tilt_down(host, move_interval=DEFAULT_MI):
    """
    Tilt camera at host downward. The higher the move_interval, the
    farther the camera moves.
    move_interval is in seconds and can be a floating point value.
    """
    decoder_control(TILT_DOWN, host)
    time.sleep(move_interval)
    decoder_control(TILT_DOWN_STOP, host)


def pan_left(host, move_interval=DEFAULT_MI):
    """
    Pan camera at host left. The higher the move_interval, the
    farther the camera moves.
    move_interval is in seconds and can be a floating point value.
    """
    decoder_control(PAN_LEFT, host)
    time.sleep(move_interval)
    decoder_control(PAN_LEFT_STOP, host)


def pan_right(host, move_interval=DEFAULT_MI):
    """
    Pan camera at host right. The higher the move_interval, the
    farther the camera moves.
    move_interval is in seconds and can be a floating point value.
    """
    decoder_control(PAN_RIGHT, host)
    time.sleep(move_interval)
    decoder_control(PAN_RIGHT_STOP, host)


def ir_on(host):
    """
    Turn on infrared (night vision) for camera at host.
    """
    decoder_control(IO_ON, host)


def ir_off(host):
    """
    Turn off infrared (night vision) for camera at host.
    """
    decoder_control(IO_OFF, host)


if (__name__ == '__main__'):
    import sys
    cmds = {
        'r': 'pan_right',
        'l': 'pan_left',
        'u': 'tilt_up',
        'd': 'tilt_down',
    }

    if len(sys.argv) > 1:
        action = sys.argv[1]
        if action in cmds:
            action = cmds[action]
        args = ""
        for a in sys.argv[2:]:
            args += "%s, " % a
        eval("%s(%s)" % (action, args))
    else:
        snapshot('foo.fakedomain.com')
