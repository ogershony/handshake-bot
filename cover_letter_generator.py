# Local Imports
import constants as const

# Standard imports
import os

# External imports
from PyPDF2 import PdfReader
import markdown
from fpdf import FPDF
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain_community.vectorstores import Chroma
from langchain_classic.chains import RetrievalQA
from langchain_classic.text_splitter import (
    CharacterTextSplitter,
    RecursiveCharacterTextSplitter,
)


def generate_cover_letter(job_desc: str, job_id: int, config: dict) -> str:
    """
    Generates a custom cover letter based on the job description and returns the file path
    """
    resume_doc = load_resume(config)
    resume_doc.extend(text_to_doc_splitter(job_desc))

    documents = split_text_documents(resume_doc)

    collection_name = f"job_{job_id}"
    vectordb = Chroma.from_documents(
        documents,
        embedding=OpenAIEmbeddings(openai_api_key=os.getenv("OPENAI_API_KEY")),
        collection_name=collection_name,
    )

    pdf_qa = RetrievalQA.from_chain_type(
        ChatOpenAI(
            temperature=0.7,
            model_name="gpt-4.1-nano",
            openai_api_key=os.getenv("OPENAI_API_KEY"),
        ),
        retriever=vectordb.as_retriever(search_kwargs={"k": 6}),
        chain_type="stuff",
    )

    result = pdf_qa.run(const.COVER_LETTER_PROMPT)

    vectordb.delete_collection()

    cover_letter_dir = os.getenv("COVER_LETTER_PATH")
    os.makedirs(cover_letter_dir, exist_ok=True)
    file_path = os.path.join(cover_letter_dir, f"{job_id}.pdf")

    # Normalize Unicode characters that Helvetica (latin-1) can't render
    replacements = {
        "\u2018": "'", "\u2019": "'",   # smart single quotes
        "\u201c": '"', "\u201d": '"',   # smart double quotes
        "\u2013": "-", "\u2014": "--",  # en-dash, em-dash
        "\u2026": "...",                # ellipsis
        "\u00a0": " ",                  # non-breaking space
    }
    for orig, repl in replacements.items():
        result = result.replace(orig, repl)
    result = result.encode("latin-1", "replace").decode("latin-1")

    html_body = markdown.markdown(result)

    pdf = FPDF()
    pdf.set_margins(25, 25, 25)
    pdf.add_page()
    pdf.set_font("Helvetica", size=11)
    pdf.write_html(html_body)
    pdf.output(file_path)

    return file_path


def load_resume(config: dict) -> list[str]:
    """
    Loads the resume file from the specified path and returns the text content in chunks
    """
    pdf_reader = PdfReader(config[const.RESUME_PATH])
    text = ""
    for page in pdf_reader.pages:
        text += page.extract_text()

    document = text_to_doc_splitter(text)

    return document


def split_text_documents(docs: list):
    text_splitter = CharacterTextSplitter(chunk_size=1000, chunk_overlap=20)
    documents = text_splitter.split_documents(docs)
    return documents


def text_to_doc_splitter(text: str):
    spliiter = RecursiveCharacterTextSplitter(
        chunk_size=10000,
        chunk_overlap=0,
        length_function=len,
        add_start_index=True,
    )
    document = spliiter.create_documents([text])
    return document
