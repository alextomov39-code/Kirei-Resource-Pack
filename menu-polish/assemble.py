import hashlib,json,zipfile,urllib.request
from pathlib import Path
base=Path('base.zip')
urllib.request.urlretrieve('https://github.com/alextomov39-code/Kirei-Resource-Pack/releases/download/leaderboardmenus2-engraved/Kirei-Leaderboard-Menus-Pack.zip',base)
assert hashlib.sha256(base.read_bytes()).hexdigest()=='ca76a03b7df658c27cfb8aac0d831c118cbcc336b12d7b3b2f5b49066d60a6de'
pack=Path('Kirei-Menu-Polish-Pack.zip')
with zipfile.ZipFile(base) as old,zipfile.ZipFile('menu-polish/delta.zip') as delta,zipfile.ZipFile(pack,'w',zipfile.ZIP_DEFLATED) as new:
 changes={n:delta.read(n) for n in delta.namelist()}
 for n in old.namelist():new.writestr(n,changes.get(n,old.read(n)))
 for n,data in changes.items():
  if n not in old.namelist():new.writestr(n,data)
with zipfile.ZipFile(base) as old,zipfile.ZipFile(pack) as new:
 assert new.testzip() is None and len(new.namelist())==len(set(new.namelist()))
 assert all(new.read(n)==old.read(n) for n in old.namelist() if n not in changes)
 assert all(new.read(n)==data for n,data in changes.items())
Path('menu-polish-checksums.json').write_text(json.dumps(dict(sha1=hashlib.sha1(pack.read_bytes()).hexdigest(),sha256=hashlib.sha256(pack.read_bytes()).hexdigest(),changed_entries=list(changes),unrelated_entries_preserved=True)))
