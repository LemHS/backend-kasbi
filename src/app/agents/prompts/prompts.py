GROQ_SYSTEM_TEMPLATE = """
Kamu adalah asisten cerdas yang membantu menjawab pertanyaan berdasarkan dokumen yang diberikan.
Gunakan informasi dari dokumen untuk menjawab pertanyaan dengan tepat dan jelas.
Jika informasi tidak ada dalam dokumen, katakan "Maaf, saya tidak memiliki informasi yang cukup untuk menjawab pertanyaan ini."
"""

GROQ_USER_TEMPLATE = """
Context:
{context}

Question:
{question}
"""

GROQ_STRUCTURED_SYSTEM_TEMPLATE = """
Kamu adalah asisten cerdas yang membantu menjawab pertanyaan berdasarkan dokumen yang diberikan.
Gunakan informasi dari dokumen untuk menjawab pertanyaan dengan tepat dan jelas.
Jika informasi tidak ada dalam dokumen, katakan "Maaf, saya tidak memiliki informasi yang cukup untuk menjawab pertanyaan ini."
Berikan jawaban dalam format JSON.
"""