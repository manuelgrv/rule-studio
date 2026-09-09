// Python source is parsed by our restricted compiler; it is never exec'd.
let ready;
async function initialize() {
  importScripts('https://cdn.jsdelivr.net/pyodide/v0.29.3/full/pyodide.js');
  const py = await loadPyodide({indexURL:'https://cdn.jsdelivr.net/pyodide/v0.29.3/full/'});
  await py.loadPackage(['micropip','jsonschema']);
  await py.runPythonAsync('import micropip\nawait micropip.install("sqlglot==30.18.0")');
  const zip = await fetch('/demo/rule_manager.zip');
  if (!zip.ok) throw new Error('No se pudo cargar la biblioteca de reglas');
  py.unpackArchive(await zip.arrayBuffer(),'zip');
  const bridge=await fetch('/demo/bridge.py');
  if(!bridge.ok) throw new Error('No se pudo cargar el compilador');
  py.runPython(await bridge.text());
  return py;
}
self.onmessage=async ({data})=>{
  try {
    ready ||= initialize().catch(e=>{ready=null;throw e});
    const py=await ready;
    const fn=py.globals.get('call');
    try { self.postMessage({id:data.id,...JSON.parse(fn(JSON.stringify(data.payload)))}); }
    finally {fn.destroy()}
  } catch(e) {self.postMessage({id:data.id,ok:false,error:{code:'RUNTIME_ERROR',message:String(e)}})}
};
