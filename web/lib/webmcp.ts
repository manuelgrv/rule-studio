export function registerNavigation(navigate:(index:number)=>void) {
 const context=(document as Document & {modelContext?:{registerTool:(tool:unknown,options:{signal:AbortSignal})=>unknown}}).modelContext;
 if(!context?.registerTool)return;
 const lifecycle=new AbortController();
 const names=['resumen','inputs','variables','reglas','aprobaciones','laboratorio'];
 try{Promise.resolve(context.registerTool({name:'open_rule_manager_module',title:'Abrir módulo del gestor',description:'Abre el módulo indicado. No modifica ni publica ninguna DSL.',inputSchema:{type:'object',properties:{module:{type:'string',enum:names}},required:['module'],additionalProperties:false},annotations:{readOnlyHint:true},execute:async(input:unknown)=>{if(!input||typeof input!=='object'||Object.keys(input).length!==1||!('module' in input)||!names.includes(String(input.module)))throw new Error('Módulo no válido');const module=String(input.module);navigate(names.indexOf(module));await new Promise(r=>requestAnimationFrame(r));return {module,opened:true}}},{signal:lifecycle.signal})).catch(()=>{});}catch{}
 return ()=>lifecycle.abort();
}
