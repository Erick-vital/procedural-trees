"""CLI pública de generación y evaluación F2."""
import argparse
import json
from pathlib import Path
import sys
from .contracts import load_spec
from .runner import execute, execute_blueprint, batch
from .evaluation import validate_result, compare


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest='command', required=True)
    generate = commands.add_parser('generate')
    generate.add_argument('spec', type=Path)
    generate.add_argument('--output', required=True, type=Path)
    generate.add_argument('--no-render', action='store_true')
    generate.add_argument('--timeout', type=float, default=120)
    commands.add_parser('blueprints', help='Listar recetas registradas y sus versiones')
    blueprint = commands.add_parser('generate-blueprint', help='Generar un ejemplar desde una receta explícita')
    blueprint.add_argument('blueprint', type=Path)
    blueprint.add_argument('--instance', type=Path, required=True)
    blueprint.add_argument('--output', type=Path, required=True)
    blueprint.add_argument('--no-render', action='store_true')
    blueprint.add_argument('--timeout', type=float, default=120)
    plan = commands.add_parser('plan-blueprints', help='Validar y congelar propuestas de Codex (F4)')
    plan.add_argument('blueprint', type=Path)
    plan.add_argument('--request', type=Path, required=True)
    plan.add_argument('--output', type=Path, required=True)
    planned = commands.add_parser('generate-blueprint-plan', help='Reproducir un plan F4 sin consultar modelos')
    planned.add_argument('plan', type=Path)
    planned.add_argument('--output', type=Path, required=True)
    planned.add_argument('--render', action='store_true')
    planned.add_argument('--timeout', type=float, default=120)
    branch_tree = commands.add_parser('generate-branch-tree', help='Generar árbol ramificado completo con/sin follaje (R4)')
    branch_tree.add_argument('definition', type=Path)
    branch_tree.add_argument('--profile', required=True)
    branch_tree.add_argument('--base-seed', required=True, type=int)
    branch_tree.add_argument('--canopy-seed', required=True, type=int)
    branch_tree.add_argument('--paint-seed', required=True, type=int)
    branch_tree.add_argument('--output', required=True, type=Path)
    growth = commands.add_parser('generate-oak-growth', help='Arquitectura de roble por madurez (O1)')
    growth.add_argument('preset', type=Path)
    growth.add_argument('--seed', type=int, required=True)
    growth.add_argument('--output', type=Path, required=True)
    bat = commands.add_parser('batch')
    bat.add_argument('--cases', type=Path, default=Path('presets/f2-cases.json'))
    bat.add_argument('--output', type=Path, required=True)
    bat.add_argument('--timeout', type=float, default=120)
    val = commands.add_parser('validate')
    val.add_argument('job', type=Path)
    comp = commands.add_parser('compare')
    comp.add_argument('left', type=Path)
    comp.add_argument('right', type=Path)
    comp.add_argument('--output', type=Path, required=True)
    serve = commands.add_parser('serve')
    serve.add_argument('--port', type=int, default=8765)
    serve.add_argument('--jobs', type=Path, default=Path('artifacts/api'))
    args = parser.parse_args()
    try:
        if args.command == 'generate':
            result = execute(args.spec, args.output, not args.no_render, args.timeout)
        elif args.command == 'generate-blueprint':
            result = execute_blueprint(args.blueprint, args.instance, args.output, not args.no_render, args.timeout)
        elif args.command == 'blueprints':
            from .blueprints import registered_blueprints
            result = {'blueprints': registered_blueprints()}
        elif args.command == 'plan-blueprints':
            from .language import prepare_plan
            result = prepare_plan(args.blueprint, args.request, args.output)
        elif args.command == 'generate-blueprint-plan':
            from .language import execute_plan
            result = execute_plan(args.plan, args.output, args.render, args.timeout)
        elif args.command == 'generate-branch-tree':
            from .branch_tree_runner import execute_branch_tree
            result = execute_branch_tree(args.definition, {'profile': args.profile, 'seeds': {
                'base': args.base_seed, 'canopy': args.canopy_seed, 'paint': args.paint_seed}}, args.output)
        elif args.command == 'generate-oak-growth':
            from .oak_growth_runner import execute_growth
            result = execute_growth(args.preset, args.seed, args.output)
        elif args.command == 'batch':
            result = batch(args.cases, args.output, args.timeout)
        elif args.command == 'validate':
            result = validate_result(args.job)
        elif args.command == 'compare':
            result = compare(args.left, args.right, args.output)
        else:
            from .api import serve
            serve(args.jobs, args.port)
            return 0
        print(json.dumps(result, indent=2))
        return 1 if result.get('status') == 'failed' else 0
    except (ValueError, OSError, RuntimeError, KeyError, TypeError, IndexError) as exc:
        print(f'ERROR: {exc}', file=sys.stderr)
        return 1


if __name__ == '__main__':
    sys.exit(main())
