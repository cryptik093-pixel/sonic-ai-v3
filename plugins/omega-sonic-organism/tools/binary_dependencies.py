"""Record native import dependencies and reject an unbundled VC runtime."""
import hashlib,json,re,subprocess,sys
from pathlib import Path
root=Path(__file__).resolve().parents[1];evidence=Path(sys.argv[1])
qualification=json.loads((evidence/'result.json').read_text(encoding='utf-8-sig'))
build=Path(qualification['buildDirectory'])
binary=build/'VST3/Release/OmegaSonicOrganism.vst3/Contents/x86_64-win/OmegaSonicOrganism.vst3'
command=json.loads((build/'compile_commands.json').read_text())[0]['command']
compiler=re.match(r'^("[^"]+"|\S+)',command).group(1).strip('"')
dumpbin=Path(compiler).with_name('dumpbin.exe')
result=subprocess.run([str(dumpbin),'/DEPENDENTS',str(binary)],capture_output=True,text=True,check=True)
(evidence/'binary-dependencies.txt').write_text(result.stdout)
imports=re.findall(r'^\s+([\w.\-]+\.dll)\s*$',result.stdout,re.M|re.I)
assert imports
assert not any(re.match(r'(?:vcruntime|msvcp|concrt)\d',x,re.I) for x in imports),imports
(evidence/'binary-dependencies.json').write_text(json.dumps(dict(binarySha256=hashlib.sha256(binary.read_bytes()).hexdigest(),vcRedistributableDependency=False,imports=imports),indent=2)+'\n')
print('PASS native dependency inventory: no external VC redistributable DLL imports')
