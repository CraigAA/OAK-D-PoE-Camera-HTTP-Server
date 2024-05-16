#!/usr/bin/env python3
import depthai as dai
import time
import sys

def run(ip,fps,focus):
    # Start defining a pipeline
    pipeline = dai.Pipeline()

    cam = pipeline.create(dai.node.MonoCamera)
    cam.setFps(fps)
    cam.setResolution(dai.MonoCameraProperties.SensorResolution.THE_720_P)
    cam.initialControl.setAutoFocusMode(dai.RawCameraControl.AutoFocusMode.OFF)
    cam.initialControl.setManualFocus(focus)
    cam.initialControl.setManualExposure(12000, 1200)

    # VideoEncoder
    jpeg = pipeline.create(dai.node.VideoEncoder)
    jpeg.setDefaultProfilePreset(fps, dai.VideoEncoderProperties.Profile.MJPEG)

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

        PORT = 8080

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
                    self.wfile.write(b'<h1>Filler Cam </h1><p>Click <a href="img">here</a> for an image</p>')
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
    cam.out.link(jpeg.input)
    jpeg.bitstream.link(script.inputs['jpeg'])

    device_info=dai.DeviceInfo(ip) # IP Address
    
    # Connect to device with pipeline
    with dai.Device(pipeline, device_info) as device:
        while not device.isClosed():
            time.sleep(1)
            
if __name__ == "__main__":
    ip=str(sys.argv[1])
    fps=int(sys.argv[2])
    focus=int(sys.argv[3])
    run(ip,fps,focus)