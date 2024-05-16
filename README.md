# OAK-D-PoE-Camera-Container-Project
Script and Container configuration that connects to several Oak-D PoE Cameras and runs a HTTP Server which streams footage from the mono camera. 

1Gb/s Network Required For 60fps+, 100Mb/s will only allow 10-20fps

Recomend only one client connect to the http server at a time, as multiple clients will drastically affect the performance of the camera.

For this project, 
1. The containers where made from a customised Python image that have depthai packages installed
2. The containers are running on a Synology NAS using the container manager software
3. the HTTP streams are recorded with Synology Surveillance Station, which also offers playback and downloading of footage.
4. In Synology Surveillance Station each camera has 2000Gb of storage which is roughly 3 days of footage
