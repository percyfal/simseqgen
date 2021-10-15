#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Simulate genealogies"""
import os
import re
import pathlib
import collections
import itertools
import tempfile
from random import choices
import tskit
import msprime
import cyvcf2
from Bio import SeqIO
from Bio.Seq import Seq
from Bio.SeqRecord import SeqRecord
import logging

FORMAT = "%(levelname)s:simseqgen:%(asctime)-15s %(message)s"
logging.basicConfig(format=FORMAT, level=logging.INFO)
logger = logging.getLogger("simseqgen")


def update_individual_metadata(ts):
    """Update individual metadata in ts object.

    Returns new list of individuals with updated metadata
    """
    individuals = []
    oldname = None
    i = 0
    for ind in ts.individuals():
        popindex = ts.nodes()[ind.nodes[0]].population
        popname = ts.population(popindex).metadata["name"]
        if oldname is not None and oldname != popname:
            i = 0
        oldname = popname
        name = f"tsk_{ind.id}_{popname}_{i}"
        md = {
            "id": ind.id,
            "tskit_id": f"tsk_{ind.id}",
            "name": name,
            "popname": popname,
            "ind_index": i,
            "population": ts.population(popindex),
            "description": (
                f"tskit_individual:tsk_{ind.id}, name:{name}, "
                f"population:{ts.population(popindex)}"
            ),
            "is_reference": False,
        }
        md["vcfheader"] = (
            f"##<SAMPLE=<ID={md['tskit_id']},Name={md['name']},"
            f"Index={md['id']},Population={md['popname']},"
            f"Description=\"{md['population'].metadata['description']}\">"
        )
        newind = ind.replace(metadata=md)
        individuals.append(newind)
        i = i + 1
    return individuals


def set_reference_individual(ref, individuals):
    if ref is None:
        return individuals
    values = ref.split(":")
    refpop = int(values[0]) if re.match(r"\d+", values[0]) else values[0]
    refind = int(values[1])
    for i, ind in enumerate(individuals):
        if ind.metadata["ind_index"] == refind:
            if (
                ind.metadata["population"].id == refpop
                or ind.metadata["popname"] == refpop
            ):
                ind.metadata["is_reference"] = True
                individuals[i] = ind
                break
    return individuals


def partition_individuals(individuals):
    def _filter_reference(ind):
        return ind.metadata["is_reference"]

    return list(filter(_filter_reference, individuals)), list(
        itertools.filterfalse(_filter_reference, individuals)
    )


def make_sequence(ts, individual, node, haplotype, reference):
    """Create DNA sequence with variants at sites"""
    seqid = f"tsk_{individual.id}-{haplotype}"
    for site, variant in zip(ts.sites(), list(ts.haplotypes())[node]):
        i = int(site.position)
        reference[i] = variant
    desc = (
        f"id:{individual.id}, node:{node}, name:{individual.metadata['name']}, "
        f"haplotype:{haplotype}, "
        f"population:{individual.metadata['population']}"
    )
    record = SeqRecord(
        Seq("".join(reference)),
        name=individual.metadata["name"],
        id=seqid,
        description=desc,
    )
    return record


def write_variants(ref_ind, individuals, vcf_tmp_fn, outdir, prefix):
    """Write variants to output vcf.

    If reference vcf is provided flip alleles where necessary
    """
    vcf_ref = None
    if len(ref_ind) > 0:
        vcf_ref = cyvcf2.VCF(vcf_tmp_fn, samples=ref_ind[0].metadata["tskit_id"])

    vcf_out = outdir / f"{prefix}.vcf.gz"
    logger.info(f"Writing output vcf {vcf_out}")
    samples = [ind.metadata["tskit_id"] for ind in individuals]
    vcf_tmp = cyvcf2.VCF(vcf_tmp_fn, samples=samples)
    vcfwriter = cyvcf2.cyvcf2.Writer(str(vcf_out), vcf_tmp, "wz")
    for ind in individuals:
        vcfwriter.add_to_header(ind.metadata["vcfheader"])
    if vcf_ref is None:
        vcfwriter.set_samples(vcf_tmp.samples)
        for variant in vcf_tmp:
            vcfwriter.write_record(variant)
    else:
        # in cyvcf2: Pick one individual *haplotype* as reference: this
        # individual should have only 0's, so all calls at a site with a
        # derived allele should be flipped for all individuals.
        for gt, variant in zip(vcf_ref, vcf_tmp):
            ref = gt.genotypes[0][0]
            if ref == 1:
                # Flip states for all other genotypes
                for i in range(len(variant.genotypes)):
                    alleles = variant.genotypes[i]
                    variant.genotypes[i] = [1 - alleles[0], 1 - alleles[1], alleles[2]]
                variant.genotypes = variant.genotypes
                variant.REF = gt.ALT[0]
                variant.ALT = [gt.REF]
            vcfwriter.write_record(variant)
    vcfwriter.close()


def run(
    *,
    tsfile,
    reference_chromosome=None,
    prefix="simseqgen",
    outdir=pathlib.Path(os.curdir),
    single=False,
    refseq_fn=None,
):
    """Runner to generate vcf and fasta output from a tree sequence

    Args:
      tsfile (str): tree sequence file name
      reference_chromosome (str): reference chromosome identifier formatted as
        <population_id>:<individual_index>, where the index refers to
        the index within the population
      prefix (str): prefix of output files
      outdir (path): output directory path
      single (bool): write fasta sequences to separate files
      refseq_fn (str): reference sequence file name to base output

    """
    ts = tskit.load(tsfile)
    individuals = update_individual_metadata(ts)
    individuals = set_reference_individual(reference_chromosome, individuals)
    ref_ind, individuals = partition_individuals(individuals)

    vcf_tmp_fn = tempfile.mkstemp(suffix=".vcf")[1]
    logger.info(f"Writing temporary ts vcf {vcf_tmp_fn}")
    with open(vcf_tmp_fn, "w") as fh:
        ts.write_vcf(fh)

    write_variants(ref_ind, individuals, vcf_tmp_fn, outdir, prefix)

    logger.info("Writing fasta sequences")
    # Make fasta sequences
    reference = None
    if refseq_fn is None:
        dna = ["A", "C", "G", "T"]
        reference = choices(dna, k=int(ts.sequence_length))
    # Reference individual; only print first node
    if len(ref_ind) > 0:
        ind = ref_ind[0]
        node = ind.nodes[0]
        haplotype = node % len(ind.nodes)
        rec = make_sequence(ts, ind, node, haplotype, reference)
        ref_out = outdir / f"{prefix}.reference.fasta"
        SeqIO.write(rec, ref_out, "fasta")
    if not single:
        seq_out = outdir / f"{prefix}.fasta"
        fh = open(seq_out, "w")
    for ind in individuals:
        nodes = ind.nodes
        for node in nodes:
            haplotype = node % len(nodes)
            rec = make_sequence(ts, ind, node, haplotype, reference)
            if single:
                SeqIO.write(rec, f"{rec.id}.fasta", "fasta")
            else:
                SeqIO.write(rec, fh, "fasta")
