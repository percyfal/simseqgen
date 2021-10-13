"""Console script for simseqgen."""
import os
import pathlib
import argparse
import simseqgen


def run_make_references(args):
    if args.outdir is None:
        args.outdir = pathlib.Path(os.curdir)
    simseqgen.generate_references.run(
        args.ts, args.reference_chromosome, args.prefix, args.outdir, args.single_fasta
    )


def run_repo(args):
    if args.ls:
        print("{0: <30}uri".format("name"))
        for k, v in simseqgen.repo.demography_models.items():
            print("{: <30}{}".format(k, v))


def add_make_ref_subcommand(subparsers):
    parser = subparsers.add_parser(
        "make_ref",
        help="Convert tree sequence file to variant output and fasta sequences",
    )
    parser.add_argument(
        "ts",
        help=("Tree sequence file obtained from a sequence simulator"),
    )
    parser.add_argument(
        "--reference_chromosome",
        "-r",
        help=(
            "Select chromosome from reference population to represent reference sequence."
            "The identifier string must be provided as <population identifier>:<index>."
        ),
    )
    parser.add_argument(
        "--prefix",
        "-p",
        action="store",
        help="output prefix for output files",
        default="simseqgen",
    )
    parser.add_argument("--outdir", "-o", action="store", help="output directory")
    parser.add_argument(
        "--single-fasta",
        "-s",
        action="store_true",
        help="write all sequences to one fasta file",
    )
    parser.set_defaults(runner=run_make_references)


def add_repo_subcommand(subparsers):
    parser = subparsers.add_parser("repo", help="Commands to manipulate repo")
    parser.add_argument(
        "--ls",
        action="store_true",
        help=("List available demographic models"),
    )
    parser.set_defaults(runner=run_repo)


def get_simseqgen_parser():
    top_parser = argparse.ArgumentParser(
        description="Command line interface for simseqgen."
    )
    top_parser.add_argument(
        "-V", "--version", action="version", version=f"%(prog)s {simseqgen.__version__}"
    )

    subparsers = top_parser.add_subparsers(dest="subcommand")
    subparsers.required = True

    add_make_ref_subcommand(subparsers)
    add_repo_subcommand(subparsers)

    return top_parser


def main(arg_list=None):
    """Console script for simseqgen."""
    parser = get_simseqgen_parser()
    args = parser.parse_args(arg_list)
    args.runner(args)


if __name__ == "__main__":
    main()
