"""Example script for pushing the ARC mini dataset to Hugging Face Hub."""

from datasets import load_dataset

# Load the BIDS dataset
print("Loading BIDS dataset...")
ds = load_dataset('bids', data_dir="data/openneuro/ds004884-download", streaming=True)

print(f"Dataset loaded: {ds}")

ds.push_to_hub(
    repo_id="TobiasPitters/ds004884",
    commit_message="Add Aphasia Recovery Cohort (ARC) BIDS dataset",
    private=False,
    num_shards={"train": 500}  # Needed, otherwise I ran into OOM issues.
)

# After pushing, manually:
# 1. Go to the dataset page on HF Hub
# 2. Edit the README.md to add the dataset card from DATASET_CARD_TEMPLATE.md
# 3. Verify the citation and license info are correct

print("""
To push this dataset to the Hub:

1. Make sure you're logged in: `huggingface-cli login`

2. Uncomment and update the push_to_hub() call above with your username

3. Run this script

4. Add the dataset card from DATASET_CARD_TEMPLATE.md to the repo

Required metadata already included:
✓ License: CC0 (public domain)
✓ Citation: Gibson et al. 2024, Sci Data
✓ DOI: 10.18112/openneuro.ds004884.v1.0.2
✓ Authors: 8 authors listed
✓ Funding: 4 NIH grants
✓ Ethics: IRB approved, anonymized
""")
