def get_default_prompt(context: str,query: str):
    return f"""
        Context:
        {context}

        Question:
        {query}
        """

def get_default_system_prompt():
    return  "Use the provided context to answer the following question. If the context does not contain enough information, respond with 'I don't know.'"
