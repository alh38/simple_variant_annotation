#!/usr/bin/env nextflow

nextflow.enable.dsl = 2

process VALIDATE_INPUTS {
    tag "validate_inputs"

    input:
    path fasta_file
    path gff_file
    path vcf_file

    output:
    tuple path('ref.fa'), path('annotations.gff'), path('variants.vcf'), emit: validated_ch

    script:
    """
    python3 /app/src/validate_inputs.py \
      --fasta ${fasta_file} \
      --gff   ${gff_file} \
      --vcf   ${vcf_file}
    """
}

process ANNOTATE_VCF {
    tag "annotate_vcf"

    input:
    tuple path(ref_fa), path(ann_gff), path(var_vcf)

    publishDir params.publish_dir, mode: 'copy'

    output:
    path("variants.ann.vcf"), emit: ann_vcf_ch

    script:
    """
    python3 /app/src/run_snpeff.py \
      --fasta ${ref_fa} \
      --gff   ${ann_gff} \
      --vcf   ${var_vcf} \
      --output_vcf variants.ann.vcf \
      --snpeff_dir /app/snpEff/
    """
}

process WRITE_REPORT {
    tag "write_report"

    input:
    path ann_vcf_file

    publishDir params.publish_dir, mode: 'copy'

    output:
    path("report.csv")

    script:
    """
    python3 /app/src/write_report.py \
      --vcf ${ann_vcf_file} \
      --output report.csv
    """
}

workflow {
    // input channels
    gff_file   = Channel.fromPath(params.gff)
    fasta_file = Channel.fromPath(params.fasta)
    vcf_file   = Channel.fromPath(params.vcf)

    // lightly validate and decompress inputs and normalize file names
    validated_ch = VALIDATE_INPUTS(fasta_file, gff_file, vcf_file)

    // feed those into annotation
    ann_vcf_ch = ANNOTATE_VCF(validated_ch)

    // generate csv report
    WRITE_REPORT(ann_vcf_ch)
}
