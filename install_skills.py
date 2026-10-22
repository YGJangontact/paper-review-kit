"""Copy the five sibling skills. Existing skills require --force; no hooks installed."""
import argparse
import shutil
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('--destination',type=Path,required=True);p.add_argument('--force',action='store_true');a=p.parse_args()
root=Path(__file__).resolve().parent
folders=list((root/'skills').iterdir())
conflicts=[x.name for x in folders if (a.destination/x.name).exists()]
if conflicts and not a.force:raise SystemExit('Existing skills: '+', '.join(conflicts)+'; inspect changes before --force')
for folder in folders:
    shutil.copytree(folder,a.destination/folder.name,dirs_exist_ok=a.force)
print('Installed five skill folders. Python tools remain in the cloned repository. Hooks not registered.')
