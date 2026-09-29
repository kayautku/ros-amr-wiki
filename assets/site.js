/* ROS AMR Wiki: arama, tema, menü, Mermaid. Bağımlılık yok (Mermaid ayrı dosyada). */
(function(){
  'use strict';
  var root=document.documentElement;

  /* ---- tema: Sistem -> Açık -> Koyu ---- */
  var LABEL={system:'Sistem',light:'Açık',dark:'Koyu'};
  function getTheme(){try{var t=localStorage.getItem('rw-theme');return (t==='light'||t==='dark')?t:'system';}catch(e){return 'system';}}
  function setTheme(t){
    if(t==='system')root.removeAttribute('data-theme'); else root.setAttribute('data-theme',t);
    try{ if(t==='system')localStorage.removeItem('rw-theme'); else localStorage.setItem('rw-theme',t);}catch(e){}
    var b=document.getElementById('themebtn'); if(b)b.textContent='Tema: '+LABEL[t];
    runMermaid();
  }
  function effTheme(){var a=root.getAttribute('data-theme'); if(a)return a; return (window.matchMedia&&matchMedia('(prefers-color-scheme: dark)').matches)?'dark':'light';}

  /* ---- Mermaid ---- */
  function runMermaid(){
    if(!window.mermaid)return;
    var nodes=[].slice.call(document.querySelectorAll('pre.mermaid'));
    if(!nodes.length)return;
    nodes.forEach(function(n){
      if(n.getAttribute('data-src')==null){n.setAttribute('data-src',n.textContent);}
      else{n.removeAttribute('data-processed'); n.textContent=n.getAttribute('data-src');}
    });
    try{
      window.mermaid.initialize({startOnLoad:false,theme:effTheme()==='dark'?'dark':'default',fontFamily:'"IBM Plex Sans",system-ui,sans-serif'});
      var p=window.mermaid.run({nodes:nodes}); if(p&&p.catch)p.catch(function(){});
    }catch(e){}
  }

  /* ---- arama ---- */
  var IDX=window.SEARCH_INDEX||[];
  function norm(s){return s.toLocaleLowerCase('tr').normalize('NFD').replace(/[̀-ͯ]/g,'').replace(/ı/g,'i');}
  IDX.forEach(function(e){e.nt=norm(e.t);e.nx=norm(e.x);});
  function esc(s){return s.replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;');}
  function hl(text,toks){
    var n=norm(text),marks=[];
    toks.forEach(function(t){var i=n.indexOf(t); if(i>=0)marks.push([i,i+t.length]);});
    marks.sort(function(a,b){return a[0]-b[0];});
    var out='',pos=0;
    marks.forEach(function(m){ if(m[0]<pos)return; out+=esc(text.slice(pos,m[0]))+'<mark>'+esc(text.slice(m[0],m[1]))+'</mark>'; pos=m[1]; });
    return out+esc(text.slice(pos));
  }
  function search(q){
    var toks=norm(q).split(/\s+/).filter(Boolean); if(!toks.length)return {toks:toks,res:[]};
    var res=[];
    IDX.forEach(function(e){
      var score=0,ok=true;
      toks.forEach(function(t){
        var it=e.nt.indexOf(t), ix=e.nx.indexOf(t);
        if(it<0&&ix<0){ok=false;return;}
        if(it>=0)score+=10;
        if(ix>=0){score+=1;var c=0,p=ix;while(p>=0&&c<6){c++;p=e.nx.indexOf(t,p+t.length);}score+=c*0.3;}
      });
      if(ok)res.push({e:e,s:score});
    });
    res.sort(function(a,b){return b.s-a.s;});
    return {toks:toks,res:res.slice(0,8)};
  }
  function snippet(e,toks){
    var pos=-1; toks.forEach(function(t){var i=e.nx.indexOf(t); if(i>=0&&(pos<0||i<pos))pos=i;});
    if(pos<0)return esc(e.x.slice(0,110));
    var st=Math.max(0,pos-48), txt=e.x.slice(st,st+150);
    return (st>0?'…':'')+hl(txt,toks)+(st+150<e.x.length?'…':'');
  }
  function initSearch(){
    var inp=document.getElementById('find'), box=document.getElementById('results'); if(!inp||!box)return;
    var sel=-1;
    function items(){return [].slice.call(box.querySelectorAll('a'));}
    function mark(i){var a=items(); a.forEach(function(x){x.classList.remove('sel');}); sel=i; if(a[i]){a[i].classList.add('sel'); a[i].scrollIntoView({block:'nearest'});}}
    function render(){
      var q=inp.value.trim();
      if(!q){box.hidden=true;box.innerHTML='';sel=-1;return;}
      var r=search(q);
      if(!r.res.length){box.innerHTML='<li><p class="noresult">Sonuç yok.</p></li>';box.hidden=false;sel=-1;return;}
      box.innerHTML=r.res.map(function(x){
        return '<li><a href="'+x.e.p+'#'+x.e.id+'"><b>'+hl(x.e.t,r.toks)+'</b><small>'+snippet(x.e,r.toks)+'</small><span class="pgn">'+esc(x.e.pg)+'</span></a></li>';
      }).join('');
      box.hidden=false; sel=-1;
    }
    inp.addEventListener('input',render);
    inp.addEventListener('keydown',function(e){
      var a=items();
      if(e.key==='ArrowDown'){e.preventDefault();mark(Math.min(a.length-1,sel+1));}
      else if(e.key==='ArrowUp'){e.preventDefault();mark(Math.max(0,sel-1));}
      else if(e.key==='Enter'){var t=a[sel>=0?sel:0]; if(t){e.preventDefault();location.href=t.getAttribute('href');}}
      else if(e.key==='Escape'){inp.value='';render();inp.blur();}
    });
    document.addEventListener('keydown',function(e){
      if(e.key==='/' && !/^(INPUT|TEXTAREA)$/.test((document.activeElement||{}).tagName||'')){e.preventDefault();inp.focus();}
    });
  }

  /* ---- kod/terminal bloklarına kopyala düğmesi ---- */
  var COPY_ICON='<svg viewBox="0 0 24 24"><rect x="8" y="8" width="12" height="12" rx="2"></rect><path d="M16 8V6a2 2 0 0 0-2-2H6a2 2 0 0 0-2 2v8a2 2 0 0 0 2 2h2"></path></svg>';
  var CHECK_ICON='<svg viewBox="0 0 24 24"><path d="M20 6 9 17l-5-5"></path></svg>';
  function copyText(text){
    if(navigator.clipboard&&navigator.clipboard.writeText)return navigator.clipboard.writeText(text);
    return new Promise(function(resolve,reject){
      var ta=document.createElement('textarea');
      ta.value=text; ta.setAttribute('readonly',''); ta.style.position='fixed'; ta.style.top='-1000px';
      document.body.appendChild(ta); ta.select();
      try{ document.execCommand('copy')?resolve():reject(new Error('execCommand')); }
      catch(e){ reject(e); }
      finally{ document.body.removeChild(ta); }
    });
  }
  function initCopyButtons(){
    var pres=[].slice.call(document.querySelectorAll('main pre:not(.mermaid):not(.tree)'));
    pres.forEach(function(pre){
      pre.classList.add('has-copybtn');
      var btn=document.createElement('button');
      btn.type='button'; btn.className='copybtn'; btn.setAttribute('aria-label','Kopyala'); btn.innerHTML=COPY_ICON;
      var timer=null;
      btn.addEventListener('click',function(){
        copyText(pre.textContent).then(function(){
          btn.classList.remove('copyerr'); btn.classList.add('copied');
          btn.innerHTML=CHECK_ICON; btn.setAttribute('aria-label','Kopyalandı');
        },function(){
          btn.classList.remove('copied'); btn.classList.add('copyerr');
          btn.setAttribute('aria-label','Kopyalanamadı');
        });
        clearTimeout(timer);
        timer=setTimeout(function(){
          btn.classList.remove('copied','copyerr'); btn.innerHTML=COPY_ICON; btn.setAttribute('aria-label','Kopyala');
        },1500);
      });
      pre.appendChild(btn);
    });
  }

  /* ---- menü: mobilde kapat, bölüm izleme ---- */
  function initNav(){
    var navd=document.getElementById('navd');
    var mobile=function(){return window.matchMedia&&matchMedia('(max-width:900px)').matches;};
    if(navd&&mobile())navd.removeAttribute('open');
    if(navd)[].forEach.call(document.querySelectorAll('.side a'),function(a){a.addEventListener('click',function(){if(mobile())navd.removeAttribute('open');});});

    var subs={}; [].forEach.call(document.querySelectorAll('.side .sub a'),function(a){var h=a.getAttribute('href'); if(h&&h.charAt(0)==='#')subs[h.slice(1)]=a;});
    var secs=[].slice.call(document.querySelectorAll('section[id]'));
    if(!secs.length||!('IntersectionObserver' in window)||!Object.keys(subs).length)return;
    var io=new IntersectionObserver(function(es){
      es.forEach(function(e){
        if(!e.isIntersecting)return;
        for(var k in subs)subs[k].classList.remove('on');
        if(subs[e.target.id])subs[e.target.id].classList.add('on');
      });
    },{rootMargin:'-10% 0px -80% 0px'});
    secs.forEach(function(s){io.observe(s);});
  }

  function boot(){
    var b=document.getElementById('themebtn');
    if(b){b.textContent='Tema: '+LABEL[getTheme()]; b.addEventListener('click',function(){var c=getTheme(); setTheme(c==='system'?'light':c==='light'?'dark':'system');});}
    initSearch(); initNav(); initCopyButtons(); runMermaid();
  }
  if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',boot); else boot();
})();
