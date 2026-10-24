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
