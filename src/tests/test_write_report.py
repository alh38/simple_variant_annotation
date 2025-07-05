import pytest
from write_report import parse_ann_header, extract_snpeff_annotations


## helper classes to mimic pysam structures

class _AnnInfo:
    """
    Takes string and retuns object with string as description attribute 
    to mimic the structure of pysam VCF header INFO entry for ANN.
    """
    def __init__(self, description: str):
        self.description = description


class _Header:
    """Mimics a pysam.VariantHeader with only the parts we need."""
    def __init__(self, description: str | None = None):
        self.info = {}
        if description is not None:
            self.info["ANN"] = _AnnInfo(description)


class _Record:
    """Mimics a pysam.VariantRecord with the minimal API used by write_report."""
    def __init__(
        self,
        chrom: str,
        pos: int,
        ref: str,
        alts: list[str],
        qual: float,
        annotations: list[str],
    ) -> None:
        self.chrom = chrom
        self.pos = pos
        self.ref = ref
        self.alts = tuple(alts)
        self.qual = qual
        # the INFO field behaves like a dict in pysam
        self.info = {"ANN": annotations}


## fixtures

@pytest.fixture(scope="module")
def ann_description() -> str:
    """Return a realistic ANN header description line."""
    return (
        "Functional annotations: "
        "'Allele|Annotation|Gene_ID|Feature_ID|Transcript_BioType|HGVS.p'"
    )


@pytest.fixture(scope="module")
def ann_fields(ann_description):
    """Return a list of annotation field names parsed from a mock VCF header."""
    header = _Header(ann_description)
    return parse_ann_header(header)


## unit‑tests for parse_ann_header

def test_parse_ann_header_success(ann_description):
    """Should raise if parse_ann_header incorrectly parses a valid ANN description."""
    header = _Header(ann_description)
    fields = parse_ann_header(header)
    assert fields == [
        "Allele",
        "Annotation",
        "Gene_ID",
        "Feature_ID",
        "Transcript_BioType",
        "HGVS.p",
    ]


def test_parse_ann_header_missing_ann_field():
    """Should raise when the VCF header lacks a proper ANN definition."""
    header = _Header(description=None)  # no ANN entry.
    with pytest.raises(ValueError):
        parse_ann_header(header)


## unit‑tests for extract_snpeff_annotations

def test_extract_snpeff_annotations_single_alt(ann_fields):
    """Should raise if extract_snpeff_annotations incorrectly parses annotation string."""
    annotations = [
        # Allele|Annotation|Gene_ID|Feature_ID|Transcript_BioType|HGVS.p
        "A|missense_variant|gene1|tx1|protein_coding|p.Gly100Arg"
    ]
    rec = _Record("chr1", 100, "G", ["A"], 99.0, annotations)

    rows = extract_snpeff_annotations(rec, ann_fields)
    assert len(rows) == 1
    row = rows[0]

    # basic coordinate and allele checks
    assert row["CHROM"] == "chr1"
    assert row["POS"] == 100
    assert row["REF"] == "G"
    assert row["ALT"] == "A"

    # annotation fields
    assert row["annotation"] == "missense_variant"
    assert row["gene_id"] == "gene1"
    assert row["feature_id"] == "tx1"
    assert row["biotype"] == "protein_coding"
    assert row["consequence"] == "p.Gly100Arg"

def test_extract_snpeff_annotations_multi_alt(ann_fields):
    """Should raise if each ALT allele in a multi-allelic variant call doesn't get its own annotation row."""
    annotations = [
        # ALT A annotation
        "A|missense_variant|gene1|tx1|protein_coding|p.Gly100Arg",
        # ALT T annotation
        "T|synonymous_variant|gene1|tx1|protein_coding|p.Gly100Gly",
    ]
    rec = _Record("chr1", 100, "G", ["A", "T"], 80.0, annotations)

    rows = extract_snpeff_annotations(rec, ann_fields)
    assert len(rows) == 2

    # sort rows by ALT to make deterministic assertions
    rows_sorted = sorted(rows, key=lambda r: r["ALT"])

    # first ALT = A
    row_a = rows_sorted[0]
    assert row_a["ALT"] == "A"
    assert row_a["annotation"] == "missense_variant"
    assert row_a["consequence"] == "p.Gly100Arg"

    # second ALT = T
    row_t = rows_sorted[1]
    assert row_t["ALT"] == "T"
    assert row_t["annotation"] == "synonymous_variant"
    assert row_t["consequence"] == "p.Gly100Gly"


def test_extract_snpeff_annotations_field_mismatch_raises(ann_fields):
    """If the ANN string has too few or too many fields, an error is expected."""
    bad_ann = [
        # missing the HGVS.p component at the end
        "A|missense_variant|gene1|tx1|protein_coding"
    ]
    rec = _Record("chr1", 100, "G", ["A"], 99.0, bad_ann)

    with pytest.raises(ValueError):
        extract_snpeff_annotations(rec, ann_fields)
