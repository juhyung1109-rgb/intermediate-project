with open('web/index.html', 'r', encoding='utf-8') as f:
    html = f.read()

target = '홈 &gt; <b>가상 결함 주입 및 배치 시뮬레이터 실험실</b>\n          </div>\n        </div>'
import re
bar_match = re.search(r'<!-- Card-Level Timeline Control Bar[\s\S]*?</div>\s*</div>\s*</div>', html)
if bar_match and target in html:
    bar_code = bar_match.group(0)
    html = html.replace(target, target + '\n' + bar_code, 1)
    with open('web/index.html', 'w', encoding='utf-8') as f:
        f.write(html)
    print('Successfully inserted timeline bar into view-sim!')
else:
    print('Could not find target or bar_match in html')
