import hashlib,json,zipfile,sys,shutil
from pathlib import Path
def build(source,target):
    with source.open('rb') as f: assert hashlib.file_digest(f,'sha1').hexdigest()=='a9be3c95618a8f66333c5a1b30834f1bc28bb996'
    shutil.copyfile(source,target)
    with zipfile.ZipFile(target,'a') as z:
        bad=[i for i in z.infolist() if '/shaders/' in i.filename]
        assert len(bad)==9 and all(i.filename.startswith('client_26_3/assets/minecraft/shaders/') for i in bad)
        for i in bad:z.filelist.remove(i);del z.NameToInfo[i.filename]
        z.comment=b'Kirei 26.3 native shaders'
    with zipfile.ZipFile(target) as z,zipfile.ZipFile(source) as original:
        assert z.testzip() is None and len(original.infolist())-len(z.infolist())==9
        for i in z.infolist():assert i.CRC==original.getinfo(i.filename).CRC
        assert not any('/shaders/' in n for n in z.namelist())
    with target.open('rb') as f:print(hashlib.file_digest(f,'sha1').hexdigest())
if __name__=='__main__':build(Path(sys.argv[1]),Path(sys.argv[2]))
