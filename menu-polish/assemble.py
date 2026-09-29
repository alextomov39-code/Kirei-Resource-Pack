import hashlib,json,zipfile,urllib.request
from pathlib import Path
base=Path('base.zip')
urllib.request.urlretrieve('https://github.com/alextomov39-code/Kirei-Resource-Pack/releases/download/sharkskins1/Kirei-Shark-Skins1-match-Pack.zip',base)
assert hashlib.sha256(base.read_bytes()).hexdigest()=='657be97c9b498a71e2c52f346e49c920191f9a922c841fdeb0349ec647e10f68'
pack=Path('Kirei-Phoenix-Update-Pack.zip')
with zipfile.ZipFile(base) as old,zipfile.ZipFile('menu-polish/delta.zip') as delta,zipfile.ZipFile(pack,'w',zipfile.ZIP_DEFLATED) as new:
 changes={n:delta.read(n) for n in delta.namelist()}
 for info in old.infolist():new.writestr(info,changes.get(info.filename,old.read(info.filename)))
 for n,data in changes.items():
  if n not in old.namelist():new.writestr(delta.getinfo(n),data)
with zipfile.ZipFile(base) as old,zipfile.ZipFile(pack) as new:
 assert new.testzip() is None and len(new.namelist())==len(set(new.namelist()))
 assert all(new.read(n)==old.read(n) for n in old.namelist() if n not in changes)
 assert all(new.read(n)==data for n,data in changes.items())
Path('phoenix-checksums.json').write_text(json.dumps(dict(sha1=hashlib.sha1(pack.read_bytes()).hexdigest(),sha256=hashlib.sha256(pack.read_bytes()).hexdigest(),changed_entries=list(changes),unrelated_entries_preserved=True)))
