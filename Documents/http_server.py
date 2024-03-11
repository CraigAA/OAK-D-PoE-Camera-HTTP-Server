#!/usr/bin/env python3

import depthai as dai
import time
import cv2

# Start defining a pipeline
pipeline = dai.Pipeline()

# Define a source - color camera
cam = pipeline.create(dai.node.ColorCamera)

#Set FPS and Resolution
cam.setFps(60)
cam.setResolution(dai.ColorCameraProperties.SensorResolution.THE_1080_P)

#Auto-focus OFF and Auto Exposure OFF as this appication will be require it
cam.initialControl.setAutoFocusMode(dai.RawCameraControl.AutoFocusMode.OFF)
cam.initialControl.setManualFocus(120)
cam.initialControl.setManualExposure(20000, 1200)
print('60fps focus: 120 Exposure 20000us, 1200 ISO')
# VideoEncoder
jpeg = pipeline.create(dai.node.VideoEncoder)
jpeg.setDefaultProfilePreset(60, dai.VideoEncoderProperties.Profile.MJPEG)


# Script node
script = pipeline.create(dai.node.Script)
script.setProcessor(dai.ProcessorType.LEON_CSS)
script.setScript("""
    import time
    import socket
    import fcntl
    import struct
    from socketserver import ThreadingMixIn
    from http.server import BaseHTTPRequestHandler, HTTPServer

    PORT = 8081

    def get_ip_address(ifname):
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        return socket.inet_ntoa(fcntl.ioctl(
            s.fileno(),
            -1071617759,  # SIOCGIFADDR
            struct.pack('256s', ifname[:15].encode())
        )[20:24])

    class ThreadingSimpleServer(ThreadingMixIn, HTTPServer):
        pass

    class HTTPHandler(BaseHTTPRequestHandler):
        def do_GET(self):
            if self.path == '/':
                self.send_response(200)
                fpsCounter = 0
                timeCounter = time.time()
                while True:
                    jpegImage = node.io['jpeg'].get()
                    fpsCounter = fpsCounter + 1
                    if time.time() - timeCounter > 1:
                        fpsCounter = 0
                        timeCounter = time.time()
                self.wfile.write(b'<h1>Filler Cam:FPS '+str(fpsCounter)+'</h1><p>Click <a href="img">here</a> for an image</p>')
                self.end_headers()
            elif self.path == '/img':
                try:
                    self.send_response(200)
                    self.send_header('Content-type', 'multipart/x-mixed-replace; boundary=--jpgboundary')
                    self.end_headers()
                    fpsCounter = 0
                    timeCounter = time.time()
                    while True:
                        jpegImage = node.io['jpeg'].get()
                        self.wfile.write("--jpgboundary".encode())
                        self.wfile.write(bytes([13, 10]))
                        self.send_header('Content-type', 'image/jpeg')
                        self.send_header('Content-length', str(len(jpegImage.getData())))
                        self.end_headers()
                        self.wfile.write(jpegImage.getData())
                        self.end_headers()

                        fpsCounter = fpsCounter + 1
                        if time.time() - timeCounter > 1:
                            node.warn(f'FPS: {fpsCounter}')
                            fpsCounter = 0
                            timeCounter = time.time()
                except Exception as ex:
                    node.warn(str(ex))
            

    with ThreadingSimpleServer(("", PORT), HTTPHandler) as httpd:
        node.warn(f"Serving at {get_ip_address('re0')}:{PORT}")
        httpd.serve_forever()
""")

# Connections
cam.video.link(jpeg.input)
jpeg.bitstream.link(script.inputs['jpeg'])
  
#DAP file allows the script to be saved as a package that can be flashed to the Camera and run automatically on power up of the OAK-D
dai.DeviceBootloader.saveDepthaiApplicationPackage(
    './Filler_Cam2.dap', # Where to save the .dap file
    pipeline, # My pipeline
    compress=True, # Compress the FW and assets. In my case, it went from 24MB -> 9.5MB
    applicationName='myAppName' # Optional, so you know which app is flashed afterwards
  )

# Connect to device with pipeline
with dai.Device(pipeline) as device:
    while not device.isClosed():
        cam.setFps(60)
        time.sleep(1)