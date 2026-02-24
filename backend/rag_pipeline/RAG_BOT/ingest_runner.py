from ingest import ingest_file

company_id = 1000
file_path = "/home/ubuntu/Downloads/Augmented_Reality_Overview.pdf"

if __name__ == "__main__":
    ingest_file(file_path, company_id)
