# endoscopic_vision_disertation
A MSc. Dissertation project about image processing in endoscopic camera

**Table of Contents**

1. Introduction
2. System Requirements
3. Setting Up the Software
4. Adjusting HSV Thresholds
5. Understanding the Output
6. Troubleshooting

**Introduction**

This manual is designed to guide users through the process of using the microsurgical robot prototype's software for estimating distances from the camera lens to target objects, specifically the inner lid of a capsule painted green.

**System Requirements**

* Raspberry Pi camera
* Computer with Python 3.x installed
* Picamzero library installed

**Setting Up the Software**

1. Connect the Raspberry Pi camera to your Raspberry Pi.
2. Install the Picamzero library using pip: `pip install picamzero`
3. Install the openCV library using pip: `pip install opencv`
3. Run the software by executing the provided script.

**Adjusting HSV Thresholds**

The software allows users to adjust HSV thresholds manually using trackbars. The trackbars are labeled as follows:

* Lower H (0-179)
* Lower S (0-255)
* Lower V (0-255)
* Upper H (0-179)
* Upper S (0-255)
* Upper V (0-255)

To adjust the thresholds, move the sliders to the desired values. The software will update the output in real-time.

**Understanding the Output**

The software displays three windows:

1. Cam feed: The raw camera feed.
2. Filter h: The filtered image with the target object segmented out using HSV thresholding.
3. Contours: The contours of the target object, overlaid on the original image.

The software also prints the calibrated HSV values to the console when the user presses 'q'.

**Troubleshooting**

* If the camera fails to detect the green-painted capsule inner lid, try adjusting the HSV thresholds or increasing the camera resolution.
* If the camera feed freezes or becomes unresponsive, please restart the Raspberry Pi by pressing and holding the power button until it shuts down. This will reset the camera connection and allow you to continue using the software.
