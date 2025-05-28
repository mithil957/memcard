function GenerateTopicSummary(segments: SegmentRaw[]) -> string {
    client GeminiFlash2
    
    prompt #"
    **Task:** Generate a very concise summary for a sequence of document segments that constitute a single topic. Avoid generic phrasing that could apply to multiple topics.
    **Purpose:** To capture the core theme or main idea of the topic block succinctly. This summary will later provide context within a RAG system and serve as a standalone topic identifier.
    **Role:** Act as an expert content analyst skilled at identifying the central concept of a text block and expressing it in a brief, informative phrase.
    
    **Summary Creation Guidelines:**
    1. Include key terminology or specific concepts that define the topic. Technical precision with domain-specific terms is essential for distinguishing between related concepts.
    2. Structure summaries consistently using established patterns appropriate to the content:
       - Action-oriented: '[Action]: [subject] and [purpose]'
       - Feature-focused: '[Component/Feature]: [primary function]'
       - Concept-centered: '[Concept]: [defining characteristics]'
    3. Prioritize terms and phrases users would likely search for when seeking this information. Focus on distinctive terminology that differentiates this topic from similar ones in the document.
    4. Adapt summary style based on content type: For procedural content, emphasize actions and methods; for conceptual content, emphasize definitions and relationships; for example-based content, indicate the illustrative purpose.
    5. Prioritize information density over grammatical completeness. Use noun phrases, specialized terminology, and precise verbs rather than complete sentences when appropriate.
    
    `segments`: {{ segments }}

    {{ ctx.output_format }}
    "#
}

function GenerateContextualTopicSummary(
    previous_topic_summary: string, 
    next_topic_summary: string, 
    segments: SegmentRaw[]) -> string {
    
    client GeminiFlash2

    prompt #"
    **Task:** Synthesize the core purpose and theme of the **current topic segments** into a highly concise and informative summary, leveraging the context of adjacent topic summaries.
    **Purpose:** This summary acts as a critical contextual header that represents the core content. Its quality directly determines how effectively the content can be identified, retrieved, and utilized.
    **Role:** Act as an expert document analyst and content writer specializing in semantic synthesis. You must distill the essence of content while understanding its structural role within the document flow.

    **Contextual Information:**
    - The `previous_topic_summary` describes the content immediately preceding this topic block.
    - The `next_topic_summary` describes the content immediately following this topic block.
    - Use these to understand the current topic's relationship to surrounding material - whether it builds on previous content, introduces new information, provides supporting details, or transitions to different subject matter.

    **Analysis & Synthesis Instructions:**
    1.  **Analyze Segments:** First, analyze the provided `topic_segments`. Identify the primary subject matter, key domain-specific terms, and the overall function (e.g., explaining a concept, providing examples, presenting evidence, describing processes).
    2.  **Synthesize Core Theme:** Determine the single most important idea or purpose represented by the *combination* of these segments.
    3.  **Incorporate Context:** Evaluate how the `previous_topic_summary` and `next_topic_summary` frame the current topic. Does the context suggest this topic is continuing an established thread, introducing a new concept, or serving as a bridge between related ideas? Let this inform the nuance of your summary.
    4.  **Generate Summary:** Create a single very concise summary (4-15 words) that:
        *   Accurately captures the core essence identified in step 2.
        *   Reflects the topic's role (using appropriate framing words if they add clarity, but always prioritizing conciseness and informativeness).
        *   Uses precise terminology found within the segments where possible.
        *   Is clear, unambiguous, and maximally useful for distinguishing this topic's content during retrieval. Avoid generic phrasing.
    
    **Note: The summary should be adaptable to the document's domain - whether technical documentation, academic text, narrative content, or instructional material. Use terminology and framing appropriate to the content's domain.
    **Content Type Guidance: Consider the type of content in the segments (conceptual explanations, procedural instructions, examples, definitions, etc.) and ensure the summary reflects the predominant content type.

    `previous_topic_summary`: {{ previous_topic_summary }}

    `next_topic_summary`: {{ next_topic_summary }}
    
    `topic_segments`: {{ segments }}

    {{ ctx.output_format }}
    "#
}

test InitialSummary {
    functions [GenerateTopicSummary]
    args {
        segments [
            {
                segment_type TEXT_BLOCK
                segment_text "The installation directory also contains another file named s.k which is used to implement an SQL interface for ODBC clients. It also provides an example of how to define other languages on top of k."
            },
            {
                segment_type TEXT_BLOCK
                segment_text "On startup, the q binary must load the q.k file to pick up the q definitions. For the q binary to find this file, you must first set the QHOME environment variable to the full path of the directory holding q.k."
            },
            {
                segment_type TEXT_BLOCK
                segment_text "Once you have become more familiar with the q language, you can obtain a deeper understanding, and perhaps pick up a few coding pointers, by reading the q.k file."
            },
            {
                segment_type HEADING
                segment_text "Running q" 
            },
            {
                segment_type TEXT_BLOCK
                segment_text "Now that the binary is installed, and the QHOME environment variable is configured, we can start the kdb+ process. Here is an example of running q on my laptop. [1]"
            },
            {
                segment_type CODE_BLOCK
                segment_text "$ ./m32/q\nKDB+ 3.2 2015.03.04 Copyright (C) 1993-2015 Kx Systems\nm32/4() core 2048MB nick nicks-macbook.local 192.168.1.103 NONEXPIRE"
            },
            {
                segment_type TEXT_BLOCK
                segment_text "There are few points to highlight here. On the first line of the banner, the 3.2 refers to the kdb+ version. This is followed by the q binary release date. On the second line, the m32 matches the architecture used to start the binary..." // Truncated for brevity
            },
            {
                segment_type HEADING
                segment_text "Customization"
            },
            {
                segment_type TEXT_BLOCK
                segment_text "You can customize the q startup process by creating a file named q.q in the QHOME directory. This file, if it exists, is loaded after q.k but before the prompt is displayed."
            },
            {
                segment_type TEXT_BLOCK
                segment_text "This allows you to define custom functions or load additional libraries automatically upon startup."
            }
        ]
    }
}

test ContextualSummary {
    functions [GenerateContextualTopicSummary]
    args {
        previous_topic_summary "N/A"
        next_topic_summary "N/A"
        segments [
            {
                segment_type TEXT_BLOCK
                segment_text "The installation directory also contains another file named s.k which is used to implement an SQL interface for ODBC clients. It also provides an example of how to define other languages on top of k."
            },
            {
                segment_type TEXT_BLOCK
                segment_text "On startup, the q binary must load the q.k file to pick up the q definitions. For the q binary to find this file, you must first set the QHOME environment variable to the full path of the directory holding q.k."
            },
            {
                segment_type TEXT_BLOCK
                segment_text "Once you have become more familiar with the q language, you can obtain a deeper understanding, and perhaps pick up a few coding pointers, by reading the q.k file."
            },
            {
                segment_type HEADING
                segment_text "Running q" 
            },
            {
                segment_type TEXT_BLOCK
                segment_text "Now that the binary is installed, and the QHOME environment variable is configured, we can start the kdb+ process. Here is an example of running q on my laptop. [1]"
            },
            {
                segment_type CODE_BLOCK
                segment_text "$ ./m32/q\nKDB+ 3.2 2015.03.04 Copyright (C) 1993-2015 Kx Systems\nm32/4() core 2048MB nick nicks-macbook.local 192.168.1.103 NONEXPIRE"
            },
            {
                segment_type TEXT_BLOCK
                segment_text "There are few points to highlight here. On the first line of the banner, the 3.2 refers to the kdb+ version. This is followed by the q binary release date. On the second line, the m32 matches the architecture used to start the binary..." // Truncated for brevity
            },
            {
                segment_type HEADING
                segment_text "Customization"
            },
            {
                segment_type TEXT_BLOCK
                segment_text "You can customize the q startup process by creating a file named q.q in the QHOME directory. This file, if it exists, is loaded after q.k but before the prompt is displayed."
            },
            {
                segment_type TEXT_BLOCK
                segment_text "This allows you to define custom functions or load additional libraries automatically upon startup."
            }
        ]
    }
}