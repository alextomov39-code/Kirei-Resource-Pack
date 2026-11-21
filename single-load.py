import hashlib,io,json,os,sys,urllib.request,zipfile
from pathlib import Path
from PIL import Image
fmt=sys.argv[1]
repo='https://github.com/alextomov39-code/Kirei-Resource-Pack/releases/download/'
manifest=json.loads(Path('pack-inputs.json').read_text())
def get(key,dest):
    url,digest=manifest[key]
    urllib.request.urlretrieve(repo+url,dest)
    with open(dest,'rb') as f: assert hashlib.file_digest(f,'sha1').hexdigest()==digest
def slim(data):
    im=Image.open(io.BytesIO(data))
    if im.mode not in ('RGB','RGBA') or im.info or im.width*im.height>4_194_304:return data
    pixels=im.convert('RGBA')
    colors=pixels.getcolors(256)
    if not colors:return data
    palette=sorted(c for _,c in colors)
    indices={c:i for i,c in enumerate(palette)}
    pal=Image.frombytes('P',im.size,bytes(indices[c] for c in pixels.getdata()))
    pal.putpalette(bytes(v for c in palette for v in c[:3]))
    if any(c[3]!=255 for c in palette):pal.info['transparency']=bytes(c[3] for c in palette)
    out=io.BytesIO();pal.save(out,format='PNG',optimize=True)
    candidate=out.getvalue()
    if len(candidate)>=len(data):return data
    assert Image.open(io.BytesIO(candidate)).convert('RGBA').tobytes()==pixels.tobytes()
    return candidate
get(fmt,'base.zip');get('addon','addon.zip')
name=f'Kirei-SingleLoad-format-{fmt}.zip'
with zipfile.ZipFile('base.zip') as base,zipfile.ZipFile('addon.zip') as addon,zipfile.ZipFile(name,'w',zipfile.ZIP_DEFLATED,compresslevel=6) as out:
    assets=set(addon.namelist())-{'pack.mcmeta'}
    assert not assets.intersection(base.namelist())
    for item in base.infolist():
        data=base.read(item)
        if item.filename.endswith('.png') and len(data)>64000:data=slim(data)
        out.writestr(item,data)
    for key in sorted(assets):out.writestr(key,addon.read(key))
with zipfile.ZipFile(name) as z,zipfile.ZipFile('base.zip') as base:
    assert z.testzip() is None and set(z.namelist())==set(base.namelist())|assets
with open(name,'rb') as f:digest=hashlib.file_digest(f,'sha1').hexdigest()
Path('hash-'+fmt+'.txt').write_text(digest)
print(f'{fmt}: {Path("base.zip").stat().st_size} -> {Path(name).stat().st_size}, SHA1 {digest}')
