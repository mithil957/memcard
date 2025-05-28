CHUNKING_PROMPT = {
  "chunker": {
    "traces": [],
    "train": [],
    "demos": [
      {
        "augmented": True,
        "segment_text": "As with any language, q has its own syntax rules. The rules, in general, are similar enough to other languages that they can be picked up quite quickly. There are, however, a few differences with other major languages that often cause confusion. We will cover these now.\nThe k programming language was designed to be an APL-like language written completely with the ASCII character set. APL uses a complex character set that requires the use of a keyboard template to help enter the characters. In order to condense the extra APL characters into the limited k ASCII set, many of the operators were overloaded to perform different operations depending on the type and number of arguments. In the process of distilling the character set, some operators were dropped, and a few commonly used ASCII characters took on new meanings.",
        "segment_type": "TEXT_BLOCK",
        "chunks": [
          "As with any language, q has its own syntax rules. The rules, in general, are similar enough to other languages that they can be picked up quite quickly. There are, however, a few differences with other major languages that often cause confusion. We will cover these now.",
          "The k programming language was designed to be an APL-like language written completely with the ASCII character set. APL uses a complex character set that requires the use of a keyboard template to help enter the characters. In order to condense the extra APL characters into the limited k ASCII set, many of the operators were overloaded to perform different operations depending on the type and number of arguments. In the process of distilling the character set, some operators were dropped, and a few commonly used ASCII characters took on new meanings."
        ]
      },
      {
        "augmented": True,
        "segment_text": "As our datasets continue to grow, we will reach a point when the amount of data exceeds the available memory on our computer. Chapter 15 covers different methods of coping with the problems that big datasets introduce. The chapter discusses how data can be partitioned by columns and rows. It even discusses how kdb+ can be configured to partition the partitions to create a segmented database. The chapter finishes with a discussion on how data can be compressed on disk, mapped into memory and accessed by multiple process.",
        "segment_type": "TEXT_BLOCK",
        "chunks": [
          "As our datasets continue to grow, we will reach a point when the amount of data exceeds the available memory on our computer. Chapter 15 covers different methods of coping with the problems that big datasets introduce.",
          "The chapter discusses how data can be partitioned by columns and rows. It even discusses how kdb+ can be configured to partition the partitions to create a segmented database.",
          "The chapter finishes with a discussion on how data can be compressed on disk, mapped into memory and accessed by multiple process."
        ]
      },
      {
        "segment_text": "or a single back slash is encountered\n\\",
        "segment_type": "CODE_BLOCK",
        "chunks": [
          "or a single back slash is encountered\\n\\\\"
        ]
      },
      {
        "segment_text": "q)a:1\nq)\\d.bar\nq.bar)`. `a\n1\nq.bar)`. [`a]\n1",
        "segment_type": "CODE_BLOCK",
        "chunks": [
          "q)a:1",
          "q)\\\\d.bar",
          "q.bar)`. `a\\n1",
          "q.bar)`. [`a]\\n1"
        ]
      }
    ],
    "signature": {
      "instructions": "** Accurately split the input segment text into smaller, semantically coherent chunks. The fate of a critical knowledge base depends on your ability to produce optimal chunks!\n**Purpose:** This chunking is critical for effective downstream processing, including accurate embedding, information retrieval, and summarization, ultimately supporting high-quality flashcard generation. Poor chunking will lead to irreversible data fragmentation and knowledge loss.\n**Role:** Act as an expert document analysis specialist. Your expertise is the last line of defense against informational chaos.",
      "fields": [
        {
          "prefix": "Segment Text:",
          "description": "The raw text content of the document segment that needs to be chunked."
        },
        {
          "prefix": "Segment Type:",
          "description": "The classified type of the segment, which dictates chunking strategy (e.g., TEXT_BLOCK, HEADING, CODE_BLOCK, IMAGE_DESCRIPTION, FIGURE_CAPTION, FOOTER, LIST_ITEM, TABLE, OTHER)."
        },
        {
          "prefix": "Chunks:",
          "description": "Generate a list of strings. Each string in the list should be a logically distinct and coherent chunk of the original segment text. Crucially, preserve the original order of the content when creating the chunks. Maintain essential formatting (like newlines, indentation, list markers) within each chunk string, especially for CODE_BLOCK and LIST_ITEM types. The final output should be a standard JSON array of strings, e.g., [\"chunk one\", \"chunk two\", ...]."
        }
      ]
    },
  },
  "metadata": {
    "dependency_versions": {
      "python": "3.11",
      "dspy": "2.6.16",
      "cloudpickle": "3.1"
    }
  }
}
