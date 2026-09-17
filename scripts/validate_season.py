"""Validate one generated season against its inputs, or the publication manifest."""
import argparse
from season_io import ROOT, read, season_dir, serialized, validate_output
from build_season import build


def validate(season,root=ROOT):
    path=season_dir(season,root)/'season.json';published=read(path);validate_output(published)
    if path.read_text()!=serialized(build(season,root)):raise ValueError(f'{season}: generated data is stale.')
    return published


def validate_manifest(root=ROOT):
    manifest=read(root/'data/seasons.json')
    if manifest['schemaVersion']!=1:raise ValueError('Unsupported manifest schema.')
    ids=[s['id'] for s in manifest['seasons']]
    if len(ids)!=len(set(ids)):raise ValueError('Duplicate season in manifest.')
    published=[s for s in manifest['seasons'] if s['published']]
    if manifest['defaultSeason'] not in [s['id'] for s in published]:raise ValueError('Default season is not published.')
    for entry in published:
        if entry['dataPath']!=f'data/seasons/{entry["id"]}/season.json':raise ValueError('Invalid season path.')
        d=validate(entry['id'],root)
        if d['metadata']['status']!='finalized':raise ValueError('Only finalized seasons can be published by this workflow.')
        if not d['scoreboard']:raise ValueError('Cannot publish an empty season.')
        if set(s['teamId'] for s in d['summaries'])!=set(d['metadata']['teamIds']):raise ValueError('Each dynasty team needs a reviewed summary before publication.')
    return published


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--season');parser.add_argument('--all',action='store_true');args=parser.parse_args()
    if args.all:print(f'Validated {len(validate_manifest())} published season(s).')
    elif args.season:validate(args.season);print(f'{args.season}: inputs, output and coverage structure validated.')
    else:parser.error('Choose --season YEAR or --all.')


if __name__=='__main__':main()
