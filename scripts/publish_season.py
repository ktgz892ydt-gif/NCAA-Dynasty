"""Register a finalized, validated season locally; does not commit or push."""
import argparse
from season_io import ROOT, read, atomic_write
from validate_season import validate


def publish(season,root=ROOT):
    d=validate(season,root)
    if d['metadata']['status']!='finalized' or not d['scoreboard']:raise ValueError('Finalize a nonempty season before publication.')
    if not d['metadata'].get('lastVerified') or not d['metadata'].get('regulationGameSeconds'):raise ValueError('Record verification date and game settings first.')
    if set(s['teamId'] for s in d['summaries'])!=set(d['metadata']['teamIds']):raise ValueError('Review a summary for every dynasty team first.')
    manifest=read(root/'data/seasons.json')
    entries=[s for s in manifest['seasons'] if s['id']!=str(season)]
    entries.append({'id':str(season),'label':d['metadata']['label'],'published':True,'dataPath':f'data/seasons/{season}/season.json'})
    manifest['seasons']=sorted(entries,key=lambda s:s['id']);manifest['defaultSeason']=max(s['id'] for s in entries if s['published'])
    atomic_write(root/'data/seasons.json',manifest)


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--season',required=True);args=parser.parse_args();publish(args.season);print('Updated local manifest. Review, commit and push in GitHub Desktop when ready.')
