import sys
sys.stdout.reconfigure(encoding='utf-8')

with open('web/app.js', 'r', encoding='utf-8') as f:
    js = f.read()

idx = js.find('function renderQuickSamples')
idx2 = js.find('function ', idx + 20)
print(js[idx:idx2])
