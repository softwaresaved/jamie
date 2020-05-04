import json
from pathlib import Path
import sys
from pyparsing import (nums, alphas, alphanums,
                       Word, delimitedList, oneOf,
                       ParseException)

def filter_commas(xs):
    return [x for x in xs if x != ',']

def remove_commas(xs):
    return [x.replace("'", "") for x in xs]


if len(sys.argv) == 1:
    print("usage: parse_tags.py tags-summary-filename")
    sys.exit(1)

caps = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'
parse = Word(caps + nums) + "," + oneOf("first_run second_run third_run") + \
    "," + "[" + delimitedList(Word("'" + alphas + " ")) + "]" + \
    ("," + Word(alphanums + " _")) * 3 + "," + Word(nums + ".-")
# read tags summary file as command line argument
data = Path(sys.argv[1]).read_text().split('\n')

out = []
for i in data:
    try:
        match = parse.parseString(i)
    except ParseException:
        continue
    jobid = match[0]
    run_tag = match[2]
    consensus_tags, aggregate_tags, multi_agg_tags, agg_tags = filter_commas(match[-8:])
    agg_tags = float(agg_tags)
    tags = remove_commas(match[5:-9])
    out.append({
        'jobid': jobid,
        'run_tag': run_tag,
        'tags': tags,
        'consensus_tags': consensus_tags,
        'aggregate_tags': aggregate_tags,
        'multi_agg_tags': multi_agg_tags,
        'agg_tags': agg_tags
    })
print(json.dumps(out, indent=2))
