class Chunk {
  chunk_text string @description("A sub-segment of text representing a coherent unit of information.")
}

class DemoExample {
  segment_type SegmentType @description("The type of the content in this segment.")
  segment_text string @description("The extracted text content of the segment, or a description if it's an image.")
  chunks Chunk[]
}

class DemoExampleV2 {
  segment_type SegmentType @description("The type of the content in this segment.")
  segment_text string @description("The extracted text content of the segment, or a description if it's an image.")
  chunks string[]
}

template_string RenderDemoExample(demo: DemoExample) #"
  Segment Type: {{ demo.segment_type }}
  Segment Text:
  ---
  {{ demo.segment_text }}
  ---
  {{ demo.chunks }}
  --- End Example ---
"#

template_string RenderDemoExampleV2(demo: DemoExampleV2) #"
  Segment Type: {{ demo.segment_type }}
  Segment Text:
  ---
  {{ demo.segment_text }}
  ---
  {{ demo.chunks }}
  --- End Example ---
"#

function ChunkSegment(instruction_text: string, demos: DemoExample[], input_segment: SegmentRaw) -> Chunk[] {
  client GeminiFlash2

  prompt #"
    {{ instruction_text }}

    --- Few-Shot Examples ---
    {% for demo in demos %}
      {{ RenderDemoExample(demo) }}
    {% endfor %}

    --- Current Task ---
    Segment Type: {{ input_segment.segment_type }}
    Segment Text:
    ---
    {{ input_segment.segment_text }}
    ---

    {{ ctx.output_format }}
  "#
}

function ChunkSegmentV2(instruction_text: string, demos: DemoExampleV2[], input_segment: SegmentRaw) -> string[] {
  client GeminiFlash2

  prompt #"
    {{ instruction_text }}

    --- Few-Shot Examples ---
    {% for demo in demos %}
      {{ RenderDemoExampleV2(demo) }}
    {% endfor %}

    --- Current Task ---
    Segment Type: {{ input_segment.segment_type }}
    Segment Text:
    ---
    {{ input_segment.segment_text }}
    ---

    {{ ctx.output_format }}
  "#
}




test TestChunkTextBlockMultiSentence {
  functions [ChunkSegment]
  args {
    instruction_text #"
      ** Decompose the provided segment text into semantically meaningful chunks, optimized for downstream tasks like embedding and summarization.
      **Purpose:** High-quality chunking ensures effective information retrieval and accurate flashcard generation.
      **Role:** You are an expert in document structure and semantic analysis. Carefully consider the 'Segment Type' to guide your chunking strategy. For example, preserve code structure in 'CODE_BLOCK' segments and list formatting in 'LIST_ITEM' segments. Maintain original formatting (newlines, indentation, list markers) within each chunk.
    "#
    demos [
      {
        segment_type TEXT_BLOCK
        segment_text "This forms the foundation of meta-programming and is used in the section called \"Instrumenting Functions\" to dynamically redefine the definition of functions."
        // Define the 'chunks' list for this demo
        chunks [
          {
            chunk_text "This forms the foundation of meta-programming and is used in the section called \"Instrumenting Functions\" to dynamically redefine the definition of functions."
          }
        ]
      },
      {
        segment_type HEADING
        segment_text "Q Tip 2.3. Include sample code in your source files"
        chunks [
          {
            chunk_text "Q Tip 2.3. Include sample code in your source files"
          }
        ]
      }
    ]
    input_segment {
      segment_type TEXT_BLOCK
      segment_text "The first principle is encapsulation. It involves bundling data and methods within a class. The second principle is inheritance, allowing classes to inherit properties. Polymorphism is the third principle, enabling objects to take multiple forms."
    }
  }
}

test TestChunkTextBlockMultiSentenceV2 {
  functions [ChunkSegmentV2]
  args {
    instruction_text #"
      ** Decompose the provided segment text into semantically meaningful chunks, optimized for downstream tasks like embedding and summarization.
      **Purpose:** High-quality chunking ensures effective information retrieval and accurate flashcard generation.
      **Role:** You are an expert in document structure and semantic analysis. Carefully consider the 'Segment Type' to guide your chunking strategy. For example, preserve code structure in 'CODE_BLOCK' segments and list formatting in 'LIST_ITEM' segments. Maintain original formatting (newlines, indentation, list markers) within each chunk.
    "#
    demos [
      {
        segment_type TEXT_BLOCK
        segment_text "This forms the foundation of meta-programming and is used in the section called \"Instrumenting Functions\" to dynamically redefine the definition of functions."
        // Define the 'chunks' list for this demo
        chunks [
          
            "This forms the foundation of meta-programming and is used in the section called \"Instrumenting Functions\" to dynamically redefine the definition of functions."
          
        ]
      },
      {
        segment_type HEADING
        segment_text "Q Tip 2.3. Include sample code in your source files"
        chunks [
          
             "Q Tip 2.3. Include sample code in your source files"
          
        ]
      }
    ]
    input_segment {
      segment_type TEXT_BLOCK
      segment_text "The first principle is encapsulation. It involves bundling data and methods within a class. The second principle is inheritance, allowing classes to inherit properties. Polymorphism is the third principle, enabling objects to take multiple forms."
    }
  }
}
