p = r'C:\Users\charles\workspace\becompare\tools\test_regressions.py'
L = open(p, encoding='utf-8').read().replace('\r\n', '\n').split('\n')
# lines index: 4,5 (0-based) are the broken imports; 13,14 the broken regex
L[4] = 'from pathlib import Path'
L[5] = 'import re'
i = next(k for k, l in enumerate(L) if l.startswith('    opt = re.search('))
L[i] = '    opt = re.search(r"\\$optional = ([^\\r\\n]+)", text).group(1)'
del L[i + 1]
open(p, 'w', encoding='utf-8', newline='\n').write('\n'.join(L))
