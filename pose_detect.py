import numpy as np
from picamzero import Camera
import cv2
import time
from filter import streamingEMA

OBJ_WIDTH = 10.25
OBJ_HEIGHT = 20.22

object_points_3d = np.array([
    [-OBJ_WIDTH / 2, -OBJ_HEIGHT / 2, 0],
    [ OBJ_WIDTH / 2, -OBJ_HEIGHT / 2, 0],
    [ OBJ_WIDTH / 2,  OBJ_HEIGHT / 2, 0],
    [-OBJ_WIDTH / 2,  OBJ_HEIGHT / 2, 0]
], dtype=np.float32)
camera_matrix = np.array([[830.70889398,   0,         288.25543202],
 [  0,         827.52441464, 280.22826694],
 [  0,           0,           1        ]], dtype=np.float32)
dist_coeffs = np.array([[ 2.50027365e-03, -4.29831767e-01,  2.33628640e-02, -1.45787864e-02,
  -6.59582794e+00]],dtype=np.float32)
ema = streamingEMA(alpha=0.2)


def nothing(x):
    pass

# 2. Setup Raspberry pi camera
cam = Camera()
native_cam = cam.pc2
native_cam.stop()
# 2.1 Configure the resolution of cam
config = native_cam.create_video_configuration(
    main={"size": (640, 480)},
    controls={"FrameRate": 30}  # Force the camera hardware to aim for 60 FPS
)
native_cam.configure(config)
native_cam.start()
time.sleep(5)

#cap = cv2.VideoCapture(0,cv2.CAP_V4L2)

print("Press 'q' to quit.")

cv2.namedWindow("tuning")

cv2.createTrackbar("Lower H","tuning", 0,255, nothing)
cv2.createTrackbar("Lower S","tuning", 0,255, nothing)
cv2.createTrackbar("Lower V","tuning", 0,255, nothing)
cv2.createTrackbar("Upper H","tuning", 0,255, nothing)
cv2.createTrackbar("Upper S","tuning", 0,255, nothing)
cv2.createTrackbar("Upper V","tuning", 0,255, nothing)

cv2.setTrackbarPos("Lower H","tuning",41)
cv2.setTrackbarPos("Lower S","tuning",51)
cv2.setTrackbarPos("Lower V","tuning",51)

cv2.setTrackbarPos("Upper H","tuning",102)
cv2.setTrackbarPos("Upper S","tuning",255)
cv2.setTrackbarPos("Upper V","tuning",255)
prev_center = None
MAX_DISTANCE = 100

while True:
    frame = native_cam.capture_array()
    hsv_frame = cv2.cvtColor(frame, cv2.COLOR_RGB2HSV)
    h_min = cv2.getTrackbarPos("Lower H","tuning")
    s_min = cv2.getTrackbarPos("Lower S","tuning")
    v_min = cv2.getTrackbarPos("Lower V","tuning")

    h_max = cv2.getTrackbarPos("Upper H","tuning")
    s_max = cv2.getTrackbarPos("Upper S","tuning")
    v_max = cv2.getTrackbarPos("Upper V","tuning")
    lower_green = np.array([h_min,s_min,v_min])
    uper_green = np.array([h_max,s_max,v_max])
    blur_h = cv2.GaussianBlur(hsv_frame,(5,5),0)
    kernel = np.ones((7,7),np.uint8)
    green_mask_h = cv2.inRange(hsv_frame,lower_green,uper_green)
    green_mask_h = cv2.morphologyEx(green_mask_h,cv2.MORPH_CLOSE,kernel)
    green_mask_h = cv2.morphologyEx(green_mask_h,cv2.MORPH_OPEN,kernel)
    edges = cv2.Canny(green_mask_h,100,200)
    contours, hierarchy = cv2.findContours(edges, cv2.RETR_TREE, cv2.CHAIN_APPROX_NONE)
    draw_pic = frame.copy()
    if contours:
        max_contours = max(contours, key=cv2.contourArea)
        max_a = cv2.contourArea(max_contours)
        if max_a > 550:
            rect = cv2.minAreaRect(max_contours)
            box_2d = cv2.boxPoints(rect).astype(np.float32)
            x,y,w,h = cv2.boundingRect(max_contours)
            img_moment = cv2.moments(max_contours)
            # centroid x,y
            current_center = (int(img_moment["m10"]/img_moment["m00"]), int(img_moment["m01"]/img_moment["m00"]))
            if prev_center is not None:
                distance = np.sqrt(((current_center[0] - prev_center[0])**2) + ((current_center[1] - current_center[1]) ** 2))
                if distance < MAX_DISTANCE:
                    success, rvec, tvec = cv2.solvePnP(object_points_3d, box_2d, camera_matrix, dist_coeffs)
                    if success:
                        # Convert rotation vector to 3x3 rotation matrix
                        R, _ = cv2.Rodrigues(rvec)
                        tx,ty,tz = tvec.flatten()
                        distance_mm = np.sqrt(tx**2 + ty**2 + tz**2)
                        smoothen_distance = ema.update(distance_mm)
                        # Calculate pitch angle (rotation around X-axis / pitch in X-Z plane)
                        pitch_rad = np.arctan2(R[2, 1], R[2, 2])
                        pitch_deg = np.degrees(pitch_rad)
                
                        cv2.putText(
                            draw_pic,
                            f"Exact Pitch: {pitch_deg:.1f} deg",
                            (int(rect[0][0]) - 50, int(rect[0][1]) - 10),
                            cv2.FONT_HERSHEY_SIMPLEX,
                            0.5,
                            (0, 255, 0),
                            2
                        )
                        cv2.putText(
                            draw_pic,
                            f"Distance from cam: {smoothen_distance:.1f} mm.",
                            (int(rect[0][0]) - 50, int(rect[0][1]) - 25),
                            cv2.FONT_HERSHEY_SIMPLEX,
                            0.5,
                            (0, 255, 0),
                            2
                        )
                    #cv2.putText(draw_pic, "Same Object Tracked", (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 0, 0), 3)
                    cv2.rectangle(draw_pic, (x, y), (x + w, y + h), (255, 0, 0), 2)
                else:
                    cv2.putText(draw_pic, "New Object Detected!", (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2)
                    cv2.rectangle(draw_pic, (x, y), (x + w, y + h), (0, 0, 255), 2)
            prev_center = current_center
            cv2.drawContours(draw_pic,[max_contours],-1,(255,0,0),3)
    fil_img_h = cv2.bitwise_and(frame,frame,mask=green_mask_h)
    cv2.imshow("Cam feed",frame)
    cv2.imshow("Filter h", fil_img_h)
    cv2.imshow("Contours",draw_pic)
    # Keyboard controls
    key = cv2.waitKey(1) & 0xFF
    
    if key == ord('q'):
        print("Calibrated hsv value...........")
        print("Lower bounds: [h(0-179) s(0-255) v(0-255)] ; Upper bounds [h(0-179) s(0-255) v(0-255)]")
        print(f"Lower bounds: {lower_green} ; Upper bounds: {uper_green}")
        break

# Clean up windows and camera resources
native_cam.stop()
cv2.destroyAllWindows()


