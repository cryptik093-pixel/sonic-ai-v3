"""Prepare reproducible operator comparisons; never generate listening scores."""
import argparse
import csv
import hashlib
import json
import sys
from pathlib import Path

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from apps.api.workbench import midi
from apps.api.workbench.midi_studio import compose_studio
from apps.api.workbench.midi_quality import export_studio
from apps.api.workbench.schemas import MidiCommand


def prepare_pairs(output: Path) -> dict:
    output=Path(output).resolve();output.mkdir(parents=True,exist_ok=True)
    manifest={'schema_version':'1.0','purpose':'Operator listening comparison; unscored','pairs':[]}
    scores=[]
    for style in ['cloud','trap','soul']:
        for seed in [93,194]:
            label=f'{style}_{seed}'
            pair={'pair':label,'style':style,'seed':seed,'key':'C','scale':'minor','bpm':130,'bars':8}
            for side in ['legacy','studio']:
                folder=output/label/side
                folder.mkdir(parents=True,exist_ok=True)
                if any(folder.iterdir()):raise ValueError('Output comparison folder already contains files; choose an empty destination.')
                p=MidiCommand(title=label,style=style,seed=seed,key='C',scale='minor',bpm=130,bars=8,density='balanced',settings={} if side=='studio' else None)
                if side=='legacy':midi.generate(p,folder)
                else:export_studio(p,compose_studio(p),folder,{'run_id':f'listening-{label}','owner_id':'local-producer','workspace_id':'omega-house-studio','project_id':None})
                arrangement=next(f for f in folder.glob('*.mid') if f.stem not in ['Melody','Chords','Bass','Drums'])
                pair[side]={'path':str(arrangement.relative_to(output)),'sha256':hashlib.sha256(arrangement.read_bytes()).hexdigest()}
                scores.append({'pair':label,'engine':side,'harmonic_coherence':'','melody_development':'','groove':'','usefulness':'','worth_continuing':'','notes':''})
            manifest['pairs'].append(pair)
    (output/'Comparison_Manifest.json').write_text(json.dumps(manifest,indent=2),encoding='utf-8')
    with (output/'Listening_Scores.csv').open('w',newline='',encoding='utf-8-sig') as f:
        w=csv.DictWriter(f,fieldnames=list(scores[0]));w.writeheader();w.writerows(scores)
    (output/'LISTEN_FIRST.md').write_text('# MIDI Studio listening evaluation\n\n'
        'Import each paired arrangement into FL Studio at 130 BPM. Assign identical sounds and levels to corresponding tracks in both versions. '
        'Listen to the same eight bars; simple Audition.wav timbres are only a convenience.\n\n'
        'Rate harmonic coherence, melody development, groove and usefulness from 1 to 5. Enter yes/no for worth continuing and a concrete note. '
        'Try changing listening order between pairs. Scores are intentionally blank.\n\n'
        'Target: Studio improves the overall mean by at least 0.5, each Studio dimension averages at least 3, and four of six Studio phrases are worth continuing. '
        'Save your ratings; missed targets guide musical revisions. Valid MIDI is not a professional-quality certificate.\n',encoding='utf-8')
    return manifest


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('output',type=Path)
    args=parser.parse_args()
    manifest=prepare_pairs(args.output)
    print(json.dumps({'output':str(args.output.resolve()),'pairs':len(manifest['pairs']),'scores':'unscored'}))
