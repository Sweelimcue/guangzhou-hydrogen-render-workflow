from pathlib import Path
from PIL import Image,ImageDraw
import json
R=Path(__file__).resolve().parent
im=Image.open(R/'6号_V33_内退玻璃幕墙_4K精修.png')
boxes=[(2300,760,3100,1080),(3040,720,3840,1040),(600,750,1400,1070),(1400,780,2200,1100),(2420,1300,3220,1620),(600,1080,1400,1400)]
names=['CURTAIN / MULLIONS / LIGHT SEAM','RIGHT TREE TRUNK SEAM','LEFT COLUMN / SOFFIT SEAM','CENTRE TREE / WATERFALL SEAM','PLATFORM RAIL / STONE SEAM','LOUNGE / COLUMN SEAM']
out=Image.new('RGB',(1600,1020),'#181818');d=ImageDraw.Draw(out)
for i,(box,n) in enumerate(zip(boxes,names)):
 x=i%2*800;y=i//2*340;out.paste(im.crop(box),(x,y));d.text((x+8,y+323),n+' - 100%',fill='white')
out.save(R/'6号_V33_100%接缝核验.jpg',quality=97,subsampling=0)
print(im.size)

