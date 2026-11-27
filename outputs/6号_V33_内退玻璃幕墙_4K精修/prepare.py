from pathlib import Path
from PIL import Image,ImageDraw
import json,shutil,hashlib
R=Path(__file__).resolve().parent
S=Path(r"C:/Users/WINDOWS/Desktop/氢能/氢能渲染/广州氢能_6号视角_宋式水院效果图_V33_檐下内退玻璃幕墙.png")
for d in ['sources','tiles_input','tiles_rendered','tiles_aligned','qa','prompts']:(R/d).mkdir(parents=True,exist_ok=True)
expected='5650bef7a44236a33914cdfe234d3fea6a6f94e96c59c2aceabdd27e501e63e3'
assert hashlib.sha256(S.read_bytes()).hexdigest()==expected
shutil.copy2(S,R/'V33_锁定母图.png')
q=Path(r'C:/Users/WINDOWS/Desktop/氢能/氢能渲染/6号视角_渲染标注')
for f in ['V33_交付输入与视觉自检记录.json','V33_内退玻璃幕墙局部.png','V33_上层挑檐内退玻璃幕墙提示词.txt']:shutil.copy2(q/f,R/'sources'/f)
im=Image.open(S).convert('RGB');assert im.size==(1714,918)
W,H=3840,round(3840*918/1714)
ts=[]; sheet=Image.new('RGB',(1120,580),'#181818');d=ImageDraw.Draw(sheet)
for row,y in enumerate([0,378]):
 for col,x in enumerate([0,384,770,1154]):
  n=f'{row*4+col+1:02d}_'+('upper' if row==0 else 'lower')+f'_{col+1}'
  b=[x,y,x+560,y+540];p=R/'tiles_input'/(n+'.png');im.crop(b).save(p)
  ts.append({'id':n,'box':b,'input':str(p),'output_box':[round(x*W/1714),round(y*H/918),round((x+560)*W/1714),round((y+540)*H/918)]})
  sheet.paste(im.crop(b).resize((280,270),Image.Resampling.LANCZOS),(col*280,row*290));d.text((col*280+8,row*290+273),n,fill='white')
sheet.save(R/'qa/tile_layout.jpg',quality=95)
m={'source':str(S),'source_sha256':expected,'source_size':[1714,918],'output_size':[W,H],'tile_size':[560,540],'tile_count':len(ts),'tiles':ts,'selection':'V33 ONLY. All older design directions superseded by V33.','geometry_policy':'Preserve the V33 image composition and newly added recessed glass; no geometry redesign.'}
(R/'manifest.json').write_text(json.dumps(m,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps({'output_size':m['output_size'],'tiles':[t['id'] for t in ts]}))

