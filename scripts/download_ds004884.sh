# download aws cli first
# take care, this will load 250GB of data
aws s3 sync --no-sign-request s3://openneuro.org/ds004884 ds004884-download/

