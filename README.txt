SMART ROAD SURVEILLANCE SYSTEM - GITHUB FRONTEND

This version is made with HTML, CSS and JavaScript so it can be opened directly
in Chrome and hosted on GitHub Pages.

FILES
- index.html : main website
- css/style.css : complete frontend styling
- js/script.js : local file preview
- images/ : keep your project images here if needed

IMPORTANT LIMITATION
GitHub Pages/Chrome can run HTML, CSS and JavaScript, but they cannot directly
execute your Python OpenCV/PyTorch YOLO code.

Therefore this frontend provides the browser UI and local upload/preview.
The actual Python detection code from the original project (TrafficRuleDetector,
models, utils, best.pt, etc.) needs a backend/server such as Flask to perform
real helmet detection and car counting.

The original Home.py confirms that the desktop application calls
TrafficRuleDetector for video detection and TrafficRuleDetectorImg for image
detection. The Detection screen displays helmet status, plate status, plate
number and passenger count.

For a GitHub project/demo, this frontend is suitable as the public website.
For REAL live detection from uploaded videos, a backend deployment is required.
