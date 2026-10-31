"""Export full cleaned label frequencies from EgoContact annotations.

Run from the repository root: python scripts/prepare_dataset_distributions.py
Families are editorial display groupings, not an official annotation taxonomy.
Every nonempty, non-placeholder label is retained, including rare labels.
"""
import argparse
import csv
import hashlib
import json
from collections import Counter, defaultdict
from pathlib import Path

SOURCE = Path('data/EgoContact/annotations/24_04_2026.json')
# Pipe-separated labels preserve multiword annotation names.
GROUPS = {
    'actions': [
        ('Grasp', 'take|hold|grab|grasp|catch|touch|pick|collect'),
        ('Move', 'move|lift|put|pull|push|carry|give|throw|toss|let go'),
        ('Access', 'open|close|lock|cover'),
        ('Operate', 'turn on|turn off|press|operate|turn|scroll|drive|pump'),
        ('Arrange', 'adjust|arrange|sort|pack|fill|add|serve'),
        ('Join', 'insert|attach|tighten|screw|tie|stick'),
        ('Separate', 'remove|detach|unscrew|untie|break|tear'),
        ('Cut & peel', 'cut|peel|shelling|crack|pluck'),
        ('Shape', 'knead|grind|roll|mold|fold|stretch|squeeze|twist|flip'),
        ('Mix & pour', 'stir|mix|pour|dip|scoop|sift|sprinkle'),
        ('Clean', 'clean|wash|wipe|dry|rub|dispose'),
        ('Finish', 'apply|spray|iron|sand|smooth|paint draw|draw|polish|refine|mark'),
        ('Build & craft', 'knit|sew|drill|hit|work on'),
        ('Garden', 'dig|water|plant'),
        ('Inspect', 'inspect|measure|point'),
        ('Body & play', 'wear|play|climb|swing|sit|stand'),
    ],
    'objects': [
        ('Food & ingredients', 'vegetable|food|dough|seasoning|egg|flour|ice|cake|water|powder'),
        ('Utensils', 'knife|spoon|chopstick|sieve|scissors|cutter|spatula|chopping board|fork|rolling pin|tongs|ladle|grater|whisk|straw|garlic press|scoop|funnel|peeler|toothpick|lemon squeezer|juicer|garlic chopper|nutcracker|manual lemon squeezer|pestle|cutlery|kitchen utensils|teapot|dough press'),
        ('Cookware & dishes', 'lid|plate|bowl|cup|pot|pan|tray|jug|glass|mold|dish|plastic lid|coaster|grate'),
        ('Appliances', 'fridge|cooker|oven|weighing scale|blender|microwave|kettle|hand blender|food processor|mixer|range hood|coffee maker|grinder|coffee machine|burner|cooler|dishwasher|water heater'),
        ('Containers', 'container|bag|bottle|bucket|wrapper|packet|package|basket|jerrycan|box|sachet|jar|wallet|basin'),
        ('Home & fixtures', 'faucet|drawer|cabinet|door|chair|wall|table|mat|ladder|rack|hanger|pillow|shelf|curtain|mirror|floor|sink|cover|handrail|roof|canopy|counter|decoration|padlock|tablecloth|seat|sofa|lamp|artificial tree|stand|tarp|sink drain cover'),
        ('Cleaning & laundry', 'towel|sponge|napkin|brush|spray|iron|vacuum cleaner|cloth|broom|trash|clothes iron|dustpan|soap|mop|rag|washing machine|air blower|wiper|paper towels|lron|ironing iron|steam iron|wipes|soap dispenser'),
        ('Hand tools', 'screwdriver|tool|hammer|trowel|plier|tape measure|wrench|saw|ruler|shears|caliper|scraper|clamp|axe|chisel|scrapers|file|level tool|blade|staple gun|tweezers|stapler|plastic tool|caulking gun|bar clamp|hand press|tap gun|tweezer|level|spirit level|welding钳|welding clamp'),
        ('Power tools', 'drill|sander|solder iron|machine|welding machine|machine hand|angle grinder|impact wrench|planer|wood planer|welding torch|pasting machine|cordless nail gun|chainsaw|mixer machine|buffing wheel|welding stinger'),
        ('Materials', 'wood|paper|metal|rod|brick|stone|glue|tape|sandpaper|clay|lubricant|cement|tile|paint|rubber|stick|sand|plastic|plaster|cardboard|metal rod|marble|silicone|grout|paste|ceramic|wood dust|sheet|foam|adhesive|mud|plastic piece|wax|concrete block|sealant|wicker|roll|plastic paper'),
        ('Hardware', 'wire|string|screw|rope|nut|key|button|handle|rubber band|chain|gear|strap|hinge|knob|clip|pin|spacer|keychain|hardware|bearing|bolt|dial|roller|keys|gasket|fuse|control knob|anail|filter|pin cover|nail|buckle|grip|washer|seal|mechanical seal|air filter|machine part|mounting plate|part'),
        ('Garden', 'plant|hose|mower|shovel|flower|soil|sickle|leaf|rake|grass|watering can|seed|turf tracer|blower|pruner|weedkiller|hoe|leaves|leaf blower'),
        ('Vehicles & parts', 'wheel|bicycle|pump|pedal|engine|stroller|car|motorcycle|handlebar|handlebars|scooter|sprocket|inner tube|baby stroller|brake rotor|wheel hub|seat belt|vespa|electric scooter|bike part|air pump nozzle|golf cart|tire|windshield|motorbike|motorcycle stand|gearbox|hand truck|tire changer|crank axle|brake disc|steering|padel|chassis|spark plug|handlebar 2|steering knuckle'),
        ('Electronics', 'phone|computer|tablet|mouse|remote control|device|battery|chip|keyboard|flashlight|headphones|camera|watch|torch|headphone|plug|searchlight|calculator|optical alignment system|thermostat|camera stand|clock|lamp socket|chandelier|smart watch|mic|turntable|printer|smartwatch|speaker|flash|control panel|flash drive|tripod|mouse pad|radio'),
        ('Textiles & wear', 'garment|glove|shoe|needle|fabric|mask|sewing machine|helmet|blanket|quilt|hat|hairpin|ring|bicycle helmet|clothespin|burlap|nail polish|eyeglasses|clothes|hard hat|sunglasses|bedsheet|bracelet|razor'),
        ('Arts & play', 'artwork|puzzle or game piece|book|toy|pen|playing cards|ball|dumbbell|palette|piano|golf club|pottery|guitar|saxophone|treadmill|game|poster'),
        ('Instruments', 'thermometer|timer|pipette|syringe|timer watch|test tube|medical pistol|ampoule'),
        ('Living subjects', "dog|cat|finger|child's hand|baby chick|insect|hands|animal"),
    ],
}


def clean_label(value):
    base = (value or '').split('(')[0].split('/')[0].replace('_', ' ').strip().lower()
    return {'press push': 'press', 'vegetable fruit': 'vegetable'}.get(base, base)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', type=Path, default=SOURCE)
    parser.add_argument('--taxonomy', type=Path, help='STA JSON containing verb_categories and noun_categories')
    parser.add_argument('--output', type=Path, default=Path('src/lib/data/dataset-distributions.json'))
    parser.add_argument('--audit-dir', type=Path, default=Path('reports/semantic-audit'))
    args = parser.parse_args()
    source_bytes = args.source.read_bytes()
    events = json.loads(source_bytes)
    taxonomy = json.loads(args.taxonomy.read_text()) if args.taxonomy else None
    result = {'total': len(events), 'source': str(args.source),
              'sourceSha256': hashlib.sha256(source_bytes).hexdigest(),
              'basis': 'stored_annotation_ids',
              'taxonomyVerified': taxonomy is not None, 'panels': []}
    audit = {'source': str(args.source), 'sourceSha256': result['sourceSha256'],
             'totalEvents': len(events), 'taxonomy': str(args.taxonomy) if taxonomy else None,
             'method': 'Counts use stored integer IDs >= 0. No assignments are changed. Without a taxonomy file, display labels are the most frequent observed string per ID; these are not verified canonical names. Label variation and cross-ID reuse are review signals, not proven errors.',
             'dimensions': {}}
    review = []
    for dimension, field in [('actions', 'ego4d_verb'), ('objects', 'ego4d_noun')]:
        category_key = 'verb_categories' if dimension == 'actions' else 'noun_categories'
        canonical = {c['id']: c['name'] for c in taxonomy[category_key]} if taxonomy else {}
        by_id, by_label = defaultdict(Counter), defaultdict(Counter)
        unresolved, invalid, missing = Counter(), Counter(), 0
        for event_id, event in events.items():
            semantic = event.get('semantic_annotation', {})
            label, category_id = semantic.get(field), semantic.get(field + '_id')
            if type(category_id) is int and category_id >= 0:
                by_id[category_id][label or ''] += 1
                by_label[clean_label(label)][category_id] += 1
                if taxonomy and category_id not in canonical:
                    invalid[category_id] += 1
            elif category_id == -1:
                unresolved[label or ''] += 1
            else:
                missing += 1
        rows = []
        for category_id, labels in sorted(by_id.items()):
            representative = sorted(labels, key=lambda label: (-labels[label], label))[0]
            full_label = canonical.get(category_id, representative)
            label = clean_label(full_label) or f'ID {category_id}'
            # Keep single sense qualifiers: nut (food) and nut (tool) are distinct IDs.
            if '(' in full_label and ',' not in full_label:
                label = full_label.replace('_', ' ').strip().lower()
            rows.append({'id': category_id, 'label': label, 'count': sum(labels.values()),
                         'labelVerified': category_id in canonical,
                         'observedLabelVariants': len(labels)})
        groups, selected = [], set()
        for title, label_string in GROUPS[dimension]:
            names = set(label_string.split('|'))
            group_rows = [row for row in rows if row['id'] not in selected and clean_label(row['label']) in names]
            selected.update(row['id'] for row in group_rows)
            if group_rows:
                groups.append({'title': title, 'rows': sorted(group_rows, key=lambda row: (-row['count'], row['id']))})
        remaining = [row for row in rows if row['id'] not in selected]
        if remaining:
            groups.append({'title': 'Other IDs', 'rows': sorted(remaining, key=lambda row: (-row['count'], row['id']))})
        mapped = sum(row['count'] for row in rows)
        unmapped = sum(unresolved.values())
        assert mapped + unmapped + missing == len(events)
        assert len({row['id'] for group in groups for row in group['rows']}) == len(rows)
        panel = {'key': dimension, 'title': dimension.title(), 'labelCount': len(rows),
                 'mappedEvents': mapped, 'unmappedEvents': unmapped, 'missingEvents': missing,
                 'coveragePercent': round(mapped / len(events) * 100, 4), 'groups': groups}
        result['panels'].append(panel)
        cross_id = {label: dict(sorted(counts.items())) for label, counts in sorted(by_label.items()) if len(counts) > 1}
        details = {**{k: v for k, v in panel.items() if k != 'groups'},
                   'invalidTaxonomyIds': dict(invalid),
                   'unmappedLabels': dict(unresolved.most_common()), 'labelsAcrossMultipleIds': cross_id,
                   'classes': [{**row, 'observedLabels': dict(by_id[row['id']].most_common())} for row in rows]}
        audit['dimensions'][dimension] = details
        for event_id, event in events.items():
            semantic = event.get('semantic_annotation', {})
            category_id, label = semantic.get(field + '_id'), semantic.get(field)
            reasons = []
            if category_id == -1:
                reasons.append('unmapped_id')
            elif type(category_id) is not int or category_id < 0:
                reasons.append('missing_or_invalid_id')
            else:
                if taxonomy and category_id not in canonical:
                    reasons.append('id_not_in_taxonomy')
                if clean_label(label) in cross_id:
                    reasons.append('label_used_with_multiple_ids')
                if len(by_id[category_id]) > 1:
                    reasons.append('multiple_labels_for_id')
            if reasons:
                review.append({'event_id': event_id, 'dimension': dimension, 'stored_id': category_id,
                               'stored_label': label, 'reasons': '|'.join(reasons),
                               'description': semantic.get('interaction_description', '')})
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + '\n')
    args.audit_dir.mkdir(parents=True, exist_ok=True)
    (args.audit_dir / 'summary.json').write_text(json.dumps(audit, indent=2) + '\n')
    with (args.audit_dir / 'review.csv').open('w', newline='') as handle:
        writer = csv.DictWriter(handle, fieldnames=['event_id', 'dimension', 'stored_id', 'stored_label', 'reasons', 'description'])
        writer.writeheader()
        writer.writerows(review)
    print(', '.join(f"{p['labelCount']} {p['key']} IDs; {p['unmappedEvents']} unmapped; {p['missingEvents']} missing" for p in result['panels']))


if __name__ == '__main__':
    main()
