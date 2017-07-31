#!/usr/bin/env python3

import argparse
import importlib
import pkgutil

from analysis import scripts


def main():
    parser = argparse.ArgumentParser(description='Analyze ATLeS experiment tracks.')
    subparsers = parser.add_subparsers()
    # Make the subcommand required in Python 3.3+ (https://stackoverflow.com/a/18283730/7938656)
    subparsers.required = True
    subparsers.dest = 'command'

    # add parsers for scripts in analysis
    for finder, name, ispkg in pkgutil.iter_modules(scripts.__path__):
        full_name = scripts.__name__ + '.' + name
        mod = importlib.import_module(full_name)
        parser_mod = subparsers.add_parser(mod.name, help=mod.help)
        mod.register_arguments(parser_mod)
        parser_mod.set_defaults(run_func=mod.run)
        parser_mod.set_defaults(show_func=mod.show)
        parser_mod.set_defaults(save_func=mod.save)
        # all commands get the outfile argument
        parser_mod.add_argument('outfile', type=argparse.FileType('w'), nargs='?', help="Optional output file.  If not specified, output is displayed in a window.")

    args = parser.parse_args()
    ret = args.run_func(args)  # noqa: F841

    if args.outfile is None:
        args.show_func()
    else:
        print("Saving output to {}...".format(args.outfile.name))
        if args.save_func:
            args.save_func(args.outfile.name)
        else:
            # for animations, we have to call the save() method on the animation itself
            ret.save(args.outfile.name)


if __name__ == '__main__':
    main()
