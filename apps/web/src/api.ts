export type Actor = {id:string; email:string; role:'user'|'researcher'; csrf:string};
export type Item = Record<string, any>;
let csrf='';
export function setSession(actor:Actor|null){csrf=actor?.csrf||'';}
export class ApiError extends Error{constructor(public status:number,public code:string,message:string){super(message);}}
export async function api<T=any>(path:string,options:RequestInit={}):Promise<T>{
  const headers=new Headers(options.headers);if(options.body&&!(options.body instanceof FormData))headers.set('Content-Type','application/json');if(csrf)headers.set('X-CSRF-Token',csrf);
  const response=await fetch(path,{...options,headers,credentials:'same-origin'});
  if(!response.ok){let value:any={};try{value=await response.json();}catch{}throw new ApiError(response.status,value.error?.code||'request_failed',value.error?.message||'暂时无法处理，请稍后重试。');}
  if(response.status===204)return undefined as T;return response.json();
}
export const post=<T=any>(path:string,body:unknown={})=>api<T>(path,{method:'POST',body:JSON.stringify(body)});
export function dateLabel(value:string){const d=new Date(value);return Number.isNaN(d.valueOf())?value:new Intl.DateTimeFormat('zh-CN',{month:'short',day:'numeric',hour:'2-digit',minute:'2-digit',timeZone:'Asia/Shanghai'}).format(d);}
export function displayMetric(value:unknown,suffix=''){return value===null||value===undefined?'—':`${value}${suffix}`;}
export function safeSource(url:string){try{return new URL(url).protocol==='https:'?url:undefined;}catch{return undefined;}}
