from pathlib import Path
import sys,argparse
S=Path(__file__).parent
ns={'__file__':str(S/'build.py'),'__name__':'vp_tools'}
exec(compile((S/'build.py').read_bytes(),str(S/'build.py'),'exec'),ns)
exec(compile((S/'verify.py').read_bytes(),str(S/'verify.py'),'exec'),ns)
p=argparse.ArgumentParser();p.add_argument('duo');p.add_argument('--build',action='store_true');a=p.parse_args()
if a.build:ns['build'](a.duo)
ns['verify'](a.duo);ns['package'](a.duo)
