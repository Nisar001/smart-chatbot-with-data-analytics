from langchain_core.documents import Document


def records_to_documents(dataset_name: str, rows: list[dict]) -> list[Document]:
    documents: list[Document] = []
    for index, row in enumerate(rows):
        content = "\n".join(f"{key}: {value}" for key, value in row.items())
        documents.append(
            Document(
                page_content=content,
                metadata={
                    "row_index": index,
                    "dataset_name": dataset_name,
                    "fields": list(row.keys()),
                },
            )
        )
    return documents
