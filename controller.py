import socket
from steering_acceleration import STEER, ACCEL
import time
import math
last_tap_time = 0
DOUBLE_TAP_THRESHOLD = 0.5  # Time in seconds between taps to consider it a double tap
STEER_THRES = 0.4
ACCEL_THRES = 0.4
STEER_ANGLE_THRES = 20
ACCEL_ANGLE_THRES = 15
ACCEL_ANGLE_OFFSET = -50
class Controller:

    def __init__(self, address):
        self.current_steering = STEER.NEUTRAL
        self.current_accel = ACCEL.NEUTRAL
        self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.address = address
        self.last_tap_time = 0
        self.tap_count = 0
        self.last_shake_time = 0
        self.last_accel = (0, 0, 0)
        self.shake_threshold = 15  # Ajustez cette valeur selon la sensibilité souhaitée
        self.shake_interval = 0.5  # Temps minimum entre deux secousses détectées


    def send_data(self, data):
        if len(data) > 0:
            self.client_socket.sendto(data, self.address)


    def callback_x(self, *values):
        print("got values for x: {}".format(values))
        data = b''
        acceleration = ACCEL.NEUTRAL

        if values[0] < -STEER_THRES:
            acceleration = ACCEL.DOWN
        elif values[0] > STEER_THRES:
            acceleration = ACCEL.UP

        if self.current_accel != ACCEL.NEUTRAL and acceleration == ACCEL.NEUTRAL:
            if self.current_accel == ACCEL.UP:
                data = b'R_UP'
            elif self.current_accel == ACCEL.DOWN:
                data = b'R_DOWN'

        if self.current_accel == ACCEL.NEUTRAL and acceleration != ACCEL.NEUTRAL:
            if acceleration == ACCEL.UP:
                data = b'P_UP'
            elif acceleration == ACCEL.DOWN:
                data = b'P_DOWN'

        self.send_data(data)
        self.current_accel = acceleration



    def callback_y(self, *values):
        print("got values for y: {}".format(values))
        data = b''
        steering = STEER.NEUTRAL

        if values[0] < -ACCEL_THRES:
            steering = STEER.LEFT
        elif values[0] > ACCEL_THRES:
            steering = STEER.RIGHT

        if self.current_steering != STEER.NEUTRAL and steering == STEER.NEUTRAL:
            if self.current_steering == STEER.LEFT:
                data = b'R_LEFT'
            elif self.current_steering == STEER.RIGHT:
                data = b'R_RIGHT'

        if self.current_steering == STEER.NEUTRAL and steering != STEER.NEUTRAL:
            if steering == STEER.LEFT:
                data = b'P_LEFT'
            elif steering == STEER.RIGHT:
                data = b'P_RIGHT'

        self.send_data(data)
        self.current_steering = steering



    def callback_touchUP(self, *values):
        
        data = b''

        if self.current_accel != ACCEL.NEUTRAL:
            if self.current_accel == ACCEL.UP:
                data = b'R_UP'
            elif self.current_accel == ACCEL.DOWN:
                data = b'R_DOWN'
        
        if self.current_steering != STEER.NEUTRAL:
            if self.current_steering == STEER.LEFT:
                data = b'R_LEFT'
            elif self.current_steering == STEER.RIGHT:
                data = b'R_RIGHT'

        self.send_data(data)
        
    def process_steering(self,steering):
        
        

        data = b''

        if self.current_steering != STEER.NEUTRAL and steering == STEER.NEUTRAL:
            if self.current_steering == STEER.LEFT:
                data = b'R_LEFT'
            elif self.current_steering == STEER.RIGHT:
                data = b'R_RIGHT'

        if self.current_steering == STEER.NEUTRAL and steering != STEER.NEUTRAL:
            if steering == STEER.LEFT:
                data = b'P_LEFT'
            elif steering == STEER.RIGHT:
                data = b'P_RIGHT'

        if len(data) > 0:
            self.send_data(data)

        self.current_steering = steering

    def process_acceleration(self,acceleration):
        data = b''

        

        if self.current_accel != ACCEL.NEUTRAL and acceleration == ACCEL.NEUTRAL:
            if self.current_accel == ACCEL.UP:
                data = b'R_UP'
            elif self.current_accel == ACCEL.DOWN:
                data = b'R_DOWN'



        if self.current_accel == ACCEL.NEUTRAL and acceleration != ACCEL.NEUTRAL:
            if acceleration == ACCEL.UP:
                data = b'P_UP'
            elif acceleration == ACCEL.DOWN:
                data = b'P_DOWN'

        if len(data) > 0:
            self.send_data(data)

        self.current_accel = acceleration


    def callback_yaw(self,*values):
        steering = STEER.NEUTRAL

        angle = values[0]

        if angle < - STEER_ANGLE_THRES:
            steering = STEER.RIGHT
        elif angle > STEER_ANGLE_THRES:
            steering = STEER.LEFT

        self.process_steering(steering)

   
    # Roll will control the acceleration
    def callback_roll(self,*values):
        angle = values[0]

        acceleration = ACCEL.NEUTRAL

        if angle < ACCEL_ANGLE_OFFSET - ACCEL_ANGLE_THRES:
            acceleration = ACCEL.DOWN
        elif angle > ACCEL_ANGLE_OFFSET + ACCEL_ANGLE_THRES:
            acceleration = ACCEL.UP

        self.process_acceleration(acceleration)
    def callback_pitch(*values):
        return
    def callback_double_tap(self, *args):
        print(f"Touch callback called with args: {args}")
        current_time = time.time()
        
        if args and args[0] > 0:  # If touch count is greater than 0
            if (current_time - self.last_tap_time) < DOUBLE_TAP_THRESHOLD:
                self.tap_count += 1
                if self.tap_count == 2:
                    print("Double tap detected! Sending FIRE command.")
                    self.send_data(b'FIRE')
                    self.tap_count = 0
            else:
                self.tap_count = 1
            
            self.last_tap_time = current_time
        else:
            # Reset tap count if touch ended
            self.tap_count = 0
    def callback_accelerometer(self, *values):
        print(f"Accelerometer callback called with values: {values}")
        current_time = time.time()
        
        if len(values) >= 1:
            x = values[0]  # Nous n'utilisons que la valeur de l'axe x
            delta_accel = math.fabs(x - self.last_accel)
            
            if delta_accel > self.shake_threshold:
                if current_time - self.last_shake_time > self.shake_interval:
                    print("Shake detected! Sending RESCUE command.")
                    self.send_data(b'RESCUE')
                    self.last_shake_time = current_time
            
            self.last_accel = x