from pathlib import Path
from PIL import Image
import json,hashlib,zipfile
R=Path(__file__).resolve().parent
stem='6号_V33_内退玻璃幕墙_4K精修'
m=json.loads((R/'manifest.json').read_text(encoding='utf-8'))
s=json.loads((R/'stitch_report.json').read_text(encoding='utf-8'))
files=[]
for n in [stem+'.png',stem+'.jpg','6号_V33_幕墙檐底_100%局部.png','6号_V33_平台双座与景石_100%局部.png','6号_V33_100%接缝核验.jpg']:
 p=R/n
 with Image.open(p) as im:
  im.verify()
 with Image.open(p) as im:size=im.size
 files.append({'file':n,'size':size,'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()})
assert files[0]['size']==(3840,2057) and files[1]['size']==(3840,2057)
assert hashlib.sha256(Path(m['source']).read_bytes()).hexdigest()==m['source_sha256']
with zipfile.ZipFile(R/'V33_八区原始精修结果与提示词.zip','w',compression=zipfile.ZIP_STORED) as z:
 for p in sorted((R/'tiles_rendered').glob('*.png')):z.write(p,'tiles_rendered/'+p.name)
 for p in sorted((R/'prompts').glob('*.txt')):z.write(p,'prompts/'+p.name)
 for f in ['manifest.json','generated_sources.json','stitch_report.json']:z.write(R/f,f)
checks=[
 'V33母图哈希和原比例已验证，源图未覆盖。',
 '八区各自调用内置image_gen重建细节；原生生成像素合计12578450，全部大于相应输出分区。',
 '仅单一相似变换配准，未做局部光流形变；匹配点残差不是CAD几何验算。',
 '上层长瓦檐下幕墙内退、玻璃上方可见檐底、右端檐口挑出均可读。',
 '窗框与灯带、树干分叉、薄纱和瀑脚水雾的跨区接缝经100%局部检查，未发现明显断接。',
 '右平台保留贴室关系、同向直边低栏杆及转角；仅两独立短座和低几，未恢复长沙发或蒲团。',
 '右前高低两景石、根干及门口留空保留；石脚入水连续。',
 '左廊前后各一长两短，远组在两柱间；近中段错落石岸与远端低苔岸保留。',
 '统一曝光色温，保留灰蓝暮色、暖光、轻透全幅纱帘及灰白层次水雾。',
 '图像重建会产生叶片形状、玻璃反射和石纹的局部差异；未将结果表述为工程尺寸验证。'
]
report={'status':'delivered','date':'2026-11-26','method':'built-in image_gen, 8 overlapping reconstructed tiles, registered and blended','output_size':[3840,2057],'source_preserved':True,'files':files,'visual_checks':checks,'visible_residuals':['微观叶片、玻璃反射及石纹与母图存在重建差异。未见明显分区断接。'],'engineering_verification':False}
(R/'交付与接缝核验记录.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
text='V33 4K分区精修交付\n\n实际尺寸：3840 × 2057，保持1714:918原图比例（整数像素取整）。\n方式：内置 image_gen，八个重叠分区分别真实细节重建，再配准、统一曝光色温、选缝及多频段拼合。不是单纯插值放大。\n\n'+ '\n'.join(f'{i+1}. {t}' for i,t in enumerate(checks))+'\n\n源图、分区输入、原始生成、对齐结果、提示词、接缝掩膜与核验记录均保留在本目录。\n'
(R/'交付说明.txt').write_text(text,encoding='utf-8')
print(json.dumps({'verified_files':len(files),'output_size':[3840,2057],'zip_bytes':(R/'V33_八区原始精修结果与提示词.zip').stat().st_size,'source_preserved':True}))

