function GenerateDocumentSummary(topic_summaries: string[]) -> string {
    client GeminiFlash2
    
    prompt #"
    **Task:** Generate a holistic, high-level overview of an entire document by synthesizing the sequence of topic summaries.
    **Purpose:** To create a concise summary that captures the document's core subject matter, essential structure, and potentially its underlying themes, purpose, or unique characteristics, suitable for understanding the document's essence at a glance.
    **Role:** Act as an expert Abstract Writer or Senior Editor, skilled at discerning the fundamental nature and flow of a document from its structural components (represented here by topic summaries).

    **Instructions:**
    1.  **Analyze Input Sequence:** The input `topic summaries` is a single string containing an ordered sequence of short summaries. Each summary represents the core idea of a consecutive section or topic within the original document. Treat this sequence as a structured outline or skeleton of the full document.
    2.  **Identify Core Subject & Key Concepts:** Read through the entire sequence to determine the primary subject(s) the document addresses. Identify any recurring or central concepts, terms, or ideas mentioned across multiple topic summaries.
    3.  **Determine Overall Structure & Flow:** Based on the *order* and *nature* of the topic summaries, infer the document's high-level organization. Is it chronological, thematic, comparative, problem-solution, foundational-to-advanced, narrative-driven, etc.? Describe this flow conceptually.
    4.  **Infer Purpose & Themes (Where Possible):** Examine the collective message of the summaries. Can you infer the likely purpose of the document (e.g., to inform, persuade, guide, entertain)? Are there underlying themes (e.g., innovation, conflict, methodology, analysis) suggested by the topics covered?
    5.  **Note Unique Characteristics (Where Evident):** Do the topic summaries suggest any unique features of the document, such as a specific methodology being detailed, a recurring element (like case studies or specific named tips), or a central project being developed?
    6.  **Synthesize Overview Paragraph:** Combine these insights into a single, coherent paragraph (aiming for 75-175 words). This paragraph should:
        *   Clearly state the main subject matter.
        *   Briefly describe the document's structure or progression of ideas.
        *   Touch upon key concepts or themes identified.
        *   Mention any inferred purpose or unique characteristics if strongly suggested by the input.
    7.  **Focus on Synthesis, Not Listing:** Do *not* simply enumerate the individual topic summaries. Weave the insights into a narrative that describes the *document as a whole*.
    8.  **Maintain Generality:** Apply this analysis process regardless of whether the original document seems to be fiction, non-fiction, technical, or narrative. Base the summary *strictly* on the provided topic summaries.
    
    `topic summaries`: {{ topic_summaries }}

    {{ ctx.output_format }}
    "#
}