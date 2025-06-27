from shutil import copyfile
import subprocess
import argparse
from pathlib import Path

def run_command(cmd, work_dir=None):
    print(f"Running: {' '.join(cmd)}")
    subprocess.run(cmd, cwd=work_dir, check=True)

def build_snpeff_db(genome_id, fasta, gff, snpeff_dir):
    """Build a snpEff database for a given genome using FASTA and GFF files."""
    data_dir = Path(snpeff_dir) / "data" / genome_id
    data_dir.mkdir(parents=True, exist_ok=True)

    # copy input files to snpEff data dir
    copyfile(fasta, data_dir / "sequences.fa")
    copyfile(gff, data_dir / "genes.gff")

    # update snpEff config file
    config_line = f"{genome_id}.genome : CustomGenome\n"
    config_path = Path(snpeff_dir) / "snpEff.config"
    with open(config_path, "a") as f:
        f.write(config_line)

    # build the database
    run_command(["java", "-Xmx4g", "-jar", "snpEff.jar", "build", "-gff3", "-noCheckCds", "-noCheckProtein", "-v", genome_id], work_dir=snpeff_dir)

def run_snpeff(genome_id, vcf, output_vcf, snpeff_dir):
    """Run snpEff on a VCF using the specified genome database; limit annotation window to +/- 5bp from variant site."""

    data_dir = Path(snpeff_dir) / "data" / genome_id
    # ensure that the VCF is placed in the snpEff data directory
    data_dir.mkdir(parents=True, exist_ok=True)
    vcf_path = data_dir / "variants.vcf"
    copyfile(vcf, vcf_path)

    with open(output_vcf, "w") as out:
        subprocess.run(
            ["java", "-Xmx4g", "-jar", "snpEff.jar", "-no-intergenic", "-no-upstream", "-no-downstream", "-ud", "5", genome_id, vcf_path],
            cwd=snpeff_dir,
            stdout=out,
            check=True
        )

def main():
    parser = argparse.ArgumentParser(description="Build Snpeff database and annotate VCF")
    parser.add_argument("--genome-id", help="Name for reference genome to use for snpEff db building", default="ref_genome")
    parser.add_argument("--fasta", help="Path to the validated, decompressed fasta", required=True)
    parser.add_argument("--gff", help="Path to the validated, decompressed gff", required=True)
    parser.add_argument("--vcf", help="Path to the validated, decompressed vcf", required=True)
    parser.add_argument("--output_vcf", help="Path to the output vcf with snpEff annotations", required=True)
    parser.add_argument("--snpeff_dir", help="Path to the snpEff directory", default="snpEff")
    args = parser.parse_args()

    build_snpeff_db(args.genome_id, args.fasta, args.gff, args.snpeff_dir)
    run_snpeff(args.genome_id, args.vcf, args.output_vcf, args.snpeff_dir)

if __name__ == "__main__":
    main()
