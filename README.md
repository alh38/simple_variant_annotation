# simple_variant_annotation
## Intended use case:
This workflow is intended to take reference-based variant calls, along with the reference fasta used to generate the vcf and a gff file containing annotations for the reference, and produce a user-friendly csv report containing some key information about each variant call, along with predictions about the consequences of each variant that appears within or immediately adjacent to an annotated protein-coding gene.

## Inputs:
- A vcf file produced by a standard small variant calling tool, such as Freebayes, DeepVariant, or GATK HaplotypeCaller
- The reference fasta file used to generate the vcf  
- A gff file containing annotations for the reference (adhering to gff3 standards - see [here](http://useast.ensembl.org/info/website/upload/gff3.html))

## Outputs:
- `outputs/variants.ann.vcf`: a vcf file with SnpEff annotations (appending to the INFO field of each annotated variant call as an ANN string [see SnpEff documentation for more information])
- `outputs/report.csv`: a csv report containing some key information about each variant allele called, along with predictions about the consequences of each variant that appears within or immediately adjacent to an annotated protein-coding gene
	- `CHROM`: the chromosome or contig in the reference that the variant was called in
	- `POS`: the position in CHROM that the variant was called at
	- `REF`: the allele at POS in the reference sequence
	- `ALT`: the variant allele called at POS
	- `QUAL`: the quality of the variant call (see documentation for variant caller used to generate vcf for more information on interpretation)
  	- `annotation`: the SnpEff-predicted variant effect (e.g., missense_variant, frameshift_variant, etc; see [SnpEff documentation on the ANN field](https://pcingola.github.io/SnpEff/snpeff/inputoutput/#ann-field-vcf-output-files) for more information)
	- `gene_id`: the gene identifier associated with the annotation (see [SnpEff documentation on the ANN field](https://pcingola.github.io/SnpEff/snpeff/inputoutput/#ann-field-vcf-output-files) for more information)
	- `feature_id`: the identifier of the feature (usually a transcript) associated with the annotation (see [SnpEff documentation on the ANN field](https://pcingola.github.io/SnpEff/snpeff/inputoutput/#ann-field-vcf-output-files) for more information)
	- `biotype`: the biotype of the transcript (e.g., coding) associated with the annotation (see [SnpEff documentation on the ANN field](https://pcingola.github.io/SnpEff/snpeff/inputoutput/#ann-field-vcf-output-files) for more information)
	- `consequence`: the protein change associated with the annotation (see [SnpEff documentation on the ANN field](https://pcingola.github.io/SnpEff/snpeff/inputoutput/#ann-field-vcf-output-files) for more information)

## Limitations and recommendations around usage:
- This workflow does not include any gff validation, beyond checking that the gff provided is a non-empty file that appears to contain lines with nine tab-delimited fields. It does not include any checks for CDS validity, protein sequence validity, phase accuracy, or expected feature hierarchy. It should be noted that while very egregious problems with an input gff will cause SnpEff to fail (e.g., complete absence of CDS feature annotations), other issues (e.g., inaccurate phase information) may manifest as inaccurate variant effect predictions. 
- This workflow does not support effect prediction for large structural variants (large indels, duplications, transversions, and translocations) produced by tools such as Manta. However, to ensure any relevant context is available for interpreting small variant effect predictions, it is recommended to also perform structural calling, followed by a check for proximity to small variants of interest in any cases where there is the potential for structural variants.
- The variant annotation window in this workflow is constrained to 5bp, with the goal of focusing specifically on variants in or immediately adjacent to protein-coding genes (i.e., most upstream/downstream and annotations will be excluded, as will intergenic annotations).
- The output report of this workflow does not necessarily include all relevant variant stats available in the vcf; users should consult the source vcf or the output annotated vcf for information such as variant allele frequency and genotype quality.

## Requirements:
Docker, Nextflow

## Usage:
### To run:
```
git clone https://github.com/alh38/simple_variant_annotation.git
cd simple_variant_annotation
docker build -t annotate_vars .
nextflow run main.nf -profile docker --fasta ref_seq.fna --gff ref_annotations.gff --vcf variants.vcf
```

### To run unit tests for the report generation functions:
```
docker run --entrypoint /bin/bash --rm -it annotate_vars
pytest
```

## Workflow overview:
1. `VALIDATE_INPUTS`: check that input files exist, are not empty, and appear to be in the expected formats (with no in-depth gff validation beyond checking that there is at least one row with nine tab-separated fields); decompress them if they are compressed
2. `ANNOTATE_VCF`: build a SnpEff database from the reference fasta and gff and use that database to annotate variants in vcf
3. `WRITE_REPORT`: parse annotated vcf to generate a user-friendly csv report with one line per variant allele
