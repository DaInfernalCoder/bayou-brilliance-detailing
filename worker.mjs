import policy from './policy.json';
const escaped = s => s.replace(/[.+?^${}()|[\]\\]/g, '\\$&');
function match(pattern,path) {
  if (pattern === '/(.*)' || pattern === '/:path*' || pattern === '/:path(.*)') return [path,path.slice(1)];
  if (pattern.endsWith('/(.*)')) return path.startsWith(pattern.slice(0,-4)) ? [path,path.slice(pattern.length-4)] : null;
  if (pattern.includes(':')) throw new Error('Unsupported source pattern: '+pattern);
  return path === pattern ? [path] : null;
}
function redirect(url,path,status=308) { const dest = new URL(path,url); if (!dest.search) dest.search=url.search; return Response.redirect(dest.href,status); }
export default {
 async fetch(request,env) {
  const url=new URL(request.url), p=url.pathname;
  const host=policy.domains.find(d=>d.name===url.hostname);
  if(host?.redirect) return redirect(url,'https://'+host.redirect+p,host.redirectStatusCode||308);
  for(const rule of policy.config.redirects||[]) {
   if((rule.has||[]).some(h=>h.type!=='host'||h.value!==url.hostname)) continue;
   const m=match(rule.source,p);if(!m)continue;
   const dest=rule.destination.replace(/:path\*?/g,m[1]||'').replace('$1',m[1]||'');
   return redirect(url,dest,rule.statusCode||(rule.permanent?308:307));
  }
  if(!['GET','HEAD'].includes(request.method))return new Response('Method not allowed',{status:405,headers:{Allow:'GET, HEAD'}});
  let route=p;
  const files=policy.files;
  const clean=policy.config.cleanUrls===true;
  const directory=files.includes(p.replace(/\/$/,'')+'/index.html');
  const flat=files.includes(p.replace(/\/$/,'')+'.html');
  if(p==='/index.html')return redirect(url,'/');
  if(clean&&p.endsWith('.html')&&files.includes(p))return redirect(url,p.slice(0,-5)+(policy.config.trailingSlash===true?'/':''));
  if(p!=='/'&&(directory||(clean&&flat))) {
   const desired=p.replace(/\/$/,'')+(policy.config.trailingSlash===false?'':'/');
   // Flat clean URLs default to no trailing slash; directory indexes default to slash.
   const canonical=policy.config.trailingSlash===undefined&&flat?p.replace(/\/$/,''):desired;
   if(p!==canonical)return redirect(url,canonical);
  }
  if(directory)route=p.replace(/\/$/,'')+'/index.html';
  else if(clean&&flat)route=p.replace(/\/$/,'')+'.html';
  else if(p==='/')route='/index.html';
  const assetUrl=new URL(url);assetUrl.pathname=route;
  let response=await env.ASSETS.fetch(new Request(assetUrl,request));
  if(response.status===404&&files.includes('/404.html')) {
   assetUrl.pathname='/404.html';const body=await env.ASSETS.fetch(new Request(assetUrl,request));response=new Response(body.body,{status:404,headers:body.headers});
  }
  const headers=new Headers(response.headers);
  for(const rule of policy.config.headers||[])if(match(rule.source,p))for(const h of rule.headers)headers.set(h.key,h.value);
  return new Response(response.body,{status:response.status,statusText:response.statusText,headers});
 }
};
