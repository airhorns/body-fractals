from primesense import openni2

openni2.initialize()     # can also accept the path of the OpenNI redistribution

dev = openni2.Device.open_any()
print dev.get_sensor_info()

depth_stream = dev.create_depth_stream()
depth_stream.start()
frame = depth_stream.read_frame()
frame_data = frame.get_buffer_as_uint16()
depth_stream.stop()

openni2.unload()
