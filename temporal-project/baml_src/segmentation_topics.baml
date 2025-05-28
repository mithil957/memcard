function IdentifyMultipleTopicBoundaries(segments: Segment[]) -> int[] {
  client GeminiFlash2

  prompt #"
    **ROLE:** Act as an expert structural analyst for a critical AI knowledge processing pipeline.
    **PURPOSE:** Your primary goal is to accurately identify the starting points of major thematic and structural sections within the provided text segments. This grouping is ESSENTIAL for downstream tasks like hierarchical summarization, accurate context retrieval for RAG systems, and effective knowledge structuring. Errors in identifying these major sections will lead to fragmented understanding and severely degrade the quality of the final knowledge base, potentially impacting significant research or project outcomes.
    **TASK:** Identify the starting point (**0-based index**) of every major **structural or thematic section** within this segment sequence. A new section begins when there's a significant shift in the primary subject matter OR when the document's organizational pattern fundamentally changes (e.g., moving from definitions to extended examples, or from problem setup to detailed solution).

    The input is a sequence of document segments provided in order. Analyze this entire sequence holistically.

    **Analysis Instructions:**
    1.  First, perform a preliminary analysis of the entire sequence to understand:
        *   The inferred high-level organization and logical flow.
        *   Recurring structural units or presentation patterns (e.g., repeating sequences of concept explanation -> code example -> output discussion).
        *   **Synthesize the core purpose or theme** of consecutive groups of segments to grasp the larger structure. This synthesis is key to avoiding premature splits.
    2.  Identify the `segment_number` (**0-based index within this sequence**) of the **first** segment that marks the beginning of each new major section, prioritizing based on this hierarchy:
        *   **MAJOR BOUNDARIES (Highest Priority):** Mark the start when there's a shift to a significantly different subject domain OR a fundamental change in the *type* or *purpose* of the content (e.g., finishing background theory and starting practical applications). These represent the most critical divisions.
        *   **MEDIUM BOUNDARIES:** Mark the start if the *approach* changes substantially (e.g., broad overview shifts to deep technical detail on the same general topic), representing a distinct new phase of discussion. Evaluate carefully if this truly constitutes a *major* section start for the project's purpose.
        *   **MINOR BOUNDARIES (Ignore):** Do *not* mark a start for simple elaborations, continuation of examples/lists, or new paragraphs discussing the same core point within the same approach. Incorrectly marking minor boundaries fragments crucial context.
    3.  The very first segment (segment number 0 relative to this sequence) always starts the first section.
    4.  Compile the `segment_number` (**0-based index**) values for the start of each identified **major section** into a single list of integers.

    **Specific Guidelines:**
    *   Evaluate segment types (e.g., `CODE_BLOCK`, `TEXT_BLOCK`, `LIST_ITEM`) based on their role *within the context* of surrounding segments. Resist splitting based on type alone; consider the functional relationship.
    *   Group segments forming a cohesive functional pattern together. Over-splitting these functional units is a critical error.
    *   A break in a *repeating structural pattern* is a stronger indicator of a potential major boundary than minor variations in content within that pattern.
    *   Focus on the **scale and significance** of the change relative to the overall document structure and the **purpose** of downstream knowledge processing. Only mark starts for genuinely new, high-level blocks.
    

    Input Sequence of Segments:
    ---
    {{ segments }}
    ---
    
    {{ ctx.output_format }}
  "#
}


test IdentifyMultipleBoundaries_ExpectedTrue {
  functions [IdentifyMultipleTopicBoundaries]
  args {
    segments [
      {
        segment_number 0
        segment_type TEXT_BLOCK
        segment_text "The installation directory also contains another file named s.k which is used to implement an SQL interface for ODBC clients. It also provides an example of how to define other languages on top of k."
      },
      {
        segment_number 1
        segment_type TEXT_BLOCK
        segment_text "On startup, the q binary must load the q.k file to pick up the q definitions. For the q binary to find this file, you must first set the QHOME environment variable to the full path of the directory holding q.k."
      },
      {
        segment_number 2
        segment_type TEXT_BLOCK
        segment_text "Once you have become more familiar with the q language, you can obtain a deeper understanding, and perhaps pick up a few coding pointers, by reading the q.k file."
      },
      {
        segment_number 3
        segment_type HEADING
        segment_text "Running q" 
      },
      {
        segment_number 4
        segment_type TEXT_BLOCK
        segment_text "Now that the binary is installed, and the QHOME environment variable is configured, we can start the kdb+ process. Here is an example of running q on my laptop. [1]"
      },
      {
        segment_number 5
        segment_type CODE_BLOCK
        segment_text "$ ./m32/q\nKDB+ 3.2 2015.03.04 Copyright (C) 1993-2015 Kx Systems\nm32/4() core 2048MB nick nicks-macbook.local 192.168.1.103 NONEXPIRE"
      },
      {
        segment_number 6
        segment_type TEXT_BLOCK
        segment_text "There are few points to highlight here. On the first line of the banner, the 3.2 refers to the kdb+ version. This is followed by the q binary release date. On the second line, the m32 matches the architecture used to start the binary..." // Truncated for brevity
      },
      {
        segment_number 7
        segment_type HEADING
        segment_text "Customization"
      },
      {
        segment_number 8
        segment_type TEXT_BLOCK
        segment_text "You can customize the q startup process by creating a file named q.q in the QHOME directory. This file, if it exists, is loaded after q.k but before the prompt is displayed."
      },
       {
        segment_number 9
        segment_type TEXT_BLOCK
        segment_text "This allows you to define custom functions or load additional libraries automatically upon startup."
      }
    ]
  }
}