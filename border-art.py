"""Append the border art to each currently routed archive and keep the native packet matcher intact."""
import hashlib
import json
import os
import shutil
import subprocess
import zipfile
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from PIL import Image
import numpy as np

root=Path.cwd() if os.environ.get('GITHUB_ACTIONS') else Path(__file__).resolve().parents[2]
out=root/'work/honeycomb'
out.mkdir(exist_ok=True,parents=True)
repo='alextomov39-code/Kirei-Resource-Pack'
tag='dm-honeycomb-v3'
filename='KireiLegacyClientModels-1.0.0-paper26.3-227.jar'

def digest(p,algo):
    with p.open('rb') as f:return hashlib.file_digest(f,algo).hexdigest()

# One section-wide, section-high repeat in world units. Supersample a hard stroke once.
def paint():
    n=1024
    w=16/6
    pitch=16/4
    radius=pitch/3
    y,x=np.mgrid[:n,:n]
    x=(x+.5)*16/n
    y=(y+.5)*16/n
    d=np.full_like(x,99.)
    for row in range(-1,10):
        cy=row*pitch/2
        dx=(x-(row%2)*w/2+w/2)%w-w/2
        dy=y-cy
        vertices=[(0,-radius),(w/2,-radius/2),(w/2,radius/2),(0,radius),(-w/2,radius/2),(-w/2,-radius/2)]
        for (a,b),(c,e) in zip(vertices,vertices[1:]+vertices[:1]):
            u=c-a;v=e-b
            t=np.clip(((dx-a)*u+(dy-b)*v)/(u*u+v*v),0,1)
            d=np.minimum(d,np.hypot(dx-a-u*t,dy-b-v*t))
    # Hard stroke with a separate, low-opacity halo. Only pixel coverage
    # softens the stroke itself when the high-resolution tile is downsampled.
    ink=d < .052
    halo=np.clip(1-(d-.052)/.10,0,1)**2
    img=np.stack([np.where(ink,bright,base+lift*halo) for base,lift,bright in
                  [(155,75,255),(12,18,55),(30,14,58),(30,48,203)]],axis=-1).astype('uint8')
    p=out/'honeycomb.png'
    Image.fromarray(img).resize((256,256),Image.Resampling.BOX).save(p)
    return {'assets/kireiwalls/textures/font/dm_honeycomb.png':p.read_bytes(),
            'assets/kireiwalls/font/dm_honeycomb.json':json.dumps({'providers':[{'type':'bitmap','file':'kireiwalls:font/dm_honeycomb.png','ascent':7,'height':64,'chars':['\ue000']}]}).encode()}

def run(*a):return subprocess.check_output(a,text=True).strip()

def main():
    art=paint()
    routes=json.loads((root/'border-inputs.json').read_text()) if os.environ.get('GITHUB_ACTIONS') else json.loads(zipfile.ZipFile(root/'work/lunar263/game-router.jar').read('pack-routes.json'))
    def make(r):
        oldtag,name=r['url'].split('/download/')[1].split('/')
        old=out/name
        if not old.exists() or digest(old,'sha1')!=r['sha1']:run('gh','release','download',oldtag,'-R',repo,'-p',name,'-D',str(out),'--clobber')
        assert digest(old,'sha1')==r['sha1']
        new=out/f"Kirei-Honeycomb-format-{r['format']}.zip"
        shutil.copyfile(old,new)
        with zipfile.ZipFile(new,'a',zipfile.ZIP_DEFLATED) as z:
            assert all(k not in z.namelist() for k in art)
            for k,data in art.items():z.writestr(k,data)
        with zipfile.ZipFile(old) as s,zipfile.ZipFile(new) as z:
            assert {i.filename:(i.CRC,i.file_size) for i in s.infolist()}=={i.filename:(i.CRC,i.file_size) for i in z.infolist() if i.filename not in art}
            assert all(z.read(k)==v for k,v in art.items())
        r.update(url=f'https://github.com/{repo}/releases/download/{tag}/{new.name}',sha1=digest(new,'sha1'))
        return new
    with ThreadPoolExecutor(4) as pool: archives=list(pool.map(make,routes['routes']))
    run('gh','release','create',tag,'-R',repo,'--draft','--title','Deathmatch honeycomb','--notes','Connected border art embedded in each existing version-specific pack.')
    def upload(p):run('gh','release','upload',tag,str(p),'-R',repo)
    with ThreadPoolExecutor(4) as pool:list(pool.map(upload,archives))
    assets=json.loads(run('gh','release','view',tag,'-R',repo,'--json','assets'))['assets']
    assert {a['name']:a['digest'] for a in assets}=={p.name:'sha256:'+digest(p,'sha256') for p in archives}
    manifest=out/'border-routes.json'
    manifest.write_text(json.dumps(routes,indent=2))
    upload(manifest)
    run('gh','release','edit',tag,'-R',repo,'--draft=false','--latest=false')
    if os.environ.get('GITHUB_ACTIONS'):return
    routers(routes)

def routers(routes):
    for role in ['game','lobby']:
        dest=out/role; dest.mkdir(exist_ok=True)
        with zipfile.ZipFile(root/f'work/lunar263/{role}-router.jar') as src,zipfile.ZipFile(dest/filename,'w') as z:
            assert json.loads(src.read('pack-routes.json'))['native']==routes['native']
            for i in src.infolist():z.writestr(i,json.dumps(routes).encode() if i.filename=='pack-routes.json' else src.read(i))
    print('Verified 10 published packs and generated both routers.',flush=True)

if __name__=='__main__':main()
