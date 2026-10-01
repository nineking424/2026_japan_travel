# 브라우저 추출 스니펫 (`mcp__claude-in-chrome__javascript_tool` 용)

모두 `await sleep()`를 쓰는 비동기 본문이다. 반환 문자열은 약 1.9KB를 넘으면 `[TRUNCATED]`로 잘리니 항목 수를 제한한다.
`const sleep=ms=>new Promise(r=>setTimeout(r,ms));`를 앞에 둔다.

## A1. Airbnb 검색 결과 카드 (ID | 날짜라벨 | 총액 | 평점 | 후기 | 제목)

```js
await sleep(6000); window.scrollBy(0,2500); await sleep(1500);
const seen={}, out=[];
document.querySelectorAll('a[href*="/rooms/"]').forEach(a=>{
  const m=a.getAttribute('href').match(/rooms\/(\d+)/); if(!m||seen[m[1]])return; seen[m[1]]=1;
  const c=a.closest('[data-testid="card-container"]')||a.parentElement;
  const tx=c.innerText.replace(/\n+/g,' ');
  if(/\d+월 \d+일~\d+일/.test(tx)) return;                 // 다른 날짜 추천은 제외
  const tot=(tx.match(/총액\s*₩([\d,]+)/)||tx.match(/₩([\d,]+)\s*총액/)||[])[1];
  const rt=(tx.match(/평점 ([\d.]+)점/)||[])[1], rv=(tx.match(/후기 (\d+)개/)||[])[1];
  out.push([m[1],tot,rt,rv,tx.replace(/전체 \d+장 중 1번째 사진|슈퍼호스트|게스트 선호|신규/g,'').trim().slice(0,26)].join('|'));
});
out.length+'\n'+out.join('\n')
```

## A2. Airbnb 상세 (침실·면적·편의시설·좌표·사진)

```js
await sleep(3500);
let T=document.body.innerText.split('근처의 숙소 더 보기')[0];
const DT=document.title.split(' - ')[0], id=location.pathname.split('/')[2];
const g=(re,i=1)=>{const m=T.match(re);return m?m[i]:null};
const sp=g(/최대 인원([^\n]*)/);                                  // "6명 · 침실 1개 · 침대 4개 · 욕실 1개" (임대 호실형은 비어 있음)
const bdm=(sp||'').match(/침실\s*(\d+)개/);
const sec=(T.split('숙박 장소')[1]||'').split(/숙소 편의시설|후기|위치/)[0];
const html=[...document.scripts].map(s=>s.textContent).join('\n');
// 사진: 스크립트 안의 원본 URL을 디렉터리별로 모은다
const dirs={}; let m;
const re=/https:\/\/a0\.muscache\.com\/im\/pictures\/((?:hosting|miso|BnbProperty|prohost-api)[^"\\?\s]*?)\/original\/([^"\\?\s]+)/g;
while((m=re.exec(html))){(dirs[m[1]]=dirs[m[1]]||[]); if(!dirs[m[1]].includes(m[2])) dirs[m[1]].push(m[2])}
const b64=btoa('StayListing:'+id).replace(/=+$/,'');
let keys=Object.keys(dirs).filter(k=>k.includes(id)||k.includes(b64));
if(!keys.length){const best=Object.entries(dirs).sort((a,b)=>b[1].length-a[1].length)[0]; keys=best?[best[0]]:[]}
const out={}; let n=0; keys.forEach(k=>{out[k]=dirs[k].slice(0,12-n); n+=out[k].length});
// 예전 형식(경로 없는 uuid.jpg)은 화면에 보이는 것만
const dom=[]; document.querySelectorAll('img').forEach(i=>{const s=(i.currentSrc||i.src||'').split('?')[0];
  const mm=s.match(/\/im\/pictures\/([0-9a-f]{8}-[0-9a-f-]{27}\.(?:jpe?g|png))$/); if(mm&&!dom.includes(mm[1])) dom.push(mm[1])});
const ll=(html.match(/"lat(?:itude)?":\s*(3[45]\.\d+),\s*"l(?:ng|ongitude)":\s*(13[89]\.\d+)/)||[]).slice(1,3);
const desc=(T.split('등록 세부 정보')[0]||T);
// 편의시설: '편의시설 N개 모두 보기' 모달에서 확인 (이용 불가 이전 부분만 유효)
let am=''; try{const b=[...document.querySelectorAll('button')].find(x=>/편의시설 \d+개 모두 보기/.test(x.innerText));
  if(b){b.click(); await sleep(1800); am=[...document.querySelectorAll('[role="dialog"]')].map(d=>d.innerText).filter(s=>s.includes('숙소 편의시설')).join('|')}}catch(e){}
const av=am.split('이용 불가')[0], has=k=>av.includes(k)?1:0;
JSON.stringify({id, t:DT.slice(0,40), ty:g(/\n([^\n]*(?:전체|개인실)[^\n]*)\n최대 인원/), sp:(sp||'').slice(0,30),
  bd:bdm?+bdm[1]:((sp||'').includes('원룸')?0:null), sec:sec.replace(/\n+/g,'|').slice(0,40),
  r:g(/5점 만점 중 ([\d.]+)점을 받았습니다/), rv:g(/후기 (\d+)개\n/), lo:g(/위치 항목에서 5점 만점 중 ([\d.]+)점/),
  c:g(/([^\n]*무료 취소 가능)/)||g(/(취소 수수료 없음)/)||'환불불가?', tot:g(/총액 (₩[\d,]+)/), su:/슈퍼호스트/.test(T)?1:0,
  ar:(desc.match(/(\d+)\s*(?:㎡|m²|평방미터|sqm)/)||[])[1]||(DT.match(/(\d+)\s*(?:㎡|평방미터)/)||[])[1]||null,
  w:(DT+desc).match(/도보[^\n。.]{0,14}?(\d+)\s*분/)?.[1]||DT.match(/(\d+)\s*분/)?.[1]||null,
  am:[has('주방'),has('세탁기'),has('엘리베이터'),has('에어컨'),am.length].join(''), ll:ll.join(','), out, dom})
```

- 결과의 `am`은 주방·세탁기·엘리베이터·에어컨 4자리 + 모달 길이. 길이가 작으면(<250) 모달이 안 열린 것이니 `None`으로 처리한다.
- 수집 후 `collected_v2.py`의 `AIRBNB_PHOTOS`(디렉터리→파일명 목록)와 `BEDROOMS`에 옮긴다. 디렉터리에 `==`가 있으면 URL 인코딩(`%3D%3D`)한다.

## B1. Agoda 목록 카드 (href | 평점 | 가까운 역 | 세금 포함 1박) — 실제 휠 스크롤 후 실행

```js
const out=[]; let n=0;
[...document.querySelectorAll('[data-selenium="hotel-item"]')].forEach(c=>{ n++;
  const t=c.innerText.replace(/\n+/g,' '), a=c.querySelector('a[href*="/hotel/"]');
  const h=a?(a.getAttribute('href')||'').split('?')[0].replace('/ko-kr/',''):'';
  const p=(t.match(/1박당 총 금액\s*₩\s*([\d,]+)/)||[])[1], pn=p?+p.replace(/,/g,''):null;
  const sc=(t.match(/(\d\.\d)\s*(?:매우 좋음|우수|최고|좋음|양호)/)||[])[1];
  const st=(t.match(/([가-힣A-Za-z\-·]+역) 약 ([\d.,]+)\s?(m|km)/)||[]);
  if(pn && pn<=300000 && sc && +sc>=8) out.push([h,sc,(st[1]||'')+' '+(st[2]||'')+(st[3]||''),pn].join('|'));
});
n+' cards\n'+out.join('\n')
```

- 다음 페이지: `[...document.querySelectorAll('button,a')].find(x=>/다음 페이지/.test((x.getAttribute('aria-label')||'')+x.innerText)).click()` 후 6초 대기, 다시 휠 스크롤.
- 가격 필터는 세금 포함 1박 ≤ 총액상한/4.

## B2. Agoda 상세 (면적·침실·편의시설·가까운 역·사진)

```js
await sleep(9000);
const T=document.body.innerText;
const f=(re,i=0)=>{const m=T.match(re);return m?(m[i]||'').replace(/\n+/g,' ').slice(0,50):null};
const isH=s=>/(pix\d*\.agoda\.net\/hotelImages|bstatic\.com\/xdata\/images\/hotel\/max1024)/.test(s);
const i0=[...document.querySelectorAll('img')].find(x=>isH(x.currentSrc||x.src)); if(i0){i0.click(); await sleep(2500)}   // 갤러리 열기
const im=[];
document.querySelectorAll('img').forEach(x=>{const s=(x.currentSrc||x.src||''); if(!isH(s))return; let k;
  if(/bstatic/.test(s)) k=s.replace('https://q-xx.bstatic.com/xdata/images/hotel/max1024x768/','B').replace(/\.jpg\?k=/,'|').replace(/&o=.*$/,'');  // B<id>|<서명>
  else k='P'+s.split('?')[0].replace('https://pix8.agoda.net/hotelImages/','').replace('https://','');                                       // P<hotelId>/0/<hash>.jpg
  if(!im.some(y=>y.split('|')[0]===k.split('|')[0])) im.push(k)});
JSON.stringify({h1:((document.querySelector('h1')||{}).innerText||'').slice(0,60), url:location.pathname.slice(0,60),
  size:f(/\d+\s*(?:m²|㎡)/), bed:f(/침실\s*\d+개|스튜디오|원룸/), bt:f(/(?:더블|싱글|퀸|킹|소파|이층|요이불)[^\n]{0,12}\d+개/),
  mx:f(/최대인원\s*\d+\s*명/), k:/주방/.test(T)?1:0, w:/세탁기/.test(T)?1:0, e:/엘리베이터/.test(T)?1:0, a:/에어컨/.test(T)?1:0,
  c:f(/무료 취소[^\n]{0,20}/)||f(/환불 불가/), rv:f(/([\d,]+)\s*(?:건의\s*)?이용후기/,1),
  st:f(/[가-힣A-Za-z\-·]+역\s*(?:약\s*)?[\d.,]+\s?(?:m|km)/), n:im.length, ph:im.slice(0,10)})
```

- `h1`이 "죄송합니다."이고 url이 `/pagenotfound.html`이면 주소가 틀린 것(404).
- 사진 해석: `P…` → `https://pix8.agoda.net/hotelImages/<hotelId>/0/<hash>.jpg`, `B<id>|<sig>` → `https://q-xx.bstatic.com/xdata/images/hotel/max1024x768/<id>.jpg?k=<sig>&o=`. 첫 `P`의 hotelId와 다른 `P`는 추천 숙소 사진이니 버린다.
- `st`의 역은 `build_data.py` `STATIONS`에 좌표를 추가해 `G()`의 `station=(키, 한글명)`로 넘긴다. 좌표 확인: Nominatim(`nominatim.openstreetmap.org/search?format=json&q=<역명>`, User-Agent 필수, 초당 1건).
