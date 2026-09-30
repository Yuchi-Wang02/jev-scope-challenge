"""Render a standalone research figure, or verify its data and saved assets offline."""
import argparse
import hashlib
import importlib.util
import json
import xml.etree.ElementTree as ET
from pathlib import Path

HERE = Path(__file__).resolve().parent
FIGURES = HERE / 'figures'
DEFINITION = importlib.util.spec_from_file_location('ownership_figure_analysis', HERE / 'analyze.py')
analysis = importlib.util.module_from_spec(DEFINITION)
DEFINITION.loader.exec_module(analysis)
LABELS = {
    'joint_full': 'Joint routing, full records',
    'joint_gated': 'Joint routing + ID gate',
    'direct_full': 'Direct, full records',
    'direct_filtered': 'Direct, filtered records',
    'single_full': 'Direct, full (one order)',
    'single_filtered': 'Direct, filtered (one order)',
    'known_grammar': 'Known-grammar code',
    'always_defer': 'Always defer'}


def digest(payload):
    return hashlib.sha256(payload).hexdigest()


def pretty(value):
    return (json.dumps(value, indent=2, ensure_ascii=False, allow_nan=False) + '\n').encode('utf-8')


def chart_data():
    result = analysis.analyze()
    summary = result['summary']
    return {'title': 'Same records, different request',
            'population': '24 constructed parent pairs / 48 target views; zero independent human annotations',
            'model': 'Historical Kev-LoRA N1, native causal logits; no new Jev evaluation',
            'execution_commit': summary['execution_commit'], 'config_hash': summary['config_hash'],
            'physical_scientific_forwards': 500, 'scientific_input_tokens': 188797,
            'warmup_forwards': 2,
            'rows': [{'method': method, 'label': label,
                      **{key: summary['methods'][method][key] for key in
                         ('complete_pairs_correct', 'parent_pairs', 'false_commitments',
                          'uncertain_views', 'correct_decisions', 'views', 'model_calls', 'input_tokens')}}
                     for method, label in LABELS.items()],
            'limits': 'Shared outputs and anchors are not extra calls. Code knows the inspected grammar. No confidence intervals or generalization claim.'}


def render(data):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    from matplotlib.ticker import MultipleLocator

    plt.rcParams.update({'font.family': 'DejaVu Sans', 'font.size': 10,
                         'svg.hashsalt': 'request-ownership-v0.1', 'svg.fonttype': 'none'})
    fig, axes = plt.subplots(1, 2, figsize=(12, 6.5), gridspec_kw={'width_ratios': [2, 1]})
    fig.subplots_adjust(left=.245, right=.94, top=.78, bottom=.19, wspace=.22)
    fig.suptitle(data['title'], x=.035, y=.972, ha='left', fontsize=21, weight='bold', color='#25343e')
    fig.text(.035, .915, 'Historical Kev-adapted 4B / native readout · 24 paired scenes · 0 independent human annotations',
             fontsize=10, color='#56656b')
    definitions = [('complete_pairs_correct', 24, 'Complete pairs correct', 'Higher is better · out of 24'),
                   ('false_commitments', 12, 'False commitments', 'Lower is better · out of 12 uncertain views')]
    for axis, (metric, maximum, title, subtitle) in zip(axes, definitions):
        for index, row in enumerate(data['rows']):
            model = row['method'] not in ('known_grammar', 'always_defer')
            color = '#ca8a25' if row['method'] == 'joint_gated' else '#356b87' if model else '#e5e8ea'
            axis.barh(index, row[metric], height=.58, color=color, edgecolor='#53616a', linewidth=.5)
            axis.text(row[metric] + .27, index, f"{row[metric]}/{maximum}", va='center', fontsize=10,
                      color='#263d49', weight='bold' if row['method'] == 'joint_gated' else 'normal')
        axis.set_xlim(0, maximum * 1.19)
        axis.set_ylim(len(data['rows']) - .35, -.65)
        axis.set_yticks(range(len(data['rows'])))
        axis.set_yticklabels([row['label'] for row in data['rows']] if metric == 'complete_pairs_correct' else [])
        axis.xaxis.set_major_locator(MultipleLocator(6 if maximum == 24 else 3))
        axis.set_xticks(list(range(0, maximum + 1, 6 if maximum == 24 else 3)))
        axis.tick_params(axis='both', length=0, pad=8, labelcolor='#455762')
        axis.grid(axis='x', color='#e4e7e9', linewidth=.6)
        axis.set_axisbelow(True)
        for edge in ('top', 'right', 'left'):
            axis.spines[edge].set_visible(False)
        axis.spines['bottom'].set_color('#aebac0')
        axis.set_title(title + '\n' + subtitle, loc='left', fontsize=10, pad=15, color='#334d5b')
        axis.axhline(5.5, color='#c6cfd3', linewidth=.8)
    fig.text(.035, .107, 'Both target views must be correct for a complete pair. The program gate adds no model forward.',
             fontsize=9, color='#435963')
    fig.text(.035, .073, '500 scientific forwards / 188,797 input tokens + 2 unscored warmups. Method rows share outputs.',
             fontsize=9, color='#435963')
    fig.text(.035, .039, 'New scenes reuse inspected language and policy grammar. Pure code knows that grammar; this is a diagnostic.',
             fontsize=9, color='#435963')
    FIGURES.mkdir(exist_ok=True)
    description = json.dumps(data, ensure_ascii=False, separators=(',', ':'), allow_nan=False)
    fig.savefig(FIGURES / 'ownership_results.svg', metadata={'Date': None, 'Description': description})
    svg_path = FIGURES / 'ownership_results.svg'
    normalized_svg = '\n'.join(line.rstrip() for line in svg_path.read_text(encoding='utf-8').splitlines()) + '\n'
    svg_path.write_bytes(normalized_svg.encode('utf-8'))
    fig.savefig(FIGURES / 'ownership_results.png', dpi=180,
                metadata={'Description': description, 'Software': 'Matplotlib ' + matplotlib.__version__})
    plt.close(fig)
    return matplotlib.__version__


def verify(data):
    if (FIGURES / 'chart_data.json').read_bytes() != pretty(data):
        raise ValueError('Figure data differs from verified scientific results')
    manifest = json.loads((FIGURES / 'manifest.json').read_text(encoding='utf-8'))
    actual = {name: digest((FIGURES / name).read_bytes()) for name in
              ('ownership_results.svg', 'ownership_results.png', 'chart_data.json')}
    if (manifest['asset_sha256'] != actual or manifest['config_hash'] != data['config_hash'] or
            manifest['generator_sha256_lf'] != analysis.execution.sha(Path(__file__).read_bytes())):
        raise ValueError('Figure generator or asset bytes differ from publication manifest')
    tree = ET.fromstring((FIGURES / 'ownership_results.svg').read_bytes())
    description = tree.find('.//{http://purl.org/dc/elements/1.1/}description')
    if description is None or json.loads(description.text) != data:
        raise ValueError('SVG embedded provenance differs from reviewed chart data')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command', choices=('build', 'verify'))
    args = parser.parse_args()
    data = chart_data()
    if args.command == 'build':
        version = render(data)
        (FIGURES / 'chart_data.json').write_bytes(pretty(data))
        manifest = {'status': 'rendered_scientific_figure', 'matplotlib_version': version,
                    'config_hash': data['config_hash'],
                    'generator_sha256_lf': analysis.execution.sha(Path(__file__).read_bytes()),
                    'asset_sha256': {name: digest((FIGURES / name).read_bytes()) for name in
                                     ('ownership_results.svg', 'ownership_results.png', 'chart_data.json')},
                    'verification_limit': 'Verifies source-derived chart rows, SVG metadata and saved assets; it does not rerender across Matplotlib versions.'}
        (FIGURES / 'manifest.json').write_bytes(pretty(manifest))
    verify(data)
    print(json.dumps({'status': 'passed', 'command': args.command, 'methods': len(data['rows']),
                      'scientific_inference_calls_this_command': 0}))


if __name__ == '__main__':
    main()
