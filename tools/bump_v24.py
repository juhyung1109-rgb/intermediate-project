import re

with open('web/index.html', 'r', encoding='utf-8') as f:
    html = f.read()

html = re.sub(r'(src="[^"]*\.js\?v=20261019_v)\d+', r'\g<1>24', html)

with open('web/index.html', 'w', encoding='utf-8') as f:
    f.write(html)

print("Bumped cache busters in index.html to v24!")
