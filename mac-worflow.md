

got to Automator > workflow > Run Shell Script (and past both in seprate files after updating url and your device id )



# 1. Environment ko UTF-8 par force karein ClipX Push ✓
export LANG=en_US.UTF-8
export LC_ALL=en_US.UTF-8

# 2. Python ka use karke clipboard data ko JSON-safe banayein
# Isse indentation aur emojis dono preserve rahenge
JSON_DATA=$(pbpaste | python3 -c 'import sys, json; print(json.dumps({"content": sys.stdin.read()}, ensure_ascii=False))')

# 3. Direct curl call
curl -s -X POST https://your-hosting-url.com/v1/clips \
  -H "X-Device-Secret: your-device-id-from-admin-panel" \
  -H "Content-Type: application/json; charset=utf-8" \
  --data-raw "$JSON_DATA"

# 4. Success Notification
osascript -e "display notification \"↗️\" with title \"ClipX Push ✓\""







# 1. Environment clipx-pull
export LANG=en_US.UTF-8
export LC_ALL=en_US.UTF-8

cat > /tmp/clipx.py << 'EOF'
import json
import subprocess
import time
import urllib.request

from pynput.keyboard import Controller, Key

keyboard = Controller()

try:
    # API
    url = 'https://your-hosting-url.com/v1/clips?limit=1'

    req = urllib.request.Request(url)

    req.add_header(
        'X-Device-Secret',
        'your-device-id-from-admin-panel'
    )

    req.add_header(
        'User-Agent',
        'Mozilla/5.0'
    )

    with urllib.request.urlopen(req) as response:
        d = json.loads(
            response.read().decode('utf-8')
        )

    if d and len(d) > 0:

        content = d[0]['content']

        # Copy to clipboard
        subprocess.run(
            ['pbcopy'],
            input=content,
            text=True
        )

        # Small delay
        time.sleep(0.4)

        # LOW LEVEL CMD+V
        keyboard.press(Key.cmd)
        keyboard.press('v')

        keyboard.release('v')
        keyboard.release(Key.cmd)

        # Notification
        subprocess.run([
            'osascript',
            '-e',
            'display notification "Pulled & Pasted" with title "ClipX"'
        ])

    else:

        subprocess.run([
            'osascript',
            '-e',
            'display notification "No clips found" with title "ClipX"'
        ])

except Exception as e:

    safe_error = str(e).replace('\"', '\\\"')

    subprocess.run([
        'osascript',
        '-e',
        f'display notification "{safe_error}" with title "ClipX Error"'
    ])

    print(f'Error: {e}')

EOF

/opt/homebrew/opt/python@3.13/libexec/bin/python3 /tmp/clipx.py