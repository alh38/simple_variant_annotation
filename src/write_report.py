import csv
import argparse
import pysam

def parse_ann_header(header):
    """Extract the fields from the ANN header line in a VCF file."""
    info = header.info.get('ANN')
    if not info or 'Functional annotations:' not in info.description:
        raise ValueError("VCF header does not contain a valid ANN field definition from SnpEff.")
    desc = info.description
    fields_line = desc.split("Functional annotations: '")[-1].rstrip("'>")
    return fields_line.split('|')

def extract_snpeff_annotations(record, ann_fields):
    results = []
    for alt in record.alts:
        matching_parts = None
        # ANN comma-separated list of annotation strings, where each string 
        # is a pipe-delimited set of fields describing one annotation for the variant
        for ann in record.info.get("ANN", []):
            parts = ann.split("|")
            if parts and parts[0] == alt:
                matching_parts = parts
                break                 # stop once we’ve found the right ANN

        if matching_parts is None:
            continue

        # ensure annotation has the expected number of fields
        if len(matching_parts) != len(ann_fields):
            raise ValueError(
                f"ANN field for ALT {alt!r} has {len(matching_parts)} components; "
                f"expected {len(ann_fields)}"
            )

        # remove any leading/trailing whitespace from keys before creating dict
        ann_dict = {k.strip(): v for k, v in zip(ann_fields, matching_parts)}
        results.append(
            {
                "CHROM": record.chrom,
                "POS": record.pos,
                "REF": record.ref,
                "ALT": alt,
                "QUAL": record.qual,
                "annotation": ann_dict.get("Annotation", ""),
                "gene_id": ann_dict.get("Gene_ID", ""),
                "feature_id": ann_dict.get("Feature_ID", ""),
                "biotype": ann_dict.get("Transcript_BioType", ""),
                "consequence": ann_dict.get("HGVS.p", ""),
            }
        )
    return results


def main():
    parser = argparse.ArgumentParser(description="Write csv report from SnpEff annotated VCF")
    parser.add_argument('--vcf', help='Input VCF annotated with snpEff', required=True)
    parser.add_argument('--output', help='Output CSV file', required=True)
    args = parser.parse_args()

    vcf = pysam.VariantFile(args.vcf)
    ann_fields = parse_ann_header(vcf.header)

    with open(args.output, 'w', newline='') as out_csv:
        writer = csv.DictWriter(out_csv, fieldnames=[
            'CHROM', 'POS', 'REF', 'ALT', 'QUAL',
            'annotation', 'gene_id', 'feature_id', 'biotype', 'consequence'
        ])
        writer.writeheader()

        for record in vcf.fetch():
            rows = extract_snpeff_annotations(record, ann_fields)
            for row in rows:
                writer.writerow(row)

if __name__ == '__main__':
    main()
