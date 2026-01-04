from pathlib import Path
from langchain_community.document_loaders import PyPDFLoader

def load_file(id: str) -> list:
    """
    Loads the pdf file from files directory and returns the document.
    """

    path = Path(__file__).parent.parent / "files" / f"{id}.pdf"
    loader = PyPDFLoader(path)

    docs = loader.load()
    return docs
