import sys
sys.stdout.reconfigure(encoding='utf-8')

with open('web/app.js', 'r', encoding='utf-8') as f:
    js = f.read()

idx = js.find('const allMonthsMaster = [')
print(js[idx:idx+2500])
