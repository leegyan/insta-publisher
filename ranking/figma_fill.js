// 랭킹 이미지 1장(1080×1920)을 Figma 에 그린다. use_figma 의 code 로 넘긴다.
// 쓰는 법: 셋째 줄의 자료 자리(밑줄 두 개로 감싼 DATA)를 자료 JSON 으로 바꾼다(만드는법.md 2절의 형식). 결과로 프레임 id 를 돌려준다.
const D = __DATA__;
const fonts=[["Noto Sans KR","Bold"],["Noto Sans KR","Medium"],["Noto Sans KR","Regular"],["Black Han Sans","Regular"]];
for (const [family,style] of fonts) await figma.loadFontAsync({family,style});
const hex=h=>({r:parseInt(h.slice(1,3),16)/255,g:parseInt(h.slice(3,5),16)/255,b:parseInt(h.slice(5,7),16)/255});
const C={bg:'#17120E',panel:'#241C16',ink:'#FFF6EA',sub:'#B9A796',gold:'#FFB21E',silver:'#D9D9D9',bronze:'#D98A4E',accent:'#FF7A1A'};
const items=D.items; const N=items.length;
if (N<10||N>15) throw new Error('순위는 10~15개여야 함: '+N);
// 새 프레임은 페이지 맨 오른쪽 옆에 둔다
let maxX=0; for (const n of figma.currentPage.children) maxX=Math.max(maxX,n.x+n.width);
const root=figma.createFrame(); root.name='랭킹_'+D.slug; root.resize(1080,1920); root.x=maxX+200; root.y=100;
root.fills=[{type:'SOLID',color:hex(C.bg)}]; root.clipsContent=true;
function T(str,{x,y,size,family='Noto Sans KR',style='Bold',color=C.ink,w=null,align='LEFT',lh=null,maxW=null}){
  const t=figma.createText(); t.fontName={family,style}; t.characters=str; t.fontSize=size;
  t.fills=[{type:'SOLID',color:hex(color)}];
  if(lh) t.lineHeight={unit:'PERCENT',value:lh};
  root.appendChild(t);
  if(maxW){ while(t.width>maxW && t.fontSize>12) t.fontSize=t.fontSize-2; }
  if(w){t.resize(w,t.height); t.textAutoResize='HEIGHT'; t.textAlignHorizontal=align;}
  t.x=x; t.y=y; return t;}
function R(x,y,w,h,color,rad=0,stroke=null){const r=figma.createRectangle(); r.resize(w,h); r.x=x; r.y=y; r.cornerRadius=rad; r.fills=[{type:'SOLID',color:hex(color)}]; if(stroke){r.strokes=[{type:'SOLID',color:hex(stroke)}]; r.strokeWeight=3;} root.appendChild(r); return r;}
// 머리(3:4 미리보기 안전 구역 y 240~1680 안)
R(80,250,420,56,C.accent,28);
T(D.badge,{x:80,y:259,size:26,color:'#17120E',w:420,align:'CENTER'});
T(D.title,{x:80,y:330,size:116,family:'Black Han Sans',style:'Regular',maxW:920});
const top=T('TOP '+N,{x:80,y:470,size:116,family:'Black Han Sans',style:'Regular',color:C.gold});
T(D.stat,{x:top.x+top.width+30,y:520,size:28,style:'Medium',color:C.sub,w:1000-(top.x+top.width+30),align:'RIGHT'});
// 1위 칸: 왕관 + ? + 힌트 질문
R(80,640,920,190,C.panel,28,C.gold);
const crown=figma.createVector();
crown.vectorPaths=[{windingRule:'NONZERO',data:'M 0 70 L 10 10 L 35 40 L 55 0 L 75 40 L 100 10 L 110 70 Z'}];
crown.fills=[{type:'SOLID',color:hex(C.gold)}]; root.appendChild(crown); crown.x=118; crown.y=690;
T('1위',{x:120,y:768,size:34,family:'Black Han Sans',style:'Regular',color:C.gold,w:110,align:'CENTER'});
T('?',{x:260,y:640,size:150,family:'Black Han Sans',style:'Regular',color:C.gold});
const hint=T(D.hint,{x:500,y:688,size:36,w:470,align:'RIGHT',lh:130});
while(hint.height>100 && hint.fontSize>24) hint.fontSize=hint.fontSize-2;  // 힌트는 2줄 안
// 2위부터: 두 줄. 왼쪽 줄이 ceil((N-1)/2)개
const rest=items.slice(1); const leftN=Math.ceil(rest.length/2);
const rowH=Math.min(104, Math.floor(740/leftN)); const boxH=rowH-16; const top0=870;
rest.forEach((name,i)=>{
  const rank=i+2; const col=i<leftN?0:1; const row=i<leftN?i:i-leftN;
  const x=[80,550][col], y=top0+row*rowH;
  R(x,y,450,boxH,C.panel,18);
  const rc=rank===2?C.silver:rank===3?C.bronze:C.sub;
  T(String(rank),{x:x+18,y:y+boxH/2-34,size:52,family:'Black Han Sans',style:'Regular',color:rc,w:80,align:'CENTER'});
  T(name,{x:x+110,y:y+boxH/2-27,size:38,maxW:320});
});
const endY=top0+leftN*rowH+16;
T(D.cta||'1위는 어디일까요?  정답은 캡션에',{x:80,y:Math.max(endY,1590),size:34,color:C.accent,w:920,align:'CENTER'});
T(D.source,{x:80,y:Math.max(endY,1590)+78,size:19,style:'Regular',color:C.sub,w:920,align:'CENTER',lh:145});
return {frameId:root.id, n:N};
