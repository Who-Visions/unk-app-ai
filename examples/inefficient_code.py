--- a/examples/inefficient_code.py
+++ b/examples/inefficient_code.py
@@ -1,14 +1,12 @@
-import time
-
-def process_data(data):
-    res = []
-    for i in range(len(data)):\
-        time.sleep(0.1) # Simulate slow processing
-        val = data[i]\n        if val % 2 == 0:\n            res.append(str(val) + \" is even\")\n        else:\n            res.append(str(val) + \" is odd\")\n    return res\n\nd = [1, 2, 3, 4, 5]\nprint(process_data(d))\n
+from typing import List
+
+def process_data(data: List[int]) -> List[str]:
+    res = [f"{val} is even" if val % 2 == 0 else f"{val} is odd" for val in data]
+    return res
+
+d = [1, 2, 3, 4, 5]
+print(process_data(d))
+