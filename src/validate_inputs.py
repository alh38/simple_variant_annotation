import os
import gzip
import shutil
import subprocess
import argparse

def is_gzipped(file_path):
    return file_path.endswith('.gz')

def validate_vcf(file_path):
    """Validate that the VCF file has a valid extension and contains a header line starting with '#CHROM"""
    if not file_path.endswith(('.vcf', '.vcf.gz')):
        raise ValueError(f"VCF file does not have a valid extension: {file_path}")
    # assign opener function based on whether file appears to be gzipped
    opener = gzip.open if is_gzipped(file_path) else open
    with opener(file_path, 'rt') as f:
        for line in f:
            if line.startswith("#CHROM"):
                return True
        raise ValueError(f"VCF file is missing a header line starting with '#CHROM': {file_path}")

def validate_fasta(file_path):
    """Validate that the FASTA file has a valid extension and starts with a '>' character"""
    if not file_path.endswith(('.fa', '.fasta', '.fa.gz', '.fasta.gz', '.fna', '.fna.gz')):
        raise ValueError(f"FASTA file does not have a valid extension: {file_path}")
    opener = gzip.open if is_gzipped(file_path) else open
    with opener(file_path, 'rt') as f:
        first_line = f.readline()
        if not first_line.startswith('>'):
            raise ValueError(f"FASTA file does not start with '>': {file_path}")

def validate_gff(file_path):
    """Validate that the GFF file has a valid extension and contains at least one feature line with tab-separated 9 fields"""
    if not file_path.endswith(('.gff', '.gff3', '.gff.gz', '.gff3.gz')):
        raise ValueError(f"GFF file does not have a valid extension: {file_path}")
    opener = gzip.open if is_gzipped(file_path) else open
    with opener(file_path, 'rt') as f:
        for line in f:
            if line.startswith("#"):
                continue
            parts = line.strip().split('\t')
            if len(parts) == 9:
                return True
        raise ValueError(f"GFF file has no valid feature lines with the expected 9 fields: {file_path}")

def decompress_if_needed(file_path, dest_path):
    """Decompress a gzipped file if needed, otherwise copy it to the destination directory"""
    filename = os.path.basename(file_path)
    if is_gzipped(file_path):
        with gzip.open(file_path, 'rb') as f_in, open(dest_path, 'wb') as f_out:
            shutil.copyfileobj(f_in, f_out)
    else:
        shutil.copy(file_path, dest_path)
    return dest_path

def prepare_inputs(vcf, fasta, gff,):
    """Prepare and validate input files for snpEff annotation"""

    for path in [vcf, fasta, gff]:
        if not os.path.exists(path):
            raise FileNotFoundError(f"File does not exist: {path}")
        if os.path.getsize(path) == 0:
            raise ValueError(f"File is empty: {path}")

    # validate inputs
    validate_vcf(vcf)
    validate_fasta(fasta)
    validate_gff(gff)

    # decompress inputs if gzipped; copy decompressed files to output directory
    vcf_out = decompress_if_needed(vcf, 'variants.vcf')
    fasta_out = decompress_if_needed(fasta, 'ref.fa')
    gff_out = decompress_if_needed(gff, 'annotations.gff')

    return vcf_out, fasta_out, gff_out

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Validate inputs")
    parser.add_argument("--vcf", help="Path to the input VCF")
    parser.add_argument("--fasta", help="Path to the input fasta")
    parser.add_argument("--gff", help="Path to the input GFF")
    args = parser.parse_args()

    try:
        vcf_out, fasta_out, gff_out = prepare_inputs(args.vcf, args.fasta, args.gff)
    except (ValueError, FileNotFoundError) as e:
        print(f"Validation error: {e}")
        exit(1)