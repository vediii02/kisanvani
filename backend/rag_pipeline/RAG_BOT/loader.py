import json
import pandas as pd
from pypdf import PdfReader


def load_pdf(path):
    reader = PdfReader(path)
    text = ""
    for page in reader.pages:
        text += page.extract_text() + "\n"
    return text


def load_excel(path):
    df = pd.read_excel(path)
    return df.to_string(index=False)


def load_json(path):
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    return json.dumps(data, indent=2)


def load_file(path,filename):
    if filename.endswith(".pdf"):
        return load_pdf(path)
    elif filename.endswith(".xlsx") or filename.endswith(".xls"):
        return load_excel(path)
    elif filename.endswith(".json"):
        return load_json(path)
    else:
        raise ValueError("Unsupported file format")
