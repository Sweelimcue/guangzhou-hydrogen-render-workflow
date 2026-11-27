from pathlib import Path
import json,shutil,hashlib
import numpy as np,cv2
from PIL import Image,ImageDraw,ImageCms
cv2.setNumThreads(8)
R=Path(__file__).resolve().parent
m=json.loads((R/'manifest.json').read_text(encoding='utf-8'))
src=np.array(Image.open(R/'V33_锁定母图.png').convert('RGB'))
W,H=m['output_size']; ref=cv2.resize(src,(W,H),interpolation=cv2.INTER_LANCZOS4)
paths={x['id']:x['path'] for x in json.loads((R/'generated_sources.json').read_text(encoding='utf-8'))}
ims=[];corners=[];reports=[];native=[]
def gray(x):
 return cv2.createCLAHE(clipLimit=1.4,tileGridSize=(8,8)).apply(cv2.cvtColor(x,cv2.COLOR_RGB2GRAY))
for t in m['tiles']:
 n=t['id']; p=R/'tiles_rendered'/(n+'.png');shutil.copy2(paths[n],p)
 g=np.array(Image.open(p).convert('RGB'));native.append(g)
 x,y,x2,y2=t['box'];X,Y,X2,Y2=t['output_box'];w,h=X2-X,Y2-Y
 norm=cv2.resize(g,(560,540),interpolation=cv2.INTER_AREA)
 sift=cv2.SIFT_create(nfeatures=8000,contrastThreshold=.01)
 ka,da=sift.detectAndCompute(gray(norm),None);kb,db=sift.detectAndCompute(gray(src[y:y2,x:x2]),None)
 good=[a for a,b in cv2.BFMatcher().knnMatch(da,db,k=2) if a.distance<.72*b.distance]
 pa=np.float32([ka[a.queryIdx].pt for a in good]);pb=np.float32([kb[a.trainIdx].pt for a in good])
 af,valid=cv2.estimateAffinePartial2D(pa,pb,method=cv2.RANSAC,ransacReprojThreshold=1.8,maxIters=10000)
 assert af is not None and valid.sum()>=15,(n,'insufficient registration')
 assert np.linalg.norm(af[:,:2]-np.eye(2))<.04 and np.linalg.norm(af[:,2])<12,(n,af)
 inv=cv2.invertAffineTransform(af);yy,xx=np.mgrid[0:h,0:w].astype(np.float32)
 qx=(xx+.5)*560/w-.5;qy=(yy+.5)*540/h-.5
 px=inv[0,0]*qx+inv[0,1]*qy+inv[0,2];py=inv[1,0]*qx+inv[1,1]*qy+inv[1,2]
 px=(px+.5)*g.shape[1]/560-.5;py=(py+.5)*g.shape[0]/540-.5
 aligned=cv2.remap(g,px.astype(np.float32),py.astype(np.float32),cv2.INTER_LANCZOS4,borderMode=cv2.BORDER_REFLECT_101)
 f=aligned.astype(np.float32);delta=cv2.GaussianBlur(ref[Y:Y2,X:X2].astype(np.float32)-f,(0,0),48)
 corrected=np.clip(f+.85*np.clip(delta,-38,38),0,255).astype(np.uint8)
 Image.fromarray(corrected).save(R/'tiles_aligned'/(n+'.png'))
 pred=pa@af[:,:2].T+af[:,2];err=np.linalg.norm(pred-pb,axis=1)[valid.ravel()>0]
 rr={'id':n,'native_size':[g.shape[1],g.shape[0]],'output_size':[w,h],'matches':len(good),'inliers':int(valid.sum()),'median_registration_error_source_px':float(np.median(err)),'p95_registration_error_source_px':float(np.percentile(err,95)),'similarity_transform':af.tolist(),'nonrigid_warp':False,'output_box':t['output_box'],'sha256':hashlib.sha256(p.read_bytes()).hexdigest()}
 reports.append(rr);ims.append(corrected);corners.append((X,Y))
 print(json.dumps(rr),flush=True)
contact=Image.new('RGB',(1280,660),'#181818');d=ImageDraw.Draw(contact)
for i,g in enumerate(native):
 contact.paste(Image.fromarray(g).resize((320,309),Image.Resampling.LANCZOS),((i%4)*320,(i//4)*330));d.text(((i%4)*320+8,(i//4)*330+313),m['tiles'][i]['id'],fill='white')
contact.save(R/'qa/八区生成原图总览.jpg',quality=95)
scale=.5
sm=[cv2.UMat(cv2.resize(im,None,fx=scale,fy=scale,interpolation=cv2.INTER_AREA).astype(np.float32)) for im in ims]
sc=[(round(x*scale),round(y*scale)) for x,y in corners]
# Keep the complete recessed glazing and the platform seats within a single rendered tile.
protected=[(2,(784,92,1136,206)),(7,(1165,562,1598,732))]
masks=[]
for i,im in enumerate(sm):
 mask=np.full(im.get().shape[:2],255,np.uint8);xx,yy=sc[i]
 for owner,b in protected:
  if owner==i:continue
  a,c,e,f=[round(b[0]*W/1714*scale),round(b[1]*H/918*scale),round(b[2]*W/1714*scale),round(b[3]*H/918*scale)]
  xa,ya=max(0,a-xx),max(0,c-yy);xb,yb=min(mask.shape[1],e-xx),min(mask.shape[0],f-yy)
  if xb>xa and yb>ya:mask[ya:yb,xa:xb]=0
 masks.append(cv2.UMat(mask))
cv2.detail_GraphCutSeamFinder('COST_COLOR_GRAD').find(sm,sc,masks)
blend=cv2.detail_MultiBandBlender();blend.setNumBands(5);blend.prepare((0,0,W,H))
coverage=np.zeros((H,W),np.uint8);seams=np.zeros_like(coverage)
for i,(im,(x,y),mm) in enumerate(zip(ims,corners,masks)):
 mask=cv2.resize(mm.get(),(im.shape[1],im.shape[0]),interpolation=cv2.INTER_NEAREST)
 mask=cv2.dilate(mask,np.ones((7,7),np.uint8));Image.fromarray(mask).save(R/'qa'/f'seam_mask_{i+1:02d}.png')
 blend.feed(im.astype(np.int16),mask,(x,y));coverage[y:y+im.shape[0],x:x+im.shape[1]]|=mask
 cs,_=cv2.findContours(mask,cv2.RETR_EXTERNAL,cv2.CHAIN_APPROX_SIMPLE)
 cv2.drawContours(seams[y:y+im.shape[0],x:x+im.shape[1]],cs,-1,255,2)
result,_=blend.blend(None,None);result=np.clip(result,0,255).astype(np.uint8)
assert np.all(coverage>0);assert result.shape==(H,W,3)
out=Image.fromarray(result);icc=ImageCms.ImageCmsProfile(ImageCms.createProfile('sRGB')).tobytes()
stem='6号_V33_内退玻璃幕墙_4K精修'
out.save(R/(stem+'.png'),icc_profile=icc);out.save(R/(stem+'.jpg'),quality=97,subsampling=0,icc_profile=icc)
out.resize((1920,round(H/2)),Image.Resampling.LANCZOS).save(R/'preview.jpg',quality=95)
v=result.copy();v[seams>0]=(255,70,130)
Image.fromarray(v).resize((1920,round(H/2)),Image.Resampling.LANCZOS).save(R/'qa/接缝位置图.jpg',quality=95)
# These deliverables are native 100% crops of the 4K output, not enlargements.
def crop_scaled(box,name):
 b=tuple(round(z*(W/1714 if j%2==0 else H/918)) for j,z in enumerate(box))
 out.crop(b).save(R/(name+'.png'),icc_profile=icc);return b
crop_scaled((775,82,1140,280),'6号_V33_幕墙檐底_100%局部')
crop_scaled((1115,525,1714,830),'6号_V33_平台双座与景石_100%局部')
detail_boxes=[(1710,180,2478,756),(2800,400,3568,976),(2310,800,3078,1376),(50,1050,818,1626),(850,1020,1618,1596),(3000,1280,3768,1856)]
labels=['RECESSED GLASS / EAVE / WATERFALL','TREE FORKS / LEAF VEINS','MULLIONS / SHEER CURTAINS','NEAR LOUNGE / CANE / FABRIC','FAR LOUNGE / COLUMN / SHORE','PLATFORM / TWO SEATS / STONES']
sheet=Image.new('RGB',(2304,1192),'#181818');dr=ImageDraw.Draw(sheet)
for i,(b,l) in enumerate(zip(detail_boxes,labels)):
 x=(i%3)*768;y=(i//3)*596;sheet.paste(out.crop(b),(x,y));dr.text((x+8,y+579),l+' - 100%',fill='white')
sheet.save(R/'6号_V33_100%细节.jpg',quality=97,subsampling=0)
boxes=[(1740,270,2300,570),(3000,800,3560,1100),(850,1050,1410,1350),(2550,1270,3110,1570)]
comp=Image.new('RGB',(1120,1280),'#181818');dr=ImageDraw.Draw(comp);ri=Image.fromarray(ref)
for i,b in enumerate(boxes):
 y=i*320;comp.paste(ri.crop(b),(0,y));comp.paste(out.crop(b),(560,y))
 dr.text((8,y+303),'V33 SOURCE - SAME OUTPUT SCALE',fill='white');dr.text((568,y+303),'AI DETAIL RECONSTRUCTION - 100%',fill='white')
comp.save(R/'6号_V33_100%原图与精修对照.jpg',quality=97,subsampling=0)
ov=Image.new('RGB',(1714,1876),'#181818');dr=ImageDraw.Draw(ov)
ov.paste(Image.fromarray(src),(0,0));ov.paste(out.resize((1714,918),Image.Resampling.LANCZOS),(0,938))
dr.text((8,922),'LOCKED V33 SOURCE',fill='white');dr.text((8,1860),'8-TILE DETAIL RECONSTRUCTION - 3840 x 2057',fill='white')
ov.save(R/'qa/V33母图与精修全景对照.jpg',quality=96)
report={'source_sha256':m['source_sha256'],'source_size':m['source_size'],'output_size':[W,H],'tile_count':8,'total_generated_pixels':sum(r['native_size'][0]*r['native_size'][1] for r in reports),'all_tiles_at_least_target_size':all(r['native_size'][0]>=r['output_size'][0] and r['native_size'][1]>=r['output_size'][1] for r in reports),'coverage_percent':float((coverage>0).mean()*100),'method':'Eight independent built-in image_gen detail reconstructions. Single similarity registration per tile, low-frequency exposure and color matching to V33, graph-cut seam choice and multiband blend. No optical-flow / nonrigid warping.','protected_regions':protected,'tiles':reports,'final_png_sha256':hashlib.sha256((R/(stem+'.png')).read_bytes()).hexdigest()}
(R/'stitch_report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps({k:report[k] for k in ['output_size','tile_count','total_generated_pixels','all_tiles_at_least_target_size','coverage_percent']}),flush=True)

