"""Complete pinned SpriteCollab tree inventory, splitting requests to avoid truncation.
Records files awaiting processing; inventory presence never means a rendered/tested sprite.
GitHub access uses the configured gh connection, never credentials in files.
"""
import csv,json,subprocess,time
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor,as_completed
ROOT=Path(__file__).resolve().parents[2]
CACHE=ROOT/'.cache/tera_v2';OUT=ROOT/'exports/tera_v2';OUT.mkdir(parents=True,exist_ok=True)
PIN='3609a86be2a4c8ad7cf255bd2255f044daafe24f'

def fetch(node):
    file=CACHE/'trees'/f"{node['path']}_{node['sha']}.json";file.parent.mkdir(parents=True,exist_ok=True)
    if file.exists():data=json.loads(file.read_text())
    else:
        r=subprocess.run(['gh','api',f"repos/PMDCollab/SpriteCollab/git/trees/{node['sha']}?recursive=1"],capture_output=True,text=True,timeout=90)
        if r.returncode:return node['path'],None,r.stderr[:600]
        data=json.loads(r.stdout);file.write_text(r.stdout)
    if data.get('truncated'):return node['path'],None,'Child tree also truncated; not counted as complete'
    return node['path'],data['tree'],None

def main():
    CACHE.mkdir(parents=True,exist_ok=True)
    roots_file=CACHE/'species_roots.json'
    if not roots_file.exists():
        root=json.loads(subprocess.check_output(['gh','api',f'repos/PMDCollab/SpriteCollab/git/trees/{PIN}']))
        sha=next(n['sha'] for n in root['tree'] if n['path']=='sprite')
        roots_file.write_bytes(subprocess.check_output(['gh','api',f'repos/PMDCollab/SpriteCollab/git/trees/{sha}']))
    nodes=[n for n in json.loads(roots_file.read_text())['tree'] if n['type']=='tree']
    rows=[];xmls=[];errors=[];done=0
    with ThreadPoolExecutor(max_workers=4) as pool:
        for f in as_completed([pool.submit(fetch,n) for n in nodes]):
            root,tree,error=f.result();done+=1
            if error:errors.append({'root':root,'error':error})
            else:
                for n in tree:
                    path=root+'/'+n['path']
                    if path.endswith('-Anim.png'):rows.append([path,n['sha'],n.get('size',0),'not_downloaded_or_rendered'])
                    if path.endswith('AnimData.xml'):xmls.append(path)
            if done%100==0:print(f'{done}/{len(nodes)} roots; {len(rows)} sheets; {len(errors)} errors',flush=True)
    if errors:
        (OUT/'catalogue_attempt_errors.json').write_text(json.dumps(errors,indent=2)+'\n')
        raise RuntimeError('Incomplete inventory attempt; previous complete catalogue not overwritten')
    previous=OUT/'remote_verification.json'
    verified={c['source']:c['git_blob_sha'] for c in json.loads(previous.read_text())['checks']} if previous.exists() else {}
    for row in rows:
        if verified.get(row[0])==row[1]:row[3]='24_phases_rendered_alpha_verified_not_PMDO'
    rendered=sum(row[3]!='not_downloaded_or_rendered' for row in rows)
    rows.sort()
    with (OUT/'spritecollab_catalogue.csv').open('w') as f:
        w=csv.writer(f);w.writerow(['sprite_relative_path','git_blob_sha','source_bytes','processing_state']);w.writerows(rows)
    report={'pin':PIN,'root_count':len(nodes),'roots_completed':len(nodes)-len(errors),'errors':errors,'complete_tree_inventory':not errors,'animation_sheet_count':len(rows),'form_xml_count':len(xmls),'source_bytes_total':sum(r[2] for r in rows),'rendered_remote_sheets':rendered,'remaining_remote_sheets_unrendered':len(rows)-rendered,'important':'This is an inventory of pending source files, not blanket rendering or PMDO coverage. Native PNGs stay in external cache when fetched.'}
    (OUT/'catalogue_report.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report,indent=2),flush=True)

if __name__=='__main__':main()
