"""Create an empty unpublished season. Never copy another season's results."""
import argparse
from season_io import ROOT, season_dir, atomic_write, read


def initialize(season, root=ROOT):
    folder=season_dir(season,root)
    if folder.exists():raise ValueError('Season already exists; no files changed.')
    teams=read(root/'config/teams.json')['teams']
    metadata={'schemaVersion':1,'id':str(season),'label':str(season),'status':'draft','lastVerified':None,
              'methodVersion':'v1','inputMode':'standard','teamIds':[t['id'] for t in teams],
              'regulationGameSeconds':None,'coverage':{'statistics':'Not yet captured.','results':'Not yet verified.','photos':0,'videos':0},
              'syntheticTeams':[],'syntheticRecordPolicy':'actual-games','sourceNotes':'source-notes.md'}
    folder.mkdir(parents=True)
    atomic_write(folder/'metadata.json',metadata)
    for name,value in [('scoreboard',[]),('team-stats',{}),('player-identities',{'players':[]}),('corrections',{'season':str(season),'patches':[]})]:
        atomic_write(folder/'inputs'/f'{name}.json',value)
    atomic_write(folder/'summaries.json',[])
    (folder/'leaders').mkdir();(folder/'source-notes.md').write_text(f'# {season} source notes\n\nRecord sources, coverage, unresolved discrepancies and verified corrections here.\n')
    return folder


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--season',required=True);args=parser.parse_args()
    print(f'Created {initialize(args.season)}. It is not in the published manifest.')


if __name__=='__main__':main()
