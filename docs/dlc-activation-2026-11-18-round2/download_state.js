(() => {
 const o=appStore.GetAppOverviewByAppID(1142710);
 const primitives=x=>Object.fromEntries(Object.entries(x||{}).filter(([k,v])=>v===null||['string','number','boolean'].includes(typeof v)));
 const proto=Object.getOwnPropertyNames(Object.getPrototypeOf(o||{}));
 const computed={};for(const k of proto){if(!/download|update|install|build|DLC/i.test(k))continue;try{const v=o[k];if(['string','number','boolean'].includes(typeof v))computed[k]=v;}catch{}}
 return {overview:primitives(o),computed,overviewKeys:Object.keys(o||{}),overviewMethods:proto.filter(k=>/download|update|install|build|DLC/i.test(k)),installs:Object.keys(SteamClient.Installs),apps:Object.keys(SteamClient.Apps).filter(k=>/download|update|install|build|DLC|info/i.test(k)),installStore:typeof downloadStore==='object'?primitives(downloadStore):null};
})()
