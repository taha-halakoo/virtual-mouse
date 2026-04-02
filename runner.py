import subprocess
import time

p = subprocess.Popen(['python', 'main.py'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
time.sleep(3)
if p.poll() is None:
    p.kill()
    print("Process killed after 3 seconds.")
else:
    print("Process exited with code", p.returncode)
out, err = p.communicate()
print("STDOUT:")
print(out.decode('utf-8', errors='replace'))
print("STDERR:")
print(err.decode('utf-8', errors='replace'))
